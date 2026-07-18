# Architecture

# ARCHITECTURE.md — arc3-duck-v12

Four codebases, each with one job:

| Repo | Role |
|---|---|
| `tufa-arc-agi-framework` (`taaf`) | The harness: game state, scoring, benchmark orchestration, Kaggle packaging |
| `ARC3-Inference` (`inference`) | The agent: prompt building, LLM tool-calling loop, Python sandbox, segmentation |
| `taaf-grafts` | Non-invasive behavior patches layered on top of `inference` at notebook runtime |
| `re-arc-3` | Offline game engine snapshot (used for local validation games) |

## Flow

```
Kaggle Notebook (arc3-duck-v12.ipynb)
        │
        ▼
[1] Environment & Submission-Mode Detection
        │
        ▼
[2] Install ARC Runtime (offline wheelhouse)
        │
        ▼
[3-4] Locate + Import Source Bundle (taaf, inference, taaf-grafts on sys.path)
        │
        ▼
[5] Load Benchmark (unpickled `bm`)
        │
        ▼
[6] Graft Install  ← composite.py flags dict (the thing we've been editing)
        │
        ▼
[7] Benchmark.play()  ───────────────────────────────┐
        │                                             │
        ▼                                             │
   HarnessSolver.run_games()  (per game, per pass)     │  loop over
        │                                             │  games/levels
   ┌────▼────────── per-turn loop ─────────────────┐   │
   │  Frame + HistoryEntry (runtime_state.py)       │   │
   │         │                                      │   │
   │  Prompt Builder (prompts.py)                   │   │
   │         │                                      │   │
   │  Graft Chain (recovery → retry_guard, if on)    │   │
   │         │                                      │   │
   │  vLLM call (Qwen3.6-27B-FP8, tool_agent.py)     │   │
   │         │                                      │   │
   │  Tool-call parse                               │   │
   │         │                                      │   │
   │  Python Sandbox (python_tool_sandbox.py)        │   │
   │    └─ segmentation.py available inside it       │   │
   │         │                                      │   │
   │  Action → arcengine.step_env                   │   │
   │         │                                      │   │
   │  Score update — game.py quadratic formula       │   │
   └─────────┼──────────────────────────────────────┘   │
        │  level/game done? ── no ─────────────────────┘
        ▼ yes
[8] Diagnostics (taaf.diagnostics → HTML + summary.txt)
        │
        ▼
submission.parquet write (taaf.deploy_kaggle)
        │
        ▼
Kaggle "Submit to Competition"  ← separate, manual, spends a real submission
```

## Box-by-box

### Notebook Bootstrap (cells 1-6)
- **Purpose:** detect real-vs-local run mode, install the offline wheelhouse, mount and import the three source repos, unpickle the benchmark object, install grafts.
- **Input:** Kaggle-attached datasets (wheelhouse, Qwen weights, source bundle).
- **Output:** a live `bm` (Benchmark) object with grafts wired in, ready to `.play()`.
- **Important files:** `arc3-duck-v12.ipynb` cells 1-6, `taaf-grafts/composite.py`.
- **Why it exists:** everything downstream needs `TRUE_SUBMISSION` resolved first (it silently gates baseline visibility, diagnostics verbosity, and the dup-game gate) — see EXECUTION_FLOW.md.

### Benchmark / Solver Bridge
- **Purpose:** TAAF's game-agnostic `Solver` contract adapted to this specific LLM agent.
- **Input:** `list[taaf.game.Game]`.
- **Output:** played-out games with scores, transcripts, token counts.
- **Important files:** `taaf/benchmark.py`, `taaf/solver.py` (abstract contract), `inference/framework/solver.py` (`HarnessSolver`, the concrete adapter).
- **Why it exists:** decouples "how do I score/schedule/deploy a run" (taaf) from "how does this particular agent play one turn" (inference).

### ToolAgent Turn Loop
- **Purpose:** one observe → prompt → call model → parse → act cycle.
- **Input:** current `Frame` + `HistoryEntry` list (runtime_state.py).
- **Output:** one engine action (or a short Python-tool detour first).
- **Important files:** `inference/agent/tool_agent.py`.
- **Why it exists:** this is the actual "Agent" box — everything else is plumbing around it.

### Prompt Builder
- **Purpose:** assembles the system/user prompt from templates + current state.
- **Input:** `Frame`, history, feature addenda (`GAME_OVERVIEW_ADDENDUM`, `VISUAL_GAME_ADDENDUM`, etc.)
- **Output:** the literal message list sent to vLLM.
- **Important files:** `inference/agent/prompts.py`.
- **Why it exists:** centralizes the game-playing instructions and known failure-mode warnings (e.g. the explicit "don't mistake a HUD timer bar for a clickable object" warning — see Stage 3 bottleneck notes below).

### Graft Chain (optional interception layer)
- **Purpose:** non-invasive behavior patches applied around the stock `ToolAgent`, each independently flaggable and each guaranteed to degrade to stock on any internal error.
- **Input:** the stock analyzer + flags dict from cell 6.
- **Output:** a wrapped analyzer with the same external interface.
- **Important files:** `taaf-grafts/composite.py` (the installer), `recovery.py`, `retry_guard.py`, `agent_ext.py` (efficiency), `shortcircuit_solver.py`, `banking_solver.py`, `transfer_solver.py`, `family_store.py`.
- **Why it exists:** lets us test behavior changes without forking the underlying `inference` repo. See EXPERIMENT_LOG.md for what's actually been tested.

### Model Call
- **Purpose:** the actual inference request.
- **Input:** prompt messages, tool schema.
- **Output:** text + tool call.
- **Important files:** `inference/utils/openai_compat.py`, vLLM server (started in setup commands, `max_model_len=65536`, model `vrfai/Qwen3.6-27B-FP8`).
- **Why it exists:** this is the compute-expensive step everything else is optimizing the use of.

### Python Sandbox + Segmentation
- **Purpose:** lets the model run scratch Python (build a world model, call `segmentation.py`'s connected-component tracer) between action turns, isolated from the host process.
- **Input:** code string from the model's tool call.
- **Output:** stdout/stderr/return value fed back into the next prompt.
- **Important files:** `inference/agent/python_tool_sandbox.py`, `inference/utils/segmentation.py`.
- **Why it exists:** this is the model's only way to do anything more structured than "look at ASCII grid, guess." Segmentation is deliberately dependency-free so it can be spliced into the sandbox bootstrap where project imports aren't available.

### Game Engine / Scoring
- **Purpose:** owns the actual game rules, level transitions, and score computation.
- **Input:** engine actions (`ACTION1..6`, `RESET`).
- **Output:** new frame, level/score state.
- **Important files:** `taaf/game.py` (`_compute_final_score`), `taaf/game_api.py` (`arcengine` bridge, baseline reconciliation).
- **Why it exists:** the formula here is the single most important fact in the whole system — see below.

**The scoring formula** (`game.py:_compute_final_score`):
```
per level: min(115, (baseline_actions / actions_used)² × 100)  if the level was completed
per level: 0                                                   if not completed
```
Quadratic. This is why every optimization in this project has centered on *actions per completed level*, not just "did it complete the level." A completed level taking 33% more actions than necessary loses roughly half its score, not a third.

**Important wrinkle:** on the real graded rerun, `baseline_actions` is not provided by the API (anonymized clones) — `agent_ext.py`'s efficiency note falls back to a heuristic proxy target in that case. Locally (offline validation), the real baseline is available and used directly.

### Diagnostics + Submission
- **Purpose:** turn a finished run into human-readable output and the file Kaggle actually grades.
- **Input:** finished `Benchmark` state.
- **Output:** `diagnostics.html`, `summary.txt`, `submission.parquet`.
- **Important files:** `taaf/diagnostics.py`, `taaf/deploy_kaggle.py`.
- **Why it exists:** the parquet file is the only thing the competition actually reads; everything else is for us.

## Stage 3 — Bottleneck observations (not solved, just noted)

- **Context window is the recurring root cause of wasted actions**, not reasoning quality. Every losing transcript we pulled this session showed the same shape: the agent re-testing an action it already tried, or contradicting an earlier conclusion — consistent with `_LOCAL_ANALYZER_CONTEXT_WINDOW` (32768 tokens) being half of what the vLLM server is actually configured for (`max_model_len=65536`). Untested fix logged in IDEAS.md.
- **The efficiency graft (`agent_ext.py`) is report-only by design** — it can tell the model it's wasting actions, but has no mechanical way to stop it. It's a nudge, not a guardrail.
- **The `recovery` graft's R2 probe is a real liability, not a hypothetical one** — we have direct local evidence (EXPERIMENT_LOG.md) that its stall-detection can fire correctly and still cost more than it saves, because it doesn't know how close the agent already is to solving on its own.
- **Prompt-level warnings suggest segmentation/vision misreads are a known issue** — `prompts.py`'s `VISUAL_GAME_ADDENDUM` contains an explicit, specific warning about mistaking a HUD/timer bar for clickable puzzle pieces, which implies this was a real, previously observed failure mode worth being suspicious of in new transcripts.