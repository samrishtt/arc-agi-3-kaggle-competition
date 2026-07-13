# significance.py

## Purpose
Compares candidate score files against a baseline and reports whether the result is statistically meaningful.

## Mental model
This file is the comparison layer for benchmarking results. It aligns scores by game and checks whether performance improvements are robust.

## Main responsibility
Think of it as the significance and validation tool for score comparisons.

## Core concepts
- Input: baseline and candidate score files
- Alignment: paired by game ID and repeated trials
- Analysis: compute win rate, delta, confidence intervals, and p-values
- Output: significance report

## Important functions
- compare_scores(): runs the main significance analysis
- align_results(): pairs runs by game and trial structure
- summarize_results(): reports the comparison outcome

## Typical flow
1. Load baseline and candidate results
2. Align them by game
3. Compute paired metrics
4. Produce a significance report

## Call chain
score files
↓
comparison logic
↓
significance report

## What it is not
- It is not the run executor
- It is not the solver
- It is not the UI

## One-line summary
This file evaluates whether a new score is meaningfully better than the current baseline.
