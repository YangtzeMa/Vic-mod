import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'companion'))
from identity import PREFIX, fingerprint, read_order, resolve_click
from read_identity_clicks import read_latest_session

spec = importlib.util.spec_from_file_location('identity_builder', ROOT / 'scripts/build_identity_probe.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def fixture(game, count=3):
    common = game / 'common'
    definitions = common / 'achievements'
    definitions.mkdir(parents=True, exist_ok=True)
    ids = [f'achievement_{i}' for i in range(count)]
    (definitions / 'examples.txt').write_text('\n'.join(key + ' = {}' for key in ids))
    groups = [{'name': 'easy', 'ids': ids[:1]}, {'name': 'hard', 'ids': ids[1:]}]
    (common / 'achievement_groups.txt').write_text('# group = { ignored }\n' + '\n'.join(
        'group = { name = "' + group['name'] + '" order = { ' +
        ' '.join('"' + key + '"' for key in group['ids']) + ' } }' for group in groups))
    gui = game / 'gui/achievements'
    gui.mkdir(parents=True, exist_ok=True)
    (gui / 'jomini_achievements_types.gui').write_text(
        'datamodel = "[Group.AccessVisibleAchievements]"\n' + builder.HIERARCHY + '\n' + builder.ENTRY + '\n}\n')
    for name in ['jomini_achievements_window.gui', 'popup.gui']:
        (gui / name).write_bytes(b'# native unchanged\n')
    return groups


def packet(order, **changes):
    fields = dict(table=fingerprint(order), all='1', unlocked='1', groups=str(len(order)),
                  group='1', row='0', count=str(len(order[1]['ids'])))
    fields.update(changes)
    return PREFIX + '|'.join(key + '=' + value for key, value in fields.items())


class IdentityTests(unittest.TestCase):
    def test_every_coordinate_has_exactly_one_id(self):
        with tempfile.TemporaryDirectory() as folder:
            expected = fixture(Path(folder), 152)
            groups = read_order(Path(folder))
            self.assertEqual(expected, groups)
            found = []
            for index, group in enumerate(groups):
                for row, key in enumerate(group['ids']):
                    actual = resolve_click(packet(groups, group=str(index), row=str(row), count=str(len(group['ids']))), groups)
                    self.assertEqual(key, actual['id'])
                    found.append(actual['id'])
            self.assertEqual(152, len(set(found)))

    def test_reject_filtered_locked_stale_or_shifted_packets(self):
        groups = [{'name': 'easy', 'ids': ['a']}, {'name': 'hard', 'ids': ['b', 'c']}]
        for change in [dict(all='0'), dict(unlocked='0'), dict(table='old'), dict(groups='1'),
                       dict(group='2'), dict(group='-1'), dict(row='-1'), dict(row='2'),
                       dict(count='1'), dict(row=''), dict(row='1.0')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                resolve_click(packet(groups, **change), groups)
        with self.assertRaises(ValueError):
            resolve_click(packet(groups) + '|row=0', groups)
        with self.assertRaises(ValueError):
            resolve_click(PREFIX + 'group=1|row=0', groups)
        self.assertIsNone(resolve_click('VICMOD_DIAG|known=a', groups))

    def test_reject_incomplete_or_duplicate_group_order(self):
        with tempfile.TemporaryDirectory() as folder:
            game = Path(folder)
            fixture(game)
            path = game / 'common/achievement_groups.txt'
            original = path.read_text()
            for changed in [original.replace('"achievement_2"', '"achievement_1"'),
                            original.replace('"achievement_2"', ''), original[:-2]]:
                path.write_text(changed)
                with self.assertRaises(ValueError):
                    read_order(game)

    def test_gui_budget_independent_of_catalog_and_native_windows_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game, output = root / 'game', root / 'out'
            fixture(game)
            first = builder.build(game, output)
            fixture(game, 10000)
            second = builder.build(game, output)
            self.assertEqual(first, second)
            self.assertEqual(1, second.count('text = "vicmod_identify_click"'))
            self.assertLess(len(builder.BUTTON), 4096)
            self.assertNotIn('GUIAchievement.GetName', builder.BUTTON)
            self.assertNotIn('datacontext', builder.BUTTON)
            for name in ['jomini_achievements_window.gui', 'popup.gui']:
                self.assertEqual((game / 'gui/achievements' / name).read_bytes(),
                                 (output / 'gui/achievements' / name).read_bytes())

    def test_changed_native_hierarchy_does_not_deploy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            game, output = root / 'game', root / 'out'
            fixture(game)
            (game / 'gui/achievements/jomini_achievements_types.gui').write_text(builder.ENTRY + '\n}\n')
            with self.assertRaises(ValueError):
                builder.build(game, output)
            self.assertFalse(output.exists())

    def test_log_rotation_keeps_only_latest_session(self):
        with tempfile.TemporaryDirectory() as folder:
            logs = Path(folder)
            (logs / 'debug.2.log').write_text('Log system initialized.\n' + PREFIX + 'old\n')
            (logs / 'debug.1.log').write_text('Log system initialized.\n' + PREFIX + 'first\n')
            (logs / 'debug.log').write_text(PREFIX + 'second\nQuit\n')
            self.assertEqual([PREFIX + 'first', PREFIX + 'second'], read_latest_session(logs))


if __name__ == '__main__':
    unittest.main()
