"""Durable local achievement records; never writes Steam data or game saves."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

MARKER = 'VICMOD_UNLOCK|'


def read_records(path: Path):
    if not path.exists():
        return {'version': 1, 'completed': {}, 'diagnostics': [], 'unresolved': []}
    data = json.loads(path.read_text('utf-8'))
    if (not isinstance(data, dict) or data.get('version') != 1
            or not isinstance(data.get('completed'), dict)
            or not isinstance(data.get('diagnostics', []), list)
            or not isinstance(data.get('unresolved', []), list)):
        raise ValueError('Unsupported or damaged record file; refusing to overwrite it')
    data.setdefault('diagnostics', [])
    data.setdefault('unresolved', [])
    return data


def save_records(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def build_catalog(game: Path):
    ids = set()
    for path in (game / 'common/achievements').glob('*.txt'):
        ids.update(re.findall(r'(?m)^([A-Za-z0-9_]+)\s*=\s*\{', path.read_text('utf-8-sig')))
    aliases = {}
    for language in ['english', 'simp_chinese']:
        for path in (game / 'localization' / language).glob('*.yml'):
            for key, title in re.findall(r'(?m)^\s*ACHIEVEMENT_([A-Za-z0-9_]+):(?:\d+)?\s*"((?:\\.|[^"\\])*)"[^\S\r\n]*(?:#[^\r\n]*)?$', path.read_text('utf-8-sig')):
                title = title.replace(r'\"', '"').replace('\\\\', '\\')
                if key in ids:
                    aliases.setdefault(title, set()).add(key)
    return {name: next(iter(keys)) for name, keys in aliases.items() if len(keys) == 1}


def consume(path: Path, lines, catalog):
    data = read_records(path)
    changed = False
    for line in lines:
        if 'VICMOD_ID|' in line:
            key = line.split('VICMOD_ID|', 1)[1].strip()
            if key in set(catalog.values()):
                if key not in data['completed']:
                    data['completed'][key] = {'observed_at': datetime.now(timezone.utc).isoformat(), 'source': 'game_achievement_ui', 'title': key}
                    changed = True
            elif 'unknown_id:' + key not in data['unresolved']:
                data['unresolved'].append('unknown_id:' + key)
                changed = True
            continue
        if MARKER not in line:
            continue
        title = line.split(MARKER, 1)[1].strip()
        if title == 'vicmod_capture_probe':
            if title not in data['diagnostics']:
                data['diagnostics'].append(title)
                changed = True
        elif title in catalog:
            key = catalog[title]
            if key not in data['completed']:
                data['completed'][key] = {'observed_at': datetime.now(timezone.utc).isoformat(), 'source': 'game_unlock_popup', 'title': title}
                changed = True
        elif (title or '<empty payload>') not in data['unresolved']:
            data['unresolved'].append(title or '<empty payload>')
            changed = True
    if changed:
        save_records(path, data)
    return data


def remember_clicks(path: Path, lines, groups):
    """Persist only identity packets accepted by the verified-coordinate parser."""
    from identity import PREFIX, BULK_PREFIX, resolve_click, resolve_bulk
    data = read_records(path)
    added, rejected = [], []
    for line in lines:
        if PREFIX not in line and BULK_PREFIX not in line:
            continue
        try:
            clicks = resolve_bulk(line, groups) if BULK_PREFIX in line else [resolve_click(line, groups)]
        except ValueError as error:
            message = 'identity:' + str(error)
            rejected.append(message)
            if message not in data['unresolved']:
                data['unresolved'].append(message)
            continue
        for click in clicks:
            key = click['id']
            if key not in data['completed']:
                data['completed'][key] = {
                    'observed_at': datetime.now(timezone.utc).isoformat(),
                    'source': 'native_achievement_bulk' if BULK_PREFIX in line else 'native_achievement_button', 'title': key,
                }
                added.append(key)
    if added or data != read_records(path):
        save_records(path, data)
    return data, {'added': added, 'rejected': rejected}
