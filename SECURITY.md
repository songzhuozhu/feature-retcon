# 安全策略 / Security Policy

`feature-retcon` 会指导 Coding Agent 读取仓库，并在用户明确确认后修改文件。它把“第一次调用只读、写前登记、范围锁定、漂移即停”视为安全边界，而不是使用建议。

## 支持版本

| 版本 | 安全更新 |
|---|---|
| `0.1.x` | ✅ 支持 |
| `< 0.1.0` | ❌ 不支持 |

## 私下报告漏洞

请使用 [GitHub Security Advisory](https://github.com/songzhuozhu/feature-retcon/security/advisories/new) 私下报告以下问题，不要创建公开 Issue：

- 未确认调用产生文件、Git 或外部系统写入；
- 可写根逃逸、符号链接穿透或未登记文件被覆盖；
- 恢复日志、SHA-256、权限或 Git 基线校验可被绕过；
- 敏感内容在错误信息、日志或评估报告中泄漏；
- 中断恢复不可安全重试，或恢复触碰无关工作树；
- Skill、发布包或自动化工作流存在供应链风险。

报告中请包含：受影响版本、宿主 Agent、操作系统、最小合成复现、期望/实际结果，以及已移除秘密和私有业务信息的日志。不要提交真实仓库、凭证或内部规格。

我们会尽量在 72 小时内确认收到报告，并在完成初步复现后协调披露时间。修复发布前，请避免公开漏洞细节。

## Security policy in English

Please report security-boundary failures privately through a [GitHub Security Advisory](https://github.com/songzhuozhu/feature-retcon/security/advisories/new), not a public issue. Include the affected version, host agent, OS, a minimal synthetic reproduction, expected versus actual behavior, and sanitized logs. Never attach credentials, private repositories, or proprietary specifications.

Relevant findings include writes before confirmation, writable-root escape, unsafe symlink handling, journal or baseline bypasses, sensitive-data disclosure, non-retryable restoration, unrelated worktree damage, and release-pipeline supply-chain risks. We aim to acknowledge reports within 72 hours and coordinate disclosure after initial reproduction.

