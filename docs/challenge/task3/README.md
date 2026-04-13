# Task 3: Workflow Orchestration

`POST /orchestrate`

Given a goal, a set of tools, and a list of constraints, execute the workflow and return what happened. Actually call the tools — the benchmark checks real execution, not just a plan that looks reasonable.

Read the background:

- [customer_brief.md](customer_brief.md) — what the customer needs
- [execution_guide.md](execution_guide.md) — how to think about execution
- [engineering_review.md](engineering_review.md) — what judges look for

## Request Contract

Input fields:

- `task_id`
- `goal`
- `available_tools`
- `constraints`

`available_tools[].parameters` is a list of parameter objects:

```json
{
  "name": "filter",
  "type": "string",
  "description": "Search filter expression",
  "required": true
}
```

See [../../../py/data/task3/input_schema.json](../../../py/data/task3/input_schema.json) for the formal schema.

## Response Contract

Required output fields:

- `task_id`
- `status`
- `steps_executed`

Common additional fields include:

- `constraints_satisfied`
- `accounts_processed`
- `emails_sent`
- `emails_skipped`
- `skip_reasons`

See [../../../py/data/task3/output_schema.json](../../../py/data/task3/output_schema.json) for the formal schema.

## Resolution Scoring

```
resolution = (0.20 x goal_completion + 0.15 x tool_selection + 0.05 x parameter_accuracy + 0.20 x ordering_correctness + 0.40 x constraint_compliance) x 100
```

| Dimension | Weight | Metric |
|---|---|---|
| `goal_completion` | 20% | End-state match |
| `tool_selection` | 15% | Set F1 on tools used |
| `parameter_accuracy` | 5% | Per-call parameter match |
| `ordering_correctness` | 20% | Dependency satisfaction |
| `constraint_compliance` | 40% | Outcome assertions |

## What's Hard

Multiple valid plans exist. Parameters need to be computed, not copied from the goal. Constraint violations tank your score even if the trace looks clean. Some workflows have ambiguous goals or failing tools. The benchmark tests what you actually did, not what you said you'd do.

## Tips

- Use the provided tools. Don't simulate them.
- `constraint_compliance` is 40% of resolution — it's the biggest lever.
- Small verifiable steps beat one opaque jump.
- Handle failures explicitly. Crashing on a 503 is not recovery.
