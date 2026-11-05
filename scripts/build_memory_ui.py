"""Build remembered-only GUI from native row layout and verified identity records."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'companion'))
from identity import fingerprint, read_order
from memory import read_records
from build_identity_probe import build as build_identity, ENTRY


def body_of(source, marker):
    start = source.index(marker) + len(marker)
    depth, quoted, escaped, comment = 1, False, False, False
    for pos in range(start, len(source)):
        char = source[pos]
        if comment:
            comment = char != '\n'
            continue
        if quoted:
            if char == '"' and not escaped:
                quoted = False
            escaped = char == '\\' and not escaped
            continue
        if char == '#':
            comment = True
        elif char == '"':
            quoted = True
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return source[start:pos], pos + 1
    raise ValueError('Unbalanced native widget')


def remembered_body(source, game, key):
    body, _ = body_of(source, ENTRY)
    # Only the native unlocked icon is needed; remove locked overlay subtrees.
    marker = 'highlight_icon = {'
    while marker in body:
        start = body.index(marker)
        _, end = body_of(body, marker)
        body = body[:start] + body[end:]
    texture = f'gfx/interface/icons/achievements/{key}.dds'
    if not (game / texture).is_file():
        raise ValueError(f'Missing native achievement icon: {key}')
    replacements = {
        'visible = "[GUIAchievement.GetAchievement.IsUnlocked]"': 'visible = yes',
        'alpha = "[Select_float(GUIAchievement.GetAchievement.IsUnlocked,\'(float)1.0\',\'(float)0.5\')]"': 'alpha = 1',
        '[GUIAchievement.AccessTexture]': texture,
        '[GUIAchievement.GetName]': f'ACHIEVEMENT_{key}',
        '[GUIAchievement.GetDescription]': f'ACHIEVEMENT_DESC_{key}',
        '[GUIAchievement.GetHappenedDescription]': f'ACHIEVEMENT_DESC_{key}',
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    if 'GUIAchievement.' in body:
        raise ValueError('Native row contains an unsupported data binding')
    return body


def build(game: Path, output: Path, completed=()):
    groups = read_order(game)
    saved = set(completed)
    valid = {key for group in groups for key in group['ids']}
    if saved - valid:
        raise ValueError('Records contain unknown achievement IDs; refusing to hide or discard them')
    if len(valid) > 512:
        raise ValueError('Memory UI exceeds its explicit linear row budget')
    table = fingerprint(groups)
    row_prefix, group_prefix = f'vicmod_seen_{table}_', f'vicmod_group_{table}_'
    source = (game / 'gui/achievements/jomini_achievements_types.gui').read_text('utf-8-sig')
    section_text = []
    for group_index, group in enumerate(groups):
        has_saved = bool(saved.intersection(group['ids']))
        section_visibility = 'yes' if has_saved else f'"[GetVariableSystem.Exists(\'{group_prefix}{group_index}\')]"'
        rows = []
        for row_index, key in enumerate(group['ids']):
            visible = 'yes' if key in saved else f'"[GetVariableSystem.Exists(\'{row_prefix}{group_index}_{row_index}\')]"'
            rows.append(f'widget = {{\n name = "vicmod_memory_{key}"\n visible = {visible}\n'
                        ' layoutpolicy_horizontal = expanding\n' + remembered_body(source, game, key) + '\n}\n')
        section_text.append(f'''vbox = {{
            visible = {section_visibility}
            layoutpolicy_horizontal = expanding
            button_normal = {{
                layoutpolicy_horizontal = expanding
                size = {{ 0 25 }}
                onclick = "[GetVariableSystem.Toggle('vicmod_collapsed_{group['name']}')]"
                hbox = {{
                    layoutpolicy_horizontal = expanding
                    margin = {{ 10 0 }}
                    spacing = 10
                    background = {{ using = Background_Area margin = {{ 0 5 }} }}
                    button_expand = {{
                        onclick = "[GetVariableSystem.Toggle('vicmod_collapsed_{group['name']}')]"
                        down = "[Not(GetVariableSystem.Exists('vicmod_collapsed_{group['name']}'))]"
                    }}
                    text_single = {{ text = "ACHIEVEMENT_GROUP_{group['name']}" align = nobaseline }}
                    expand = {{}}
                }}
            }}
            vbox = {{
                layoutpolicy_horizontal = expanding
                visible = "[Not(GetVariableSystem.Exists('vicmod_collapsed_{group['name']}'))]"
                {''.join(rows)}
            }}
        }}''')
    empty = 'no' if saved else '"[Not(' + or_chain([
        f"GetVariableSystem.Exists('{group_prefix}{i}')" for i in range(len(groups))]) + ')]"'
    panel = '''widget = {
        name = "vicmod_memory_panel"
        size = { 900 880 }
        parentanchor = center
        alwaystransparent = no
        visible = "[GetVariableSystem.Exists('vicmod_memory_open')]"
        using = Window_Background
        vbox = {
            using = Window_Margins
            spacing = 10
            header_pattern = {
                layoutpolicy_horizontal = expanding
                blockoverride "header_text" { text = "vicmod_memory_title" }
                blockoverride "button_close" {
                    onclick = "[GetVariableSystem.Clear('vicmod_memory_open')]"
                    onclick = "[AchievementWindow.Hide]"
                }
            }
            text_multi = { text = "vicmod_memory_note" max_width = 760 autoresize = yes }
            scrollbox = {
                layoutpolicy_horizontal = expanding
                layoutpolicy_vertical = expanding
                blockoverride "scrollbox_content" {
                    vbox = {
                        layoutpolicy_horizontal = expanding
                        text_multi = { text = "vicmod_memory_empty" visible = ''' + empty + ''' max_width = 720 autoresize = yes }
''' + '\n'.join(section_text) + '''
                    }
                }
            }
            button_primary = {
                text = "vicmod_memory_back"
                onclick = "[GetVariableSystem.Clear('vicmod_memory_open')]"
                shortcut = "close_window"
            }
        }
    }
'''
    window = (game / 'gui/achievements/jomini_achievements_window.gui').read_text('utf-8-sig')
    anchor, outer = '### CONTENT ###', '        vbox = {'
    if window.count(anchor) != 1 or outer not in window:
        raise ValueError('Native achievement host window changed')
    # Reuse the engine-instantiated host. Opening memory never calls Hide.
    entry = '''button_standard_list = {
                size = { 260 30 }
                text = "vicmod_memory_title"
                onclick = "[GetVariableSystem.Set('vicmod_memory_open', 'yes')]"
            }
            '''
    window = window.replace(anchor, entry + anchor, 1)
    window = window.replace(outer, panel + '\n' + outer +
                            '\n            visible = "[Not(GetVariableSystem.Exists(\'vicmod_memory_open\'))]"', 1)
    build_identity(game, output)
    path = output / 'gui/achievements/jomini_achievements_types.gui'
    types = path.read_text('utf-8-sig')
    execute = '            onclick = "[GetScriptedGui(\'vicmod_identify_click\').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"'
    if types.count(execute) != 1:
        raise ValueError('Identity button hook changed')
    hooks = (
        f'            onclick = "[GetVariableSystem.Set(Concatenate4(\'{row_prefix}\', GetVariableSystem.Get(\'vicmod_click_group\'), \'_\', GetVariableSystem.Get(\'vicmod_click_row\')), \'1\')]"\n'
        f'            onclick = "[GetVariableSystem.Set(Concatenate(\'{group_prefix}\', GetVariableSystem.Get(\'vicmod_click_group\')), \'1\')]"\n')
    path.write_text(types.replace(execute, hooks + execute), encoding='utf-8-sig')
    (output / 'gui/achievements/jomini_achievements_window.gui').write_text(window, encoding='utf-8-sig')
    for language, labels in {
        'simp_chinese': ('记住此成就', '我的成就 · 本地记忆', '这里只显示本机记住的成就。新标记立即显示；保持本地助手运行，以便退出游戏时保存。', '暂无本地记忆。请返回原版“全部”页，对已解锁成就点击“记住此成就”。', '返回原版成就'),
        'english': ('Remember achievement', 'My achievements - Local memory', 'Only remembered achievements appear here. New marks appear immediately; keep the local helper running to save them when exiting.', 'Nothing remembered yet. Return to All and remember an unlocked achievement.', 'Back to achievements'),
    }.items():
        loc = output / f'localization/{language}/vicmod_capture_probe_l_{language}.yml'
        text = loc.read_text('utf-8-sig')
        old = '识别此成就' if language == 'simp_chinese' else 'Identify achievement'
        text = text.replace(f'vicmod_identify_click:0 "{old}"', f'vicmod_identify_click:0 "{labels[0]}"')
        text += '\n'.join(f' {key}:0 "{value}"' for key, value in zip(
            ['vicmod_memory_title', 'vicmod_memory_note', 'vicmod_memory_empty', 'vicmod_memory_back'], labels[1:])) + '\n'
        loc.write_text(text, encoding='utf-8-sig')
    metadata = output / '.metadata/metadata.json'
    data = json.loads(metadata.read_text('utf-8'))
    data['version'] = '0.0.7'
    data['short_description'] = 'Local achievement memory test: native rows, immediate session display, helper persistence on exit.'
    metadata.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return {'saved': len(saved), 'rows': len(valid), 'table': table}


def or_chain(expressions):
    if not expressions:
        raise ValueError('No achievement groups')
    result = expressions[0]
    for expression in expressions[1:]:
        result = f'Or({result}, {expression})'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--records', type=Path, required=True)
    args = parser.parse_args()
    print(build(args.game, ROOT / '.local/memory-probe', read_records(args.records)['completed']))
