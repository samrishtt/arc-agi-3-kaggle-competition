# ARC3-Inference Architecture

## Overall Architecture

This repository implements an ARC-AGI-3 agent harness around TAAF. The core design is a tool-using LLM agent that repeatedly observes the current ARC game state, runs ephemeral Python code against a structured board representation, and executes real environment actions through a controlled host callback.

Compared with common ARC agents, this system is closer to an interactive game-playing agent than a static ARC transformation solver. It does not primarily synthesize one-shot grid transformations. Instead, it performs sequential observe-plan-act loops over a live game environment.

## Main Subsystems

| Subsystem | Files | Role |
|---|---|---|
| Run orchestration | `inference/framework/run.py`, `Makefile`, `configs/inference.json` | Select games, deployment mode, runtime budgets, model settings, and benchmark shape. |
| TAAF adapter | `inference/framework/solver.py` | Implements the TAAF solver contract and bridges game state to the agent. |
| LLM agent | `inference/agent/tool_agent.py`, `inference/agent/prompts.py` | Builds prompts, calls the model, handles tool calls, manages memory, and dispatches Python tools. |
| Python tool runtime | `inference/agent/python_tool_sandbox.py` | Runs model-generated Python in an isolated subprocess with structured state and `action(...)`. |
| Runtime state | `inference/agent/runtime_state.py` | File-backed state contract between solver, agent, and sandbox. |
| Visual abstraction | `inference/utils/segmentation.py`, `inference/utils/grid_utils.py` | Converts 64x64 ARC grids into ASCII and connected-component object graphs. |
| Model API compatibility | `inference/utils/openai_compat.py` | Builds OpenAI-compatible request payloads for vLLM/OpenRouter-style providers. |
| Deployment | `inference/framework/kaggle.py`, TAAF deploy targets | Inline, Slurm, Kaggle, and local vLLM support. |
| Evaluation and traces | `inference/tools/eval.py`, `significance.py`, `traces.py` | Score runs, compare candidates, and export traces. |
| Viewer | `viewer/server.py`, `viewer/data.py`, `viewer/index.html` | Inspect run artifacts and agent context. |

## Execution Diagram

```text
Makefile / console script
        |
        v
inference.framework.run:main
        |
        | build config, games, solver, deployment target
        v
TAAF Benchmark
        |
        | setup, start games, run solver
        v
HarnessSolver
        |
        | one _HarnessGameSession per game/pass
        v
_HarnessGameSession.play()
        |
        | write runtime state
        v
ToolAgent.analyze()
        |
        | /chat/completions with python tool schema
        v
LLM
        |
        | python tool call
        v
python_tool_sandbox subprocess
        |
        | action([...]) JSON callback
        v
_HarnessGameSession.step_env()
        |
        | arcengine.ActionInput
        v
TAAF GameAPI / arc_agi / arcengine
        |
        v
new frame, reward, score, valid actions
        |
        +--> runtime state
        +--> transcript
        +--> viewer artifacts
        +--> TAAF benchmark artifacts
```

## Important Classes

| Class | File | Role |
|---|---|---|
| `HarnessSolver` | `inference/framework/solver.py` | TAAF `Solver` implementation. Owns setup, teardown, concurrency, analyzer creation, and game scheduling. |
| `_HarnessGameSession` | `inference/framework/solver.py` | Per-game loop. Writes state, calls analyzer, executes actions, records viewer events. |
| `ToolAgent` | `inference/agent/tool_agent.py` | LLM agent loop, prompt construction, model API calls, tool dispatch, memory and context trimming. |
| `AnalyzerTurnResult` | `inference/agent/tool_agent.py` | Result of one model-analysis turn. |
| `Frame` | `inference/agent/runtime_state.py` | Minimal persisted frame object with grid, step, level, and ASCII view. |
| `HistoryEntry` | `inference/agent/runtime_state.py` | Action plus resulting frame. |
| `FrameView` | `inference/agent/python_tool_sandbox.py` bootstrap | Sandbox-visible frame object with ASCII and lazy segmentation. |
| `TransitionView` | `inference/agent/python_tool_sandbox.py` bootstrap | Sandbox-visible before/after action transition. |

## Call Graph

```text
Makefile:_taaf-run
  -> inference-taaf-run
    -> inference.framework.run.main()
      -> _run(args)
        -> _resolve_game_ids(args)
        -> _make_games(game_ids)
        -> _make_solver(args)
          -> HarnessSolver(...)
        -> _make_deployment_target(args)
        -> taaf.benchmark.Benchmark(...)
        -> benchmark.deploy(target)
          -> Benchmark.run()
            -> played_solver.setup()
              -> HarnessSolver._setup()
                -> optional _start_local_servers()
            -> played_solver.run_games(to_play)
              -> HarnessSolver._run_games(games)
                -> _play_one(game)
                  -> _make_analyzer()
                    -> ToolAgent(...)
                  -> _HarnessGameSession.play()
                    -> write_runtime_state()
                    -> analyzer.analyze(...)
                      -> ToolAgent._build_user_prompt()
                      -> ToolAgent._chat_completion()
                      -> ToolAgent._dispatch_tool()
                        -> ToolAgent._run_python_tool()
                          -> run_sandboxed_python()
                            -> sandbox action(...)
                              -> host action_handler
                                -> _HarnessGameSession.step_env()
                                  -> _normalize_actions()
                                  -> _execute_action()
                                    -> game.execute_action()
                                      -> GameAPI._execute_action()
                    -> write_viewer_payload()
            -> played_solver.teardown()
              -> HarnessSolver._teardown()
```

## Research Review: Strengths

- Strong separation between benchmark orchestration, agent logic, sandboxed tool execution, and evaluation.
- The Python tool is genuinely grounded: `action(...)` executes real environment actions and returns refreshed state.
- Structured segmentation is a strong inductive bias for ARC-style object reasoning.
- File-backed artifacts make runs inspectable and reproducible.
- The same high-level agent can run inline, Slurm, and Kaggle.
- The system already supports batched actions, per-run transcripts, request logs, and trace export.

## Research Review: Weaknesses

- The architecture relies heavily on prompt compliance rather than built-in search/planning modules.
- The sandbox starts fresh every tool call, so useful helper code and learned per-game utilities are repeatedly regenerated.
- Runtime state is minimal and does not persist rich action-result metadata directly in history.
- Segmentation is single-frame and component-based; cross-frame object matching is left to generated code.
- There is no explicit hypothesis manager, planner, or learned policy layer.
- Evaluation is mostly post-hoc; the agent does not use aggregate failures to adapt during experiments.

## Missing Components

- A library of built-in ARC/game search primitives.
- Cross-frame object tracker and diff engine.
- Explicit planner with plan validation and replanning.
- Experiment registry tied to benchmark runs and git metadata.
- Failure taxonomy for common game-solving errors.
- Prompt A/B harness with paired statistical comparison.
- Automatic trace mining for successful action motifs.
- Persistent per-game scratch memory outside model context.

## Architecture Improvement Directions

- Add a structured `diff` and `object_tracking` view beside `segmentation`.
- Move common generated Python patterns into sandbox helper APIs.
- Store action outcomes directly in runtime history.
- Add a small deterministic planner/search tool for understood objectives.
- Make context compression state-aware rather than oldest-block deletion.
- Add evaluation hooks that classify why a run failed.

