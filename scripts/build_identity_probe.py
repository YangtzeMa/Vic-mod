"""Build a bounded native-coordinate identity probe, without OCR or name conversion."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'companion'))
from identity import fingerprint, read_order

ENTRY = 'type widget_achievement_list_entry = widget {'
HIERARCHY = '''\t\t\titem = {
\t\t\t\twidget_achievement_list_entry = {
\t\t\t\t\tlayoutpolicy_horizontal = expanding
\t\t\t\t}
\t\t\t}'''
BUTTON = '''
        # vicmod: one constant-sized button per native row, no per-ID widgets.
        button_standard_list = {
            parentanchor = right|vcenter
            size = { 130 30 }
            text = "vicmod_identify_click"
            tooltip = "vicmod_identify_tooltip"
            visible = "[And(AchievementWindow.HasGameStarted, AchievementWindow.ShouldShowAll)]"
            enabled = "[And(AchievementWindow.ShouldShowAll, GUIAchievement.GetAchievement.IsUnlocked)]"
            onclick = "[GetVariableSystem.Set('vicmod_click_all', Select_CString(AchievementWindow.ShouldShowAll, '1', '0'))]"
            onclick = "[GetVariableSystem.Set('vicmod_click_unlocked', Select_CString(GUIAchievement.GetAchievement.IsUnlocked, '1', '0'))]"
            onclick = "[GetVariableSystem.Set('vicmod_click_row', ToString_int32(PdxGuiWidget.AccessParent.GetIndexInDataModel))]"
            onclick = "[GetVariableSystem.Set('vicmod_click_group', ToString_int32(PdxGuiWidget.AccessParent.AccessParent.AccessParent.GetIndexInDataModel))]"
            onclick = "[GetVariableSystem.Set('vicmod_click_groups', ToString_int32(GetDataModelSize(AchievementWindow.AccessGroups)))]"
            onclick = "[GetVariableSystem.Set('vicmod_click_count', ToString_int32(Group.GetNumberOfVisibleAchievements))]"
            onclick = "[GetScriptedGui('vicmod_identify_click').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"
        }
'''


def build(game: Path, output: Path):
    groups = read_order(game)
    table = fingerprint(groups)
    source = (game / 'gui/achievements/jomini_achievements_types.gui').read_text('utf-8-sig')
    if source.count(ENTRY) != 1:
        raise ValueError('Unexpected native achievement widget definition')
    # Index arithmetic depends on this native hierarchy; reject a changed schema.
    if HIERARCHY not in source or source.count('datamodel = "[Group.AccessVisibleAchievements]"') != 1:
        raise ValueError('Native row hierarchy changed; coordinate identity disabled')
    result = source.replace(ENTRY, ENTRY + BUTTON)
    if len(BUTTON) > 4096 or result.count('text = "vicmod_identify_click"') != 1:
        raise ValueError('Identity probe exceeds its fixed widget budget')

    def write(name, text):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8' if name.endswith('.json') else 'utf-8-sig')

    for name in ['jomini_achievements_window.gui', 'popup.gui']:
        path = output / 'gui/achievements' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((game / 'gui/achievements' / name).read_bytes())
    write('gui/achievements/jomini_achievements_types.gui', result)
    write('gui/vicmod_memory_window.gui', '# Memory display remains disabled pending verified click identity.\n')
    write('common/scripted_guis/vicmod_capture_probe.txt', '''vicmod_identify_click = {
        scope = country
        effect = { debug_log = vicmod_identify_message }
    }
''')
    for language, label, tooltip in [
        ('simp_chinese', '识别此成就', '在“全部”页点击已解锁成就以记录其身份。'),
        ('english', 'Identify achievement', 'Identify an unlocked achievement from the All list.')
    ]:
        write(f'localization/{language}/vicmod_capture_probe_l_{language}.yml',
              f'l_{language}:\n vicmod_identify_click:0 "{label}"\n vicmod_identify_tooltip:0 "{tooltip}"\n'
              f' vicmod_identify_message:0 "VICMOD_CLICK_V1|table={table}'
              '|all=[GetVariableSystem.Get(\'vicmod_click_all\')]|unlocked=[GetVariableSystem.Get(\'vicmod_click_unlocked\')]'
              '|groups=[GetVariableSystem.Get(\'vicmod_click_groups\')]|group=[GetVariableSystem.Get(\'vicmod_click_group\')]'
              '|row=[GetVariableSystem.Get(\'vicmod_click_row\')]|count=[GetVariableSystem.Get(\'vicmod_click_count\')]"\n')
    write('.metadata/metadata.json', json.dumps({
        'name': 'Vic Mod Memory - Capture Probe',
        'id': 'com.github.YangtzeMa.Vic-mod.capture-probe',
        'version': '0.0.6', 'game_id': 'victoria3',
        'supported_game_version': '1.15.*',
        'short_description': 'Native list identity probe; All filter only; no OCR, no automatic record writes.',
        'tags': ['Utilities'], 'relationships': [],
        'game_custom_data': {'multiplayer_synchronized': True},
    }, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    build(args.game, ROOT / '.local/memory-probe')
    print('Generated identity probe 0.0.6: identification buttons visible only in All; no background process.')
