# ARC-AGI-3 Research Protocol

## Purpose

This protocol governs every benchmark-affecting experiment in this repository.
Its purpose is to make results credible, comparable, reproducible, and useful
for future research rather than anecdotal.

## Research Cycle

```text
Research Question
        |
        v
Literature / Repository Analysis
        |
        v
Hypothesis
        |
        v
Experiment Design
        |
        v
Implementation
        |
        v
Benchmark
        |
        v
Statistical Analysis
        |
        v
Documentation
        |
        v
Git Commit
        |
        v
Repeat
```

## Immutable Rules

1. Change one benchmark-relevant variable per experiment. A code change that
   requires a supporting test or a matching documentation update still counts
   as one variable when those changes do not alter agent behavior.
2. Every candidate must be benchmarked against the same declared baseline,
   using the same game set, framework version, model, hardware class, runtime
   budget, pass count, and sampling configuration unless the experiment is
   explicitly studying one of those variables.
3. Every experiment must start with a written hypothesis before implementation.
4. Record the exact experiment design before running it: experiment ID, branch,
   files and functions to change, predicted effect, success criterion, and
   rollback plan.
5. Never conclude that a change is better because it appears better in a trace.
   A claim of improvement requires benchmark evidence and a comparison to the
   declared baseline.
6. Every completed experiment must be appended to `EXPERIMENTS.md`. Never
   overwrite a prior result.
7. Every failed, regressed, invalid, or inconclusive experiment must also be
   appended to `FAILED_EXPERIMENTS.md`. Failure is research evidence.
8. Never merge a benchmark-affecting change without documenting its hypothesis,
   implementation, benchmark result, token usage, runtime, and conclusion.
9. Keep every experiment reproducible. Another researcher must be able to
   identify the commit, configuration, model, data selection, random seed,
   compute budget, and commands required to repeat it.
10. Preserve benchmark integrity. Do not use hidden-test leakage, public-game
    memorization, environment exploits, or score-only shortcuts that do not
    generalize to novel ARC-AGI-3 environments.
11. Treat stochastic results as stochastic. Use repeated passes where practical,
    report per-game outcomes, and use paired statistical comparison before
    promoting a candidate as the new baseline.
12. Keep the main branch interpretable. Experimental work belongs on a dedicated
    branch and is committed only after its documentation is complete.

## Required Experiment Record

Before implementation, add a planned entry to `EXPERIMENTS.md` with:

- Experiment ID and date
- Research question and hypothesis
- Motivation and expected benchmark impact
- Baseline run identifier and score artifact
- Candidate branch, files, functions, and the single variable being changed
- Benchmark command, game selection, passes, seed, hardware, and time budget
- Primary metrics: score, completed levels, actions per completed level
- Secondary metrics: token usage, runtime, no-op actions, invalid actions, and failures
- Acceptance criterion and rollback condition

After the benchmark, append the observed results, statistical comparison,
conclusion, lessons learned, and the next proposed experiment. Failed or
inconclusive results must be duplicated in `FAILED_EXPERIMENTS.md`.

## Baseline Policy

The current best reproducible run is the baseline only after its score artifact
and run metadata are available locally. Do not compare a candidate with an
unrecorded score, a different game selection, or a run with incompatible
hardware/runtime constraints.

## Decision Policy

- Promote: the candidate improves the primary metric, does not violate the
  runtime or reproducibility constraints, and passes paired comparison.
- Retain for investigation: the result is inconclusive but exposes a useful
  failure mode or a testable follow-up hypothesis.
- Reject: the candidate regresses, cannot be reproduced, violates the protocol,
  or improves only through benchmark-specific exploitation.

## Scope of Experiment #001

Experiment #001 may begin only after a baseline run is declared. It will change
the prompt protocol alone, with no solver, sandbox, segmentation, runtime, or
evaluation changes in the same experiment.
