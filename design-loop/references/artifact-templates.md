# Loop 运行契约模板

在用户要求实现、生成 `program.md`、持久化状态或建立多角色 Loop 时读取。仅生成任务实际需要的文件。

## 目录

- `program.md`
- `state.json`
- `runs.jsonl`
- `evaluator.md`
- `approval-policy.md`
- 契约冻结流程

## `program.md`

```markdown
# <Loop name>

Spec version: 1
Owner: <person/team>
Autonomy: A0|A1|A2|A3|A4

## Objective
<one observable outcome>

## Non-goals
- <explicit exclusion>

## Trigger and input
- Trigger:
- Input source:
- Idempotency/dedup key:

## Writable surface
- <files, APIs, branches, records>

## Protected surface
- <evaluator, tests, baselines, fixtures, secrets>

## Cycle
Observe → Decide → Act → Verify → Persist

## Success and constraints
- Primary metric:
- Success threshold:
- Constraint metrics:
- Anti-gaming checks:
- Required evidence:

## Stop and escalation
- Success:
- Max iterations/time/cost:
- No-progress rule:
- Human escalation:

## Recovery
- Retryable errors:
- Backoff:
- Restart or resume:
- Rollback/compensation:
```

## `state.json`

只保存恢复所需的结构化事实。原子写入临时文件后再重命名；需要并发时加版本号或租约。

```json
{
  "spec_version": 1,
  "run_id": "",
  "status": "idle",
  "input_cursor": null,
  "iteration": 0,
  "best_metric": null,
  "budget": {"tokens": 0, "money": 0, "elapsed_seconds": 0},
  "last_confirmed_side_effect": null,
  "pending_approval": null,
  "checkpoint": null,
  "updated_at": ""
}
```

定义有限状态，例如 `idle → observing → acting → verifying → succeeded|failed|awaiting_approval`。拒绝自由文本状态。

## `runs.jsonl`

每行一个不可变事件，保留旧 spec 版本：

```json
{"run_id":"","spec_version":1,"iteration":1,"event":"verification","action":"","metric":null,"evidence":"","cost":{},"timestamp":""}
```

避免记录凭证、完整 prompt、敏感原文或无助于审计的全部对话。

## `evaluator.md`

```markdown
# Evaluator contract

## Inputs
- Artifact under evaluation:
- Frozen baseline:
- Read-only/hidden fixtures:

## Deterministic checks
1. <command or comparison and expected result>

## Judgment rubric
- Use only when deterministic checks are insufficient.
- Score dimensions independently and cite artifact evidence.

## Anti-gaming checks
- Verify sample count, compute budget, skipped cases and report provenance.
- Reject runs that modify protected files or evaluation configuration.

## Output schema
`status`, `primary_metric`, `constraint_metrics`, `evidence`, `failure_class`.
```

评估者只读取冻结契约、待评产物和必要证据；不要传入生成者的自我辩护或预期结论。

## `approval-policy.md`

```markdown
# Approval policy

| Action | Default | Approver | Evidence required | Timeout behavior |
|---|---|---|---|---|
| Read/draft | allow | — | audit log | continue |
| Reversible scoped write | <allow/ask> | <role> | diff + checks | stop safely |
| Merge/deploy/delete/pay/send | ask | <role> | diff, impact, rollback | stop safely |
```

## 契约冻结流程

1. Planner 起草目标、边界、指标和副作用策略。
2. Generator 只检查契约是否足以执行，不改写成功标准。
3. Evaluator 检查指标可测量性、受保护面和防刷分条件。
4. 人类批准高风险权限及预算。
5. 写入 spec 版本并冻结 evaluator 后开始运行。
6. 规则变更时创建新版本；旧运行继续引用旧版本，不覆盖历史。
