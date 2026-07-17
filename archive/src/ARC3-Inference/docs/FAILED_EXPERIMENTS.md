# Failed Experiments

Append failed experiments only. Do not remove historical failed entries.

## Format

```markdown
## Experiment ID - Title

Date:
Branch:
Hypothesis:
Implementation:
Files Changed:
Benchmark Results:
Tokens:
Runtime:
Failure Mode:
Lessons Learned:
Future Ideas:
```

Historical failed experiments follow.

## CONTROL-001 - Record And Propagate The Local Analyzer Seed

Date: 2026-07-13 to 2026-07-14

Branch: `codex/control-001-seed`

Hypothesis: A fixed local-analyzer seed would make repeated one-pass Duck
harness runs substantially more reproducible.

Implementation: Added a default, overrideable `LOCAL_ANALYZER_SEED=1729` to
the Kaggle deployment path. The completed Kaggle runs recorded the same seed
in `taaf_setup_env.json`.

Files Changed:
- `Makefile`
- `inference/framework/kaggle.py`
- `docs/EXPERIMENTS.md`
- `docs/CHANGELOG_RESEARCH.md`

Benchmark Results: Run A mean score `1.52`; run B mean score `0.93`. Both
runs used 25 games, one pass, the same recorded setup environment, and RTX
Pro 6000 hardware. Their game trajectories diverged at action 1 or 2 on
representative games. Run A's reported live Kaggle public score was `0.81`,
below the researcher's earlier reported `0.86` submission.

Tokens: 1,623,849 (A); 1,607,492 (B).

Runtime: 2h 12m 24s (A); 2h 12m 28s (B).

Failure Mode: Request-level seed recording did not produce repeatable
trajectories under 28 concurrent vLLM requests. Request payload logs were not
enabled, so the exact server-side seed behavior cannot be audited.

Lessons Learned: A single seeded full-harness run is still insufficient for a
score claim. Use multi-run paired evaluation and a small logged diagnostic
slice before interpreting a code change as an improvement.

Future Ideas: CONTROL-002 should hold the seed constant, reduce concurrency
on a fixed small game slice, and enable request logs to isolate scheduling and
server nondeterminism.
