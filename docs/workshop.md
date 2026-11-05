# 创意工坊上传准备

当前项目准备可上传的内容目录与 ZIP，不会自动创建创意工坊条目。正式发布由用户提出发布要求后执行。

## 已提供的内容

- 可加载目录：仓库中的 `mod/`。
- 描述文件：`mod/.metadata/metadata.json`，游戏 ID 为 `victoria3`。
- 稳定 Mod ID：`com.github.YangtzeMa.Vic-mod`。
- 原创占位封面：根目录和 `.metadata/` 中的 `thumbnail.png`，1024×1024 RGB PNG。
- 版本：Mod `0.1.0`；目标游戏 `1.15.*`。
- 依赖：无；当前内容：空框架，不修改玩法。

封面由 `scripts/make_thumbnail.py` 绘制，无第三方游戏素材。开发文档、Git 文件与本地日志都在上传目录外。

## 正式发布步骤

1. 先完成并记录 [测试流程](testing.md)。
2. 如已有正式主题，更新显示名称、描述、标签和封面；继续沿用稳定 ID。
3. 使用当前 Paradox Launcher 的 Mod 上传功能选择本地 Mod，发布到 Steam Workshop。具体入口以本机界面为准。
4. 填写准确的中英文说明，写明游戏版本、功能、依赖和已知限制。空框架发布时必须明确没有玩法内容。
5. Steam 账户须拥有游戏并满足 Steam 的上传条件；如要求接受 Workshop 协议，由用户本人完成。
6. 后续更新已有条目，保留发布平台分配的 Workshop ID，避免误建重复条目。
7. 测试订阅版时关闭本地开发版，避免同一 Mod 被同时加载。

ZIP 是备份与分发构建产物；Launcher 通常从已注册的本地 Mod 目录上传，并非把整个 GitHub 仓库作为游戏 Mod 上传。

参考：[Paradox 官方 Mod 入门](https://www.paradoxinteractive.com/games/victoria-3/news/victoria-3-dev-diary-60-modding)、[Modding Co-op 模板](https://github.com/Victoria-3-Modding-Co-op/Mod-Template)。
