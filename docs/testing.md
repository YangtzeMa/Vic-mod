# 框架验证流程

## 静态与打包检查

```powershell
python scripts/validate_mod.py
python scripts/package_mod.py
git diff --check
git diff --cached --check
```

校验覆盖：元数据字段、稳定 ID、兼容版本、两份 PNG 的结构/CRC/解压长度、封面一致性、ASCII 路径，以及 Mod 包内无功能文件。打包后再核对 ZIP 内容与源文件逐字节一致。

包根应直接包含 `.metadata/metadata.json`，不能多套 `mod/` 或仓库根目录。`dist/` 是生成物，不提交 Git；GitHub Actions 会提供相同类型的构建产物。

## 本机加载与成就验收

1. 重新读取已安装可执行文件与 Launcher 版本，确认目标为 1.15.x。
2. 执行链接脚本，在 Launcher 中新建本项目专用播放集，仅启用本 Mod。
3. 检查名称、封面和兼容版本显示；正常启动，不使用调试启动方式进行成就验收。
4. 新开测试局，不覆盖既有存档。确认能进入游戏，成就规则允许、成就面板可用。
5. 检查当前运行的新增错误；必要时与无 Mod 基线比较。保留本机日志和截图于 `.local/`，只提交简洁结果。
6. 正常退出游戏，记录游戏版本、测试范围和结论。

不要把静态 CI 通过当作游戏运行证据。纯文档变更完成文档检查即可；后续修改游戏加载内容时应重做相应运行测试。

## GitHub 同步

用户已授权每次检查及必要测试通过后及时 commit/push。同步前检查 diff 和待提交文件；同步后确认本地 HEAD 与远端 HEAD 相同，并检查该提交的 CI。禁止 force-push，禁止提交本机凭据和原版资源。
