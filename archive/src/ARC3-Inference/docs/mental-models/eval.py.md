# eval.py

## Purpose
Provides scoring and evaluation support for saved benchmark runs.

## Mental model
This file is the reporting layer. It reads completed runs and produces evaluation artifacts such as scores and summaries.

## Main responsibility
Think of it as the post-run analysis component.

## Core concepts
- Input: benchmark artifacts and saved run state
- Analysis: compute or export evaluation scores
- Output: evaluation.json, score.json, and related summaries

## Important functions
- run_evaluation(): orchestrates scoring for selected runs
- load_run_state(): collects the saved benchmark data
- export_score_artifacts(): writes the final evaluation outputs

## Typical flow
1. Load saved run data
2. Compute or retrieve the score
3. Write evaluation artifacts
4. Return summaries for downstream use

## Call chain
saved run data
↓
evaluation logic
↓
score artifacts

## What it is not
- It is not the game runner
- It is not the agent policy
- It is not the live viewer

## One-line summary
This file turns completed runs into machine-readable evaluation outputs.
