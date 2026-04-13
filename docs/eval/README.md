# Eval Harness

Runs the same scoring as the platform, locally. Full Tier 1 breakdown: resolution, efficiency, robustness, probes — per task.

Code: `py/apps/eval/run_eval.py`. Scoring library: `py/common/libs/fdebenchkit/`.

## Quick Start

```bash
cd py/apps/eval

# All 3 tasks
python run_eval.py --endpoint http://localhost:8000

# Single task
python run_eval.py --endpoint http://localhost:8000 --task triage
python run_eval.py --endpoint http://localhost:8000 --task extract
python run_eval.py --endpoint http://localhost:8000 --task orchestrate

# Custom dataset (Task 1)
python run_eval.py \
  --endpoint http://localhost:8000 \
  --dataset ../../py/data/task1/sample.json \
  --gold ../../py/data/task1/sample_gold.json
```

## What It Scores

```
tier1_k = 0.50 x Resolution + 0.20 x Efficiency + 0.30 x Robustness
fdebench = mean(tier1_task1, tier1_task2, tier1_task3)
```

- **Resolution** (50%) — per-task scoring against gold answers. Weights differ by task.
- **Efficiency** (20%) — P95 latency + model tier cost from `X-Model-Name` header.
- **Robustness** (30%) — adversarial accuracy (60%) + 7 API resilience probes (40%).

## Output

For each run, the harness prints:

- FDEBench composite and per-task Tier 1 scores
- Per-task resolution dimensions and weights
- Latency, model name, and cost-tier score
- Adversarial accuracy and API resilience
- Probe results (pass/fail per probe)
- Items scored and items errored

## Checked-In Datasets

| Task | Items | Input | Gold |
|------|-------|-------|------|
| Triage (sample) | 25 | `py/data/task1/sample.json` | `sample_gold.json` |
| Triage | 50 | `py/data/task1/public_eval_50.json` | `public_eval_50_gold.json` |
| Extract | 50 | `py/data/task2/public_eval_50.json` | `public_eval_50_gold.json` |
| Orchestrate | 50 | `py/data/task3/public_eval_50.json` | `public_eval_50_gold.json` |

## fdebenchkit Library

Located at `py/common/libs/fdebenchkit/`. The harness adds it to `sys.path` automatically.

| File | What it does |
|------|-------------|
| `scorers/ticket_triage.py` | Task 1 scoring (5 dimensions) |
| `scorers/document_extraction.py` | Task 2 scoring (8 dimensions) |
| `scorers/workflow_orchestration.py` | Task 3 scoring (5 dimensions) |
| `weights.py` | All Tier 1 weights and formulas |
| `probes.py` | 7 API resilience probes |
| `caller.py` | Async HTTP caller with retries and latency tracking |
| `runner.py` | End-to-end Tier 1 orchestrator |
| `registry.py` | Task definitions (endpoints, required keys, weights) |

## Dependencies

```bash
cd py && uv sync
```
