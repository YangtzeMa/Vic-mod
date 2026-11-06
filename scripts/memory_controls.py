"""Frontend and bounded bulk controls for the manually accepted 0.0.8 UI."""
import re


def upgrade(types, window, groups, table, body_of):
    prefix = f'vicmod_seen_{table}_'
    group_prefix = f'vicmod_group_{table}_'
    start = types.index('        button_standard_list = {', types.index('type widget_achievement_list_entry'))
    body, end = body_of(types[start:], 'button_standard_list = {')
    actions = [line.strip().replace('onclick =', 'on_start =', 1)
               for line in body.splitlines() if line.strip().startswith('onclick =')]
    actions = [line for line in actions if 'GetScriptedGui' not in line]
    # Animation lives on the row, so its widget context IS the old button's parent.
    actions = [line.replace('PdxGuiWidget.AccessParent.AccessParent.AccessParent.GetIndexInDataModel',
                            'PdxGuiWidget.AccessParent.AccessParent.GetIndexInDataModel')
                   .replace('PdxGuiWidget.AccessParent.GetIndexInDataModel', 'PdxGuiWidget.GetIndexInDataModel')
               for line in actions]
    # The second replacement must not shorten the group chain again.
    actions = [line.replace('ToString_int32(PdxGuiWidget.AccessParent.GetIndexInDataModel)',
                            'ToString_int32(PdxGuiWidget.AccessParent.AccessParent.GetIndexInDataModel)')
               if 'vicmod_click_group\'' in line else line for line in actions]
    valid = "And(AchievementWindow.ShouldShowAll, GUIAchievement.GetAchievement.IsUnlocked)"
    flag = f"Concatenate4('{prefix}', GetVariableSystem.Get('vicmod_click_group'), '_', GetVariableSystem.Get('vicmod_click_row'))"
    gflag = f"Concatenate('{group_prefix}', GetVariableSystem.Get('vicmod_click_group'))"
    actions = [line for line in actions if 'Concatenate' not in line]
    actions += [
        f'''on_start = "[GetVariableSystem.Set({flag}, Select_CString(Or(GetVariableSystem.HasValue({flag}, '1'), {valid}), '1', '0'))]"''',
        f'''on_start = "[GetVariableSystem.Set({gflag}, Select_CString(Or(GetVariableSystem.HasValue({gflag}, '1'), {valid}), '1', '0'))]"''',
        f'''on_start = "[GetVariableSystem.Set(Concatenate4('vicmod_batch_', GetVariableSystem.Get('vicmod_click_group'), '_', GetVariableSystem.Get('vicmod_click_row')), GetVariableSystem.Get('vicmod_click_unlocked'))]"''',
        '''on_start = "[GetVariableSystem.Set(Concatenate('vicmod_batch_count_', GetVariableSystem.Get('vicmod_click_group')), GetVariableSystem.Get('vicmod_click_count'))]"''',
        f'''on_start = "[GetScriptedGui(Select_CString(And({valid}, Not(GetVariableSystem.Exists('vicmod_bulk_active'))), 'vicmod_frontend_click', 'vicmod_skip_click')).Execute(GuiScope.End)]"''',
    ]
    properties = '\n'.join(line for line in body.splitlines() if not line.strip().startswith('onclick ='))
    properties = properties.replace('[And(AchievementWindow.HasGameStarted, AchievementWindow.ShouldShowAll)]',
                                    '[AchievementWindow.ShouldShowAll]')
    replacement = ('        button_standard_list = {' + properties +
                   '\n onclick = "[PdxGuiWidget.AccessParent.TriggerAnimation(\'vicmod_remember_row\')]"\n}\n'
                   'state = { name = vicmod_remember_row duration = 0.01\n' + '\n'.join(actions) + '\n}\n')
    types = types[:start] + replacement + types[start + end:]
    types = types.replace('type vbox_achievement_group = vbox {', '''type vbox_achievement_group = vbox {
        state = {
            name = vicmod_bulk_expand
            trigger_when = "[And(GetVariableSystem.Exists('vicmod_bulk_active'), Group.IsCollapsed)]"
            on_start = "[Group.ToggleCollapsed]"
            duration = 0.01
        }
''', 1)
    # Zero is a valid snapshot value for locked rows, but must never display them.
    window = re.sub(r"GetVariableSystem.Exists\('(vicmod_(?:seen|group)_[^']+)'\)",
                    r"GetVariableSystem.HasValue('\1', '1')", window)
    clears = '\n'.join(f'''onclick = "[GetVariableSystem.Clear('vicmod_batch_{g}_{r}')]"'''
                       for g, group in enumerate(groups) for r in range(len(group['ids'])))
    clears += '\n' + '\n'.join(f'''onclick = "[GetVariableSystem.Clear('vicmod_batch_count_{g}')]"'''
                                for g in range(len(groups)))
    bulk = '''button_standard_list = {
        size = { 260 30 }
        text = "vicmod_bulk_remember"
        visible = "[AchievementWindow.ShouldShowAll]"
        enabled = "[Not(GetVariableSystem.Exists('vicmod_bulk_active'))]"
''' + clears + '''
        onclick = "[GetVariableSystem.Set('vicmod_bulk_active', '1')]"
        onclick = "[PdxGuiWidget.TriggerAnimation('vicmod_bulk_start')]"
        state = {
            name = vicmod_bulk_start
            duration = 0.2
            next = vicmod_bulk_finish
            on_finish = "[PdxGuiTriggerAllAnimations('vicmod_remember_row')]"
        }
        state = {
            name = vicmod_bulk_finish
            duration = 0.3
            on_finish = "[GetScriptedGui('vicmod_bulk_record').Execute(GuiScope.End)]"
            on_finish = "[GetVariableSystem.Clear('vicmod_bulk_active')]"
        }
    }
'''
    window = window.replace('### CONTENT ###', bulk + '### CONTENT ###', 1)
    # No world or country reference: these effects only write local diagnostic text.
    sguis = '''vicmod_frontend_click = {
        scope = none
        effect = { debug_log = vicmod_identify_message }
    }
    vicmod_skip_click = { scope = none effect = {} }
    vicmod_bulk_record = {
        scope = none
        effect = {
''' + '\n'.join(f'debug_log = vicmod_bulk_message_{g}' for g in range(len(groups))) + '\n}\n}\n'
    loc = ''
    for g, group in enumerate(groups):
        bits = ''.join(f"[Select_CString(GetVariableSystem.HasValue('vicmod_batch_{g}_{r}', '1'), '1', Select_CString(GetVariableSystem.HasValue('vicmod_batch_{g}_{r}', '0'), '0', '?'))]"
                       for r in range(len(group['ids'])))
        loc += (f' vicmod_bulk_message_{g}:0 "VICMOD_BULK_V1|table={table}'
                "|all=[GetVariableSystem.Get('vicmod_click_all')]|groups=[GetVariableSystem.Get('vicmod_click_groups')]"
                f"|group={g}|count=[GetVariableSystem.Get('vicmod_batch_count_{g}')]|bits={bits}\"\n")
    return types, window, sguis, loc
