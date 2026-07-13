# Research Ideas

## Prompt

- Compress the prompt into a smaller inspect-plan-act protocol.
- Add game-type-specific prompt modes.
- Replace repeated warnings with structured checklists.
- Add an explicit “what evidence would falsify this plan?” instruction.
- Add coordinate convention reminders only when `MOUSE` is valid.

## Planning

- Maintain a mechanics table: action, observed effect, confidence, exceptions.
- Require re-grounding after each level transition.
- Add confidence thresholds before long action batches.
- Add loop detection and plan abandonment.
- Add a small critic pass before executing high-risk actions.

## Reasoning

- Store failed hypotheses separately from current beliefs.
- Track known gameplay objects versus suspected HUD objects.
- Track controllable object candidates.
- Track goal candidates and evidence for each.
- Track cross-level transfer separately from current-level state.

## Sandbox

- Add helper functions for crops, diffs, object grouping, and BFS.
- Add a persistent helper library instead of asking the model to retype utilities.
- Improve error messages from generated Python.
- Return partial results on timeout.
- Add action sequence builders that stop automatically on terminal state.

## Context

- Keep successful level-completion reasoning longer.
- Compress old tool outputs into structured action summaries.
- Use different context profiles for short smoke runs and long official runs.
- Keep per-level summaries rather than raw full conversation turns.
- Detect context overflow earlier using model-specific tokenization if available.

## Segmentation

- Add bounding boxes, centroids, aspect ratios, and edge contact.
- Add holes and enclosure descriptors.
- Add line/bar detectors for HUD identification.
- Add cross-frame object matching.
- Add changed-object summaries after each action.
- Add symmetry and repeated-pattern descriptors.

## Evaluation

- Add failure taxonomies: invalid action, no-op loop, HUD confusion, stale plan, timeout, context loss.
- Add per-level action efficiency and token efficiency.
- Mine traces before successful level transitions.
- Compare prompt variants with paired run reports.
- Maintain benchmark smoke sets grouped by failure mode.

## Paper-Review Style Comparison To Common ARC Agent Architectures

### Design Strengths

- Better suited to interactive ARC-AGI-3 than static one-shot ARC solvers.
- Strong tool-grounding: model-generated code can inspect state and execute real actions.
- Segmentation creates an object-centric representation, matching a common ARC prior.
- The harness has serious engineering support: concurrency, deployment, artifacts, viewer, scoring, traces.
- The model is discouraged from raw pixel memorization and encouraged toward programmatic evidence gathering.

### Design Weaknesses

- Search and planning are emergent from prompts, not first-class algorithmic modules.
- State abstraction is useful but still shallow: object identity across frames is not built in.
- The Python tool has no persistent helper library or learned routines.
- The world model is text-extracted from assistant messages, so memory quality depends on compliance.
- No explicit separation between proposer, verifier, planner, and executor.

### Missing Components

- Deterministic object tracker.
- Built-in grid/action search tools.
- Hypothesis manager.
- Failure classifier.
- Prompt-variant benchmark harness.
- Experience replay or retrieval from prior successful traces.
- Program synthesis module for reusable game mechanics.

### Architecture Improvements

- Add a small deterministic perception layer before prompting.
- Add a stable action-effect memory schema.
- Add helper APIs so the model spends fewer tokens writing boilerplate.
- Add automatic failure labels to evaluation.
- Add a planner/executor split once baseline prompt and perception changes stabilize.

### Potential Research Ideas

- Compare prompt-only search against built-in BFS/search helper APIs.
- Study whether object-centric descriptors improve transfer across levels.
- Mine successful traces to generate reusable game-mechanic templates.
- Evaluate text-only segmentation versus multimodal grid images.
- Add a critic that predicts whether a planned action sequence is likely to be a no-op/HUD trap.

