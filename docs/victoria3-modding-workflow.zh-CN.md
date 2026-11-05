# Victoria 3 Mod 制作基本流程：适用于 AI 辅助开发

整理日期：2026-11-05（北京时间）。基于用户提供的前序聊天、Paradox 官方开发日志、社区作者的一手开发记录与工具文档。

本文是后续开发的入门参考。本次完成了资料阅读与流程整理，尚未核验本机游戏版本、安装路径或 DLC，也未创建可加载 Mod、安装工具或进行游戏测试。以下目录树和命令均为后续操作示例。

**基本路线：确定一个可验收的小功能 → 查当前版本原版实现 → 建立可加载工程 → 编写最小改动 → 静态检查 → 游戏内验证与日志排错 → Git 保存 → 扩展、发布和维护。**

**1. 先理解 V3 Mod 在修改什么**

Victoria 3 的常规内容 Mod 主要由 Paradox 脚本、数据定义、本地化、界面和素材构成。脚本常见形式是 `key = value` 和 `key = { ... }`。开发时通常直接编辑文本与资源文件，再让游戏加载；Python、PowerShell 等可以用于生成文件或检查工程。能否实现某项机制，取决于游戏引擎开放了哪些接口；遇到没有暴露的功能，需要调整设计或寻找替代实现。

官方入门教程展示了从目录、定义、历史设置到本地化的完整关联。它发表于 2022 年，适合理解工作方式，具体文件内容应对照当前版本使用。[官方 Dev Diary #60](https://www.paradoxinteractive.com/games/victoria-3/news/victoria-3-dev-diary-60-modding)

开发前至少认识下面这些概念：

| 概念 | 含义 | 开发时需要回答的问题 |
| --- | --- | --- |
| 定义与标识符 | 用唯一 key 定义建筑、生产方式、法律、事件等内容 | 引用的对象存在吗？新 key 是否与别人冲突？ |
| Scope（作用域） | 当前正在操作的国家、州、建筑、角色等对象 | 这条命令支持当前对象吗？切换对象后 `root`、`prev` 指谁？ |
| Trigger（条件） | 判断某个条件是否满足 | 功能何时显示、激活、允许执行或结束？ |
| Effect（效果） | 改变游戏状态 | 执行后改变什么？作用于谁？执行几次？ |
| Modifier（修正） | 给游戏对象增加数值影响 | 是哪种修正？支持哪个对象？数值是相加还是相乘？ |
| on_action（钩子） | 游戏或脚本在某个时机执行的入口 | 谁会调用这段逻辑？入口提供哪些作用域？ |
| Localization（本地化） | 将脚本 key 转换成玩家看到的文本 | 标题、描述、选项和提示是否都有对应文字？ |

这些名称相近的系统不能互换。尤其要区分玩家拥有的州（`state`）与地图上的州区域（`state_region`），并检查每个 trigger/effect 的受支持作用域。可参考当前版本导出的 [1.15 技术文档目录](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/tree/main/1.15.0/docs)；正式编码时仍优先读取本机同版本文档。

**2. 对前序聊天的核对与补充**

| 前序建议 | 本次整理后的结论 |
| --- | --- |
| Git 仓库与游戏安装目录分开，`mod/` 放实际内容 | 保留。当前工作区可以继续使用 `F:\Vic-mod`。 |
| Windows 用 Junction 连接仓库与游戏的本地 Mod 目录 | 保留。链接目标必须是仓库的 `mod/`，且先核对实际 Documents 路径。 |
| 通过 `.metadata/metadata.json` 识别 Mod | 保留。优先以当前 Launcher 实际生成的文件为起点。 |
| 新项目面向 1.15 | 官方已公告 1.15 发布；实际开发基线仍须记录本机安装的完整版本。 |
| 社区模板能直接使用 | 需要检查。此次读取模板时，版本字段仍为 `1.8.*`，并存在占位内容与旧目录写法。 |
| 尽量少做原版整文件覆盖 | 保留，并补充数据库条目模式：支持的数据库应使用 `INJECT:`、`REPLACE:` 等显式处理已有对象。 |
| 参考旧事件、日志条目教程 | 必须核对版本。1.15 的日志条目结局系统发生破坏性变更。 |
| 静态检查后就算完成 | 需要游戏内验收，尤其要验证正常触发路径、数值结果和读档行为。 |

版本事实由 [Steam 官方公告](https://steamcommunity.com/app/529340/announcements/)核对：2026-11-05 发布 1.15。社区模板的旧默认值见其 [metadata.json](https://github.com/Victoria-3-Modding-Co-op/Mod-Template/blob/main/mod/.metadata/metadata.json)。模板结构可借鉴，但改兼容版本字段本身不会完成代码迁移。

**3. 第一步：把想法写成可验证的需求**

建议第一轮只做一个小功能。例如：为一个建筑增加一种生产方式；为一个国家增加一个有条件的决议；增加一段可触发且有中文文本的事件。先完成能从正常游戏入口使用的功能，再扩展成完整机制。

每项需求至少说明：适用国家或建筑、出现条件、玩家操作、具体结果、持续时间、是否允许重复、AI 是否使用，以及如何判断成功。经济改动还应说明投入、产出、就业、成本和解锁条件。

可采用下面的任务描述：

```text
功能目标：
适用对象：
出现与解锁条件：
玩家如何使用：
执行效果与持续时间：
重复执行与 AI 行为：
中文显示要求：
游戏内验收标准：
```

这一阶段的交付物是一小段清晰需求，足以让作者和 AI 对同一次游戏操作的结果达成一致。

**4. 第二步：记录版本与本地路径**

建议在后续工程的 `docs/game-environment.md` 中记录：完整游戏版本、测试日期、启用的 DLC、原版 `game/` 路径、实际用户数据目录、测试播放集、文档导出日期及校验器版本。

三种位置应分别管理：

| 位置 | 用途 | Git 管理建议 |
| --- | --- | --- |
| `F:\Vic-mod` | 开发项目与文档 | 管理自己编写的文件 |
| Steam 库中的 `Victoria 3\game` | 查询原版实现、帮助文本与素材路径 | 只读参考，避免复制整个原版目录 |
| 实际 Documents 中的 `Paradox Interactive\Victoria 3` | 本地 Mod、日志、存档及导出文档 | 日志、存档、机器路径通常不提交 |

Windows Documents 可能重定向到 OneDrive，可用以下命令确定：

```powershell
[Environment]::GetFolderPath('MyDocuments')
```

资料取舍建议：同版本本机原版文件和导出文档优先；遇到引擎行为问题，用最小游戏实验核对；其次查询官方版本变更、社区作者的对应版本实测记录，再参考 Wiki 和旧教程。AI 的记忆只用于提出检索方向。

**5. 第三步：建立最小工程并接入 Launcher**

推荐的后续结构如下，内容目录按需求创建：

```text
F:\Vic-mod\
├── mod\
│   ├── .metadata\metadata.json
│   ├── common\                 按需添加定义、历史或逻辑
│   ├── events\                 按需添加事件
│   ├── localization\simp_chinese\
│   └── gfx\、gui\ 等           有实际需要时添加
├── docs\                       需求、环境、实现说明、测试记录
├── scripts\                    有需要再添加检查与生成工具
├── AGENTS.md                    后续 AI 协作约定
├── README.md
└── .gitignore
```

先通过当前 Launcher 创建一个空 Mod，确认它生成的元数据及目录；再将实际内容整理到仓库中。也可以参考 [Modding Co-op 模板](https://github.com/Victoria-3-Modding-Co-op/Mod-Template)，但要处理占位事件、旧版本字段及目录差异。V3 的钩子目录为 `common/on_actions/`，应按本机原版核对，避免照搬 CK3 的单数写法。[工具作者的目录核对记录](https://github.com/JDeffner/paradox-modding-toolkit/wiki/Supported-Games)

后续需要建立链接时，可使用 PowerShell 的 `New-Item -ItemType Junction`。下面只展示创建步骤；本次没有执行：

```powershell
$vicRepoMod = 'F:\Vic-mod\mod'
$vicDocuments = [Environment]::GetFolderPath('MyDocuments')
$vicLocalMods = Join-Path $vicDocuments 'Paradox Interactive\Victoria 3\mod'
$vicLocalLink = Join-Path $vicLocalMods 'vic-mod-dev'

if (-not (Test-Path -LiteralPath (Join-Path $vicRepoMod '.metadata\metadata.json'))) {
    throw '请先创建仓库中的 mod 目录和元数据。'
}
New-Item -ItemType Directory -Path $vicLocalMods -Force | Out-Null
if (Test-Path -LiteralPath $vicLocalLink) {
    throw '链接位置已存在，请检查已有目录，勿直接覆盖。'
}
New-Item -ItemType Junction -Path $vicLocalLink -Target $vicRepoMod
```

链接方式与链接目标可对照 [模板的 Windows 说明](https://github.com/Victoria-3-Modding-Co-op/Mod-Template#adding-your-mod-to-the-game)。然后在 Launcher 中建立专用播放集，加入并启用本地 Mod。第一轮验收是 Launcher 能识别它，游戏能启动并新开测试局。

**6. 第四步：先找到原版参照，再选择修改方式**

先定位当前原版中最接近需求的对象，读取其定义、帮助文本和引用。仅找到一个同名 key 通常还不够：新增生产方式可能还涉及生产方式组、建筑关联、解锁条件与本地化；新增国家可能涉及国家定义、领土、人口、建筑和开局历史。

| 需求 | 常见检索位置（相对原版 `game/` 或 Mod 根目录） |
| --- | --- |
| 建筑、生产方式与商品 | `common/buildings/`、`common/production_methods/`、`common/production_method_groups/`、`common/goods/` |
| 法律、科技与数值修正 | `common/laws/`、`common/technology/`、`common/static_modifiers/`、`common/modifier_type_definitions/` |
| 事件、日志条目与决议 | `events/`、`common/journal_entries/`、`common/journal_entry_groups/`、`common/decisions/` |
| 触发入口与复用逻辑 | `common/on_actions/`、`common/scripted_effects/`、`common/scripted_triggers/`、`common/script_values/` |
| 国家与开局状态 | `common/country_definitions/`、`common/history/`；地图资源另查 `map_data/` |
| 文字、图标与界面 | `localization/`、`gfx/`、`gui/` |

这些目录是检索地图，具体依赖仍由功能决定。目录与原版实测示例见 [Mod 结构参考](https://github.com/Autumnnus/vic3-mod-tools/blob/main/docs/reference/01-mod-structure.md)。

对已有内容进行修改时，先区分以下情况：

| 情况 | 推荐处理 |
| --- | --- |
| 增加自己的内容 | 新文件、新 key，使用统一且独特的前缀与事件命名空间 |
| 修改已有数据库对象 | 检查目标数据库是否支持条目模式，再显式注入或替换 |
| 替换原版整个文件 | 保持完全相同的相对路径，并保留仍需要的其他内容；记录覆盖理由 |
| GUI、本地化、历史执行等特殊加载内容 | 查对应系统规则，不能直接套用数据库对象的处理方式 |

**当前版本尤其要理解 Database Entry Modes。** 官方在 1.12 更新前说明：支持这一机制的数据库不再接受旧式隐式替换，需要明确指定模式。核心模式如下：

| 写法 | 对已有对象的操作 | 目标不存在时 |
| --- | --- | --- |
| `INJECT:key` | 注入内容 | 报错 |
| `REPLACE:key` | 替换整个条目 | 报错 |
| `TRY_INJECT:key` | 尝试注入 | 跳过 |
| `TRY_REPLACE:key` | 尝试替换 | 跳过 |
| `INJECT_OR_CREATE:key` | 注入或新建 | 新建 |
| `REPLACE_OR_CREATE:key` | 替换或新建 | 新建 |

注入并不等同于“把数值设为我写的值”。官方给出的修正示例是：已有 25%，再注入 50%，结果为 75%。应检查字段语义与目标数据库支持情况，再决定使用哪种模式；替换整个条目仍可能与其他 Mod 冲突。[官方 Dev Diary #164](https://steamcommunity.com/games/529340/announcements/detail/588409432234263926)

同路径文件覆盖也会影响整份文件。只想新增一个事件时，不应意外使用原版文件名而遮蔽其中全部事件。对每个整文件覆盖保留一条记录，之后更新游戏时重新比较。

**7. 第五步：实现功能，补齐入口与文字**

一次实现一个能够验证的改动。新增事件后，需要说明由哪个钩子、日志条目、决议或其他事件调用；通过控制台手动触发，只验证了其中一部分行为。新增生产方式后，需要确认建筑中可以正常选择它，而且科技与条件按预期限制使用。

简体中文本地化通常采用以下对应关系，创建时应对照本机原版：

```text
目录：mod/localization/simp_chinese/
文件：vicmod_content_l_simp_chinese.yml
```

```yaml
l_simp_chinese:
 vicmod_example_title:0 "示例标题"
 vicmod_example_desc:0 "示例说明。"
```

本地化采用 UTF-8 with BOM，文件名语言后缀、首行语言标记和脚本引用的 key 必须一致。脚本文本也建议匹配本机原版编码；“原版使用 BOM”与“所有类型文件缺少 BOM 都必然被拒绝”是不同结论，不应混写。以上布局和编码惯例可参考 [作者的 setup 记录](https://github.com/JDeffner/paradox-ai-modding/blob/main/plugins/paradox-ai-modding/skills/vic3-modding/references/setup.md)，该记录注明其验证基线为 1.13.10，需要结合当前版本使用。

工程路径、文件名和脚本标识符建议使用 ASCII 字符，中文放在显示文本中。图标先复用合适的原版资源路径，可以减少首轮实现的依赖。

**1.15 的具体注意事项：** 日志条目的旧 `complete`、`on_complete`、`fail`、`invalid` 等块已经整合为新的 `outcome` 机制；自定义进度条及日志条目组插图也涉及迁移。不要直接使用旧教程生成一套日志条目。[1.15 破坏性变更](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/main/1.15.0/changes_breaking.md)、[1.15 日志条目结构文档](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/main/1.15.0/types/journal_entries.md)

**8. 第六步：静态检查与游戏内验证分开进行**

建议按下面顺序验证，前一层通过后再继续：

| 层次 | 要验证什么 | 可以得出的结论 |
| --- | --- | --- |
| 文件检查 | 路径、JSON、括号、引号、编码、key 与引用 | 工程结构与基础文本检查通过 |
| 脚本校验 | 运行匹配游戏版本的 `vic3-tiger`，检查标识符、作用域与本地化 | 静态校验通过，或存在已说明的诊断 |
| 加载检查 | 仅启用目标 Mod，启动游戏并新开局 | 游戏能够加载这组内容 |
| 功能检查 | 从正常入口操作，分别测试条件成立与不成立 | 指定功能在已测试情形下符合预期 |
| 持续与回归检查 | 推进时间、重复操作、保存读档、相关系统与必要的 AI 行为 | 这些场景已经验证 |

[Tiger](https://github.com/amtep/tiger) 能检查语法、引用、本地化和作用域等问题。V3 使用 Mod 目录作为输入，例如 `vic3-tiger "F:\Vic-mod\mod"`。作者明确说明，校验器可能有误报，也可能晚于游戏补丁更新；应记录其版本并核对诊断，不能靠批量屏蔽错误来证明兼容。

调试启动参数：

```text
-debug_mode
```

进入测试局后，可以在控制台生成文档：

```text
script_docs
dump_data_types
```

当前工具作者记录：前者输出到用户目录的 `docs/`，后者将界面数据绑定文档输出到 `logs/data_types/`。旧资料可能写作 `DumpDataTypes`，应以本机控制台可用命令为准。[文档导出步骤](https://github.com/JDeffner/paradox-ai-modding/wiki/Victoria-3-Getting-Started)

排错时优先查看本次运行新产生的日志：

- `logs/error.log`：加载与脚本错误的主要入口。
- `logs/game.log`：结合触发时刻检查运行时脚本问题。
- `logs/database_conflicts.log`：辅助检查数据库冲突与覆盖情况。

官方教程强调了 debug mode 和 `error.log` 的用途；其他日志示例见前述 [结构与调试记录](https://github.com/Autumnnus/vic3-mod-tools/blob/main/docs/reference/01-mod-structure.md)。

建议先保存一次无 Mod 的基线日志，再比较启用 Mod 后新增的问题。日志为空也不代表功能必然正确：还需要观察实际结果。不确定热重载是否覆盖本次修改时，重新启动；涉及开局历史、地图或结构变化时，优先使用新档验证。

经济、AI 或循环逻辑应额外观察游戏速度与长期数值。避免把本来只涉及一个国家的检查写成高频全世界遍历。

**9. 第七步：把 Vibe Coding 组织成可重复的协作方式**

建议项目后续的 `AGENTS.md` 记录以下约定：

- 版本、原版路径、日志和导出文档位置，以及统一 key 前缀。
- 修改前查同版本原版示例；未验证的 trigger、effect、modifier 和数据绑定先标明不确定性。
- 实际内容写入 `mod/`，原版和其他 Mod 只作参考。
- 新增定义、显式数据库修改与整文件覆盖分别说明理由。
- 涉及同一数值时，说明注入、替换、叠加和单位。
- 完成报告列出文件、验证结果、游戏内验收步骤及剩余问题。

这些是本项目可采用的协作规则，本次尚未写入生效的 `AGENTS.md`。

每轮可直接使用下面的提示：

```text
请为本项目实现以下小功能：[填写需求]。

先读取项目约定、已记录的游戏版本和相关文档。
在当前原版中找到对应实现，说明要引用的对象、作用域与正常触发入口。
核对目标数据库的修改方式及数值叠加行为，再实施最小改动。
补齐中文本地化并运行现有静态检查。
最后报告改动文件、检查结果、游戏内操作步骤与预期结果。
未完成游戏内测试的部分请明确标注。
```

建议将每个小功能的原版参照、设计决定与测试结论记入 `docs/`。对于难以复现的问题，记录游戏版本、播放集顺序、开局国家、操作顺序、预期/实际结果及当次日志。作者提供的 [AI 辅助 Mod 工作流](https://github.com/JDeffner/paradox-ai-modding)也采用了从本地依据、静态验证到游戏内证据的流程；它属于可选工具，并非开始开发的必要条件。

**10. 第八步：保存、发布与适配更新**

每完成一个已验证的小功能，保存一个清晰的 Git 提交。测试记录应区分“已实现”“静态检查通过”“游戏内通过”，不要把尚待测试的功能记为完成。

准备发布时，建议检查以下内容：

- 发包内容以 `mod/` 为边界，排除仓库文档、日志、存档和临时生成物。
- Mod 名称、稳定 ID、Mod 版本、游戏兼容版本与封面正确。
- 描述说明作用、依赖、已验证的游戏版本、加载顺序和已知冲突。
- 新档及读档行为有测试依据；会改变地图或开局历史时说明存档限制。
- 经由当前 Launcher 或所用发布工具的实际流程发布；不要同时启用本地版和订阅版进行验收。

模板将开发文档与可发布内容分开的目的，见 [模板目录说明](https://github.com/Victoria-3-Modding-Co-op/Mod-Template#folder-structure)。游戏更新后，先保存可用版本，再重新导出文档，检查覆盖过的原版文件、引用 key、结构变化和校验器支持情况，最后重测受影响功能。社区维护的 [Modding Digests](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests)适合用于定位差异。

**11. 第一轮开发的建议验收目标**

这是针对当前项目的工作建议，尚未执行：

1. 查明本机游戏版本、DLC、原版和用户数据路径。
2. 建好最小 Mod 目录，接入 Launcher，使用独立播放集成功启动。
3. 导出当前版本文档，保存基线日志。
4. 选一个数值、生产方式、决议或事件作为第一项功能。
5. 补齐文字，从正常入口验证条件与结果，检查新增日志错误。
6. 保存第一个可以复现测试结果的 Git 提交。

可选工具方面，[Paradox Modding Toolkit](https://marketplace.visualstudio.com/items?itemName=JDeffner.px-toolkit)提供 V3 补全、导航和 Tiger 集成，当前仍标注 Beta。先让基础加载与验证流程跑通，再按实际需要增加工具。

**资料可用性说明：** 本次部分 Victoria 3 Wiki 页面返回访问限制，因此没有将其当作已阅读全文的依据；使用官方公告、开发者原文及作者仓库交叉核对。前序聊天中的 `Autumnnus/vic3-mod-tools` 旧 `codex/standalone-tools/` 链接已失效，本次定位到的参考文件位于 `main/docs/reference/`。所有网络资料都应检查适用版本，尤其不能把 1.13 的实测记录当作已完成 1.15 游戏测试的证明。
