# Ideas

# IDEAS.md — arc3-duck-v12

Untested. Nothing here is validated — see EXPERIMENT_LOG.md for what's actually
been run. Move an idea to that log once it's been tried.

## High confidence, cheap to test

- **Widen `context_window` toward the vLLM server's real ceiling** (currently
  32768 vs. server `max_model_len=65536`). Directly targets the repeated-
  hypothesis / self-contradiction pattern seen in every losing transcript so
  far. Single notebook flag, no dataset edit. Main risk is slower per-turn
  generation eating into the fixed wall-clock budget — watch `tokens/sec` and
  total actions reached on the stuck games, not just final score.

## Medium confidence, needs a source edit (new dataset version)

- **Fix `recovery`'s R2 probe to account for "about to solve anyway."**
  Right now `probe_due()` fires on a pure flatline/dominance signal with no
  sense of whether the level is close to done. Options:
  - Raise `PROBE_MIN_ACTS` well above a typical clean-solve action count
    (e.g. 400+) so it only fires in the genuinely-stuck long tail (m0r0/sk48
    territory), never on a slow-but-working game like tn36.
  - Or make the probe check something progress-adjacent (e.g. skip firing if
    novelty has increased at all in the last N actions, not just check for
    near-flatline) — more surgical but more invasive to test safely.
- **Test `transfer`/`banking` in isolation from `recovery`.** Unknown effect
  either direction. The `sk48-d8078629-dup` local game exists to prove
  transfer fires — check its transcript for a `[transfer] adopted level...`
  line as the pass/fail signal before trusting a score delta.

## Speculative / needs more investigation first

- Understand exactly what state does and doesn't survive the game engine's
  level-transition wipe (referenced by `recovery.py`'s R3 handoff design, but
  the actual wipe mechanics live in `game.py`/`game_api.py` and haven't been
  read closely). Would clarify whether `cross_level_notes` is really the only
  surviving channel, or whether there's a cheaper/bigger lever there.
- Check whether `agent_ext.py`'s heuristic baseline-proxy (used on the real
  submission, where the true baseline is hidden) is actually a good proxy —
  if it's badly miscalibrated, the efficiency nudge could be firing at the
  wrong times specifically on the graded run vs. local validation, which
  would explain some local-vs-real score divergence beyond what grafts alone
  explain.
