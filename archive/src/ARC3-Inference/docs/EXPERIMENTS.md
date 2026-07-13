# Experiments

This file is the research notebook for ARC3-Inference experiments. Do not overwrite completed entries. Append new results chronologically.

## Experiment Result Template

```markdown
## Experiment ID

Date:
Branch:
Hypothesis:
Motivation:
Files Changed:
Functions Changed:
Prompt Used:
Expected Outcome:
Benchmark Before:
Benchmark After:
Runtime:
Token Usage:
Observations:
Conclusion:
Next Experiment:
```

## Completion Logging Rule

Whenever an experiment is completed, append a result block with:

- Hypothesis
- Implementation
- Files Changed
- Benchmark Results
- Tokens
- Runtime
- Success or Failure
- Lessons Learned
- Future Ideas

If the experiment failed, also append a short entry to `docs/FAILED_EXPERIMENTS.md`.

## Initial 50 Performance-Relevant Experiments

| ID | Group | Experiment | Difficulty | Impact | Risk | Expected Time | Novelty |
|---|---|---|---:|---:|---:|---|---|
| #001 | Prompt Engineering | Shorten and sharpen `PYTHON_ADDENDUM` around inspect-search-act. | 1 | 4 | 2 | 30m | Low |
| #002 | Prompt Engineering | Add explicit rule to print a compact diff after every probe action. | 1 | 4 | 2 | 30m | Low |
| #003 | Prompt Engineering | Add game-type checklist: navigation, clicking, object transformation, memory. | 2 | 4 | 2 | 1h | Medium |
| #004 | Prompt Engineering | Replace repeated warnings with a single concise anti-HUD protocol. | 1 | 3 | 2 | 30m | Low |
| #005 | Prompt Engineering | Require a hypothesis/action/evidence trio before first action on each level. | 2 | 4 | 3 | 1h | Medium |
| #006 | Context Management | Preserve last successful level-completion reasoning longer than ordinary turns. | 3 | 4 | 3 | 2h | Medium |
| #007 | Context Management | Trim system prompt from transcript persistence while keeping it in request. | 3 | 3 | 3 | 2h | Low |
| #008 | Context Management | Keep compact action-result summaries while dropping verbose tool outputs. | 2 | 4 | 2 | 1h | Low |
| #009 | Context Management | Reduce carried assistant turns from 30 to a smaller validated value. | 1 | 3 | 2 | 30m | Low |
| #010 | Context Management | Add configurable context profiles: short, balanced, long. | 2 | 3 | 2 | 1h | Low |
| #011 | Planning | Add explicit replan trigger after `level_completed` or major board change. | 2 | 4 | 2 | 1h | Low |
| #012 | Planning | Add persistent fields for failed hypotheses and verified mechanics. | 2 | 4 | 2 | 1h | Medium |
| #013 | Planning | Force action batching only after objective and path are explicitly identified. | 2 | 4 | 3 | 1h | Medium |
| #014 | Planning | Add planner prompt mode for levels with stable controllable avatar. | 2 | 4 | 2 | 1h | Medium |
| #015 | Planning | Add planner prompt mode for mouse/click selection games. | 2 | 4 | 2 | 1h | Medium |
| #016 | Tool Calling | Add `diff_summary` field to Python tool action results. | 3 | 5 | 3 | 3h | Medium |
| #017 | Tool Calling | Add `changed_components` field after each action. | 4 | 5 | 3 | 4h | Medium |
| #018 | Tool Calling | Improve malformed tool-call recovery for nested JSON strings. | 2 | 2 | 1 | 1h | Low |
| #019 | Tool Calling | Add a `yield` tool result path for inspect-only turns. | 3 | 3 | 3 | 2h | Medium |
| #020 | Tool Calling | Add stricter invalid-action feedback with nearest valid alternatives. | 2 | 3 | 2 | 1h | Low |
| #021 | Sandbox | Add `current_frame.crop(r1,c1,r2,c2)` helper. | 2 | 4 | 2 | 1h | Low |
| #022 | Sandbox | Add `diff_frames(before, after)` helper. | 3 | 5 | 2 | 2h | Medium |
| #023 | Sandbox | Add `objects_by_color()` helper over segmentation nodes. | 2 | 4 | 1 | 1h | Low |
| #024 | Sandbox | Add `bbox`, `centroid`, and `touches_edge` to segmentation nodes. | 3 | 5 | 2 | 2h | Medium |
| #025 | Sandbox | Add allowed `deque` examples and helper wrappers for BFS. | 2 | 4 | 1 | 1h | Low |
| #026 | Segmentation | Add bounding boxes to each component. | 2 | 5 | 2 | 1h | Low |
| #027 | Segmentation | Add centroids and aspect ratios to each component. | 2 | 4 | 1 | 1h | Low |
| #028 | Segmentation | Add component edge-contact flags. | 2 | 4 | 1 | 1h | Low |
| #029 | Segmentation | Add hole count or enclosed-background descriptors. | 4 | 4 | 3 | 4h | Medium |
| #030 | Segmentation | Add cross-frame object matching helper by hash, overlap, and distance. | 4 | 5 | 3 | 4h | High |
| #031 | Search Strategy | Add reusable BFS helper in sandbox prompt examples. | 2 | 4 | 2 | 1h | Low |
| #032 | Search Strategy | Add deterministic shortest-path helper for avatar-target levels. | 4 | 5 | 3 | 4h | Medium |
| #033 | Search Strategy | Add limited action-sequence beam search template. | 3 | 4 | 3 | 2h | Medium |
| #034 | Search Strategy | Add probe policy: one action per direction, summarize effects, then plan. | 2 | 4 | 3 | 1h | Medium |
| #035 | Search Strategy | Add score-aware action ranking from recent transitions. | 3 | 4 | 3 | 3h | Medium |
| #036 | Evaluation | Add per-game failure taxonomy to eval output. | 3 | 3 | 1 | 3h | Medium |
| #037 | Evaluation | Add per-level completion/action efficiency table. | 2 | 3 | 1 | 2h | Low |
| #038 | Evaluation | Add token-per-score and runtime-per-score metrics. | 2 | 3 | 1 | 2h | Low |
| #039 | Evaluation | Add automatic before/after paired benchmark report for two runs. | 3 | 3 | 1 | 3h | Low |
| #040 | Evaluation | Add trace mining for actions preceding level completion. | 4 | 4 | 2 | 5h | Medium |
| #041 | Runtime | Tune temperature/top-p/top-k grid for current model. | 1 | 4 | 1 | 2h | Low |
| #042 | Runtime | Tune `tool_output_tokens` to balance evidence and context. | 1 | 4 | 1 | 1h | Low |
| #043 | Runtime | Tune `tool_steps` and `yield_seconds`. | 1 | 3 | 2 | 1h | Low |
| #044 | Runtime | Tune concurrency against local server latency and failure rate. | 2 | 3 | 2 | 2h | Low |
| #045 | Runtime | Enable request logs for small benchmark slices to inspect hidden failures. | 1 | 2 | 1 | 30m | Low |
| #046 | Reasoning | Add explicit “mechanics table” memory: action -> observed effect. | 2 | 5 | 2 | 1h | Medium |
| #047 | Reasoning | Add “do not repeat failed action sequence unless new evidence” memory rule. | 2 | 4 | 2 | 1h | Low |
| #048 | Reasoning | Add cross-level transfer memory field. | 2 | 4 | 2 | 1h | Medium |
| #049 | Reasoning | Require confidence label before batching more than 3 actions. | 2 | 3 | 2 | 1h | Low |
| #050 | Reasoning | Add final pre-action sanity check: valid action, target object, expected change. | 1 | 4 | 1 | 30m | Low |

## Top 10 Experiments To Attempt First

These are small, isolated, easy to benchmark, easy to revert, high expected impact, and relatively low risk.

### #001 Sharpen Inspect-Search-Act Prompt

Hypothesis: A shorter, more directive Python-tool prompt will reduce wandering and increase useful tool calls.

Why it might improve ARC: The current prompt is comprehensive but repetitive. A cleaner instruction may improve model compliance and reduce context burden.

Files changed: `inference/agent/prompts.py`.

Expected code change: Edit `PYTHON_ADDENDUM` wording only. No runtime code changes.

Measure success: Compare score, actions per completed level, tool-call failure rate, and token usage on the same small game slice.

### #002 Add Compact Diff Rule After Probes

Hypothesis: Requiring compact before/after diffs will improve causal inference.

Why it might improve ARC: Many ARC game failures come from confusing gameplay changes with HUD/timer changes.

Files changed: `inference/agent/prompts.py`.

Expected code change: Add one instruction in `PYTHON_ADDENDUM` and/or `_build_user_prompt()` requesting compact diffs after probe actions.

Measure success: More correct action-effect summaries in transcripts; improved score on games requiring mechanical discovery.

### #011 Replan After Level Completion

Hypothesis: Stronger re-grounding after level transitions will prevent stale plans.

Why it might improve ARC: Levels often change layouts or mechanics. Blindly continuing prior strategy wastes actions.

Files changed: `inference/agent/tool_agent.py`.

Expected code change: Adjust `_build_user_prompt()` to emphasize re-grounding when `previous_step_summary.level_transition` is true.

Measure success: Lower first-few-actions waste after level completion.

### #023 Add `objects_by_color()` Helper

Hypothesis: A tiny object grouping helper will reduce repeated boilerplate and object-counting errors.

Why it might improve ARC: Many levels are solved by identifying colors/objects and their counts.

Files changed: `inference/agent/python_tool_sandbox.py`.

Expected code change: Add a sandbox helper that groups `current_frame.segmentation["nodes"]` by `color`.

Measure success: Shorter tool code, fewer malformed segmentation loops, better score on object-centric games.

### #026 Add Bounding Boxes To Segmentation

Hypothesis: Bounding boxes are a high-value, low-risk object feature.

Why it might improve ARC: Position, size, edge contact, and alignment are central to ARC reasoning.

Files changed: `inference/utils/segmentation.py`, maybe prompt docs.

Expected code change: Add `bbox: [min_row, min_col, max_row, max_col]` to each node.

Measure success: More frequent use of bboxes in tool code; better performance on spatial-object tasks.

### #027 Add Centroids And Aspect Ratios

Hypothesis: Simple geometry descriptors improve target selection and movement planning.

Why it might improve ARC: Centroids/aspect ratios help distinguish bars, blocks, agents, targets, and UI strips.

Files changed: `inference/utils/segmentation.py`.

Expected code change: Add `centroid` and `aspect_ratio` fields to nodes.

Measure success: Better object classification and fewer HUD confusions.

### #028 Add Edge-Contact Flags

Hypothesis: Explicit edge contact helps distinguish HUD/timer bars from gameplay objects.

Why it might improve ARC: The prompt already warns about edge bars; data support makes the warning easier to act on.

Files changed: `inference/utils/segmentation.py`.

Expected code change: Add `touches_edge` and side-specific flags.

Measure success: Reduced repeated actions against border UI elements.

### #042 Tune Tool Output Tokens

Hypothesis: Current tool result budget may hide useful evidence or waste context.

Why it might improve ARC: Tool output size directly affects the model’s available state and memory.

Files changed: `configs/inference.json` only.

Expected code change: Adjust `analyzer.tool_output_tokens`, benchmark several values.

Measure success: Score/token tradeoff and context-overflow rate.

### #046 Add Mechanics Table Memory

Hypothesis: Persisting action-effect mappings will reduce rediscovery.

Why it might improve ARC: Sequential ARC games often require learning controls or mechanics before solving.

Files changed: `inference/agent/tool_agent.py`, possibly `prompts.py`.

Expected code change: Add/update a world-model field such as `action_model` or structured mechanics table.

Measure success: Fewer repeated probes, better level-to-level transfer, improved score on multi-level games.

### #050 Add Pre-Action Sanity Check

Hypothesis: A simple sanity-check instruction prevents invalid or poorly grounded actions.

Why it might improve ARC: Many failures are cheap mistakes: invalid action, wrong coordinate convention, no expected change.

Files changed: `inference/agent/prompts.py`.

Expected code change: Add one concise checklist before calling `action(...)`.

Measure success: Lower invalid-action count and fewer no-op actions.

## Roadmap: Experiment #001 To #100

### Phase 1: Fast Prompt And Config Calibration

#001 Sharpen inspect-search-act prompt.
#002 Add compact diff rule after probes.
#003 Add game-type checklist.
#004 Consolidate anti-HUD guidance.
#005 Require hypothesis/action/evidence trio.
#006 Preserve successful level-completion reasoning.
#007 Reduce prompt repetition in persisted history.
#008 Keep compact action summaries, drop verbose tool output.
#009 Tune carried assistant turns.
#010 Add context profiles.
#011 Replan after level completion.
#012 Add failed-hypothesis and verified-mechanic memory fields.
#013 Restrict batching until objective/path confidence.
#014 Navigation-specific planner mode.
#015 Mouse/click-specific planner mode.
#016 Tune temperature/top-p/top-k.
#017 Tune tool-output tokens.
#018 Tune tool steps and yield seconds.
#019 Enable request logs on smoke slices.
#020 Add invalid-action feedback wording.

### Phase 2: Low-Risk State And Segmentation Features

#021 Add `crop()` helper.
#022 Add frame diff helper.
#023 Add `objects_by_color()` helper.
#024 Add bbox to segmentation nodes.
#025 Add centroid/aspect ratio to nodes.
#026 Add edge-contact flags.
#027 Add area rank and dominant-background hints.
#028 Add component compactness descriptor.
#029 Add small-object and large-region classification.
#030 Add local crop around changed cells.
#031 Store last action result in runtime history.
#032 Store valid actions with history entries.
#033 Store board-changed metadata in history.
#034 Add action count since level start.
#035 Add per-level memory reset/transfer policy.
#036 Add transition summaries to runtime state.
#037 Add stable object IDs within a turn.
#038 Add object hash frequency summaries.
#039 Add simple line/bar detector.
#040 Add hole/enclosure descriptors.

### Phase 3: Built-In Search And Planning Helpers

#041 Add BFS helper template.
#042 Add shortest-path helper for avatar-target levels.
#043 Add beam-search template.
#044 Add directional probe policy.
#045 Add score-aware action ranking.
#046 Add mechanics table memory.
#047 Add no-repeat-failed-sequence rule.
#048 Add cross-level transfer memory.
#049 Add confidence threshold for long batches.
#050 Add pre-action sanity check.
#051 Add reusable object matching helper.
#052 Add changed-component action scorer.
#053 Add click-target ranking helper.
#054 Add movement-effect classifier.
#055 Add terminal-state-aware batch builder.
#056 Add macro expansion for repeated directional moves.
#057 Add route compression for movement sequences.
#058 Add action-loop detector.
#059 Add exploratory policy for unknown mechanics.
#060 Add conservative policy for near-complete levels.

### Phase 4: Tool And Sandbox Expansion

#061 Add dedicated `diff` tool.
#062 Add dedicated `object_summary` tool.
#063 Add dedicated `search_actions` tool.
#064 Add structured tool result schema versioning.
#065 Add richer sandbox exceptions with user-code line context.
#066 Add optional persistent helper library loaded into sandbox.
#067 Add configurable safe helper imports.
#068 Add sandbox execution telemetry.
#069 Add timeout-aware partial result return.
#070 Add lightweight persistent per-game scratchpad outside model context.
#071 Add automatic tool-output summarizer.
#072 Add action-result visual crop attachment.
#073 Add multimodal off/on comparison.
#074 Add image crop context instead of full grid image.
#075 Add model-specific tool-call format profiles.
#076 Add retry after malformed tool-call with stricter prompt.
#077 Add retry after no-action inspect-only turn.
#078 Add adaptive tool budget by game stage.
#079 Add adaptive temperature by uncertainty.
#080 Add local server load-aware scheduling.

### Phase 5: Evaluation, Mining, And Higher-Risk Research

#081 Add per-game failure taxonomy.
#082 Add per-level action-efficiency table.
#083 Add token-per-score metrics.
#084 Add paired before/after report.
#085 Mine traces before level completion.
#086 Mine common failed loops.
#087 Build benchmark smoke subset by failure category.
#088 Add automatic transcript linting for prompt compliance.
#089 Add run comparison dashboard fields.
#090 Add success-case prompt distillation.
#091 Add failure-case prompt patch proposals.
#092 Add learned retrieval from prior successful traces.
#093 Add rule library generated from mined traces.
#094 Add per-game strategy memory cache.
#095 Add self-consistency over multiple proposed plans.
#096 Add critic pass before action execution.
#097 Add speculative search using copied game state if safely available.
#098 Add multi-agent planner/executor split.
#099 Add offline fine-tuning trace exporter improvements.
#100 Add full research harness for automated experiment sweeps.

## Approval Rule For Future Code Changes

For every proposed experiment, before changing code:

1. Explain the hypothesis.
2. Explain the reasoning.
3. Explain why this might improve ARC.
4. Estimate expected benchmark impact.
5. Estimate possible drawbacks.
6. Wait for approval.

