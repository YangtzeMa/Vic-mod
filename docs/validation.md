# 环境与验证记录

## 开发基线

- 检查日期：2026-11-05（北京时间）。
- 游戏版本：1.15.0，Launcher 显示 `1.15.0 (Ivan-Chai)`。
- Steam App ID：529340；本机安装 Build ID：26453692。
- 原版分支：`release/1.15.0`。
- 平台：Windows / Steam；仓库使用独立开发目录。
- 最初检查时仍为 1.13.11，用户完成更新后已重新读取文件确认 1.15.0；本项目按更新后的版本建立。
- 目标兼容范围：1.15.*。本机实际测试只能证明已记录的具体版本与场景。

## 本次检查状态

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| 可执行文件与 Launcher 版本 | 通过 | 两者均为 1.15.0；Steam 安装完成 |
| 原版成就规则 | 通过 | 更新后规则仍默认 `achievements_allowed`；禁用选项使用 `blocks_achievements` |
| 静态框架检查 | 通过 | 元数据、封面与空框架文件边界检查通过 |
| 打包与 ZIP 内容检查 | 通过 | 三份文件，ZIP 与源文件逐字节一致，包根结构正确 |
| 封面视觉检查 | 通过 | 1024×1024 原创占位封面显示正常 |
| 本地链接和 Launcher 注册 | 通过 | 目录联接与重复运行检查通过；Launcher 名称、封面显示正常；用户确认已在播放集中启用 |
| 正常启动与成就界面 | 通过（用户手动） | 用户确认正常启动、新开局、成就资格及推进数日均通过；本次不是实际解锁某项成就的测试 |
| GitHub 上传 | 通过 | 私有仓库 `YangtzeMa/Vic-mod` 已创建；首次上传后本地与远端 `main` 提交一致 |
| GitHub CI | 通过 | [首次运行](https://github.com/YangtzeMa/Vic-mod/actions/runs/42041426273)的元数据/封面检查、打包和构建产物上传均通过 |

待执行项目不能作为已经通过的结论。实际日志、机器路径和截图保存在忽略的 `.local/` 中；本文仅记录可核实的简洁结果。

本地链接工具改用 Python，避免依赖 PowerShell 脚本执行策略；未更改 Windows 执行策略。

## 手动运行验收与日志核对

用户于 2026-11-05 确认四项手动检查全部通过：播放集仅启用本模板、正常启动并新开局、成就面板未显示资格禁用、推进数日无崩溃或异常弹窗。此结论来自用户手动检查，未标记为自动界面测试。

随后核对本机加载配置：仅启用了 `vic-mod-dev`，无其他 Mod；运行日志记录版本为 `release/1.15.0`。

本次 `error.log` 并非空文件：389 条记录中，374 条为游戏路径的纹理缺失，15 条为游戏建筑本地化 key 缺失；没有匹配到本项目名称、路径或前缀的条目。本模板也没有打包任何对应资源或脚本覆盖。未进行无 Mod 对照，不据此声称全部日志错误已被修复或已确定来源。

本次使用用户创建并启用的播放集，未更改用户原版游戏文件、已有存档或成就机制。测试后的播放集选择由用户保留。

## 2026-11-06：成就记忆实验（尚未通过）

目标仍为已安装的 Victoria 3 1.15.0（Steam build 26453692）。用户报告先前实验的补录及自然解锁均未进入本地列表，随后固定 ID 分支版本打开成就窗口卡死；该版本已停用，后台记录器已停止，失败生成器禁止重新部署。

后续单按钮诊断没有输出预期标记。轮换日志明确记录 `Could not find promote for 'Self' in 'GUIAchievement.Self'`，已移除错误的显式上下文绑定，并重新生成本地诊断版本。十项 Python 测试、框架校验、打包和 diff 空白检查通过；这些结果不证明游戏内捕获或性能通过。修订后的诊断点击、真实成就记录及跨重启展示均待验证。正式 `mod/` 仍为空模板；实验未提交为可用功能。

退出游戏后读取本次会话日志：01:02:08 及 01:04:16–17 的八条 `VICMOD_DIAG` 均为 `control=static-control`，`raw`、`concat`、`localize` 为空，`literal` 为未展开的 `[GUIAchievement.GetName]`。用户确认在战役中点击可用按钮。故确认本次点击已执行，动态名称捕获失败；退出前未出现记录，退出后可读取，后台即时捕获的日志延迟也需另行处理。不能把旧 00:38:02 的同类记录归为本次测试。

随后准备 0.0.3 诊断：仍只有一个按钮，新增已解锁布尔值对照，以及仅针对用户已完成的两项成就的固定 ID 比较。新标记使用 `VICMOD_DIAG_V2` 区分日志；不会导入真实完成记录。该版本尚无游戏内结果。

0.0.3 用户完成点击并正常退出后，01:11:37–43 日志出现六条 `VICMOD_DIAG_V2`：`control=static-control|context=unlocked|match=|raw=|concat=|localize=|literal=[GUIAchievement.GetName]`。确认按钮执行且可读取已解锁布尔状态；名称及名称比较路径仍不能输出稳定 ID。不能据此写入真实完成记录，也不能声称捕获通道可用。此轮未发现对应的新表达式错误日志；这不等于运行时表达式有效。

备选捕获可行性：本机 Windows OCR 提供 en-US 和 zh-Hans-CN。对用户先前提供的成就列表截图执行离线识别，经完整标题精确匹配得到五个候选 ID：achievement_knock_knock、anarchy_in_the_uk、deeds_not_words、the_berlin_conference、three_hurrahs。只忽略空格并统一 Unicode 宽度，不做模糊或子串匹配，规范化后重名则拒绝。候选结果没有写入用户记录。十二项离线测试通过。截图本身不足以证明完成状态；窗口实时采集、完成状态上下文识别、自动解锁捕获、性能和记忆展示均未实现或验收。本机未改变执行策略；Windows OCR 通过 PowerShell 命令文本调用。

## 2026-11-06：名称映射与本地化求值实验

按用户要求暂停 OCR 路线，继续名称捕获。用本机定义及中英文本地化生成忽略目录下的名称表：302 个无歧义名称对应 151 个稳定成就 ID；“穷困潦倒的芸芸众生”对应 poor_huddled_masses。新增测试确认双语别名导入同一记录、重名拒绝，不将显示名称直接作为永久主键。十三项离线测试、框架校验、打包、staged/unstaged 空白检查通过。

本地探针更新到 0.0.4，按钮为“取名测试”。不再直接把 CUTF8String 喂给字符串比较，而是尝试 Localize('vicmod_diag_current_name')，该本地化 key 的内容为 [GUIAchievement.GetName]；另测 $key$ 引用方式。对照读取固定原版标题并在 CString 之间比较，记录已解锁状态及是否仍为字面占位符。标记 VICMOD_DIAG_V3；每行仍只有一个按钮，无 OCR 或后台记录器。名称能否在 Localize 内按行上下文求值尚待游戏检查，不能把生成成功视为捕获成功。

研究参考：[另一 Mod 作者对 1.14.5 editbox CUTF8String 的直接实测记录](https://github.com/jakeOmega/Vic3TimelineExtended/blob/main/docs/guides/gui_modding_guide.md#typed-text-into-script-only-through-a-base-game-rename-popup-tested-in-game-1145)。与本项目现象相似，但不是本项目 1.15 验证结果；也未证明本轮间接本地化方案可行。

0.0.4 用户确认点击两次；本次日志 01:29:28、01:29:41 各收到一条 VICMOD_DIAG_V3，随后 01:29:43 正常退出。两次均为 context=unlocked、known=穷困潦倒的芸芸众生、known_match=known-match、name/alias 为空、expansion=not-literal、match=unmatched。对应 error.log 明确报 `Wrong context supplied, wanted context of type 'GUIAchievement' for 'GUIAchievement.GetName', got context 'Container'`，发生在 vicmod_diag_current_name 及 alias 的本地化求值。故固定 CString 标题与比较可用，间接本地化不能继承行对象上下文；名称映射仍未接通。这不证明原按钮缺少对象，也不将 not-literal 误认为已得到名称。无真实记录写入，OCR 继续暂停。没有部署下一轮猜测性实验。

## 2026-11-06：原版列表坐标识别（0.0.5，首轮盲测通过）

改用 `PdxGuiWidget.GetIndexInDataModel` 的 int32 返回值，经 ToString_int32 写 GUI 变量，再经已有脚本日志通道传出。该接口出现在已安装的原版 GUI（如 companies_panel、custom_tooltip）中，且 [1.15 GUI 数据接口导出](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/main/1.15.0/docs/data_types_gui.txt)列出了它及 AccessParent 的签名；不是新增或猜测的 GetID 方法。按钮还读取本行 GUIAchievement.GetAchievement.IsUnlocked。具体父层级索引能否对应目标分组和行，需要正常游戏实测。

发现本机 common/achievement_groups.txt 明确给出4组顺序和全部152个ID，组内数量为35/70/37/10，所有ID与实际成就定义一一覆盖。新脚本 build_identity_probe.py 仅在每行增加一个固定大小按钮，原版窗口和弹窗逐字节保留。按钮只在战役显示，只允许 All 页的已解锁项；日志传出对应表指纹、All/解锁布尔值、组数、组索引、行索引和组内数量。helper identity.py 不根据预设名称猜目标，拒绝过滤列表、数量不符、越界、缺字段和旧指纹，且不写用户记录。

修复名称目录解析未接受行尾注释的问题（bootlicker 的本地化带注释）；现在304个中英文名称覆盖152个稳定ID。19项离线测试通过：含152个坐标完整映射、失败拒绝、最新会话日志轮换、原版窗口/弹窗保留，以及扩大至10000项时新增GUI文本规模不变。框架校验、打包与diff检查通过；正常游戏盲测待执行，没有将其称为任意按钮识别已通过，也未推送为正式功能。当前会话尚无 VICMOD_CLICK_V1；读取器正常输出空列表，未把旧诊断当成新点击。

0.0.5 首轮盲测：用户仅告知选了3项并点击，没有预告名称。02:05:22、02:05:29、02:05:43 收到3条 VICMOD_CLICK_V1，02:05:49 正常退出；全部为 all=1、unlocked=1、groups=4、group=0、count=35，row 依次18、29、3。对应表指纹一致，读取器无拒绝项，解析顺序为 achievement_systembolaget（酒品公卖局）、achievement_knock_knock（把门开开）、institutional（机构建制）。这些是依据新日志和原版表推导的结果，尚待用户核对实际点击名称；本轮全在 easy_group，不据此宣称其余组或筛选页已验收。当前 error.log 未匹配到本轮接口错误；旧取名错误只见于轮换历史日志。没有向用户成就记忆写记录。

## 2026-11-06：本地记忆与显示 0.0.7（已试用，保存流程已核验）

新增 build_memory_ui.py 和 run_memory.py。保留0.0.6中盲测通过的原版行坐标捕获，仅在按钮点击后增加两个GUI变量赋值，用对应表指纹、组/行坐标构造会话标记；记忆页只显示保存记录或这些会话标记对应的条目。记忆页嵌入已有 achievements_window，打开入口不调用 Hide。显示行抽取原版 widget_achievement_list_entry 布局，沿用64×64图标、字体、标题、说明和分隔线，移除未完成叠层；已检查全部152项原版DDS存在。基础成就图标直接以ID命名，无统一 achievement_ 前缀，已修复并加回归覆盖。

remember_clicks 只接受既有 resolve_click 校验通过的身份包，按稳定ID去重、保留首次观测时间和旧诊断，临时文件flush/fsync后原子替换；损坏JSON拒绝覆盖。助手无OCR、无进程内存读取，只以SYNCHRONIZE权限等待游戏退出，随后导入日志并生成下一次启动的记忆快照。游戏未运行时每2秒枚举进程名称等待启动；运行时阻塞等待退出，不轮询屏幕或日志。

26项本地离线测试通过，其中新测试覆盖身份包持久化/重复通知/损坏文件保护、原版宿主保留、一成就一行、越界规模拒绝、正常退出后的快照生成及基础成就图标路径。已在忽略目录用本机原版文件生成152行并检查宿主括号平衡，未发现生成器错误；这些不证明游戏实际布局或会话变量可见性通过。

已从实际0.0.5盲测日志导入用户确认的3项（机构建制、酒品公卖局、把门开开），不是测试造假记录。旧 records.json 已备份到忽略目录，原diagnostics/unresolved保留。真实用户JSON中三项source均为 native_achievement_button，生成快照中恰好这三项初始可见。已启动本地隐藏助手，stdout为 MEMORY_READY saved=3、rows=152、rejected=[]，stderr为空；部署版本0.0.7，Launcher播放集仍只启用同一 Capture Probe。尚未观察游戏内即时新增、列表视觉、主菜单显示或跨重启结果，等待用户手动验证。本轮未提交为已验收功能，正式 mod/ 仍为空模板。

## 模板交付与同步记录

### 0.0.7 用户试用后的补充证据

用户随后评价此版本良好并要求确认GitHub同步。核对助手日志：检测到一次游戏退出后，MEMORY_READY 从 saved=3 更新到 saved=5，新增 mightier_than_the_sword、achievement_huge_ego_sorry，rejected=[]；随后检测到另一次游戏启动，助手继续等待其退出，stderr为空。真实records.json包含5个唯一ID，当前生成快照中初始可见的5项与JSON完全一致。确认真实点击记录经游戏退出后持久化、快照生成、助手跨两次启动持续运行这些环节通过。未在本轮用自动界面操作复测，也没有把用户的总体好评扩写成对即时显示、图标、返回及主菜单等每一项的单独确认。

提交范围仅为0.0.7记忆与显示代码、相关测试及文档；不包含本地记录、日志、生成的原版GUI或已停用的OCR/旧后台实验。26项本地测试通过，其中纳入GitHub CI的相关测试为19项；正式 mod/ 和模板ZIP边界保持不变。本次按已有GitHub同步授权保存0.0.7开发版本，仍保留尚未完成自动解锁捕获的限制。

已将上述用户核对通过的识别版本单独提交为 `15f2e5d4e575fb738972712fc3e337b485976cd0` 并推送 main；[GitHub Actions](https://github.com/YangtzeMa/Vic-mod/actions/runs/42081933883) 的空白、框架、识别单元测试、打包及产物步骤全部通过。检查点只包含坐标识别依赖、12项相关测试和文档；本地旧实验未混入提交。

随后按用户要求生成0.0.6：识别按钮的 visible 改为 HasGameStarted 且 ShouldShowAll，筛选页隐藏按钮；保留原来的 enabled、回调 All 校验及读取器校验。与0.0.5生成物比较，GUI仅此一行变化，其他变化为提示文字和实验版本号。19项本地离线测试通过，正式框架校验和打包通过。未重复运行游戏，筛选页隐藏效果待下次正常启动检查；不将此显示改动或未测试分组称为已完成游戏验收。

用户随后明确回复“完全一致”，确认上述三个名称及点击顺序均正确。因此将 0.0.5 在 All 页 easy_group 的三项识别标为用户手动盲测通过；其他分组、记忆持久化及自动捕获仍不在本次通过范围。用户授权先保存此版本，再隐藏筛选页的识别按钮。正式 mod/ 仍为空框架，识别实验由生成脚本部署到忽略目录，不将原版 GUI 文件提交仓库。

- 仓库：[YangtzeMa/Vic-mod](https://github.com/YangtzeMa/Vic-mod)，可见性为私有，默认分支为 `main`。
- 自动检查：[Validate and package](https://github.com/YangtzeMa/Vic-mod/actions/workflows/validate.yml)。每次推送及 Pull Request 自动运行，并提供 `vic-mod-package` 构建产物。
- 已配置本地 `origin/main` 跟踪与推送前检查。后续更改按 `AGENTS.md` 完成必要检查后及时提交和推送。
- 当前只准备 Workshop 上传目录与包；没有创建创意工坊条目。
