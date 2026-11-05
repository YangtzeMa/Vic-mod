"""Print identified clicks from the latest normal game session; never write records."""
import argparse
import json
from pathlib import Path
import re

from identity import PREFIX, read_order, resolve_click
from memory import build_catalog


def read_latest_session(log_directory):
    def rotation(path):
        match = re.fullmatch(r'debug\.(\d+)\.log', path.name)
        return int(match.group(1)) + 1 if match else 0
    lines = []
    for path in sorted(log_directory.glob('debug*.log'), key=rotation, reverse=True):
        for line in path.read_text('utf-8-sig', errors='replace').splitlines():
            if 'Log system initialized.' in line:
                lines.clear()
            if PREFIX in line:
                lines.append(line)
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--logs', type=Path, required=True)
    args = parser.parse_args()
    groups = read_order(args.game)
    aliases = {}
    for title, key in build_catalog(args.game).items():
        aliases.setdefault(key, []).append(title)
    clicks, rejected = [], []
    for line in read_latest_session(args.logs):
        try:
            result = resolve_click(line, groups)
            result['names'] = aliases.get(result['id'], [])
            clicks.append(result)
        except ValueError as error:
            rejected.append(str(error))
    print(json.dumps({'clicks': clicks, 'rejected': rejected, 'records_written': False},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
