"""Resolve native all-list coordinates without OCR, guessed names or record writes."""
import hashlib
import json
from pathlib import Path
import re

PREFIX = 'VICMOD_CLICK_V1|'
IDENTIFIER = re.compile(r'[A-Za-z0-9_]+\Z')


def read_order(game: Path):
    source = (game / 'common/achievement_groups.txt').read_text('utf-8-sig')
    tokens = [t for t in re.findall(r'"(?:\\.|[^"\\])*"|\#[^\n]*|[{}=]|[A-Za-z0-9_]+|\S', source)
              if not t.startswith('#')]
    position = 0

    def take(expected=None):
        nonlocal position
        if position >= len(tokens):
            raise ValueError('Incomplete achievement group definition')
        value = tokens[position]
        position += 1
        if expected is not None and value != expected:
            raise ValueError(f'Unexpected achievement group syntax: {value!r}')
        return value

    def quoted_id():
        value = json.loads(take())
        if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
            raise ValueError('Invalid achievement identifier')
        return value

    groups = []
    while position < len(tokens):
        take('group'); take('='); take('{'); take('name'); take('=')
        name = quoted_id()
        take('order'); take('='); take('{')
        keys = []
        while position < len(tokens) and tokens[position] != '}':
            keys.append(quoted_id())
        take('}'); take('}')
        if not keys:
            raise ValueError('Empty achievement group')
        groups.append({'name': name, 'ids': keys})
    keys = [key for group in groups for key in group['ids']]
    definitions = {key for path in (game / 'common/achievements').glob('*.txt')
                   for key in re.findall(r'(?m)^([A-Za-z0-9_]+)\s*=\s*\{', path.read_text('utf-8-sig'))}
    if (not groups or len({g['name'] for g in groups}) != len(groups)
            or len(set(keys)) != len(keys) or set(keys) != definitions):
        raise ValueError('Achievement group order is incomplete or ambiguous')
    return groups


def fingerprint(groups):
    data = json.dumps(groups, sort_keys=True, separators=(',', ':')).encode('ascii')
    return hashlib.sha256(data).hexdigest()


def resolve_click(line, groups):
    """Reject filtered, stale, malformed or incomplete coordinates, never guess."""
    if PREFIX not in line:
        return None
    fields = {}
    for pair in line.split(PREFIX, 1)[1].strip().split('|'):
        key, separator, value = pair.partition('=')
        if not separator or key in fields:
            raise ValueError('Malformed identity packet')
        fields[key] = value
    if set(fields) != {'table', 'all', 'unlocked', 'groups', 'group', 'row', 'count'}:
        raise ValueError('Incomplete identity packet')
    if fields['table'] != fingerprint(groups):
        raise ValueError('Installed achievement order differs from probe build')
    if fields['all'] != '1' or fields['unlocked'] != '1':
        raise ValueError('Identity requires the All filter and an unlocked achievement')
    if any(not re.fullmatch(r'0|[1-9][0-9]*', fields[key])
           for key in ('groups', 'group', 'row', 'count')):
        raise ValueError('Invalid native list coordinate')
    group_count, group_index, row, count = (int(fields[key]) for key in ('groups', 'group', 'row', 'count'))
    if group_count != len(groups) or group_index >= group_count:
        raise ValueError('Native group count or index differs from installed order')
    group = groups[group_index]
    if count != len(group['ids']) or row >= count:
        raise ValueError('Native achievement count or index differs from installed order')
    return {'id': group['ids'][row], 'group': group['name'], 'group_index': group_index, 'row_index': row}
