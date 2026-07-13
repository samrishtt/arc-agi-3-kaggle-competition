# Research Changelog

This changelog tracks architectural and research changes separately from Git history.

## Format

```markdown
## YYYY-MM-DD - Change Title

Type:
Experiment ID:
Files Changed:
Architectural Area:
Summary:
Benchmark Impact:
Risks:
Follow-up:
```

## 2026-07-12 - Initial Research Documentation

Type: Documentation
Experiment ID: N/A
Files Changed:
- `docs/ARCHITECTURE.md`
- `docs/EXECUTION_FLOW.md`
- `docs/CORE_FILES.md`
- `docs/EXPERIMENTS.md`
- `docs/IDEAS.md`
- `docs/CHANGELOG_RESEARCH.md`
- `docs/FAILED_EXPERIMENTS.md`

Architectural Area: Research workflow

Summary: Added architecture map, execution flow, core file guide, experiment template, first 50 experiment ideas, top 10 recommended experiments, and roadmap through experiment #100.

Benchmark Impact: None directly; enables controlled experimentation.

Risks: Documentation may drift if source architecture changes.

Follow-up: Append each completed experiment to `EXPERIMENTS.md`; append failed experiments to `FAILED_EXPERIMENTS.md`.

## 2026-07-13 - Root Harness Baseline Evidence

Type: Baseline characterization
Experiment ID: BASELINE-000
Files Changed:
- `docs/EXPERIMENTS.md`

Architectural Area: Evaluation and reproducibility

Summary: Recorded a paired analysis of the supplied Tufa Labs and replication
result archives. The source snapshots and visible run settings matched, but
the one-pass offline framework means differed by 0.248867 and the gains were
concentrated in a few games. No ARC implementation was changed.

Benchmark Impact: None. This establishes that subsequent score claims require
a fixed-seed or repeated-run comparison.

Risks: The archives do not independently verify the reported Kaggle leaderboard
scores, and the offline game list differs from the live competition rerun path.

Follow-up: Run CONTROL-001 before beginning benchmark-improvement Experiment
#001.

## 2026-07-13 - Analyzer Seed Reproducibility Control

Type: Experimental infrastructure
Experiment ID: CONTROL-001
Files Changed:
- `Makefile`
- `inference/framework/kaggle.py`
- `docs/EXPERIMENTS.md`

Architectural Area: Kaggle runtime configuration and evaluation reproducibility

Summary: Added a default, overrideable `LOCAL_ANALYZER_SEED=1729` to the
Kaggle deployment environment. The existing agent already forwards this
variable to vLLM; this change makes the chosen value visible in generated run
artifacts.

Benchmark Impact: Not yet measured. This is a measurement control, not a
claimed agent improvement.

Risks: Request-level seeding may not remove every source of GPU or concurrent
scheduling variance. A fixed seed may also happen to select an unrepresentative
trajectory.

Follow-up: Build the archive, run two matching offline Kaggle benchmarks, and
append the per-game comparison to CONTROL-001. Do not begin score-improvement
Experiment #001 until the control result is recorded.
