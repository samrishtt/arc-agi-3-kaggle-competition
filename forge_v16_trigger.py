# --- Cell ---
!pip install --no-index --find-links \
    /kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels \
    arc-agi python-dotenv

# --- Cell ---
%%writefile /kaggle/working/my_agent.py
# =====================================================================
# v17-16
# hash() instead of MD5 for state hashing	~5x faster BFS exploration
# Fix counter A* hash to use tuples	Prevents crash if dead-code A* path activates
# Multiplier [2, 3, 1.5] → [2, 3, 4]	Fix: int(1.5)=1 was a no-op
# Adaptive BFS time budget	If BFS solved L0, give L1 20% instead of 10%
# Init _visited_hashes in __init__ + level reset	Fix: was checked via hasattr — fragile
# Reward: new states +1.5, revisited +0.2, track properly	CNN learns smoother value signal
# Prioritized experience replay	High-reward + recent transitions sampled more
# Beam search after IDDFS (width 20-200, depth 60)	Covers medium-branching games BFS/IDDFS miss
# =====================================================================
import heapq
import pickle
import copy
import glob
import hashlib
import importlib.util
import logging
import os
import random
import time
import traceback
from collections import deque
from itertools import permutations
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from agents.agent import Agent
from arcengine import FrameData, GameAction, GameState, ActionInput

logger = logging.getLogger(__name__)

# Faster cloning via pickle — 2-3x faster than copy.deepcopy for game objects
copy.deepcopy = lambda obj, _memo=None: pickle.loads(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))

# ==================== BFS SOLVER ====================

class BFSSolver:
    """Offline BFS solver using direct game class instantiation."""

    def __init__(self, game_path, game_class_name, scan_timeout=3, bfs_timeout=120):
        self.game_path = game_path
        self.class_name = game_class_name
        self.scan_timeout = scan_timeout
        self.bfs_timeout = bfs_timeout
        self.game_cls = None
        self.solutions = {}  # level_idx → action list
        self._warmup_prefix = []  # v14: prepended to solutions when warm-up unlock used

    def load(self):
        """Load the game class from source."""
        try:
            spec = importlib.util.spec_from_file_location('game_mod', self.game_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.game_cls = getattr(mod, self.class_name)
            return True
        except Exception as e:
            logger.warning(f"BFS: Failed to load game class: {e}")
            return False

    def _state_hash(self, g, frame, hidden_fields=None):
        """Hash frame + hidden scalar fields. Uses builtin hash (5x faster than MD5)."""
        fh = hash(frame.tobytes())
        if hidden_fields:
            return (fh, tuple(getattr(g, f, None) for f in hidden_fields))
        return fh

    def _extract_win_field(self):
        """v11: Extract win-condition field name from source code."""
        try:
            source = open(self.game_path).read()
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if 'self.next_level()' in line:
                    for j in range(i-1, max(0, i-8), -1):
                        s = lines[j].strip()
                        if s.startswith('if ') or s.startswith('elif '):
                            import re
                            m = re.search(r'self\.(\w+)', s)
                            if m:
                                return m.group(1)
                    break
        except:
            pass
        return None

    def _probe_hidden_fields(self, game, actions):
        """v11: Dynamic state probing with win-field awareness."""
        if not actions:
            return []
        # Always include the win field if we can extract it
        win_field = self._extract_win_field()

        initial = {}
        for k, v in game.__dict__.items():
            if isinstance(v, (int, float, bool)) and not k.startswith('__'):
                initial[k] = v

        changing_fields = set()
        # If we found win field, always include it
        if win_field and win_field in initial:
            changing_fields.add(win_field)

        frame0 = game.get_pixels(0, 0, 64, 64)
        for act_id, data in actions[:10]:
            g = copy.deepcopy(game)
            try:
                ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                g.perform_action(ai, raw=True)
            except:
                continue
            f = g.get_pixels(0, 0, 64, 64)
            pixels_changed = np.sum(frame0 != f) > 0
            for k, v in g.__dict__.items():
                if isinstance(v, (int, float, bool)) and not k.startswith('__'):
                    if k in initial and v != initial[k]:
                        if k not in ('_action_count', '_full_reset', '_action_complete'):
                            changing_fields.add(k)

        # Filter: only keep fields that change WITHOUT pixel changes (truly hidden)
        # Also keep counters that might be win-relevant
        hidden = []
        for f in changing_fields:
            if f.startswith('_') and f not in ('_current_level_index', '_score'):
                continue
            hidden.append(f)
        return sorted(hidden)

    def _scan_actions(self, game, f0, bg):
        """Scan for effective actions. Returns list of (action_id, data)."""
        avail = game._available_actions
        actions = []
        # Directional/interact actions
        for a in [a for a in avail if a <= 5]:
            g = copy.deepcopy(game)
            try:
                r = g.perform_action(ActionInput(id=GameAction.from_id(a)), raw=True)
                if r.frame and np.sum(f0 != np.array(r.frame[-1])) > 0:
                    actions.append((a, None))
            except:
                pass
        # v15: Click scan WITHOUT dedup — dedup killed cd82 L1 and sp80 L1
        # v16: Also probe stride-1 neighbors of hits to catch odd-coordinate sprites
        if 6 in avail:
            t0 = time.time()
            hit_positions = []
            for y in range(0, 64, 2):
                if time.time() - t0 > self.scan_timeout:
                    break
                for x in range(0, 64, 2):
                    if f0[y, x] == bg:
                        continue
                    g = copy.deepcopy(game)
                    try:
                        r = g.perform_action(
                            ActionInput(id=GameAction.ACTION6, data={'x': x, 'y': y, 'game_id': 'bfs'}),
                            raw=True
                        )
                        if not r.frame:
                            continue
                        f = np.array(r.frame[-1])
                        if np.sum(f0 != f) > 0:
                            actions.append((6, {'x': x, 'y': y, 'game_id': 'bfs'}))
                            hit_positions.append((x, y))
                    except:
                        pass
            # Probe stride-1 neighbors of hits (catch odd-coordinate sprites)
            tried = {(x, y) for x, y in hit_positions}
            for hx, hy in hit_positions:
                if time.time() - t0 > self.scan_timeout * 1.5:
                    break
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = hx+dx, hy+dy
                    if (nx, ny) in tried or not (0 <= nx < 64 and 0 <= ny < 64):
                        continue
                    tried.add((nx, ny))
                    if f0[ny, nx] == bg:
                        continue
                    g = copy.deepcopy(game)
                    try:
                        r = g.perform_action(
                            ActionInput(id=GameAction.ACTION6, data={'x': nx, 'y': ny, 'game_id': 'bfs'}),
                            raw=True
                        )
                        if r.frame and np.sum(f0 != np.array(r.frame[-1])) > 0:
                            actions.append((6, {'x': nx, 'y': ny, 'game_id': 'bfs'}))
                    except:
                        pass
        return actions

    def solve_level(self, level_idx, max_states=500000, prev_solution=None):
        """Find optimal solution for a level via BFS."""
        if not self.game_cls:
            return None

        game = self.game_cls()
        game.set_level(level_idx)
        game.perform_action(ActionInput(id=GameAction.RESET), raw=True)

        r0 = game.perform_action(ActionInput(id=GameAction.RESET), raw=True)
        if not r0.frame:
            return None
        f0 = np.array(r0.frame[-1])
        bg = int(np.bincount(f0.flatten(), minlength=16).argmax())

        # v9: Try solution transfer from previous level first
        if prev_solution and level_idx > 0:
            transfer_result = self._try_transfer(game, level_idx, prev_solution, f0)
            if transfer_result:
                return transfer_result

        # Phase 1: Scan for effective actions
        actions = self._scan_actions(game, f0, bg)

        # v14 FIX 1: Warm-up unlock — if no actions found, try a warm-up action then re-scan
        if not actions:
            logger.info(f"BFS L{level_idx}: 0 actions found, trying warm-up unlock")
            avail = game._available_actions
            for warmup_id in [a for a in avail if a <= 4]:  # try directional as warm-up
                g_warmup = copy.deepcopy(game)
                try:
                    g_warmup.perform_action(ActionInput(id=GameAction.from_id(warmup_id)), raw=True)
                    f_after = np.array(g_warmup.get_pixels(0, 0, 64, 64))
                    # Re-scan from warmed-up state
                    warmup_actions = self._scan_actions(g_warmup, f_after, bg)
                    if warmup_actions:
                        logger.info(f"BFS L{level_idx}: UNLOCKED with ACTION{warmup_id}! {len(warmup_actions)} actions found")
                        game = g_warmup  # use warmed-up game as new start
                        f0 = f_after
                        actions = warmup_actions
                        # Prepend warm-up to any solution found
                        self._warmup_prefix = [(warmup_id, None)]
                        break
                except:
                    pass

        logger.info(f"BFS L{level_idx}: {len(actions)} effective actions (after dedup)")
        if not actions:
            return None

        # v16: Probe trigger fields BEFORE main BFS for better state distinction
        trigger_fields = None
        raw_hidden = self._probe_hidden_fields(game, actions)
        if raw_hidden:
            clock_fields = set()
            if actions:
                try:
                    g_t1 = copy.deepcopy(game)
                    ai_t = ActionInput(id=GameAction.from_id(actions[0][0]), data=actions[0][1]) if actions[0][1] else ActionInput(id=GameAction.from_id(actions[0][0]))
                    g_t1.perform_action(ai_t, raw=True)
                    g_t2 = copy.deepcopy(g_t1)
                    g_t2.perform_action(ai_t, raw=True)
                    for fld in raw_hidden:
                        v1 = getattr(g_t1, fld, None)
                        v2 = getattr(g_t2, fld, None)
                        if v1 != v2:
                            clock_fields.add(fld)
                except:
                    pass
            trigger_fields = [fld for fld in raw_hidden if fld not in clock_fields]
            if not trigger_fields:
                trigger_fields = None
            else:
                logger.info(f"BFS L{level_idx}: trigger fields for hash: {trigger_fields}")

        # v12: Detect win field + counter direction for A* priority
        win_field = self._extract_win_field()
        counter_dir = 0  # 0=unknown, +1=maximize, -1=minimize
        win_initial = None
        if win_field:
            win_initial = getattr(game, win_field, None)
            if isinstance(win_initial, (int, float)):
                for act_id, data in actions[:5]:
                    g_probe = copy.deepcopy(game)
                    try:
                        ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                        g_probe.perform_action(ai, raw=True)
                        new_val = getattr(g_probe, win_field, win_initial)
                        if isinstance(new_val, (int, float)) and new_val != win_initial:
                            source = open(self.game_path).read()
                            if f'{win_field} >=' in source or f'{win_field} >' in source:
                                counter_dir = +1
                            elif f'{win_field} <=' in source or f'{win_field} <' in source:
                                counter_dir = -1
                            break
                    except:
                        pass
            if counter_dir != 0:
                logger.info(f"BFS L{level_idx}: counter detected: {win_field}={win_initial}, dir={'max' if counter_dir>0 else 'min'}")
                if trigger_fields and win_field not in trigger_fields:
                    trigger_fields.append(win_field)
                elif not trigger_fields:
                    trigger_fields = [win_field]

        # v16: Plain BFS first (with trigger fields in hash), counter A* as fallback
        use_counter_priority = False
        visited = set()
        h0 = self._state_hash(game, f0, trigger_fields)
        visited.add(h0)
        t0 = time.time()
        explored = 0
        fifo_counter = 0

        if use_counter_priority:
            # v12: Lexicographic A* — (counter_rank, depth, fifo_id)
            initial_counter = getattr(game, win_field, 0)
            if not isinstance(initial_counter, (int, float)):
                initial_counter = 0
            counter_rank = -initial_counter * counter_dir  # lower = better
            heap = [(counter_rank, 0, fifo_counter, copy.deepcopy(game), [])]
            fifo_counter += 1

            while heap and explored < max_states and (time.time() - t0) < self.bfs_timeout:
                cr, depth, _, g, hist = heapq.heappop(heap)
                for act_id, data in actions:
                    g2 = copy.deepcopy(g)
                    try:
                        ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                        r = g2.perform_action(ai, raw=True)
                    except: continue
                    explored += 1
                    if not r.frame: continue
                    f = np.array(r.frame[-1])
                    # Include win field in hash for counter games
                    wv = getattr(g2, win_field, '')
                    h = (self._state_hash(g2, f, None), win_field, wv)
                    if h in visited: continue
                    visited.add(h)
                    new_hist = hist + [(act_id, data)]
                    if r.levels_completed > level_idx or g2._current_level_index > level_idx:
                        logger.info(f"BFS L{level_idx}: SOLVED (A*) in {len(new_hist)} actions ({explored} explored, {time.time()-t0:.1f}s)")
                        self.solutions[level_idx] = new_hist
                        return new_hist
                    cv = getattr(g2, win_field, 0)
                    new_cr = -(cv if isinstance(cv, (int,float)) else 0) * counter_dir
                    fifo_counter += 1
                    if depth < 30:
                        heapq.heappush(heap, (new_cr, depth+1, fifo_counter, g2, new_hist))
        else:
            # Standard BFS with trigger-aware hashing
            queue = deque()
            queue.append((copy.deepcopy(game), [], 0))
            while queue and explored < max_states and (time.time() - t0) < self.bfs_timeout:
                g, hist, depth = queue.popleft()
                for act_id, data in actions:
                    g2 = copy.deepcopy(g)
                    try:
                        ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                        r = g2.perform_action(ai, raw=True)
                    except: continue
                    explored += 1
                    if not r.frame: continue
                    f = np.array(r.frame[-1])
                    h = self._state_hash(g2, f, trigger_fields)
                    if h in visited: continue
                    visited.add(h)
                    new_hist = hist + [(act_id, data)]
                    if r.levels_completed > level_idx or g2._current_level_index > level_idx:
                        logger.info(f"BFS L{level_idx}: SOLVED in {len(new_hist)} actions ({explored} explored, {time.time()-t0:.1f}s)")
                        sol = self._warmup_prefix + new_hist
                        self.solutions[level_idx] = sol
                        return sol
                    if depth < 30:
                        queue.append((g2, new_hist, depth + 1))

        elapsed_first = time.time() - t0
        logger.info(f"BFS L{level_idx}: first pass timeout ({explored} explored, {len(visited)} unique, {elapsed_first:.1f}s)")

        # v16: Counter A* fallback — only runs AFTER plain BFS fails, only when counter detected
        if counter_dir != 0 and win_field and elapsed_first < self.bfs_timeout * 0.6:
            remaining_ca = max(60, self.bfs_timeout - elapsed_first)
            logger.info(f"BFS L{level_idx}: trying counter A* fallback ({win_field}, dir={'max' if counter_dir>0 else 'min'}, {remaining_ca:.0f}s)")
            game_ca = self.game_cls()
            game_ca.set_level(level_idx)
            game_ca.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            game_ca.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            f0_ca = np.array(game_ca.get_pixels(0, 0, 64, 64))
            initial_counter = getattr(game_ca, win_field, 0)
            if not isinstance(initial_counter, (int, float)):
                initial_counter = 0
            visited_ca = set()
            h0_ca = self._state_hash(game_ca, f0_ca, trigger_fields)
            visited_ca.add(h0_ca)
            counter_rank = -initial_counter * counter_dir
            fifo_ca = 0
            heap_ca = [(counter_rank, 0, fifo_ca, copy.deepcopy(game_ca), [])]
            fifo_ca += 1
            t0_ca = time.time()
            explored_ca = 0
            while heap_ca and explored_ca < max_states and (time.time() - t0_ca) < remaining_ca:
                cr, depth, _, g, hist = heapq.heappop(heap_ca)
                for act_id, data in actions:
                    g2 = copy.deepcopy(g)
                    try:
                        ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                        r = g2.perform_action(ai, raw=True)
                    except: continue
                    explored_ca += 1
                    if not r.frame: continue
                    f = np.array(r.frame[-1])
                    h = self._state_hash(g2, f, trigger_fields)
                    if h in visited_ca: continue
                    visited_ca.add(h)
                    new_hist = hist + [(act_id, data)]
                    if r.levels_completed > level_idx or g2._current_level_index > level_idx:
                        logger.info(f"BFS L{level_idx}: SOLVED (counter A*) in {len(new_hist)} actions ({explored_ca} explored, {time.time()-t0_ca:.1f}s)")
                        sol = self._warmup_prefix + new_hist
                        self.solutions[level_idx] = sol
                        return sol
                    cv = getattr(g2, win_field, 0)
                    new_cr = -(cv if isinstance(cv, (int, float)) else 0) * counter_dir
                    fifo_ca += 1
                    if depth < 40:
                        heapq.heappush(heap_ca, (new_cr, depth + 1, fifo_ca, g2, new_hist))
            logger.info(f"BFS L{level_idx}: counter A* done ({explored_ca} explored, {len(visited_ca)} unique, {time.time()-t0_ca:.1f}s)")

        # v13: ACMD Trigger Finder — when pixels alias, use internal state delta as priority
        # (CHRONOS Gemini T34, n=0.109: "Action-Conditional Masked RAM Delta Priority")
        if len(visited) < 100 and elapsed_first < self.bfs_timeout * 0.8:
            hidden_fields = self._probe_hidden_fields(game, actions)
            if hidden_fields:
                logger.info(f"BFS L{level_idx}: ACMD trigger search with fields: {hidden_fields}")

                # Pre-compute clock mask: fields that change on NO-OP (timers, not triggers)
                clock_fields = set()
                g_noop = copy.deepcopy(game)
                snap_before = {f: getattr(g_noop, f, None) for f in hidden_fields}
                try:
                    # Try a no-op: perform same action twice, see what auto-changes
                    if actions:
                        g_noop2 = copy.deepcopy(g_noop)
                        ai = ActionInput(id=GameAction.from_id(actions[0][0]), data=actions[0][1]) if actions[0][1] else ActionInput(id=GameAction.from_id(actions[0][0]))
                        g_noop2.perform_action(ai, raw=True)
                        g_noop3 = copy.deepcopy(g_noop2)
                        g_noop3.perform_action(ai, raw=True)
                        for f in hidden_fields:
                            v1 = getattr(g_noop2, f, None)
                            v2 = getattr(g_noop3, f, None)
                            if v1 == v2:  # didn't change between identical actions → not a clock
                                pass
                            else:
                                clock_fields.add(f)
                except: pass
                trigger_fields = [f for f in hidden_fields if f not in clock_fields]
                if not trigger_fields:
                    trigger_fields = hidden_fields  # fallback: use all

                # ACMD priority search: promote actions that change trigger fields
                game2 = self.game_cls()
                game2.set_level(level_idx)
                game2.perform_action(ActionInput(id=GameAction.RESET), raw=True)
                game2.perform_action(ActionInput(id=GameAction.RESET), raw=True)
                f0_2 = np.array(game2.perform_action(ActionInput(id=GameAction.RESET), raw=True).frame[-1])

                visited2 = set()
                init_state = {f: getattr(game2, f, None) for f in trigger_fields}
                h0_2 = self._state_hash(game2, f0_2, trigger_fields)
                visited2.add(h0_2)
                fifo2 = 0
                # Priority: (negative_trigger_delta, depth, fifo) — lower = better
                heap2 = [(0, 0, fifo2, copy.deepcopy(game2), [])]
                fifo2 += 1

                t0_2 = time.time()
                explored2 = 0
                remaining = max(60, self.bfs_timeout - elapsed_first)

                while heap2 and explored2 < max_states and (time.time() - t0_2) < remaining:
                    neg_delta, depth, _, g, hist = heapq.heappop(heap2)

                    for act_id, data in actions:
                        g2 = copy.deepcopy(g)
                        try:
                            ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                            r = g2.perform_action(ai, raw=True)
                        except: continue
                        explored2 += 1
                        if not r.frame: continue
                        f = np.array(r.frame[-1])
                        h = self._state_hash(g2, f, trigger_fields)
                        if h in visited2: continue
                        visited2.add(h)
                        new_hist = hist + [(act_id, data)]

                        if r.levels_completed > level_idx or g2._current_level_index > level_idx:
                            logger.info(f"BFS L{level_idx}: SOLVED (ACMD) in {len(new_hist)} actions ({explored2} explored, {time.time()-t0_2:.1f}s)")
                            self.solutions[level_idx] = new_hist
                            return new_hist

                        # Compute trigger delta: how much did trigger fields change?
                        pixels_changed = np.sum(f0_2 != f) > 0
                        trigger_delta = 0
                        for tf in trigger_fields:
                            cv = getattr(g2, tf, None)
                            iv = init_state.get(tf)
                            if isinstance(cv, (int, float)) and isinstance(iv, (int, float)):
                                trigger_delta += abs(cv - iv)
                            elif cv != iv:
                                trigger_delta += 1

                        # ACMD priority: PROMOTE if trigger changed, PRUNE if nothing changed
                        if not pixels_changed and trigger_delta == 0:
                            continue  # true no-op: prune completely
                        # Lower priority = explored first. Negative delta = more trigger progress
                        priority = -trigger_delta
                        fifo2 += 1
                        if depth < 40:
                            heapq.heappush(heap2, (priority, depth + 1, fifo2, g2, new_hist))

                logger.info(f"BFS L{level_idx}: ACMD finished ({explored2} explored, {len(visited2)} unique, {time.time()-t0_2:.1f}s)")

        # v16: Sprite permutation for pure-click games with few targets
        elapsed_perm_start = time.time() - t0
        click_actions = [a for a in actions if a[0] == 6]
        non_click = [a for a in actions if a[0] != 6]
        if not non_click and 1 <= len(click_actions) <= 8 and (self.bfs_timeout - elapsed_perm_start) > 10:
            n_perms = 1
            for i in range(1, len(click_actions)+1): n_perms *= i
            logger.info(f"BFS L{level_idx}: trying sprite permutation ({len(click_actions)} clicks, {n_perms} perms)")
            t0_perm = time.time()
            perm_timeout = min(60, self.bfs_timeout - elapsed_perm_start)
            for perm in permutations(range(len(click_actions))):
                if time.time() - t0_perm > perm_timeout:
                    break
                g_perm = copy.deepcopy(game)
                hist_perm = []
                solved = False
                for idx in perm:
                    act_id, data = click_actions[idx]
                    try:
                        ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                        r = g_perm.perform_action(ai, raw=True)
                        hist_perm.append((act_id, data))
                        if r.levels_completed > level_idx or g_perm._current_level_index > level_idx:
                            logger.info(f"BFS L{level_idx}: SOLVED (permutation) in {len(hist_perm)} actions")
                            sol = self._warmup_prefix + hist_perm
                            self.solutions[level_idx] = sol
                            return sol
                    except:
                        break
            logger.info(f"BFS L{level_idx}: permutation exhausted ({time.time()-t0_perm:.1f}s)")

        # v14 FIX 2: IDDFS for deep directional games (low branching, deep solution)
        elapsed_total = time.time() - t0
        remaining_time = max(30, self.bfs_timeout - elapsed_total)
        if len(actions) <= 6 and remaining_time > 30:
            logger.info(f"BFS L{level_idx}: trying IDDFS (branching={len(actions)}, {remaining_time:.0f}s remaining)")
            game3 = self.game_cls()
            game3.set_level(level_idx)
            game3.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            game3.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            t0_3 = time.time()
            for max_depth in range(10, 60):
                if time.time() - t0_3 > remaining_time:
                    break
                # DFS with depth limit + path-based cycle detection
                stack = [(copy.deepcopy(game3), [], set())]
                explored3 = 0
                while stack and (time.time() - t0_3) < remaining_time:
                    g, hist, path_hashes = stack.pop()
                    if len(hist) >= max_depth:
                        continue
                    for act_id, data in actions:
                        g2 = copy.deepcopy(g)
                        try:
                            ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                            r = g2.perform_action(ai, raw=True)
                        except: continue
                        explored3 += 1
                        if not r.frame: continue
                        f = np.array(r.frame[-1])
                        h = self._state_hash(g2, f, trigger_fields)
                        if h in path_hashes: continue
                        new_hist = hist + [(act_id, data)]
                        if r.levels_completed > level_idx or g2._current_level_index > level_idx:
                            logger.info(f"BFS L{level_idx}: SOLVED (IDDFS depth={max_depth}) in {len(new_hist)} actions ({explored3} explored, {time.time()-t0_3:.1f}s)")
                            sol = self._warmup_prefix + new_hist
                            self.solutions[level_idx] = sol
                            return sol
                        new_path = path_hashes | {h}
                        stack.append((g2, new_hist, new_path))
            logger.info(f"BFS L{level_idx}: IDDFS exhausted (depth={max_depth}, {time.time()-t0_3:.1f}s)")

        # v17: Beam search fallback — guided by trigger + pixel progress
        elapsed_bs = time.time() - t0
        remaining_bs = max(20, self.bfs_timeout - elapsed_bs)
        if 2 <= len(actions) <= 15 and remaining_bs > 20:
            logger.info(f"BFS L{level_idx}: trying beam search (b={len(actions)}, {remaining_bs:.0f}s)")
            bw = min(200, max(20, max_states // (len(actions) * 50)))
            game_b = self.game_cls()
            game_b.set_level(level_idx)
            game_b.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            game_b.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            f0_b = np.array(game_b.get_pixels(0, 0, 64, 64))
            beam = [(copy.deepcopy(game_b), [])]
            t0_b = time.time()
            vis_b = set()
            vis_b.add(self._state_hash(game_b, f0_b, trigger_fields))
            for bd in range(60):
                if time.time() - t0_b > remaining_bs or not beam:
                    break
                cands = []
                for g_b, hist_b in beam:
                    for act_id, data in actions:
                        g2 = copy.deepcopy(g_b)
                        try:
                            ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                            r = g2.perform_action(ai, raw=True)
                        except Exception:
                            continue
                        if not r.frame:
                            continue
                        f = np.array(r.frame[-1])
                        h = self._state_hash(g2, f, trigger_fields)
                        if h in vis_b:
                            continue
                        vis_b.add(h)
                        nh = hist_b + [(act_id, data)]
                        if r.levels_completed > level_idx or g2._current_level_index > level_idx:
                            logger.info(f"BFS L{level_idx}: SOLVED (beam d={bd}) in {len(nh)} acts")
                            sol = self._warmup_prefix + nh
                            self.solutions[level_idx] = sol
                            return sol
                        pdiff = float(np.sum(f != f0_b)) / 4096.0
                        tscore = 0.0
                        if trigger_fields:
                            for tf in trigger_fields:
                                cv = getattr(g2, tf, None)
                                iv = getattr(game_b, tf, None)
                                if isinstance(cv, (int, float)) and isinstance(iv, (int, float)):
                                    tscore += abs(cv - iv)
                        cands.append((tscore * 10.0 + pdiff, g2, nh))
                if not cands:
                    break
                cands.sort(key=lambda x: x[0], reverse=True)
                beam = [(g_b, h_b) for _, g_b, h_b in cands[:bw]]
            logger.info(f"BFS L{level_idx}: beam done ({len(vis_b)} unique, {time.time()-t0_b:.1f}s)")

        return None

    def _try_transfer(self, game, level_idx, prev_solution, f1):
        """v13: Affine transfer with scale detection + action count multiplier."""
        try:
            # Try executing prev solution directly (sometimes levels share exact solution)
            g = copy.deepcopy(game)
            for i, (act_id, data) in enumerate(prev_solution):
                try:
                    ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                    r = g.perform_action(ai, raw=True)
                    if r.levels_completed > level_idx or g._current_level_index > level_idx:
                        logger.info(f"BFS L{level_idx}: TRANSFER SUCCESS (direct replay, {i+1} actions)")
                        sol = prev_solution[:i+1]
                        self.solutions[level_idx] = sol
                        return sol
                except:
                    break

            # Try object-relative transfer (CHRONOS Opus T11)
            prev_game = self.game_cls()
            prev_game.set_level(level_idx - 1)
            prev_game.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            r_prev = prev_game.perform_action(ActionInput(id=GameAction.RESET), raw=True)
            if not r_prev.frame:
                return None
            f0 = np.array(r_prev.frame[-1])
            bg = int(np.bincount(f0.flatten(), minlength=16).argmax())

            # Extract objects from both levels
            def get_objects(frame, bg_c):
                objs = []
                for c in range(16):
                    if c == bg_c:
                        continue
                    mask = (frame == c)
                    npix = int(np.sum(mask))
                    if npix < 2:
                        continue
                    ys, xs = np.where(mask)
                    objs.append({'color': c, 'cx': float(np.mean(xs)), 'cy': float(np.mean(ys)), 'n': npix})
                return sorted(objs, key=lambda o: (o['color'], -o['n']))

            objs_prev = get_objects(f0, bg)
            objs_curr = get_objects(f1, bg)

            if not objs_prev or not objs_curr:
                return None

            # Match objects by color + relative size
            matched = []
            for op in objs_prev:
                best = None
                best_dist = float('inf')
                for oc in objs_curr:
                    if oc['color'] == op['color'] and abs(oc['n'] - op['n']) < max(op['n'], oc['n']) * 0.5:
                        d = abs(oc['cx'] - op['cx']) + abs(oc['cy'] - op['cy'])
                        if d < best_dist:
                            best_dist = d
                            best = oc
                if best:
                    matched.append((op, best))

            if not matched:
                return None

            # Compute offset
            dx = np.mean([m[1]['cx'] - m[0]['cx'] for m in matched])
            dy = np.mean([m[1]['cy'] - m[0]['cy'] for m in matched])

            # Apply offset to click actions
            transferred = []
            for act_id, data in prev_solution:
                if data and 'x' in data:
                    new_data = dict(data)
                    new_data['x'] = max(0, min(63, int(data['x'] + dx)))
                    new_data['y'] = max(0, min(63, int(data['y'] + dy)))
                    transferred.append((act_id, new_data))
                else:
                    transferred.append((act_id, data))

            # Validate transferred solution
            g = copy.deepcopy(game)
            for i, (act_id, data) in enumerate(transferred):
                try:
                    ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                    r = g.perform_action(ai, raw=True)
                    if r.levels_completed > level_idx or g._current_level_index > level_idx:
                        logger.info(f"BFS L{level_idx}: TRANSFER SUCCESS (offset dx={dx:.0f},dy={dy:.0f}, {i+1} actions)")
                        sol = transferred[:i+1]
                        self.solutions[level_idx] = sol
                        return sol
                except:
                    break

            # v13: If offset transfer failed, try action-count multiplier (CHRONOS T28)
            # L1 might need same actions repeated more times
            for multiplier in [2, 3, 4]:
                expanded = []
                for act_id, data in prev_solution:
                    for _ in range(int(multiplier)):
                        if data:
                            new_data = dict(data)
                            new_data['x'] = max(0, min(63, int(data.get('x', 32) + dx)))
                            new_data['y'] = max(0, min(63, int(data.get('y', 32) + dy)))
                            expanded.append((act_id, new_data))
                        else:
                            expanded.append((act_id, data))
                g = copy.deepcopy(game)
                for i, (act_id, data) in enumerate(expanded):
                    try:
                        ai = ActionInput(id=GameAction.from_id(act_id), data=data) if data else ActionInput(id=GameAction.from_id(act_id))
                        r = g.perform_action(ai, raw=True)
                        if r.levels_completed > level_idx or g._current_level_index > level_idx:
                            logger.info(f"BFS L{level_idx}: TRANSFER SUCCESS (multiplier={multiplier}, {i+1} actions)")
                            sol = expanded[:i+1]
                            self.solutions[level_idx] = sol
                            return sol
                    except:
                        break

        except Exception as e:
            logger.warning(f"BFS transfer failed: {e}")
        return None


def find_game_source_and_class(game_id, arc_env=None):
    """Find the game .py file and class name."""
    gid = game_id.split('-')[0]
    cls_name = gid.capitalize()
    if len(gid) == 4 and gid[0].isalpha():
        cls_name = gid[0].upper() + gid[1:]

    src = None
    # Method 1: from arc_env
    if arc_env and hasattr(arc_env, 'environment_info'):
        ei = arc_env.environment_info
        if hasattr(ei, 'local_dir') and ei.local_dir:
            from pathlib import Path
            ld = Path(ei.local_dir)
            for candidate in [ld / f"{gid}.py", ld / f"{cls_name.lower()}.py"]:
                if candidate.exists():
                    src = str(candidate)
                    # Get class name from source
                    import re
                    content = candidate.read_text()[:2000]
                    m = re.search(r'class\s+(\w+)\s*\(\s*ARCBaseGame', content)
                    if m:
                        cls_name = m.group(1)
                    break

    # Method 2: glob
    if not src:
        for pattern in [
            f"/tmp/*/{gid}/*/{gid}.py",
            f"/kaggle/*/{gid}*/{gid}.py",
            f"**/game_sources/**/{gid}.py",
        ]:
            matches = glob.glob(pattern, recursive=True)
            if matches:
                src = matches[0]
                import re
                content = open(src).read()[:2000]
                m = re.search(r'class\s+(\w+)\s*\(\s*ARCBaseGame', content)
                if m:
                    cls_name = m.group(1)
                break

    return src, cls_name


# ==================== CNN FALLBACK (v8 core) ====================

class CBAM(nn.Module):
    def __init__(s, ch, r=16):
        super().__init__()
        s.fc1=nn.Linear(ch,max(ch//r,4)); s.fc2=nn.Linear(max(ch//r,4),ch)
        s.sp=nn.Conv2d(2,1,7,padding=3)
    def forward(s, x):
        B,C,H,W=x.shape
        w=torch.sigmoid(s.fc2(F.relu(s.fc1(x.mean(dim=[2,3]))))); x=x*w.view(B,C,1,1)
        a=torch.sigmoid(s.sp(torch.cat([x.max(1,keepdim=True)[0],x.mean(1,keepdim=True)],1)))
        return x*a

class ActionEffectAttention(nn.Module):
    def __init__(s, feat_dim=64, mem_dim=32, n_actions=5):
        super().__init__()
        s.mem_dim=mem_dim
        s.diff_enc=nn.Sequential(nn.Conv2d(1,8,8,stride=8),nn.ReLU(),nn.Conv2d(8,16,4,stride=4),nn.ReLU(),nn.Flatten(),nn.Linear(16*2*2,mem_dim))
        s.q_proj=nn.Linear(feat_dim,mem_dim)
        s.v_proj=nn.Linear(mem_dim+1+n_actions,n_actions)
        s.scale=mem_dim**0.5
    def forward(s, cnn_feat, mem_diffs, mem_actions, mem_rewards):
        B,M=mem_actions.shape
        if M==0:return torch.zeros(B,5,device=cnn_feat.device)
        keys=s.diff_enc(mem_diffs.reshape(B*M,1,64,64)).reshape(B,M,s.mem_dim)
        q=s.q_proj(cnn_feat).unsqueeze(1)
        attn=F.softmax(torch.bmm(q,keys.transpose(1,2))/s.scale,dim=-1)
        act_oh=F.one_hot(mem_actions.clamp(0,4),5).float()
        vals=torch.cat([keys,mem_rewards.unsqueeze(-1),act_oh],dim=-1)
        ctx=torch.bmm(attn,vals).squeeze(1)
        return s.v_proj(ctx)

class ForgeNet(nn.Module):
    def __init__(s, in_ch=26, g=64):
        super().__init__()
        s.g=g
        s.c1=nn.Conv2d(in_ch,32,3,padding=1);s.c2=nn.Conv2d(32,64,3,padding=1)
        s.c3=nn.Conv2d(64,128,3,padding=1);s.c4=nn.Conv2d(128,256,3,padding=1)
        s.attn=CBAM(256);s.ar=nn.Conv2d(256,64,1);s.ap=nn.MaxPool2d(4,4)
        s.af=nn.Linear(64*16*16,256);s.ah=nn.Linear(256,5);s.dr=nn.Dropout(0.15)
        s.cc1=nn.Conv2d(256,128,3,padding=1);s.cc2=nn.Conv2d(128,64,3,padding=1)
        s.cc3=nn.Conv2d(64,32,1);s.cc4=nn.Conv2d(32,1,1)
        s.gp=nn.AdaptiveAvgPool2d(1);s.gf=nn.Linear(256,64)
        s.aea=ActionEffectAttention(feat_dim=64,mem_dim=32,n_actions=5)
    def forward(s, x, mem_diffs=None, mem_actions=None, mem_rewards=None):
        x=F.relu(s.c1(x));x=F.relu(s.c2(x));x=F.relu(s.c3(x));f=F.relu(s.c4(x))
        f=s.attn(f);af=F.relu(s.ar(f));af=s.ap(af).reshape(f.size(0),-1)
        al=s.ah(s.dr(F.relu(s.af(af))))
        cf=F.relu(s.cc1(f));cf=F.relu(s.cc2(cf));cf=F.relu(s.cc3(cf))
        cl=s.cc4(cf).reshape(f.size(0),-1)
        if mem_diffs is not None and mem_actions is not None:
            gf=s.gf(s.gp(f).reshape(f.size(0),-1))
            al=al+s.aea(gf,mem_diffs,mem_actions,mem_rewards)
        return torch.cat([al,cl],1)


def fast_objects(frame, bg):
    objs=[]
    for c in range(16):
        if c==bg:continue
        mask=(frame==c);npix=int(np.sum(mask))
        if npix<4 or npix>3000:continue
        ys,xs=np.where(mask)
        objs.append((c,float(np.mean(xs)),float(np.mean(ys)),npix))
    return objs


# ==================== AGENT ====================

class MyAgent(Agent):
    MAX_ACTIONS = float('inf')
    _MAX_FRAMES = 10

    def __init__(s, *a, **kw):
        super().__init__(*a, **kw)
        seed = int(time.time()*1e6) + hash(s.game_id) % 1000000
        random.seed(seed); np.random.seed(seed%(2**32-1)); torch.manual_seed(seed%(2**32-1))
        s.start_time = time.time()
        s.device = torch.device('cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu'))
        s.G=64; s.IN=26
        s.net=None; s.opt=None
        s.buf=deque(maxlen=50000); s.buf_h=set()
        s.bsz=64; s.tfreq=10
        s.pt=None; s.pai=None; s.pr=None; s.ph=None
        s.cl=-1; s.fhist=deque(maxlen=6); s.la=0
        s.al=[GameAction.ACTION1,GameAction.ACTION2,GameAction.ACTION3,GameAction.ACTION4,GameAction.ACTION5]
        s._wd=False; s._bg=0; s._wm=None
        s._aem_diffs=deque(maxlen=256); s._aem_actions=deque(maxlen=256); s._aem_rewards=deque(maxlen=256)
        s._ckpt_hash=None; s._unproductive=0; s._undo_avail=False
        s._eps=0.15; s._eps_min=0.03; s._eps_decay=0.9997
        s._prev_objs=None; s._obj_moved=0
        s._visited_hashes=set()
        # BFS solver
        s._bfs = None
        s._bfs_solution = None  # current level's solution
        s._bfs_step = 0  # current step in solution
        s._bfs_tried = False

    def append_frame(s, f):
        s.frames.append(f)
        if len(s.frames) > s._MAX_FRAMES: s.frames = s.frames[-s._MAX_FRAMES:]
        if f.guid: s.guid = f.guid
        if hasattr(s, "recorder") and not s.is_playback:
            import json; s.recorder.record(json.loads(f.model_dump_json()))

    def _lvl(s, f): return getattr(f, 'score', None) or f.levels_completed
    def _raw(s, fd): return np.array(fd.frame, dtype=np.int64)[-1]

    def _init_bfs(s):
        """Initialize BFS solver on first call."""
        src, cls = find_game_source_and_class(s.game_id, s.arc_env)
        if src:
            s._bfs = BFSSolver(src, cls, scan_timeout=5, bfs_timeout=180)
            if s._bfs.load():
                logger.info(f"BFS: loaded {cls} from {src}")
            else:
                s._bfs = None
                logger.warning(f"BFS: failed to load game class")
        else:
            logger.warning(f"BFS: game source not found for {s.game_id}")

    def _try_bfs_solve(s, level_idx):
        """Try to solve current level with BFS, using adaptive time budget."""
        if s._bfs is None:
            return None
        elapsed = time.time() - s.start_time
        total_budget = 8 * 3600 - 600
        remaining = max(60, total_budget - elapsed)
        # Adaptive: if BFS solved previous level, it's likely viable — give more time
        if level_idx == 0:
            time_for_bfs = min(remaining * 0.3, 600)  # up to 10 min for L0
        elif s._bfs.solutions.get(level_idx - 1) is not None:
            time_for_bfs = min(remaining * 0.2, 480)  # BFS worked before — give 20%
        else:
            time_for_bfs = min(remaining * 0.08, 180)  # BFS failed — cap at 3 min
        time_for_bfs = max(30, time_for_bfs)
        s._bfs.bfs_timeout = int(time_for_bfs)
        logger.info(f"BFS L{level_idx}: budget={time_for_bfs:.0f}s (elapsed={elapsed:.0f}s, remaining={remaining:.0f}s, CNN gets {remaining-time_for_bfs:.0f}s)")

        prev_sol = s._bfs.solutions.get(level_idx - 1) if level_idx > 0 else None
        sol = s._bfs.solve_level(level_idx, prev_solution=prev_sol)
        if sol:
            s._bfs_solution = sol
            s._bfs_step = 0
            return sol
        return None

    def _tensor(s, fd):
        frame = s._raw(fd)
        oh=torch.zeros(16,64,64,dtype=torch.float32)
        oh.scatter_(0,torch.from_numpy(frame).unsqueeze(0),1)
        cnt=np.bincount(frame.flatten(),minlength=16)
        s._bg=int(cnt.argmax());mx=max(cnt.max(),1)
        bg_m=(frame==s._bg).astype(np.float32)
        rar=np.zeros((64,64),np.float32)
        for c in range(16):
            if cnt[c]>0:rar[frame==c]=1.0-cnt[c]/mx
        pad=np.pad(frame,1,mode='edge')
        edge=((frame!=pad[:-2,1:-1])|(frame!=pad[2:,1:-1])|(frame!=pad[1:-1,:-2])|(frame!=pad[1:-1,2:])).astype(np.float32)
        rp=np.linspace(0,1,64,dtype=np.float32).reshape(64,1).repeat(64,1)
        cp=np.linspace(0,1,64,dtype=np.float32).reshape(1,64).repeat(64,0)
        aug=torch.from_numpy(np.stack([bg_m,rar,edge,rp,cp]))
        d1=torch.zeros(3,64,64,dtype=torch.float32)
        for i,prev in enumerate(reversed(list(s.fhist))):
            if i>=3:break
            d1[i]=torch.from_numpy((frame!=prev).astype(np.float32))
        d2=torch.zeros(2,64,64,dtype=torch.float32)
        h=list(s.fhist)
        if len(h)>=2:d2[0]=torch.from_numpy((h[-1]!=h[-2]).astype(np.float32))
        if len(h)>=4:d2[1]=torch.from_numpy((h[-2]!=h[-4]).astype(np.float32))
        s.fhist.append(frame.copy())
        return torch.cat([oh,aug,d1,d2],0).to(s.device)

    def _detect_template(s, frame):
        mask=torch.ones(4096,dtype=torch.float32)
        col_act=np.sum(frame!=s._bg,axis=0)
        for c in range(20,44):
            if col_act[c]<=2 and np.sum(col_act[:c]>0)>=5 and np.sum(col_act[c+1:]>0)>=5:
                for y in range(64):
                    for x in range(c+1):mask[y*64+x]=0.05
                return mask
        row_act=np.sum(frame!=s._bg,axis=1)
        for r in range(20,44):
            if row_act[r]<=2 and np.sum(row_act[:r]>0)>=5 and np.sum(row_act[r+1:]>0)>=5:
                for y in range(r+1):
                    for x in range(64):mask[y*64+x]=0.05
                return mask
        return mask

    def _reward(s, prev_raw, curr_raw, prev_h, curr_h):
        mask=np.ones((64,64),dtype=bool);mask[:2]=False;mask[62:]=False
        diff=(prev_raw!=curr_raw)&mask;changed=np.any(diff)
        r=0.0
        if curr_h!=prev_h:r+=1.5 if curr_h not in s._visited_hashes else 0.2
        elif curr_h==prev_h:r-=0.1
        s._visited_hashes.add(curr_h)
        if changed:r+=0.5
        curr_objs=fast_objects(curr_raw,s._bg)
        if s._prev_objs and curr_objs:
            moved=0
            for co in curr_objs:
                for po in s._prev_objs:
                    if co[0]==po[0]:
                        dist=abs(co[1]-po[1])+abs(co[2]-po[2])
                        if 2<dist<20:moved+=1;break
            if moved>0:r+=0.3*min(moved,3);s._obj_moved=moved
        s._prev_objs=curr_objs
        return r

    def _sample(s, logits, avail=None, temp=1.0):
        al=logits[:5].clone();cl=logits[5:5+4096].clone()
        if avail is not None and len(avail)>0:
            mask=torch.full_like(al,float('-inf'));a6=False
            for a in avail:
                aid=a.value if hasattr(a,'value') else int(a)
                if 1<=aid<=5:mask[aid-1]=0.0
                elif aid==6:a6=True
            al=al+mask
            if not a6:cl=cl+torch.full_like(cl,float('-inf'))
        if s._wm is not None:cl=cl+torch.log(s._wm.to(s.device).clamp(min=0.01))
        ap=torch.sigmoid(al/temp);cp=torch.sigmoid(cl/temp)/(s.G*s.G)
        allp=torch.cat([ap,cp]);sm=allp.sum()
        if sm<1e-8:allp=torch.ones_like(allp)/len(allp)
        else:allp=allp/sm
        idx=np.random.choice(len(allp),p=allp.cpu().numpy())
        if idx<5:return idx,None
        ci=idx-5;return 5,(ci//s.G,ci%s.G)

    def _heuristic(s, frame, avail, step):
        av=set(int(a.value) if hasattr(a,'value') else int(a) for a in avail)
        for d in[1,2,3,4]:
            if d in av and step<4:return d-1,None
        if 6 in av:
            cnt=np.bincount(frame.flatten(),minlength=16);targets=[]
            for c in range(16):
                if c==s._bg or cnt[c]==0 or cnt[c]>2000:continue
                ys,xs=np.where(frame==c)
                if len(ys)>=2:targets.append((int(np.median(xs)),int(np.median(ys)),len(ys)))
            targets.sort(key=lambda t:t[2]);pidx=step-4
            if 0<=pidx<len(targets):return 5,(targets[pidx][1],targets[pidx][0])
        if 5 in av:return 4,None
        choices=[a for a in av if 1<=a<=5]
        if choices:return random.choice(choices)-1,None
        return 0,None

    def _frame_to_tensor(s, frame):
        oh=torch.zeros(16,64,64,dtype=torch.float32)
        oh.scatter_(0,torch.from_numpy(frame).unsqueeze(0),1)
        cnt=np.bincount(frame.flatten(),minlength=16)
        bg=int(cnt.argmax());mx=max(cnt.max(),1)
        bg_m=(frame==bg).astype(np.float32)
        rar=np.zeros((64,64),np.float32)
        for c in range(16):
            if cnt[c]>0:rar[frame==c]=1.0-cnt[c]/mx
        pad=np.pad(frame,1,mode='edge')
        edge=((frame!=pad[:-2,1:-1])|(frame!=pad[2:,1:-1])|(frame!=pad[1:-1,:-2])|(frame!=pad[1:-1,2:])).astype(np.float32)
        rp=np.linspace(0,1,64,dtype=np.float32).reshape(64,1).repeat(64,1)
        cp=np.linspace(0,1,64,dtype=np.float32).reshape(1,64).repeat(64,0)
        aug=torch.from_numpy(np.stack([bg_m,rar,edge,rp,cp]))
        zeros=torch.zeros(5,64,64,dtype=torch.float32)
        return torch.cat([oh,aug,zeros],0)

    def _train(s):
        if len(s.buf)<s.bsz:return
        weights=np.array([abs(e['r'])+0.1 for e in s.buf])
        n=len(weights);weights[max(0,n-100):]*=2.0
        weights/=weights.sum()
        indices=np.random.choice(n,s.bsz,replace=False,p=weights)
        batch=[s.buf[i] for i in indices]
        states=torch.stack([s._frame_to_tensor(e['s']).to(s.device) for e in batch])
        acts=torch.tensor([e['a'] for e in batch],dtype=torch.long,device=s.device)
        rews=torch.tensor([e['r'] for e in batch],dtype=torch.float32,device=s.device)
        rews=torch.sigmoid(rews);s.opt.zero_grad()
        logits=s.net(states)
        acts_c=acts.clamp(0,logits.size(1)-1)
        sel=logits.gather(1,acts_c.unsqueeze(1)).squeeze(1)
        loss=F.binary_cross_entropy_with_logits(sel,rews)
        p=torch.sigmoid(logits);loss=loss-0.0001*p[:,:5].mean()-0.00001*p[:,5:].mean()
        loss.backward();s.opt.step()

    def _get_aem_tensors(s):
        if len(s._aem_diffs)<2:return None,None,None
        M=len(s._aem_diffs)
        diffs=torch.zeros(1,M,1,64,64,device=s.device)
        acts=torch.zeros(1,M,dtype=torch.long,device=s.device)
        rews=torch.zeros(1,M,device=s.device)
        for i,(d,a,r) in enumerate(zip(s._aem_diffs,s._aem_actions,s._aem_rewards)):
            diffs[0,i,0]=torch.from_numpy(d.astype(np.float32));acts[0,i]=min(a,4);rews[0,i]=r
        return diffs,acts,rews

    def is_done(s, frames, lf):
        try: return lf.state is GameState.WIN or (time.time()-s.start_time) >= 8*3600-300
        except: return True

    def choose_action(s, frames, lf):
        try:
            lvl = s._lvl(lf)

            # ===== LEVEL CHANGE =====
            if lvl != s.cl:
                # Init BFS solver on first level
                if not s._bfs_tried:
                    s._bfs_tried = True
                    s._init_bfs()

                # Try BFS for this level
                s._bfs_solution = None
                s._bfs_step = 0
                if s._bfs:
                    s._try_bfs_solve(lvl)

                # Init CNN fallback
                s.buf.clear(); s.buf_h.clear()
                s.net = ForgeNet(s.IN, s.G).to(s.device)
                for wp in ['/kaggle/input/forge-pretrained-weights/pretrained_weights.pt',
                           'pretrained_weights.pt']:
                    try:
                        if os.path.exists(wp):
                            state=torch.load(wp,map_location=s.device,weights_only=True)
                            ms=s.net.state_dict()
                            for k in list(state.keys()):
                                if k in ms and state[k].shape==ms[k].shape:ms[k]=state[k]
                            s.net.load_state_dict(ms);break
                    except: pass
                s.opt = optim.Adam(s.net.parameters(), lr=0.0003)
                s.pt=None;s.pai=None;s.pr=None;s.ph=None
                s.cl=lvl;s.fhist.clear();s.la=0
                s._wd=False;s._wm=None;s._eps=0.15
                s._aem_diffs.clear();s._aem_actions.clear();s._aem_rewards.clear()
                s._prev_objs=None;s._obj_moved=0;s._ckpt_hash=None;s._unproductive=0;s._visited_hashes=set()

            # ===== RESET =====
            if lf.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
                s.pt=None;s.pai=None;s.pr=None;s.ph=None
                a=GameAction.RESET;a.reasoning="reset";return a

            # ===== BFS SOLUTION EXECUTION =====
            if s._bfs_solution and s._bfs_step < len(s._bfs_solution):
                act_id, data = s._bfs_solution[s._bfs_step]
                s._bfs_step += 1
                sel = GameAction.from_id(act_id)
                if data:
                    sel.set_data(data)
                sel.reasoning = f"bfs:{s._bfs_step}/{len(s._bfs_solution)}"
                # Still update prev state for fallback
                raw = s._raw(lf)
                s.fhist.append(raw.copy())
                s.pr = raw.copy()
                s.la += 1
                return sel

            # ===== CNN FALLBACK (v8 core) =====
            tensor = s._tensor(lf)
            raw = s._raw(lf)
            ch = hashlib.md5(raw.tobytes()).hexdigest()[:16]
            avail = getattr(lf, 'available_actions', None) or []
            s._undo_avail = any((a.value if hasattr(a,'value') else int(a))==7 for a in avail)

            if s.pt is not None and s.pai is not None:
                mask=np.ones((64,64),dtype=bool);mask[:2]=False;mask[62:]=False
                diff_map=(s.pr!=raw)&mask;changed=np.any(diff_map)
                eh=hashlib.md5(s.pr.tobytes()[:1000]+str(s.pai).encode()).hexdigest()[:16]
                if eh not in s.buf_h:
                    r=s._reward(s.pr,raw,'',ch)
                    s.buf.append({'s':s.pr.copy(),'a':s.pai,'r':r})
                    s.buf_h.add(eh)
                    if changed:
                        s._aem_diffs.append(diff_map)
                        s._aem_actions.append(min(s.pai,4))
                        s._aem_rewards.append(r)
                if changed:s._ckpt_hash=ch;s._unproductive=0
                else:s._unproductive+=1

            avail_idx=[]
            for a in avail:
                aid=a.value if hasattr(a,'value') else int(a)
                if 1<=aid<=5:avail_idx.append(aid-1)
                elif aid==6:avail_idx.extend([5+i for i in range(0,4096,128)])

            if s._wm is None:s._wm=s._detect_template(raw)

            if s._undo_avail and s._unproductive>=30 and s._ckpt_hash:
                s._unproductive=0;a=GameAction.ACTION7;a.reasoning="undo"
                s.pt=tensor;s.pai=6;s.pr=raw.copy();s.ph=ch;s.la+=1;return a

            if not s._wd:
                if s.la<10:aidx,coords=s._heuristic(raw,avail,s.la)
                else:
                    s._wd=True
                    for _ in range(min(5,len(s.buf)//s.bsz)):s._train()

            if s._wd:
                if random.random()<s._eps:
                    aidx,coords=s._sample(torch.zeros(4101,device=s.device),avail,temp=2.0)
                else:
                    with torch.no_grad():
                        mem=s._get_aem_tensors()
                        if mem[0] is not None:logits=s.net(tensor.unsqueeze(0),*mem).squeeze(0)
                        else:logits=s.net(tensor.unsqueeze(0)).squeeze(0)
                    aidx,coords=s._sample(logits,avail,temp=0.5)
                s._eps=max(s._eps_min,s._eps*s._eps_decay)
            elif s.la>=10:s._wd=True;aidx,coords=0,None

            if aidx<5:sel=s.al[aidx];sel.reasoning=f"cnn:a{aidx+1}"
            else:
                sel=GameAction.ACTION6;y,x=coords
                sel.set_data({"x":int(x),"y":int(y)});sel.reasoning=f"cnn:c({x},{y})"

            s.pt=tensor;s.pai=aidx if aidx<5 else(5+coords[0]*s.G+coords[1])
            s.pr=raw.copy();s.ph=ch;s.la+=1
            if s.action_counter%s.tfreq==0 and s._wd:s._train()
            return sel

        except Exception as e:
            traceback.print_exc()
            a=random.choice(s.al);a.reasoning=f"err:{e}";return a


# --- Cell ---
import os
if os.getenv('KAGGLE_IS_COMPETITION_RERUN'):
    !curl --fail --retry 999 --retry-all-errors --retry-delay 5 --retry-max-time 600 http://gateway:8001/api/games
    !cp -r /kaggle/input/competitions/arc-prize-2026-arc-agi-3/ARC-AGI-3-Agents /kaggle/working/ARC-AGI-3-Agents
    !cp /kaggle/working/my_agent.py /kaggle/working/ARC-AGI-3-Agents/agents/templates/my_agent.py
    with open('/kaggle/working/ARC-AGI-3-Agents/agents/__init__.py','w') as f:
        f.write("""from typing import Type
from dotenv import load_dotenv
from .agent import Agent, Playback
from .swarm import Swarm
from .templates.random_agent import Random
from .templates.my_agent import MyAgent
load_dotenv()
AVAILABLE_AGENTS: dict[str, Type[Agent]] = {"random": Random, "myagent": MyAgent}
""")
    with open('/kaggle/working/ARC-AGI-3-Agents/.env','w') as f:
        f.write("""SCHEME=http
HOST=gateway
PORT=8001
ARC_API_KEY=test-key-123
ARC_BASE_URL=http://gateway:8001/
OPERATION_MODE=online
RECORDINGS_DIR=/kaggle/working/server_recording
""")
    !cd /kaggle/working/ARC-AGI-3-Agents && MPLBACKEND=agg python main.py --agent myagent

# --- Cell ---
import os
if not os.getenv('KAGGLE_IS_COMPETITION_RERUN'):
    import pandas as pd
    submission = pd.DataFrame(data=[['1_0','1',True,1]],columns=['row_id','game_id','end_of_game','score'])
    submission.to_parquet('/kaggle/working/submission.parquet',index=False)
