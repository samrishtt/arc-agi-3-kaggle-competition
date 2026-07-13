# Core Files

## `inference/framework/run.py`

Purpose: true run entry point and benchmark constructor.

Dependencies: TAAF benchmark/deploy/game APIs, `HarnessSolver`, config/env values, `re_arc.EnvSampler`.

Experiment opportunities:

- Game selection and benchmark slicing.
- Runtime and concurrency budget policies.
- Deployment target behavior.
- Experiment directory and metadata design.
- Local server pool configuration.

## `inference/framework/solver.py`

Purpose: TAAF solver adapter and environment-action bridge.

Dependencies: TAAF `Solver`, TAAF `Game`, `arcengine`, `ToolAgent`, runtime state, viewer artifacts, Kaggle helpers.

Experiment opportunities:

- Action batching and early-stop behavior.
- Richer action result payloads.
- Auto-reset policy.
- Per-game scheduling and concurrency.
- Alternative analyzer factories.
- Local server routing and load balancing.
- Runtime state enrichment.

## `inference/agent/tool_agent.py`

Purpose: main LLM agent loop.

Dependencies: prompt constants, sandbox runner, runtime state, OpenAI-compatible request helpers, vision context.

Experiment opportunities:

- Prompt construction and per-turn instruction design.
- Tool schema design.
- Tool-call recovery and retry policy.
- Context trimming.
- Persistent history and world model design.
- Tool output compaction.
- Model sampling and request payload.
- New tools for search, diffing, object tracking, or planning.

## `inference/agent/python_tool_sandbox.py`

Purpose: isolated Python tool runtime.

Dependencies: segmentation source, grid color constants, subprocess protocol.

Experiment opportunities:

- Built-in helper APIs for BFS, object lookup, diffs, and local crops.
- Allowed module set.
- Persistent or cached sandbox design.
- Timeout and resource limits.
- Structured error messages.
- Richer frame/history/transition views.

## `inference/agent/prompts.py`

Purpose: prompt policy for the Duck agent.

Dependencies: ARC color legend.

Experiment opportunities:

- Better reasoning instructions.
- Stronger anti-HUD guidance.
- More precise planning and search instructions.
- Reduced prompt verbosity.
- Game-type-specific prompt modes.
- Tool-call reliability instructions.

## `inference/agent/runtime_state.py`

Purpose: persisted runtime state schema.

Dependencies: ASCII grid formatting.

Experiment opportunities:

- Store action results in history.
- Store frame diffs.
- Store object summaries.
- Store valid actions per state.
- Add compact per-level memory.

## `inference/utils/segmentation.py`

Purpose: connected-component object extraction.

Dependencies: standard library only so it can be injected into the sandbox.

Experiment opportunities:

- Add bounding boxes and centroids.
- Add holes/interior regions.
- Add color histograms and shape descriptors.
- Add cross-frame matching helpers.
- Add symmetry and line detection.
- Optimize component and containment calculation.

## `inference/agent/action_names.py`

Purpose: maps model-facing actions to engine actions.

Dependencies: none.

Experiment opportunities:

- Add aliases or action macros.
- Improve mouse-action ergonomics.
- Validate action vocabulary earlier.

## `inference/utils/openai_compat.py`

Purpose: provider-specific OpenAI-compatible request construction.

Dependencies: none.

Experiment opportunities:

- Sampling parameters.
- Provider-specific reasoning/tool-call knobs.
- Tool-choice policies.

## `inference/tools/eval.py`

Purpose: score saved benchmark runs.

Dependencies: TAAF benchmark and game artifacts.

Experiment opportunities:

- More diagnostic metrics.
- Per-level aggregation.
- Failure classification.
- Cost-normalized scoring.

## `inference/tools/traces.py`

Purpose: export chat/tool traces from saved runs.

Dependencies: viewer artifacts, transcripts, score metadata.

Experiment opportunities:

- Trace mining.
- Training data generation.
- Failure/success motif extraction.

## `inference/tools/significance.py`

Purpose: compare benchmark score files statistically.

Dependencies: score JSON, TAAF paired tests.

Experiment opportunities:

- Better acceptance criteria.
- Bootstrap variants.
- Per-game cluster analysis.

