# 变更日志 / Changelog

本项目记录所有面向用户的重要变化，并遵循 [Semantic Versioning](https://semver.org/)。中文为主，关键发布信息同时提供英文摘要。

## [Unreleased]

## [0.2.0] - 2026-10-19

### Fixed

- 将本次执行上限 `target_stage` 与整轮闭环终点 `completion_stage` 分开；设计完成但实现仍待追平时保留契约。
- 关闭必须具备逐阶段证据、明确为零的剩余工作，并在删除前重新检查契约、文件与证据是否变化。
- 补充共享字段和状态的既有读取路径检查，覆盖对原有行为的间接影响。
- 修复 ClawHub 工作流对不存在的 `v1` 标签的引用，固定到已核验的上游提交，并支持手动 dry-run。
- 发布包排除工作流检出的 ClawHub 工具源码，避免把发布工具和大体积 fixture 混入 Skill。

### Added

- `paused` 状态及 `scope` 命令：在同一轮次继续，保留初始基线和完整恢复日志，记录新增授权。
- `close` 命令、关闭证据格式，以及阶段性完成、证据缺失、证据漂移和旧契约兼容回归。

### Migration

- 旧契约仍可读取和恢复。正常关闭前，用 `scope` 按原始确认补齐 `completion_stage`；不要删除重建契约。
- `verify --mark-ready` 现在必须提供 `--evidence <closing-evidence.json>`；随后运行 `close`，不再手动删除。
- `restore` 成功后停在 `restored`；基线和引用复验通过后才进入关闭流程。
- 暂停保留当前成果和契约；明确撤销时才恢复文件。

### English summary

Separate the execution limit from the round's completion stage. Partial design work now keeps the same contract and recovery journal. Closing requires stage evidence, zero remaining work, and drift checks. Adds pause/resume scope tracking and an explicit close command. Existing contracts remain readable and restorable, but must adopt an explicit completion stage and closing evidence before normal closure.

## [0.1.0] - 2026-08-07

首个公开版本：把“功能做到一半后需求改变”从一次模糊的仓库修改，变成可评估、可确认、可恢复的权威态追平流程。

### Added

- 六阶段 retcon 工作流：权威定位、只读评估、契约锁定、逐层追平、机械验证、完成或恢复。
- `RECONCILIATION.md` 本地契约，以及 `prepare → applied → restore` 写前日志协议。
- SHA-256、文件模式、Git 基线冻结、符号链接和工作根逃逸防护。
- 需求、API 兼容迁移、高风险能力删除三个可复制黄金案例及独立合成仓库 forward-test。
- 中英双语 README 与 15–25 秒双语终端演示。
- Codex、Claude Code、Cursor、OpenCode、Gemini CLI、GitHub Copilot、OpenClaw 的 Skills CLI 安装路径。
- skills.sh 与 ClawHub 双渠道发布准备；ClawHub 包限制为 9 个运行必需文件。
- Linux/macOS、Python 3.9/3.12 CI，覆盖正常路径、故障注入、分发边界与社区健康文件。

### Security

- 第一次调用严格只读；未确认变更断言、目标阶段、可写根、删除清单和风险前禁止写入。
- 恢复遇到外部漂移时失败关闭，不自动重置、暂存、提交或推送 Git。
- 敏感内容不回显；无 Git 时的 Base64 载荷明确不作为加密。

### English summary

Initial public release of a repository-safe feature retcon workflow: read-only impact assessment first, explicit scope confirmation before writes, per-file recovery journaling, stage-by-stage reconciliation, and fail-closed validation. Includes three copy-ready cases, bilingual docs and demos, multi-agent installation, and cross-platform safety tests.

[Unreleased]: https://github.com/songzhuozhu/feature-retcon/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/songzhuozhu/feature-retcon/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/songzhuozhu/feature-retcon/releases/tag/v0.1.0

