# Vic Mod Template

Victoria 3 Mod 开发框架，目标游戏版本 **1.15.x**，当前 Mod 版本 **0.1.0**。

当前仅包含 Mod 元数据与原创占位封面，**没有事件、决议、数值修改或其他玩法代码**。后续功能按实际需求逐项添加。

已在 **1.15.0** 完成用户手动加载、成就资格与短时运行检查，并通过本地静态及打包检查。[验证记录](docs/validation.md)

## 工程结构

```text
mod/                         游戏加载和创意工坊上传的内容
  .metadata/metadata.json     名称、稳定 ID、版本和兼容范围
  .metadata/thumbnail.png     Launcher 占位封面
  thumbnail.png               创意工坊占位封面
docs/                        开发、测试与发布说明
scripts/                     校验、打包、本地链接和封面生成工具
.github/workflows/           GitHub 自动检查与打包
.githooks/                   本地推送前检查
AGENTS.md                    本项目的 AI 开发与 GitHub 同步约定
```

Mod 稳定 ID：`com.github.YangtzeMa.Vic-mod`。显示名称可在确定正式主题后修改；发布后保持 ID 连续。

## 本地使用

需要 Python 3.12+；日常校验和打包只使用 Python 标准库。

```powershell
python scripts/validate_mod.py
python scripts/package_mod.py
python scripts/link_local_mod.py
```

链接脚本将仓库的 `mod/` 接入当前 Windows 用户真实 Documents 下的 Victoria 3 本地 Mod 目录，遇到已有非目标目录会停止，不覆盖用户内容。随后在 Paradox Launcher 中把 **Vic Mod Template** 加入独立播放集并启用。

如在另一台电脑使用，应先在该电脑核对游戏版本；当前兼容字段不声明 1.14 或其他版本已通过测试。

## 成就兼容

Victoria 3 允许在加载 Mod 的情况下获得成就。这个框架不替换原版成就、不改游戏规则、不加入禁用成就的标记。`multiplayer_synchronized` 是多人同步元数据，不是成就开关。

实际游玩仍须选择允许成就的规则，并在正常启动的新游戏中核对成就界面；调试验证与正常成就验证分别记录。后续增加功能时要保留这一约束。[具体依据和验证方法](docs/achievements.md)

## 开发与同步

后续新增内容放入 `mod/` 对应的原版相对路径。当前校验器强制检查“空框架”边界，开始编写玩法功能时应同步更新校验范围，不能默默加入功能代码。

每次更改完成对应检查、必要的游戏测试后，提交并推送到 GitHub。用户已授权这一持续同步流程，不需要每次重复询问；测试失败或尚需游戏验证的更改不能被报告成已验证版本。不得提交原版资源、存档、日志、凭据或本机配置。

克隆后启用本地推送检查：

```powershell
git config core.hooksPath .githooks
```

GitHub CI 在推送和 Pull Request 时检查框架并生成 ZIP 构建产物。CI 通过说明静态检查与打包通过，不能替代游戏运行和成就界面验证。

[测试流程](docs/testing.md) · [创意工坊发布说明](docs/workshop.md) · [已记录的环境与测试结果](docs/validation.md) · [V3 Mod 制作流程笔记](docs/victoria3-modding-workflow.zh-CN.md)
