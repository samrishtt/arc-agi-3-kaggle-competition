# 🧠 ARC-AGI-3 Solver — Go-Explore Graph Exploration Agent

<p align="center">
  <img src="docs/images/architecture.png" alt="Agent Architecture" width="700"/>
</p>

> A high-performing training-free agent for the [ARC Prize 2026](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3) (ARC-AGI-3) competition. The agent implements a deterministic **Go-Explore style state-graph explorer** that optimizes Relative Human-Adjusted Efficiency (RHAE) without relying on heavy deep-learning dependencies.

[![Competition](https://img.shields.io/badge/Kaggle-ARC_Prize_2026-20BEFF?logo=kaggle)](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3)
[![Score](https://img.shields.io/badge/Best_Score-0.33-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)]()

---

## 🏗️ Architecture: Why This Design?

### Why Pure Search Beat Online Reinforcement Learning
Scoring in ARC-AGI-3 is evaluated using **RHAE (Relative Human Action Efficiency)**:
$$\text{Score} = \left(\min\left(1, \frac{\text{Human Actions}}{\text{Agent Actions}}\right)\right)^2$$
This score is weighted by level index and averaged across 110 unseen games. Because the scoring squares the efficiency ratio and penalizes redundant moves heavily, **two things matter most**:
1. Completing the level at all.
2. Completing the level in as few real actions as possible (shortest path length).

Turn-based, grid-world puzzle games on ARC are **deterministic**. Training an online neural network (CNN/RL) from scratch inside the limited action budget of a single game level is highly unstable and rarely learns sparse reward signals. Deep learning models also fail to optimize path length. 

By removing PyTorch entirely and focusing on a pure, fast graph-exploration algorithm, we achieve far higher robustness and speed.

---

## 🔬 Core System Components

### 1. Volatile Status-Bar Masking
To prevent state explosion, we track which pixels change frequently (like step counters or score readouts).
* The agent calculates cell change frequency over the first few ticks.
* Rows and columns with volatility $> 0.5$ at the borders are masked out.
* The state hash is calculated only on the remaining static/functional board grid:
  $$\text{Hash} = \text{MD5}(\text{Masked Grid})[:20]$$

### 2. Connected Component Segmentation & Action Tiers
Actions are proposed using a tiered priority system based on spatial analysis:
* **Tier 0**: Simple keys (directional movement, select, etc.).
* **Tier 1–4**: Click coordinates proposed at the centroids of 4-connected components, prioritized by component size (smaller components clicked first) and biased by colors that have previously caused grid state changes.
* **Tier 5**: Coarse grid clicks (background/empty space search).
* **Tier 6**: Undo actions (lowest priority).

### 3. Directed Level Graph & Replay
The agent maintains a directed state graph for each level:
* **Frontier BFS**: When all proposed actions at the current state are tested, the agent runs a BFS over the known directed transition graph to find and navigate to the nearest untested frontier state.
* **Win-Path Replay Cache**: The first time a level is advanced, the sequence of actions is cached. If a death or regression resets the agent to a previous level, it replays the win-path immediately without wasting actions on re-exploration.

### 4. Self-Disabling Offline Planner
If the game source file is importable in the sandbox, the agent spins up a simulated copy of the level. It runs an offline BFS to find a short winning sequence. If the simulation matches the live frame exactly, it replays it. If it fails, it shuts down instantly and falls back to live graph exploration.

---

## 📊 Results & Journey

| Version | Score | Key Change / Description |
|---------|-------|--------------------------|
| Early Baseline | 0.06 | Basic random-walk search |
| No-Error Heartbeat | 0.26 | Beam search + MCTS |
| Forge v3 | 0.18 | Clean Forge v3 BFS + online CNN |
| **MASTER BASELINE v10** | **0.23** | Fixed pickling, enum serialization, and sorting bugs |
| **MASTER BASELINE v11** | **0.09** | Trigger-aware hashing, clock elimination, ACMD search |
| **Forge v20 Patched (v12)**| **0.33** | Deployed Go-Explore graph explorer, status-bar masking, win-path replay |

---

## 🚀 Quickstart

### Prerequisites
- Python 3.12+
- `arc-agi` package (≥0.9.6)

### 1. Setup
```bash
make setup
```

### 2. Local Testing
```bash
# Run against a specific game
make play-local GAME=ls20

# Run a verification check
make verify-local
```

### 3. Submit to Kaggle
```bash
make submit
```

---

## 📁 Repository Structure

```
arc_agi3_solver/
├── agent/
│   └── my_agent.py          # ← Deployed Go-Explore Agent
├── scripts/
│   └── build_notebook.py     # Packages agent → submission.ipynb
├── notebooks/
│   ├── submission.ipynb       # Auto-generated submission notebook
│   └── kernel-metadata.json   # Kaggle kernel config
├── docs/images/               # Architecture diagrams
├── environment_files/          # Local game environments for testing
└── Makefile                    # Dev workflow automation
```
