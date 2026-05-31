# ARC-AGI-3 Forge v3 + Heuristic Solver

This repository contains my custom implementation for the ARC Prize 2026 (ARC-AGI-3) Kaggle competition.

## Attribution & Origins

This project is built upon and inspired by the following open-source solutions:
- **Built on Forge v3**: Originally developed by [jihangli1121](https://github.com/jihangli1121). It serves as the core engine, utilizing curriculum learning via template injection (CLTI) and online training of a convolutional neural network (ForgeNet) combined with A*/BFS navigation heuristics.
- **No-Error Heartbeat**: Copied and adapted from [Yaroslav kholmirzayev](https://github.com/Yaroslav-kholmirzayev). It features beam search, MCTS, and novelty guidance heuristics.

## Results

Here are the leaderboard submission results of the different iterations/approaches evaluated on the ARC-AGI-3 test set:

| Version / Approach | Public Score | Notes / Labels |
|---|---|---|
| **Early Baseline** | **0.06** | Initial basic heuristic search attempt. |
| **No-Error Heartbeat** | **0.26** | Adapted from Yaroslav kholmirzayev. High complexity (beam search, MCTS, novelty guidance), but limited by execution constraints or overfitting on complex puzzles. |
| **Forge v3** | **0.42** | Built on Forge v3 by jihangli1121. BFS + online CNN (ForgeNet) with dynamic curriculum learning. Best performing core solver. |

---

## Architecture

The solver uses **Forge v3** as the core agent framework, which is built on top of the official `ARC-AGI-3-Agents` framework. 

### Key Features
- **Breadth-First Search (BFS) & A* Search**: First-pass programmatic search using distance heuristics and indicator checks to find exact winning sequences of actions.
- **Online CNN (ForgeNet)**: If BFS times out or fails, the agent falls back to an online CNN initialized from scratch and trained dynamically during the game run itself using experience replay (CLTI - Curriculum Learning via Template Injection).
- **Targeted Heuristics**: The agent uses domain-specific knowledge to prioritize actions and prune non-productive exploration loops.
- **No External Weights**: The model trains entirely online during execution, requiring no pre-trained checkpoints or external datasets.

## Quickstart

### 1. Setup
Make sure you have `python 3.12` installed. Run the setup to create the virtual environment and install dependencies:
```powershell
make setup
```

### 2. Local Testing
Test the agent locally on the interactive environments:
```powershell
# Run against a specific game (e.g., ls20)
.\.venv\Scripts\python.exe scripts/play_local.py --game ls20

# List all available games
.\.venv\Scripts\python.exe scripts/play_local.py --list
```

### 3. Submission
Splice `agent/my_agent.py` into a Kaggle-ready notebook:
```powershell
.\.venv\Scripts\python.exe scripts/build_notebook.py
```
Then upload `notebooks/submission.ipynb` or push it directly using the Kaggle CLI:
```powershell
$env:KAGGLE_API_TOKEN = (Get-Content .kaggle/access_token).Trim()
.\.venv\Scripts\kaggle.exe kernels push -p notebooks/
```
