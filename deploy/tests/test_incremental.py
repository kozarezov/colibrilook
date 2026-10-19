import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from deploy.package import build
from deploy.release import unpack

SHA = 'b' * 40


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'
        self.previous = self.root / 'previous'
        self.candidate = self.root / 'candidate'
        self.archive = self.root / 'release.tar.gz'
        for name in ('manage.py', 'requirements.txt', 'requirements-hosting.txt',
                     'content/catalog.json', 'static/keep.mp4', 'static/change.css'):
            self.write(self.source / name, b'original')
        for folder in ('boutique', 'config', 'templates', 'deploy'):
            (self.source / folder).mkdir()
        self.write(self.previous / 'static/keep.mp4', b'original')
        self.write(self.previous / 'static/change.css', b'original')
        self.write(self.previous / 'static/deleted.jpg', b'deleted')
        self.manifest = {'version': 1, 'files': {
            'keep.mp4': hashlib.sha256(b'original').hexdigest(),
            'change.css': hashlib.sha256(b'original').hexdigest(),
            'deleted.jpg': hashlib.sha256(b'deleted').hexdigest(),
        }}

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def make_incremental(self):
        build(self.source, self.archive, SHA, base_manifest=self.manifest)
        self.candidate.mkdir()
        unpack(self.archive, self.candidate, SHA, previous=self.previous)

    def test_sends_only_changed_assets_and_reconstructs_complete_release(self):
        self.write(self.source / 'static/change.css', b'changed')
        self.write(self.source / 'static/new.jpg', b'new')
        self.make_incremental()
        with tarfile.open(self.archive) as bundle:
            self.assertNotIn('static/keep.mp4', bundle.getnames())
            self.assertIn('static/change.css', bundle.getnames())
            self.assertIn('static/new.jpg', bundle.getnames())
        self.assertEqual((self.candidate / 'static/keep.mp4').read_bytes(), b'original')
        self.assertEqual((self.candidate / 'static/change.css').read_bytes(), b'changed')
        self.assertEqual((self.candidate / 'static/new.jpg').read_bytes(), b'new')
        self.assertFalse((self.candidate / 'static/deleted.jpg').exists())
        self.assertEqual((self.previous / 'static/change.css').read_bytes(), b'original')
        (self.candidate / 'static/keep.mp4').write_bytes(b'candidate edit')
        self.assertEqual((self.previous / 'static/keep.mp4').read_bytes(), b'original')

    def test_missing_or_corrupt_base_stops_preparation(self):
        for corrupt in (None, b'corrupt'):
            with self.subTest(corrupt=corrupt):
                base = self.previous / 'static/keep.mp4'
                base.unlink(missing_ok=True)
                if corrupt is not None:
                    base.write_bytes(corrupt)
                build(self.source, self.archive, SHA, base_manifest=self.manifest)
                with self.assertRaisesRegex(ValueError, 'static'):
                    unpack(self.archive, self.candidate, SHA, previous=self.previous)

    def test_full_archive_works_without_previous_release(self):
        build(self.source, self.archive, SHA)
        unpack(self.archive, self.candidate, SHA)
        self.assertEqual((self.candidate / 'static/keep.mp4').read_bytes(), b'original')

    def test_manifest_rejects_paths_outside_public_static(self):
        for name in ('.', '../production.json', '/absolute', '.env', 'images/../../private',
                     'images/.secret', 'images//x', 'images/./x'):
            with self.subTest(name=name):
                manifest = {'version': 1, 'files': {name: 'a' * 64}}
                with self.assertRaises(ValueError):
                    build(self.source, self.archive, SHA, base_manifest=manifest)

    def test_old_full_archive_without_manifest_is_still_accepted(self):
        build(self.source, self.archive, SHA)
        legacy = self.root / 'legacy.tar.gz'
        with tarfile.open(self.archive) as source, tarfile.open(legacy, 'w:gz') as target:
            for member in source.getmembers():
                if member.name != 'STATIC_MANIFEST.json':
                    target.addfile(member, source.extractfile(member))
        unpack(legacy, self.candidate, SHA)
        self.assertEqual((self.candidate / 'static/keep.mp4').read_bytes(), b'original')

    def test_deleting_all_static_assets_does_not_copy_old_files(self):
        import shutil
        shutil.rmtree(self.source / 'static')
        self.make_incremental()
        self.assertFalse((self.candidate / 'static').exists())

    def test_rejects_symlinked_parent_directory_in_base(self):
        self.write(self.source / 'static/images/photo.jpg', b'photo')
        self.manifest['files']['images/photo.jpg'] = hashlib.sha256(b'photo').hexdigest()
        (self.previous / 'static/images').symlink_to(self.source / 'static/images', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'static'):
            self.make_incremental()

    def test_server_refuses_manifest_traversal_and_corrupt_uploaded_assets(self):
        import io
        for manifest in ({'version': 1, 'files': {'../private': 'a' * 64}},
                         {'version': 1, 'files': {'keep.mp4': '0' * 64,
                                                'change.css': hashlib.sha256(b'original').hexdigest()}}):
            build(self.source, self.archive, SHA)
            modified = self.root / 'modified.tar.gz'
            with tarfile.open(self.archive) as source, tarfile.open(modified, 'w:gz') as target:
                for member in source.getmembers():
                    if member.name != 'STATIC_MANIFEST.json':
                        target.addfile(member, source.extractfile(member))
                data = json.dumps(manifest).encode()
                item = tarfile.TarInfo('STATIC_MANIFEST.json')
                item.size = len(data)
                target.addfile(item, io.BytesIO(data))
            with self.assertRaises(ValueError):
                unpack(modified, self.candidate, SHA, previous=self.previous)

    def test_does_not_reuse_symlinked_base_files(self):
        base = self.previous / 'static/keep.mp4'
        base.unlink()
        base.symlink_to(self.source / 'static/keep.mp4')
        with self.assertRaisesRegex(ValueError, 'static'):
            self.make_incremental()

    def test_manifest_command_only_exposes_static_hashes(self):
        # Run the real forced-command entry point, with only its APP path replaced.
        self.write(self.previous / 'production.json', b'private')
        self.write(self.previous / 'static/.private', b'private')
        script = Path(__file__).resolve().parents[1] / 'receive.py'
        harness = ('import pathlib, sys\n'
                   'sys.path.insert(0, str(pathlib.Path(sys.argv[1]).parent))\n'
                   'code = pathlib.Path(sys.argv[1]).read_text()\n'
                   'code = code.replace("APP = Path(\'/var/www/u3688705/data/apps/colibri\')", '
                   '"APP = Path(" + repr(sys.argv[2]) + ")")\n'
                   'exec(compile(code, sys.argv[1], "exec"), {"__name__": "__main__"})')
        import os
        result = subprocess.run([sys.executable, '-c', harness, str(script), str(self.previous)],
                                env=dict(os.environ, SSH_ORIGINAL_COMMAND='manifest'),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.manifest)
        self.assertNotIn('private', result.stdout)
