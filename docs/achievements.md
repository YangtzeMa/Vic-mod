# 成就兼容约定

目标：在正常支持成就的游戏设置下，加载本 Mod 不额外阻断原版成就。

Victoria 3 的成就机制不要求原版校验和或铁人模式，Mod 本身不是禁用成就的充分条件。官方最早在 [Dev Diary #55 — Achievements](https://forum.paradoxplaza.com/forum/developer-diary/victoria-3-dev-diary-55-achievements.1538861/)说明这一点。

本机 1.15.0 的原版依据：

- `game/common/game_rules/00_game_rules.txt` 中成就规则默认是 `achievements_allowed`。
- 同文件的禁用选项设置 `flag = blocks_achievements`。
- `game/common/game_rules/game_rules.md` 说明该标记会阻断成就。

本框架只打包元数据及两份封面，没有成就、规则、defines 或其他脚本，因此不改上述行为。多人同步元数据设为 `true` 与成就资格是两个独立事项；不通过伪造校验和或修改成就规则实现兼容。

验收方法：正常启动（成就验收不用调试启动），启用本地播放集，新开单人局，保持允许成就的游戏规则，查看该局成就面板是否显示可完成成就。记录游戏版本和观察结果。实际某项成就解锁仍须满足该成就自身的国家、规则、DLC 和进度条件。

不使用控制台强制完成成就，也不把“界面可用”写成“已经实际解锁全部成就”。具体本次证据见 [validation.md](validation.md)。
