import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'companion')]
from package_release import package, FILES
from release_metadata import MOD_ID
from run_memory import synchronize
from test_memory_ui import memory_fixture

spec = importlib.util.spec_from_file_location('release_install', ROOT / 'distribution/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class ReleaseTests(unittest.TestCase):
    def test_archive_is_deterministic_and_contains_no_personal_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            path = package(ROOT, output)
            first = path.read_bytes()
            package(ROOT, output)
            self.assertEqual(first, path.read_bytes())
            with ZipFile(path) as archive:
                names = [name.split('/', 1)[1] for name in archive.namelist()]
                self.assertEqual(set(FILES) | {'mod/.metadata/metadata.json', 'VERSION.txt', 'MANIFEST.sha256'}, set(names))
                self.assertFalse(any('.local/' in n or n.endswith('.log') or 'records.json' in n or n.startswith('mod/gui/') for n in names))
                for name in names:
                    self.assertNotIn('..', Path(name).parts)

    def test_fresh_install_starts_empty_and_public_id_survives_regeneration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = package(ROOT, root / 'dist')
            with ZipFile(archive) as zipfile:
                zipfile.extractall(root / 'extract')
            extracted = next((root / 'extract').iterdir())
            game = root / 'game'
            memory_fixture(game)
            launcher = root / 'launcher'
            launcher.mkdir()
            (launcher / 'launcher-settings.json').write_text(json.dumps({'rawVersion': '1.15.0'}))
            user = root / 'new-user'
            report = installer.prepare(game, user, root=extracted, link=False)
            self.assertEqual(0, report['saved'])
            window = (extracted / 'mod/gui/achievements/jomini_achievements_window.gui').read_text('utf-8-sig')
            self.assertEqual([], re.findall(r'name = "vicmod_memory_\w+"\n visible = yes', window))
            self.assertFalse((user / 'vicmod_achievement_memory/records.json').exists())
            written_ids = []
            original_write = Path.write_text
            def observe_write(path, text, *args, **kwargs):
                if path.name == 'metadata.json':
                    written_ids.append(json.loads(text)['id'])
                return original_write(path, text, *args, **kwargs)
            with patch.object(Path, 'write_text', observe_write):
                synchronize(game, user, extracted / 'mod', release=True)
            self.assertTrue(written_ids)
            self.assertEqual({MOD_ID}, set(written_ids))
            data = json.loads((extracted / 'mod/.metadata/metadata.json').read_text('utf-8'))
            self.assertEqual(MOD_ID, data['id'])
            self.assertEqual('0.0.8', data['version'])

    def test_install_refuses_unrelated_destination_and_unsupported_game(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game = root / 'game'
            memory_fixture(game)
            launcher = root / 'launcher'
            launcher.mkdir()
            version = launcher / 'launcher-settings.json'
            version.write_text(json.dumps({'rawVersion': '1.15.0'}))
            user = root / 'user'
            existing = user / 'mod/vicmod_achievement_memory'
            existing.mkdir(parents=True)
            marker = existing / 'keep.txt'
            marker.write_text('user data')
            with self.assertRaises(ValueError):
                installer.prepare(game, user, root / 'release', link=False)
            self.assertEqual('user data', marker.read_text())
            version.write_text(json.dumps({'rawVersion': '1.16.0'}))
            with self.assertRaises(ValueError):
                installer.validate_game(game)


if __name__ == '__main__':
    unittest.main()
