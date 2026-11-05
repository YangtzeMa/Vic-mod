import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('memory', Path(__file__).resolve().parents[1] / 'companion/memory.py')
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)


class MemoryTests(unittest.TestCase):
    def test_catalog_languages_and_ambiguous_names(self):
        with tempfile.TemporaryDirectory() as folder:
            game = Path(folder)
            definitions = game / 'common/achievements'
            definitions.mkdir(parents=True)
            (definitions / 'example.txt').write_text('one = {}\ntwo = {}\nthree = {}\n')
            for language, text in [
                ('english', ' ACHIEVEMENT_one: "First" # trailing comment\n ACHIEVEMENT_two: "Shared"\n ACHIEVEMENT_three: "Shared"\n'),
                ('simp_chinese', ' ACHIEVEMENT_one: "第一项"\n')
            ]:
                directory = game / 'localization' / language
                directory.mkdir(parents=True)
                (directory / 'achievements.yml').write_text(f'l_{language}:\n' + text, encoding='utf-8-sig')
            catalog = memory.build_catalog(game)
            self.assertEqual({'First': 'one', '第一项': 'one'}, catalog)
            records = game / 'records.json'
            memory.consume(records, ['VICMOD_UNLOCK|First', 'VICMOD_UNLOCK|第一项', 'VICMOD_UNLOCK|Shared'], catalog)
            data = memory.read_records(records)
            self.assertEqual(['one'], list(data['completed']))
            self.assertEqual(['Shared'], data['unresolved'])

    def test_stable_id_capture_and_unknown_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.json'
            data = memory.consume(path, ['prefix VICMOD_ID|poor_huddled_masses', 'VICMOD_ID|poor_huddled_masses', 'VICMOD_ID|invented'], {'Title': 'poor_huddled_masses'})
            self.assertEqual(['poor_huddled_masses'], list(data['completed']))
            self.assertIn('unknown_id:invented', data['unresolved'])
    def test_empty_payload_is_diagnostic_not_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            data = memory.consume(Path(folder) / 'records.json', ['VICMOD_UNLOCK|'], {})
            self.assertEqual({}, data['completed'])
            self.assertEqual(['<empty payload>'], data['unresolved'])

    def test_restart_duplicates_and_no_downgrade(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.json'
            memory.consume(path, ['VICMOD_UNLOCK|Example'], {'Example': 'example'})
            first = memory.read_records(path)
            memory.consume(path, ['VICMOD_UNLOCK|Example', 'unlocked list is empty'], {'Example': 'example'})
            self.assertEqual(first, memory.read_records(path))

    def test_probe_and_unknown_are_not_achievements(self):
        with tempfile.TemporaryDirectory() as folder:
            data = memory.consume(Path(folder) / 'records.json', ['VICMOD_UNLOCK|vicmod_capture_probe', 'VICMOD_UNLOCK|unknown'], {})
            self.assertEqual({}, data['completed'])
            self.assertEqual(['vicmod_capture_probe'], data['diagnostics'])
            self.assertEqual(['unknown'], data['unresolved'])

    def test_corruption_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.json'
            path.write_text('broken', encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError):
                memory.consume(path, ['VICMOD_UNLOCK|Example'], {'Example': 'example'})
            self.assertEqual('broken', path.read_text('utf-8'))


if __name__ == '__main__':
    unittest.main()
