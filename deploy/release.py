"""Deploy a tested artifact on REG.RU. Never seed or replace editorial data."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import tarfile
import tempfile
import time
import urllib.request

if __package__:
    from .assets import MANIFEST, restore
else:
    from assets import MANIFEST, restore

APP = Path('/var/www/u3688705/data/apps/colibri')
PUBLIC = Path('/var/www/u3688705/data/www/colibrilook.ru')
PYTHON = '/opt/python/python-3.14/bin/python3'
ROOTS = {'boutique', 'config', 'templates', 'static', 'deploy'}
FILES = {'manage.py', 'requirements.txt', 'requirements-hosting.txt', 'content/catalog.json', 'REVISION'}


def unpack(archive, destination, revision, previous=None):
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or not path.parts
                    or any(p.startswith('.') or p == '__pycache__' for p in path.parts)
                    or not member.isfile()
                    or not (path.parts[0] in ROOTS or member.name in FILES | {MANIFEST})):
                raise ValueError(f'Unsafe archive member: {member.name}')
        if sum(m.size for m in members) > 1024 * 1024 * 1024:
            raise ValueError('Artifact exceeds 1 GiB unpacked')
        bundle.extractall(destination, members=members, filter='data')
    if (destination / 'REVISION').read_text().strip() != revision:
        raise ValueError('Artifact revision mismatch')
    for required in FILES:
        if not (destination / required).is_file():
            raise ValueError(f'Missing required file: {required}')
    restore(destination, previous)


def link(target, name):
    temporary = name.with_name(name.name + '.next')
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target)
    os.replace(temporary, name)


def restart(public):
    (public / 'tmp').mkdir(exist_ok=True)
    (public / 'tmp/restart.txt').touch()
    (public / '.restart-app').touch()


def healthy(revision, timeout=90):
    # REG.RU Apache is bound to loopback behind nginx. No public TLS bypass.
    request = urllib.request.Request('http://127.0.0.1:8080/healthz/', headers={
        'Host': 'colibrilook.ru', 'X-Forwarded-Proto': 'https', 'Cache-Control': 'no-cache'})
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                result = json.load(response)
            if result.get('status') == 'ok' and result.get('revision') == revision:
                for path in ('/', '/catalog/', '/admin/login/', '/static/css/site.css'):
                    check = urllib.request.Request('http://127.0.0.1:8080' + path,
                                                   headers=dict(request.header_items()))
                    with urllib.request.urlopen(check, timeout=5) as page:
                        if page.status != 200:
                            raise ValueError('Page check failed')
                return True
        except (OSError, ValueError):
            pass
        time.sleep(2)
    return False


def activate(app, public, release, revision, probe=healthy):
    current = app / 'current'
    previous = current.resolve() if current.is_symlink() else None
    static = public / 'static'
    previous_static = static.resolve() if static.is_symlink() else None
    if static.exists() and not static.is_symlink():
        raise RuntimeError('Public static path must be a symlink; refusing to replace a directory')
    if current.exists() and not current.is_symlink():
        raise RuntimeError('Current release must be a symlink')
    try:
        link(release, current)
        link(release / 'staticfiles', static)
        restart(public)
        if not probe(revision):
            raise RuntimeError('New release failed the database/revision health check')
    except BaseException:
        if previous is None:
            current.unlink(missing_ok=True)
        else:
            link(previous, current)
        if previous_static is not None:
            link(previous_static, static)
        else:
            static.unlink(missing_ok=True)
        restart(public)
        print('Previous code/static links restored. Database migrations were NOT rolled back.', flush=True)
        raise


def install_and_activate(app, public, release, revision, probe=healthy):
    startup = public / 'passenger_wsgi.py'
    original = startup.read_bytes()
    temporary = public / 'passenger_wsgi.py.next'
    try:
        shutil.copyfile(release / 'deploy/passenger_wsgi.py', temporary)
        temporary.chmod(0o644)
        os.replace(temporary, startup)
        activate(app, public, release, revision, probe=probe)
    except BaseException:
        temporary.write_bytes(original)
        temporary.chmod(0o644)
        os.replace(temporary, startup)
        restart(public)
        raise


def backup_database(config, destination):
    # Credentials never appear in argv or logs. The dump is a consistent InnoDB snapshot.
    lines = ['[client]']
    for key, source in [('user', 'DATABASE_USER'), ('password', 'DATABASE_PASSWORD'),
                        ('host', 'DATABASE_HOST'), ('port', 'DATABASE_PORT')]:
        value = config.get(source, {'host': 'localhost', 'port': '3306'}.get(key, ''))
        lines.append(f'{key}={json.dumps(str(value))}')
    with tempfile.NamedTemporaryFile(mode='w', prefix='mysql-', dir=destination.parent) as option:
        option.write('\n'.join(lines) + '\n')
        option.flush()
        command = ['mysqldump', f'--defaults-extra-file={option.name}', '--single-transaction',
                   '--quick', '--no-tablespaces', '--set-gtid-purged=OFF', config['DATABASE_NAME']]
        with tempfile.TemporaryFile() as errors, gzip.open(destination, 'wb') as output:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors)
            try:
                shutil.copyfileobj(process.stdout, output)
                process.stdout.close()
                if process.wait() != 0:
                    raise RuntimeError('MySQL backup failed; deployment stopped before migrations')
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
    destination.chmod(0o600)


def deploy(archive, revision, run_id, check_only=False):
    def interrupted(signum, frame):
        raise RuntimeError(f'Deployment interrupted by signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    os.umask(0o077)
    APP.mkdir(exist_ok=True)
    with (APP / '.deploy.lock').open('w') as lock:
        print('Waiting for deployment lock', flush=True)
        fcntl.flock(lock, fcntl.LOCK_EX)
        releases = APP / 'releases'
        releases.mkdir(exist_ok=True)
        release = releases / f'{revision}-{run_id}'
        if release.exists():
            raise RuntimeError('Release already exists; rerun with a new attempt ID')
        release.mkdir()
        print('Preparing release and verifying static assets', flush=True)
        previous = (APP / 'current').resolve() if (APP / 'current').is_symlink() else APP
        unpack(archive, release, revision, previous=previous)
        config = json.loads((APP / 'production.json').read_text())
        if config.get('DATABASE_ENGINE') != 'mysql':
            raise RuntimeError('This deployment requires the configured production MySQL database')
        env = dict(os.environ, DJANGO_ENV_FILE=str(APP / 'production.json'),
                   DJANGO_MEDIA_ROOT=str(APP / 'media'), PYTHONDONTWRITEBYTECODE='1')
        def run(*args):
            print('Running:', ' '.join(args), flush=True)
            subprocess.run(args, cwd=release, env=env, check=True)
        run(PYTHON, '-m', 'venv', str(release / '.venv'))
        python = str(release / '.venv/bin/python')
        run(python, '-m', 'pip', 'install', '-r', 'requirements-hosting.txt')
        run(python, 'manage.py', 'check', '--deploy', '--fail-level', 'WARNING')
        run(python, 'manage.py', 'makemigrations', '--check', '--dry-run')
        run(python, 'manage.py', 'collectstatic', '--noinput')
        if check_only:
            run(python, 'manage.py', 'migrate', '--plan')
            archive.unlink()
            shutil.rmtree(release)
            print('PREFLIGHT PASSED: no migrations applied; live release unchanged', flush=True)
            return
        backups = APP / 'backups' / release.name
        backups.mkdir(parents=True)
        backup_database(config, backups / 'database.sql.gz')
        with tarfile.open(backups / 'media.tar.gz', 'w:gz') as tar:
            tar.add(APP / 'media', arcname='media')
        print('Backups saved:', backups, flush=True)
        # MySQL DDL is not transactional. Only backward-compatible migrations belong
        # in automatic deployment; failed DDL requires operator review, not auto-restore.
        run(python, 'manage.py', 'migrate', '--noinput')
        # nginx serves assets as a separate user; release assets must be traversable.
        for folder in (releases, release, release / 'staticfiles'):
            folder.chmod(0o755)
        for folder, dirs, files in os.walk(release / 'staticfiles'):
            Path(folder).chmod(0o755)
            for name in files:
                (Path(folder) / name).chmod(0o644)
        install_and_activate(APP, PUBLIC, release, revision)
        (APP / 'DEPLOYED_REVISION').write_text(revision + '\n')
        archive.unlink()
        print('DEPLOYED', revision, flush=True)
        # Retain three releases and three backup snapshots; preserve active release.
        for directory in (releases, APP / 'backups'):
            items = sorted((p for p in directory.iterdir() if p.is_dir()),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            for old in items[3:]:
                if old.resolve() != (APP / 'current').resolve():
                    shutil.rmtree(old)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('revision')
    parser.add_argument('run_id')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.revision) or not re.fullmatch(r'[0-9]+-[0-9]+', args.run_id):
        parser.error('Invalid commit SHA or run-attempt ID')
    deploy(args.archive.resolve(), args.revision, args.run_id)
