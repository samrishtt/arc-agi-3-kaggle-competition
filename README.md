# ARC-AGI-3 Heuristic Explorer Solver

This repository contains my custom implementation for the ARC Prize 2026 (ARC-AGI-3) Kaggle competition.

## Architecture

The solver uses a **Heuristic Explorer Agent** built on top of the official `ARC-AGI-3-Agents` framework. Instead of random actions, the agent tracks its observations and filters out ineffective moves (like walking into walls) by checking if the grid state changed after its previous action.

### Key Features
- Subclasses the official `agents.agent.Agent` framework template.
- Implements `_hash_frame` to represent the grid computationally.
- Uses `bad_actions_for_state` to strictly blacklist non-productive loops in real-time.
- Supports 100% offline, local testing without LLM API keys.

## Quickstart

### 1. Setup
Make sure you have `python 3.12` installed.
```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt # (or run make setup if using WSL/Bash)
```

### 2. Local Testing
Test the heuristic agent locally on the interactive environments:
```bash
.\.venv\Scripts\python.exe scripts/play_local.py --game ls20
```

### 3. Submission
Splice `agent/my_agent.py` into a Kaggle-ready notebook:
```bash
.\.venv\Scripts\python.exe scripts/build_notebook.py
```
Then upload `notebooks/submission.ipynb` or push using the Kaggle CLI!
