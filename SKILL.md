---
name: feature-retcon
description: 当用户需要推翻或修改一个已推进到需求、设计、任务、实现或验证阶段的功能决定时，先只读评估影响，确认后再逐层追平权威产物，并提供可验证、可恢复的执行边界。
---

# 后悔药

把用户确认的功能变更视为一次 **retcon**：重写当前权威态，而不是给旧结论追加补丁。每轮只追平到用户指定阶段，并以零未解释残留结束。

## 门禁

- 将没有现存追平契约的调用限定为只读评估；评估完成后结束本轮对话，等待用户确认。
- 只在用户明确确认变更断言、目标阶段、可写工作根、删除清单和已披露风险后修改文件。
- 将未获授权的根保持只读。执行中发现实质范围扩张时暂停并重新确认。
- 在每次修改、创建或删除目标文件前调用恢复脚本登记写前状态；登记成功后才执行该次修改。
- 将契约存在视为未完成轮次。完成或恢复并通过全部门槛前保留契约。
- 保持终态式权威文档：当前有效产物只描述新目标，历史证据留在明确的历史载体中。

## 读取路线

执行对应分支前完整读取指定参考文件：

- 每次评估：读取 [assessment.md](references/assessment.md) 和 [stage-gates.md](references/stage-gates.md)。
- 用户确认后、继续轮次或恢复轮次：读取 [contract-schema.md](references/contract-schema.md)。
- 目标包含任务阶段：读取 [task-rebuild.md](references/task-rebuild.md)。
- 检测到项目规格工具、Hook 或多个工作根：读取 [spec-kit-adapter.md](references/spec-kit-adapter.md)。
- 需要校准边界或解释编号规则：读取 [case-catalog.md](references/case-catalog.md)。

## 步骤 1：定位轮次与权威态

先搜索候选权威根中的 `RECONCILIATION.md`。发现契约时，运行：

```bash
python3 <skill-dir>/scripts/contract.py status <authority-root>/RECONCILIATION.md
python3 <skill-dir>/scripts/contract.py verify <authority-root>/RECONCILIATION.md
```

将该调用路由为继续、重新评估或停止并恢复；范围重叠的新轮次保持阻塞。没有契约时，按权威解析顺序确定唯一权威根，无法排除多个候选时让用户裁决。

完成标准：已找到唯一权威根，或已报告全部候选及其证据并等待用户裁决；现存契约的状态和允许动作已明确。

## 步骤 2：执行只读评估

构建语义阶段和产物依赖图，收集工作根、版本状态、冲突、基线验证、删除候选、Hook、副作用、敏感候选与残留签名。量化每个可选目标阶段的文件、仓库、接口、任务、测试和验证影响，给出一个有理由的推荐。

按 [assessment.md](references/assessment.md) 的固定结构交付评估。不得创建契约、修改权威产物、运行写入型命令或把建议当成授权。以一个确认请求结束当前调用。

完成标准：评估的全部固定栏目均有结论或明确的未知项；本次调用没有产生文件、Git 或外部系统写入；用户尚未确认时保持停止。

## 步骤 3：锁定追平契约

把用户确认的全部内容写入契约：被推翻行为、当前目标、保持不变、排除项、兼容与迁移影响、目标阶段、可写根、删除清单、冲突处置、Hook、副作用以及敏感或大载荷授权。

用脚本创建契约：

```bash
python3 <skill-dir>/scripts/contract.py init <authority-root> \
  --target-stage <stage> \
  --version-control <git|none> \
  --baseline-ref <ref> \
  --writable-root <root>
```

按需重复 `--writable-root`；无 Git 时省略 `--baseline-ref`。补全契约正文，运行相关验证取得基线，再执行 `verify`。

完成标准：契约权限为 `0600`，未被 Git 跟踪或暂存；确认内容全部持久化；验证基线可复现；任何未处置冲突仍保持阻塞。

## 步骤 4：逐层收敛

从需求开始，只推进到已确认目标阶段。每层先更新上游，再验证当前层；下游暴露上游缺陷时回流修正，并重新计算受影响下游。

每次修改目标文件都执行写前协议：

```bash
python3 <skill-dir>/scripts/contract.py prepare <contract> --path <file>
# 修改、创建或删除该文件
python3 <skill-dir>/scripts/contract.py applied <contract> --path <file>
```

敏感文件和超过载荷门槛的文件，只能在契约记录对应确认后使用脚本给出的显式选项继续。将闭包补充写入契约后继续；将实质范围扩张写入契约、设置 `blocked` 并等待重新确认。

完成标准：目标阶段及全部上游阶段逐层通过 [stage-gates.md](references/stage-gates.md)；每次文件变更都有连续日志；依赖图、删除清单和验证结果与实际修改一致。

## 步骤 5：验证当前权威态

运行项目原生检查和确定性静态检查。扫描词法与行为残留签名，对每个命中分类为已替换、明确历史证据或与本轮无关。验证新需求能够沿依赖图追踪到目标阶段，并更新追平水位和阶段陈旧状态。

失败的归因和处置严格采用 [stage-gates.md](references/stage-gates.md)。必要验证无法运行、失败无法归因或存在未解释命中时，把契约状态设为 `blocked`。

完成标准：所有必需验证通过或有证据证明失败既有且无关；残留签名零未解释命中；机械校验返回 `valid: true`。

## 步骤 6：完成或恢复

正常完成时，先确认契约的有效语义全部吸收到权威产物，再运行：

```bash
python3 <skill-dir>/scripts/contract.py verify <contract> --mark-ready
```

逐项复核契约完成门槛，然后显式删除契约。脚本不提供关闭或删除命令。

用户停止未完成轮次时，运行 `restore`，复核恢复后的权威态与验证基线；只有状态为 `ready_to_close`、基线一致且没有半完成引用时，才删除契约。

最后在对话中报告修改与删除数量、验证结果、残留扫描、追平水位、阶段陈旧状态和各工作根状态。不得自动初始化 Git、暂存、提交、重置、改写历史、推送或调用外部系统。

完成标准：契约已经删除；指定阶段的权威态唯一、自洽、可验证且零未解释残留；未获授权的根和用户无关修改保持不变。
