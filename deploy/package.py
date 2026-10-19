"""Build an allowlisted deployment artifact without credentials or editorial uploads."""
import argparse
import io
import json
import re
import tarfile
from pathlib import Path

if __package__:
    from .assets import MANIFEST, inventory, validate_manifest
else:
    from assets import MANIFEST, inventory, validate_manifest

ROOTS = ('boutique', 'config', 'templates', 'static', 'deploy')
FILES = ('manage.py', 'requirements.txt', 'requirements-hosting.txt', 'content/catalog.json')


def build(root, output, revision, base_manifest=None):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Expected a full commit SHA')
    base = validate_manifest(base_manifest) if base_manifest is not None else {}
    manifest = inventory(root / 'static')
    reused = 0
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
                    if relative.parts[0] == 'static':
                        key = item.relative_to(root / 'static').as_posix()
                        if base.get(key) == manifest['files'][key]:
                            reused += 1
                            continue
                    archive.add(item, arcname=str(relative), recursive=False)
        for name, data in [('REVISION', (revision + '\n').encode()),
                           (MANIFEST, json.dumps(manifest, sort_keys=True).encode())]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    print(f'Archive: {output.stat().st_size:,} bytes; static sent: '
          f'{len(manifest["files"]) - reused}, reused: {reused}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('revision')
    parser.add_argument('output', type=Path)
    parser.add_argument('--base-manifest', type=Path)
    args = parser.parse_args()
    base = json.loads(args.base_manifest.read_text()) if args.base_manifest else None
    build(Path(__file__).resolve().parent.parent, args.output, args.revision, base_manifest=base)
