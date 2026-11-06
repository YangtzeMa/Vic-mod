from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'companion'))
sys.path.insert(0, str(ROOT / 'scripts'))
from identity import fingerprint, read_order
from memory import read_records, remember_clicks, save_records
from build_memory_ui import build, remembered_body
from run_memory import synchronize
from test_identity import fixture, packet


def memory_fixture(game, count=3):
    groups = fixture(game, count)
    path = game / 'gui/achievements/jomini_achievements_types.gui'
    source = path.read_text().replace('type widget_achievement_list_entry = widget {\n}', '''type widget_achievement_list_entry = widget {
        minimumsize = { 0 80 }
        # nested braces inside strings must not terminate this body
        hbox = {
            icon = {
                visible = "[GUIAchievement.GetAchievement.IsUnlocked]"
                texture = "[GUIAchievement.AccessTexture]"
                size = { 64 64 }
            }
            highlight_icon = { visible = "[Not(GUIAchievement.GetAchievement.IsUnlocked)]" }
            text_single = { text = "[GUIAchievement.GetName]" }
            text_multi = { text = "[GUIAchievement.GetDescription]" tooltip = "[GUIAchievement.GetHappenedDescription]" }
        }
    }''')
    path.write_text(source)
    window = game / 'gui/achievements/jomini_achievements_window.gui'
    window.write_text('window = { widget = {\n        vbox = {\n### CONTENT ###\n}\n}\n}\n')
    for group in groups:
        for key in group['ids']:
            icon = game / f'gfx/interface/icons/achievements/{key}.dds'
            icon.parent.mkdir(parents=True, exist_ok=True)
            icon.touch()
    return groups


class MemoryIntegrationTests(unittest.TestCase):
    def test_base_achievement_uses_its_actual_icon_filename(self):
        with tempfile.TemporaryDirectory() as folder:
            game = Path(folder)
            memory_fixture(game)
            icon = game / 'gfx/interface/icons/achievements/institutional.dds'
            icon.touch()
            source = (game / 'gui/achievements/jomini_achievements_types.gui').read_text()
            row = remembered_body(source, game, 'institutional')
            self.assertIn('achievements/institutional.dds', row)
            self.assertNotIn('GUIAchievement.', row)

    def test_identity_import_survives_restart_and_keeps_old_diagnostics(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            groups = fixture(root / 'game')
            path = root / 'records.json'
            save_records(path, {'version': 1, 'completed': {}, 'diagnostics': ['old'], 'unresolved': ['empty']})
            line = packet(groups)
            first, report = remember_clicks(path, [line, line, 'VICMOD_DIAG|ignored'], groups)
            self.assertEqual(['achievement_1'], report['added'])
            before = path.read_bytes()
            second, report = remember_clicks(path, [line], groups)
            self.assertEqual(first, second)
            self.assertEqual(before, path.read_bytes())
            self.assertEqual([], report['added'])
            self.assertEqual(['old'], second['diagnostics'])
            self.assertEqual(['empty'], second['unresolved'])

    def test_rejected_identity_is_never_a_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            groups = fixture(root / 'game')
            data, report = remember_clicks(root / 'records.json', [packet(groups, all='0')], groups)
            self.assertEqual({}, data['completed'])
            self.assertEqual(1, len(report['rejected']))

    def test_corrupt_record_is_preserved_during_import(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.json'
            path.write_text('[]')
            with self.assertRaises(ValueError):
                remember_clicks(path, [], [])
            self.assertEqual('[]', path.read_text())

    def test_native_host_and_one_display_row_per_achievement(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game, output = root / 'game', root / 'out'
            groups = memory_fixture(game)
            build(game, output, ['achievement_1'])
            window = (output / 'gui/achievements/jomini_achievements_window.gui').read_text('utf-8-sig')
            types = (output / 'gui/achievements/jomini_achievements_types.gui').read_text('utf-8-sig')
            self.assertEqual(3, window.count('name = "vicmod_memory_achievement_'))
            self.assertNotIn('GUIAchievement.', window)
            self.assertNotIn('GetPlayer', window)
            entry = window[window.index('text = "vicmod_memory_title"', window.index('button_standard_list = {')):]
            self.assertNotIn('AchievementWindow.Hide', entry.split('### CONTENT ###')[0])
            self.assertIn('name = "vicmod_memory_achievement_1"\n visible = yes', window)
            self.assertIn(f"vicmod_seen_{fingerprint(groups)}_1_1", window)
            self.assertEqual(1, types.count('text = "vicmod_identify_click"'))
            self.assertIn('Concatenate4(', types)
            self.assertNotIn('GetPlayer', types)
            self.assertIn('PdxGuiTriggerAllAnimations', window)
            self.assertIn('vicmod_remember_row', types)
            self.assertEqual((game / 'gui/achievements/popup.gui').read_bytes(),
                             (output / 'gui/achievements/popup.gui').read_bytes())

    def test_unknown_records_or_excess_rows_do_not_deploy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game, output = root / 'game', root / 'out'
            memory_fixture(game)
            with self.assertRaises(ValueError):
                build(game, output, ['invented'])
            self.assertFalse(output.exists())
            fixture(game, 513)
            with self.assertRaises(ValueError):
                build(game, output)
            self.assertFalse(output.exists())

    def test_exit_sync_writes_verified_ids_and_generates_restart_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game, user, output = root / 'game', root / 'user', root / 'out'
            groups = memory_fixture(game)
            logs = user / 'logs'
            logs.mkdir(parents=True)
            (logs / 'debug.log').write_text(packet(groups) + '\n' + packet(groups, row='1') + '\n')
            report = synchronize(game, user, output)
            self.assertEqual(['achievement_1', 'achievement_2'], report['added'])
            records = user / 'vicmod_achievement_memory/records.json'
            self.assertEqual({'achievement_1', 'achievement_2'}, set(read_records(records)['completed']))
            report = synchronize(game, user, output)
            self.assertEqual([], report['added'])
            window = (output / 'gui/achievements/jomini_achievements_window.gui').read_text('utf-8-sig')
            self.assertIn('name = "vicmod_memory_achievement_2"\n visible = yes', window)


if __name__ == '__main__':
    unittest.main()
