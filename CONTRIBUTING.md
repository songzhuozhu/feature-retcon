# 贡献指南

感谢改进 `feature-retcon`。

## 内容边界

提交的说明、案例、fixture、测试、注释和提交信息必须是从零构造的中性内容。不要提交真实业务规格、内部项目名称、私有路径、接口、代码、日志、凭证、提交记录或可以关联来源的演进信息。

如果缺陷只能用私有材料复现，请先构造最小合成案例，再提交该案例。

## 修改原则

- 保持 `SKILL.md` 聚焦顺序步骤和可检查的完成标准。
- 把仅特定分支需要的规则放入直接引用的 `references/` 文件。
- 让每个行为规则只有一个权威位置。
- 对恢复、哈希和状态迁移使用确定性脚本，不要求模型手工模拟。
- 不降低只读评估、显式确认、写前日志或零未解释残留门槛。

## 测试

提交前运行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/contract.py --help
```

脚本行为变更应补充覆盖成功、阻塞和恢复路径的测试。测试必须在临时目录中运行，不得修改真实项目或调用网络服务。

## 提交前检查

- 没有秘密、真实业务材料或来源线索。
- 中英文 README 与实际安装方式一致。
- `agents/openai.yaml` 与 `SKILL.md` 的调用方式一致。
- 所有测试通过。
- 新增参考文件由 `SKILL.md` 直接指向，并说明读取时机。

## 双渠道发布

发布前先完成常规测试，并验证 Skills CLI 能发现且只发现根目录中的 `feature-retcon`：

```bash
npx skills add . --list
```

两个渠道使用同一个 Git 提交作为来源：

1. **skills.sh**：推送公共 GitHub 仓库后，用 `npx skills add songzhuozhu/feature-retcon` 完成一次真实安装。skills.sh 会根据 Skills CLI 的匿名安装遥测自动收录，不存在单独的“发布”按钮。
2. **ClawHub**：先运行 `clawhub skill publish . --owner songzhuozhu --slug feature-retcon --version <version> --dry-run --json`，确认 `.clawhubignore` 只包含运行必需文件。需要与 GitHub Release 使用相同版本时，使用已登录 CLI 显式传入 `--version`、`--source-repo`、`--source-commit`、`--source-ref` 和 `--source-path .` 发布。仓库工作流支持 PR 或手动 dry-run；自动补丁版本发布还需要 Secret `CLAWHUB_TOKEN`，并显式设置 `dry_run=false`、`confirm_mit0=true`。

ClawHub 发布会把该渠道中的 Skill 版本置于 **MIT-0** 下，且不要求署名。这是一次真实的许可选择，不得绕过确认门禁或改成自动随 tag 发布。首次发布后，验证：

```bash
clawhub inspect @songzhuozhu/feature-retcon --files
clawhub install @songzhuozhu/feature-retcon
```
