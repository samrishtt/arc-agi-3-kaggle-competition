# Execution Flow

## Step-by-Step Flow

1. User launches a run through `make interactive`, `make sbatch`, `make kaggle-duck`, or `uv run inference-taaf-run`.
2. `Makefile` reads `configs/inference.json` through `inference/tools/config_value.py`.
3. `Makefile` exports model, analyzer, multimodal, server, and deployment environment variables.
4. The console script calls `inference.framework.run:main`.
5. `main()` configures logging and parses CLI arguments.
6. `main()` validates basic argument constraints such as positive pass count and model presence.
7. `main()` calls `_run(args)`.
8. `_run()` calls `_resolve_game_ids(args)` to select ARC-AGI-3 games.
9. `_run()` optionally enters competition-arcade simulation through `_enter_competition_arcade(...)`.
10. `_run()` resolves experiment directory through `_experiment_dir(args)`.
11. `_run()` computes effective concurrency through `_effective_concurrent_jobs(args)`.
12. `_run()` computes per-game runtime through `_max_runtime_minutes_per_game(...)`.
13. `_run()` writes `run_config.json` through `_write_run_config(...)`.
14. `_run()` calls `_make_solver(...)`.
15. `_make_solver()` creates a `HarnessSolver`.
16. `_run()` calls `_make_games(...)`.
17. `_make_games()` creates TAAF `GameAPI` instances.
18. `_run()` creates `taaf.benchmark.Benchmark`.
19. `_run()` calls `_make_deployment_target(...)`.
20. `_run()` calls `asyncio.run(benchmark.deploy(target))`.
21. The deployment target eventually calls `Benchmark.run(...)`.
22. `Benchmark.run()` deep-copies solver and games.
23. `Benchmark.run()` calls `played_solver.setup()`.
24. `HarnessSolver._setup()` optionally starts local vLLM servers.
25. `HarnessSolver._setup()` creates a worker thread pool sized to concurrency.
26. `Benchmark.run()` starts each game through `Game.start_game(...)`.
27. `Benchmark.run()` awaits `played_solver.run_games(to_play)`.
28. `HarnessSolver._run_games()` creates a bounded async task for each game/pass.
29. `HarnessSolver._run_games()` schedules each game into the worker pool.
30. Worker calls `HarnessSolver._play_one(game, index, pass_index, local_server)`.
31. `_play_one()` builds paths for runtime state, transcript, analysis HTML, and viewer data.
32. `_play_one()` calls `_make_analyzer(...)`.
33. `_make_analyzer()` creates `ToolAgent`.
34. `_play_one()` creates `_HarnessGameSession`.
35. `_HarnessGameSession.play()` starts the per-game loop.
36. `play()` seeds initial history.
37. `play()` writes runtime state via `write_runtime_state()`.
38. `play()` writes initial viewer payload.
39. `play()` checks stop conditions with `should_stop()`.
40. If the engine is in recoverable `GAME_OVER`, `play()` executes auto-reset.
41. `play()` calls `analyzer.analyze(...)`.
42. `ToolAgent.analyze()` loads runtime state through `load_runtime_state(...)`.
43. `ToolAgent.analyze()` builds a per-turn user prompt through `_build_user_prompt(...)`.
44. `ToolAgent.analyze()` builds the available tool schema through `_tools(...)`.
45. `ToolAgent.analyze()` trims messages through `_trim_messages_for_context(...)`.
46. `ToolAgent.analyze()` calls `_chat_completion(...)`.
47. `_chat_completion()` sends an OpenAI-compatible request to vLLM/OpenRouter.
48. The model returns text, reasoning, and/or tool calls.
49. `ToolAgent.analyze()` recovers tool-call markup if needed.
50. `ToolAgent.analyze()` dispatches a `python` tool through `_dispatch_tool(...)`.
51. `_dispatch_tool()` calls `_run_python_tool(...)`.
52. `_run_python_tool()` serializes current frame, history, valid actions, and last action result.
53. `_run_python_tool()` calls `run_sandboxed_python(...)`.
54. `run_sandboxed_python()` starts an isolated Python subprocess.
55. The sandbox bootstrap creates `FrameView`, `HistoryEntryView`, `TransitionView`, and `action(...)`.
56. The sandbox executes model-provided Python code.
57. If tool code calls `action(actions)`, the sandbox sends an action message to the host.
58. Host `action_handler` calls `ToolAgent._handle_action(...)`.
59. `_handle_action(...)` normalizes action payloads.
60. `_handle_action(...)` calls `_HarnessGameSession.step_env(...)`.
61. `step_env()` normalizes model-facing action names into `arcengine.ActionInput`.
62. `step_env()` rejects invalid or unavailable actions.
63. `step_env()` calls `_execute_action(...)`.
64. `_execute_action()` calls `game.execute_action(...)`.
65. TAAF `Game.execute_action()` records action metadata and calls `GameAPI._execute_action(...)`.
66. `GameAPI._execute_action()` calls `env.step(...)`.
67. The environment returns a new raw frame/state.
68. `_execute_action()` updates `history_entries`.
69. `_execute_action()` writes refreshed runtime state.
70. `_execute_action()` computes reward, board change, level completion, game-over, run-complete, and valid actions.
71. `_execute_action()` appends a viewer action event.
72. `step_env()` aggregates batch results and returns a compact payload.
73. The sandbox receives the action result and refreshed runtime state.
74. The sandbox may continue executing more Python code or more actions.
75. The sandbox returns final stdout/result/action results.
76. `_run_python_tool()` compacts the tool result.
77. `ToolAgent.analyze()` appends the tool result to conversation history.
78. If an action executed, `ToolAgent.analyze()` returns `AnalyzerTurnResult(step_executed=True)`.
79. `_HarnessGameSession.play()` records transcript deltas as viewer analysis events.
80. `_HarnessGameSession.play()` repeats until stop conditions fire.
81. On game completion, timeout, max actions, cancellation, or crash, `_finish_if_needed()` calls `game.finish_game()`.
82. The session removes temporary runtime state.
83. The session writes analysis HTML and final viewer payload.
84. `HarnessSolver._run_games()` awaits all game tasks.
85. `Benchmark.run()` calls `played_solver.teardown()`.
86. `HarnessSolver._teardown()` stops local servers and shuts down worker pool.
87. `Benchmark.run()` marks any still-playing games as crashed.
88. `Benchmark.run()` closes session resources.
89. `Benchmark.run()` saves benchmark JSON, intermediate states, game artifacts, solver artifact, and diagnostics.
90. Evaluation tools later read `benchmark.json` and run artifacts to compute scores.

## Important Function Chain

```text
run.main
  -> run._run
    -> run._resolve_game_ids
    -> run._make_solver
    -> run._make_games
    -> run._make_deployment_target
    -> Benchmark.deploy
      -> Benchmark.run
        -> HarnessSolver._setup
        -> HarnessSolver._run_games
          -> HarnessSolver._play_one
            -> _HarnessGameSession.play
              -> ToolAgent.analyze
                -> ToolAgent._build_user_prompt
                -> ToolAgent._chat_completion
                -> ToolAgent._dispatch_tool
                  -> ToolAgent._run_python_tool
                    -> run_sandboxed_python
                      -> sandbox action
                        -> _HarnessGameSession.step_env
                          -> _HarnessGameSession._execute_action
                            -> Game.execute_action
                              -> GameAPI._execute_action
        -> HarnessSolver._teardown
```

