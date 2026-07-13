# run.py

## Purpose
Runs the ARC3 Duck harness through TAAF by acting as the top-level orchestrator.
It takes user configuration, resolves which games should run, prepares the solver and deployment target, writes run metadata, and launches the benchmark.

## Mental model
This file is the controller layer. It does not play the game itself; it coordinates the full execution pipeline.

## Main responsibility
Think of it as the “command center” for a run.

## Core concepts
- Input: CLI arguments and environment settings
- Decision layer: which games, model, runtime limits, deployment target
- Execution layer: solver + benchmark + deployment backend
- Output: run directory, artifacts, logs, and remote submission

## Important functions
- main(): parses CLI arguments and starts the run
- _run(): high-level orchestration for one benchmark execution
- _resolve_game_ids(): resolves games from explicit IDs, datasets, or tags
- _make_solver(): constructs the HarnessSolver with runtime and server settings
- _make_deployment_target(): selects inline, Slurm, or Kaggle deployment
- _write_run_config(): saves a reproducible snapshot of the run configuration
- _enter_competition_arcade(): optionally wraps the run in the local competition Arcade simulator

## Typical flow
1. Parse CLI options
2. Validate basic settings
3. Resolve selected games
4. Create a run directory
5. Build the solver
6. Write run_config.json
7. Start TAAF benchmark deployment

## Call chain
CLI / args
↓
main()
↓
_run()
↓
_resolve_game_ids()
↓
_make_solver()
↓
Benchmark.deploy()
↓
Inline / Slurm / Kaggle target

## What it is not
- It is not the game logic
- It is not the model agent logic
- It is not the viewer or scoring pipeline

## One-line summary
This file is the launcher and coordinator that turns run settings into an actual benchmark execution.
