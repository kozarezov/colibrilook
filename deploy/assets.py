"""Hash public static files and safely reconstruct incremental release assets."""
import hashlib
import json
from pathlib import PurePosixPath
import re
import shutil

MANIFEST = 'STATIC_MANIFEST.json'


def validate_manifest(value):
    if (not isinstance(value, dict) or value.get('version') != 1
            or not isinstance(value.get('files'), dict) or len(value['files']) > 10000):
        raise ValueError('Invalid static manifest')
    for name, digest in value['files'].items():
        path = PurePosixPath(name)
        if (not name or not path.parts or path.is_absolute() or str(path) != name
                or any(p.startswith('.') or p == '__pycache__' for p in path.parts)
                or '\\' in name or any(ord(c) < 32 for c in name)
                or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
            raise ValueError(f'Invalid static manifest entry: {name!r}')
    return value['files']


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def static_path(root, name):
    path = root
    if root.is_symlink():
        raise ValueError('Symlinked static root is not allowed')
    for part in PurePosixPath(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f'Symlinked static asset is not allowed: {name}')
    return path


def inventory(root):
    files = {}
    if root.is_symlink():
        raise ValueError('Symlinked static root is not allowed')
    for path in sorted(root.rglob('*')):
        name = path.relative_to(root).as_posix()
        if any(p.startswith('.') or p == '__pycache__' for p in PurePosixPath(name).parts):
            continue
        static_path(root, name)
        if path.is_file():
            files[name] = digest(path)
    result = {'version': 1, 'files': files}
    validate_manifest(result)
    return result


def restore(release, previous=None):
    manifest = release / MANIFEST
    if not manifest.exists():
        return  # Existing full-archive workflows remain compatible.
    if manifest.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('Static manifest exceeds size limit')
    files = validate_manifest(json.loads(manifest.read_text()))
    supplied = inventory(release / 'static')['files']
    if supplied.keys() - files.keys():
        raise ValueError('Uploaded static files are missing from manifest')
    reused = 0
    total = 0
    for name, expected in files.items():
        target = static_path(release / 'static', name)
        if not target.exists():
            if previous is None:
                raise ValueError(f'Missing static asset with no base release: {name}')
            source = static_path(previous / 'static', name)
            if not source.is_file():
                raise ValueError(f'Missing base static asset: {name}; rebuild with a fresh manifest')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            reused += 1
        total += target.stat().st_size
        if total > 1024 * 1024 * 1024:
            raise ValueError('Reconstructed static exceeds 1 GiB')
        if digest(target) != expected:
            raise ValueError(f'Corrupt or stale static asset: {name}; rebuild with a fresh manifest')
    print(f'Static verified: {len(files)} files, {reused} reused locally', flush=True)
