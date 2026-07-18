# Experiment Log
# EXPERIMENT_LOG.md — arc3-duck-v12

Format: config → result → what we learned. Only real runs, real numbers.

---

## Baseline progression (leaderboard, pre-this-session)
0.86 (initial forge-based agent) → 0.50 (vLLM liveness bug) → 0.62 (liveness+BFS fix)
→ 0.35 (reflection fix backfired under latency contention) → 0.96 (switched to
Tufa Labs TAAF harness) → 1.32 → **1.33 (starting point for this log)**

Config at 1.33: `{"efficiency": True, "retry_guard": True, "shortcircuit": True}`

---

## Experiment 1 — Local validation of the 1.33 config
**Config:** `{"efficiency": True, "retry_guard": True, "shortcircuit": True}` (unchanged)
**Mode:** local (Save & Run All, `TRUE_SUBMISSION=False`), 4-game offline sample
(m0r0, sk48, sk48-dup, tn36)

**Result:** mean 0.89
| Game | Score | Levels | Actions |
|---|---|---|---|
| m0r0-492f87ba | 0.00 | 0/6 | 883 |
| sk48-d8078629 | 0.00 | 0/8 | 317 |
| sk48-d8078629-dup | 0.00 | 0/8 | 409 |
| tn36-ef4dde99 | 3.57 | 1/7 | 183 |

**Learned:** m0r0 shows a GAME_OVER confusion loop (27 occurrences in transcript).
sk48 stalls hard past level 0. tn36 is the only clean solve, and it's efficient
(183 actions). This 4-game sample is small and skewed — 3 of 4 are hard fails,
so it's sensitive to anything that touches the one working game.

---

## Experiment 2 — `recovery: True` added
**Config:** `{"efficiency": True, "retry_guard": True, "shortcircuit": True, "recovery": True}`
**Mode:** local (Save & Run All), same 4 games

**Result:** mean 0.03 (regression vs. 0.89)
| Game | Score | Levels | Actions |
|---|---|---|---|
| m0r0-492f87ba | 0.00 | 0/6 | 535 (down from 883) |
| sk48-d8078629 | 0.00 | 0/8 | 266 (down from 317) |
| sk48-d8078629-dup | 0.00 | 0/8 | 353 (down from 409) |
| tn36-ef4dde99 | **0.13** | 1/7 | **244 (up from 183)** |

**Confirmed:** `recovery` armed correctly — transcripts show `[recovery] refresh fired`,
`[recovery] probe fired`, `[recovery] handoff level=1`. Not a bug/crash.

**Root cause of the regression:** the R2 probe correctly detected a real
flatline/dominance stall signal in tn36 around action 120 and fired — but tn36
was about to solve the puzzle on its own within another ~60 actions anyway. The
probe's extra actions (183→244, +33%) landed right before a natural solve, and
because score is quadratic in actions, that timing cost ~97% of the level's score.
Meanwhile the free R1/R3 pieces cut wasted actions on m0r0/sk48 but weren't
sufficient to unlock a level on either — those games are hard for reasons deeper
than stall/loop avoidance.

**Verdict:** do not ship as-is. Never submitted to leaderboard directly with this
exact 4-flag config (see Experiment 3 for what was actually submitted).

---

## Experiment 3 — Real submission: recovery + banking + transfer + dead flags
**Config (from `arc3-duck-v12-optimized.ipynb`, diffed against the working copy):**
```
{"efficiency": True, "retry_guard": True, "shortcircuit": True,
 "recovery": True, "banking": True, "transfer": True,
 "schema_void": True, "schema_notes": True, "schema_helpers": True}
```
**Mode:** REAL submission (Submit to Competition clicked — spent a daily submission)

**Result: 0.82** (regression vs. 1.33 baseline)

**Notes:**
- `context_window` — the change actually planned/discussed before this submission —
  was never included.
- `recovery` was carried over from Experiment 2 without a fix, onto the full
  25-game / ~110-clone real set (more surface area for the same probe-tax problem).
- `banking` and `transfer` were both turned on with zero prior isolated testing.
- `schema_void`/`schema_notes`/`schema_helpers` do not exist in `composite.py` —
  confirmed inert (unknown dict keys, no error, no effect).
- **Multiple unvalidated variables were stacked in one submission**, so the 0.82
  result can't be attributed to any single change. `recovery`'s already-proven
  probe-tax problem is the most likely dominant contributor, but banking/transfer's
  individual effect (positive, negative, or neutral) is genuinely unknown from
  this data point alone.

**Verdict:** reverted config back to the known 1.33 baseline
(`{"efficiency": True, "retry_guard": True, "shortcircuit": True}`) as the floor
to build forward from, one variable at a time.

---

## Planned but not yet run

- **`context_window: 57344` alone**, `recovery` reverted to `False` — isolates
  whether widening the analyzer's context window (currently 32768, half of the
  vLLM server's real 65536 ceiling) reduces the repeated-hypothesis-testing
  pattern seen in every losing transcript so far. Local validation only, not
  yet submitted for real. Risk to watch: slower per-turn generation could mean
  fewer total turns fit in the fixed wall-clock budget — check `total wallclock`
  and `generated tokens/sec` against Experiment 1/2's numbers.
- **`recovery` with a fixed R2 probe trigger** (e.g. `PROBE_MIN_ACTS` raised well
  above 183) — untested. Would need a source edit to `recovery.py` (a new
  dataset version), not just a notebook flag change.
- **`transfer`/`banking` alone**, isolated from `recovery` — untested. The
  `sk48-d8078629-dup` local game exists specifically to prove `transfer` fires;
  next isolated test should check its transcript for a `[transfer] adopted
  level...` line..
