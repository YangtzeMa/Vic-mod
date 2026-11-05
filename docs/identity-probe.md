# 成就按钮身份识别检查点

0.0.7在此已验证的坐标链路上增加会话记忆列表和退出后保存。用户已试用并给予良好反馈，日志确认新增记录在游戏退出后保存、快照更新，助手在下一次启动继续运行。测试入口为 `companion/run_memory.py`；详细证据和未单独确认的显示检查见 [validation.md](validation.md) 与 [testing.md](testing.md#本地记忆与显示测试实验-007)。以下内容描述此前0.0.5/0.0.6识别检查点。

当前可用入口是 `scripts/build_identity_probe.py` 与 `companion/read_identity_clicks.py`。目标 Victoria 3 1.15.0（Steam build 26453692）。这仍是开发实验：正式 `mod/` 保留空框架，生成的 Capture Probe 在忽略的 `.local/memory-probe/`，不提交原版 GUI 内容。

## 已验证范围

用户在普通战役、原版成就“全部”页自行选择三项已解锁成就，未预告名称。根据日志解析出“酒品公卖局 → 把门开开 → 机构建制”，用户确认名称与顺序完全一致。三项均在 easy_group；其他组尚无游戏内证据。记忆列表、持久化和自动捕获尚未接入此路径。

## 识别方式

每个原版成就行只增加一个按钮。按钮读取本行 `GUIAchievement.GetAchievement.IsUnlocked`，以及 `PdxGuiWidget.GetIndexInDataModel` 返回的行索引和祖先分组索引；将 int32 转为 CString，通过已经验证的 scripted GUI 日志通道输出 `VICMOD_CLICK_V1`。

读取器解析安装版 `common/achievement_groups.txt` 的分组顺序，将组索引和行索引还原成稳定 ID，再用本机中英文本地化显示名称。它校验完整152项覆盖、重复ID、对应表指纹、All/解锁状态、组数、组内数量和坐标范围；不依赖预设目标名称，不使用 OCR，不启动后台程序，也不写真实成就记忆。

筛选会压缩原版列表，因此只支持“全部”页。0.0.6起，其他筛选页隐藏识别按钮；保留回调和读取器的 All 校验，避免位置变化造成错误映射。旧的名称转换、OCR、窗口和后台记录器实验不是此检查点的受支持入口。

## 使用与检查

```powershell
python scripts/build_identity_probe.py --game "<Victoria 3/game>"
python -X utf8 companion/read_identity_clicks.py --game "<Victoria 3/game>" --logs "<Victoria 3 user directory/logs>"
```

在 Launcher 中启用已注册的独立 Capture Probe 播放集，普通启动并进入战役。点击后正常退出再读取日志；已观察到退出前的日志缓冲。具体盲测流程和限制见 [testing.md](testing.md)，实际证据见 [validation.md](validation.md)。

只生成和读取本地实验，不会修改原版文件、Steam 状态、成就规则或用户存档。当前正式 ZIP 仍为空模板，不能当作成就记忆功能的发布包。
