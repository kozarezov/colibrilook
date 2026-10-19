import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from deploy.package import build
from deploy.release import unpack, activate

SHA = 'a' * 40


class ArtifactTests(unittest.TestCase):
    def test_only_release_files_and_no_secrets_or_uploads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('manage.py', 'requirements.txt', 'requirements-hosting.txt', 'content/catalog.json',
                         'config/settings.py', 'static/image.png', 'production.json', '.env',
                         'media/editor.jpg', '.admin-credentials.json', 'config/__pycache__/x.pyc'):
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text('test')
            for folder in ('boutique', 'templates', 'deploy'):
                (root / folder).mkdir()
            archive = root / 'release.tar.gz'
            build(root, archive, SHA)
            destination = root / 'release'
            destination.mkdir()
            unpack(archive, destination, SHA)
            self.assertTrue((destination / 'static/image.png').exists())
            self.assertFalse((destination / 'production.json').exists())
            self.assertFalse((destination / 'media').exists())
            self.assertFalse((destination / 'config/__pycache__').exists())

    def test_rejects_traversal_links_and_private_configuration(self):
        for name, kind in [('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                           ('config/link', tarfile.SYMTYPE), ('production.json', tarfile.REGTYPE),
                           ('static/.env', tarfile.REGTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                archive = root / 'bad.tar.gz'
                with tarfile.open(archive, 'w:gz') as tar:
                    item = tarfile.TarInfo(name)
                    item.type = kind
                    item.linkname = '../../escape' if kind == tarfile.SYMTYPE else ''
                    tar.addfile(item, io.BytesIO(b''))
                with self.assertRaises(ValueError):
                    unpack(archive, root / 'release', SHA)
                self.assertFalse((root / 'escape').exists())

    def test_rejects_invalid_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                build(Path(temp), Path(temp) / 'out', 'main; command')


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.app = self.root / 'app'
        self.public = self.root / 'public'
        self.old = self.app / 'old'
        self.new = self.app / 'new'
        for folder in (self.public, self.old / 'staticfiles', self.new / 'staticfiles', self.app / 'media'):
            folder.mkdir(parents=True)
        (self.app / 'current').symlink_to(self.old)
        (self.public / 'static').symlink_to(self.old / 'staticfiles')
        (self.app / 'production.json').write_text('private')
        (self.app / 'media/editor.jpg').write_text('editor upload')

    def test_success_switches_release_and_preserves_shared_data(self):
        activate(self.app, self.public, self.new, SHA, probe=lambda sha: sha == SHA)
        self.assertEqual((self.app / 'current').resolve(), self.new)
        self.assertEqual((self.public / 'static').resolve(), self.new / 'staticfiles')
        self.assertEqual((self.app / 'media/editor.jpg').read_text(), 'editor upload')
        self.assertEqual((self.app / 'production.json').read_text(), 'private')
        self.assertTrue((self.public / '.restart-app').exists())

    def test_failed_health_rolls_back_code_and_static(self):
        with self.assertRaises(RuntimeError):
            activate(self.app, self.public, self.new, SHA, probe=lambda sha: False)
        self.assertEqual((self.app / 'current').resolve(), self.old)
        self.assertEqual((self.public / 'static').resolve(), self.old / 'staticfiles')

    def test_first_release_failure_restores_legacy_layout(self):
        (self.app / 'current').unlink()
        with self.assertRaises(RuntimeError):
            activate(self.app, self.public, self.new, SHA, probe=lambda sha: False)
        self.assertFalse((self.app / 'current').exists())
        self.assertEqual((self.public / 'static').resolve(), self.old / 'staticfiles')

    def test_refuses_to_replace_real_static_directory(self):
        (self.public / 'static').unlink()
        (self.public / 'static').mkdir()
        with self.assertRaises(RuntimeError):
            activate(self.app, self.public, self.new, SHA)
        self.assertEqual((self.app / 'current').resolve(), self.old)

    def test_failed_startup_restores_passenger_entrypoint_too(self):
        from deploy.release import install_and_activate
        (self.public / 'passenger_wsgi.py').write_text('original startup')
        (self.new / 'deploy').mkdir()
        (self.new / 'deploy/passenger_wsgi.py').write_text('broken startup')
        with self.assertRaises(RuntimeError):
            install_and_activate(self.app, self.public, self.new, SHA, probe=lambda sha: False)
        self.assertEqual((self.app / 'current').resolve(), self.old)
        self.assertEqual((self.public / 'passenger_wsgi.py').read_text(), 'original startup')

class ReceiverTests(unittest.TestCase):
    def test_only_fixed_deployment_command_is_allowed(self):
        from deploy.receive import command
        self.assertEqual(command('deploy ' + SHA + ' 123-1'), ('deploy', SHA, '123-1'))
        self.assertEqual(command('check ' + SHA + ' 123-1'), ('check', SHA, '123-1'))
        for value in ('', 'sh', 'cat production.json', 'scp -t /tmp/file',
                      'manifest ../production.json', 'manifest; id', 'manifest\nid',
                      'deploy ' + SHA + ' 123-1; id', 'deploy ../x 123-1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                command(value)

    def test_upload_size_limit_and_no_overwrite(self):
        from deploy.receive import receive
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'upload'
            with self.assertRaises(ValueError):
                receive(io.BytesIO(b'too large'), path, limit=3)
            with self.assertRaises(FileExistsError):
                receive(io.BytesIO(b'new'), path)

class PreparationTests(unittest.TestCase):
    def test_check_mode_never_migrates_backs_up_or_activates(self):
        import json
        from deploy.release import deploy
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / 'app'
            app.mkdir()
            (app / 'production.json').write_text(json.dumps({'DATABASE_ENGINE': 'mysql'}))
            archive = Path(temp) / 'release.tar.gz'
            archive.write_bytes(b'test fixture')
            with patch('deploy.release.APP', app), patch('deploy.release.unpack'), \
                    patch('deploy.release.signal.signal'), patch('deploy.release.subprocess.run') as run, \
                    patch('deploy.release.backup_database') as backup, patch('deploy.release.activate') as activate:
                deploy(archive, SHA, '1-1', check_only=True)
            backup.assert_not_called()
            activate.assert_not_called()
            commands = [call.args[0] for call in run.call_args_list]
            self.assertTrue(any('migrate' in c and '--plan' in c for c in commands))
            self.assertFalse(any('migrate' in c and '--noinput' in c for c in commands))
            self.assertFalse((app / 'current').exists())
            self.assertFalse(list((app / 'releases').iterdir()))

    def test_backup_failure_stops_before_migrations(self):
        import json
        from deploy.release import deploy
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / 'app'
            app.mkdir()
            (app / 'production.json').write_text(json.dumps({'DATABASE_ENGINE': 'mysql'}))
            archive = Path(temp) / 'release.tar.gz'
            archive.write_bytes(b'test fixture')
            with patch('deploy.release.APP', app), patch('deploy.release.unpack'), \
                    patch('deploy.release.signal.signal'), patch('deploy.release.subprocess.run') as run, \
                    patch('deploy.release.backup_database', side_effect=RuntimeError('dump failed')), \
                    patch('deploy.release.activate') as activate:
                with self.assertRaisesRegex(RuntimeError, 'dump failed'):
                    deploy(archive, SHA, '1-1')
            activate.assert_not_called()
            self.assertFalse(any('migrate' in c.args[0] for c in run.call_args_list))
