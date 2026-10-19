"""Forced SSH command for the CI key: accept a release, never a shell command."""
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time

APP = Path('/var/www/u3688705/data/apps/colibri')
MAX_ARCHIVE = 512 * 1024 * 1024


def command(value):
    if value == 'manifest':
        return ('manifest', None, None)
    match = re.fullmatch(r'(deploy|check) ([0-9a-f]{40}) ([0-9]+-[0-9]+)', value)
    if not match:
        raise ValueError('Only manifest or deploy/check <commit-sha> <run-id>-<attempt> is permitted')
    return match.groups()


def receive(source, target, limit=MAX_ARCHIVE):
    count = 0
    started = last_report = time.monotonic()
    print('Receiving release archive', file=sys.stderr, flush=True)
    with target.open('xb') as output:
        while chunk := source.read(1024 * 1024):
            count += len(chunk)
            if count > limit:
                raise ValueError('Release archive exceeds size limit')
            output.write(chunk)
            if time.monotonic() - last_report >= 15:
                print(f'Received {count:,} bytes', file=sys.stderr, flush=True)
                last_report = time.monotonic()
    if count == 0:
        raise ValueError('Empty release archive')
    print(f'Received {count:,} bytes in {time.monotonic() - started:.1f}s',
          file=sys.stderr, flush=True)


if __name__ == '__main__':
    # SSH_ORIGINAL_COMMAND is data, never passed to a shell.
    try:
        mode, revision, run_id = command(os.environ.get('SSH_ORIGINAL_COMMAND', ''))
        os.umask(0o077)
        if mode == 'manifest':
            from assets import inventory
            with (APP / '.deploy.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_SH)
                current = (APP / 'current').resolve() if (APP / 'current').is_symlink() else APP
                print(json.dumps(inventory(current / 'static'), sort_keys=True))
            sys.exit(0)
        incoming = APP / 'incoming' / f'{revision}-{run_id}'
        incoming.mkdir(parents=True, exist_ok=False)
        archive = incoming / 'release.tar.gz'
        receive(sys.stdin.buffer, archive)
        # The deployment controller is installed by the operator, not executed from the upload.
        from release import deploy
        deploy(archive, revision, run_id, check_only=(mode == 'check'))
        shutil.rmtree(incoming)
    except Exception as error:
        print(f'Deployment rejected or failed: {error}', file=sys.stderr)
        sys.exit(1)
