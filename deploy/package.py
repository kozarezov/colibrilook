"""Build an allowlisted deployment artifact without credentials or editorial uploads."""
import argparse
import re
import tarfile
from pathlib import Path

ROOTS = ('boutique', 'config', 'templates', 'static', 'deploy')
FILES = ('manage.py', 'requirements.txt', 'requirements-hosting.txt', 'content/catalog.json')


def build(root, output, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Expected a full commit SHA')
    with tarfile.open(output, 'w:gz') as archive:
        for name in (*ROOTS, *FILES):
            path = root / name
            paths = sorted(path.rglob('*')) if path.is_dir() else [path]
            for item in paths:
                relative = item.relative_to(root)
                if any(p.startswith('.') or p == '__pycache__' for p in relative.parts):
                    continue
                if item.is_symlink():
                    raise ValueError(f'Symlink is not allowed: {relative}')
                if item.is_file():
                    archive.add(item, arcname=str(relative), recursive=False)
        import io
        data = (revision + '\n').encode()
        info = tarfile.TarInfo('REVISION')
        info.size = len(data)
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(data))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('revision')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(Path(__file__).resolve().parent.parent, args.output, args.revision)
