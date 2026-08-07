# 变更日志 / Changelog

本项目记录所有面向用户的重要变化，并遵循 [Semantic Versioning](https://semver.org/)。中文为主，关键发布信息同时提供英文摘要。

## [Unreleased]

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

[Unreleased]: https://github.com/songzhuozhu/feature-retcon/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/songzhuozhu/feature-retcon/releases/tag/v0.1.0

