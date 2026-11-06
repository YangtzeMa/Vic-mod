from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'companion'))
from identity import BULK_PREFIX, fingerprint, resolve_bulk
from memory import remember_clicks


class BulkMemoryTests(unittest.TestCase):
    def test_only_unlocked_bits_are_remembered_and_deduplicated(self):
        groups = [{'name': 'easy', 'ids': ['a', 'b', 'c']}]
        packet = BULK_PREFIX + f'table={fingerprint(groups)}|all=1|groups=1|group=0|count=3|bits=101'
        self.assertEqual(['a', 'c'], [x['id'] for x in resolve_bulk(packet, groups)])
        with tempfile.TemporaryDirectory() as folder:
            data, report = remember_clicks(Path(folder) / 'records.json', [packet, packet], groups)
            self.assertEqual(['a', 'c'], list(data['completed']))
            self.assertEqual(['a', 'c'], report['added'])

    def test_reject_missing_states_filtered_or_shortened_snapshots(self):
        groups = [{'name': 'easy', 'ids': ['a', 'b']}]
        packet = BULK_PREFIX + f'table={fingerprint(groups)}|all=1|groups=1|group=0|count=2|bits=10'
        for bad in [packet.replace('bits=10', 'bits=1?'), packet.replace('bits=10', 'bits=1'),
                    packet.replace('all=1', 'all=0'), packet.replace('count=2', 'count=1')]:
            with self.assertRaises(ValueError):
                resolve_bulk(bad, groups)


if __name__ == '__main__':
    unittest.main()
