"""Forced SSH command for the CI key: accept a release, never a shell command."""
import os
from pathlib import Path
import re
import shutil
import sys

APP = Path('/var/www/u3688705/data/apps/colibri')
MAX_ARCHIVE = 512 * 1024 * 1024


def command(value):
    match = re.fullmatch(r'(deploy|check) ([0-9a-f]{40}) ([0-9]+-[0-9]+)', value)
    if not match:
        raise ValueError('Only deploy/check <commit-sha> <run-id>-<attempt> is permitted')
    return match.groups()


def receive(source, target, limit=MAX_ARCHIVE):
    count = 0
    with target.open('xb') as output:
        while chunk := source.read(1024 * 1024):
            count += len(chunk)
            if count > limit:
                raise ValueError('Release archive exceeds size limit')
            output.write(chunk)
    if count == 0:
        raise ValueError('Empty release archive')


if __name__ == '__main__':
    # SSH_ORIGINAL_COMMAND is data, never passed to a shell.
    try:
        mode, revision, run_id = command(os.environ.get('SSH_ORIGINAL_COMMAND', ''))
        os.umask(0o077)
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
