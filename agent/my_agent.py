"""Your ARC-AGI-3 agent. This is the *only* file you should normally edit.

`scripts/build_notebook.py` splices the contents of this file into the
Kaggle submission notebook, so your local dev loop and your Kaggle
submission stay in lock-step:

    [edit my_agent.py] -> [make play-local] -> [make submit]

Contract (enforced by the ARC-AGI-3-Agents framework):
  - Subclass `agents.agent.Agent`.
  - Class must be named `MyAgent` (the notebook's __init__.py registers it).
  - Implement `is_done(frames, latest_frame) -> bool`.
  - Implement `choose_action(frames, latest_frame) -> GameAction`.
"""
from __future__ import annotations

import random
import time
from typing import Any

from arcengine import FrameData, GameAction, GameState

# When run inside the ARC-AGI-3-Agents framework (locally or on Kaggle)
# the `agents` package is on sys.path, so this import resolves.
from agents.agent import Agent


class MyAgent(Agent):
    """A heuristic explorer that avoids repeating ineffective actions."""

    # Upper bound on actions per game; the framework also enforces global limits.
    MAX_ACTIONS = 80

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Seed per game_id so replays from the same game are reproducible but
        # different games explore independently.
        seed = int(time.time() * 1_000_000) + hash(self.game_id) % 1_000_000
        random.seed(seed)
        
        # Track bad actions for a specific state representation
        self.bad_actions_for_state: dict[str, set[GameAction]] = {}
        # Track the last action we took
        self.last_action: GameAction | None = None
        # Track the last state we were in
        self.last_state_hash: str | None = None

    @property
    def name(self) -> str:
        return f"{super().name}.HeuristicExplorer"

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        # Stop once we win. Don't stop on GAME_OVER — we want to RESET and retry.
        return latest_frame.state is GameState.WIN

    def _hash_frame(self, frame_data: FrameData) -> str:
        """Create a simple hash/string representation of the grid."""
        if not frame_data.frame:
            return ""
        return str(frame_data.frame)

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        # First call or after a death -> reset the level.
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self.last_action = None
            self.last_state_hash = None
            return GameAction.RESET

        current_state_hash = self._hash_frame(latest_frame)

        # Update heuristics if we have a history
        if self.last_state_hash is not None and self.last_action is not None:
            if current_state_hash == self.last_state_hash:
                # The action did not change the state (e.g. walked into a wall)
                if self.last_state_hash not in self.bad_actions_for_state:
                    self.bad_actions_for_state[self.last_state_hash] = set()
                self.bad_actions_for_state[self.last_state_hash].add(self.last_action)

        # For our basic explorer, only use simple actions (non-coordinate based)
        candidate_actions = [a for a in GameAction if a is not GameAction.RESET and not a.is_complex()]
        
        # Filter out bad actions for the current state
        bad_actions = self.bad_actions_for_state.get(current_state_hash, set())
        valid_actions = [a for a in candidate_actions if a not in bad_actions]
        
        # If all simple actions are bad (we're stuck), just pick random again or try complex if implemented
        if not valid_actions:
            valid_actions = candidate_actions
            
        action = random.choice(valid_actions)
        
        self.last_action = action
        self.last_state_hash = current_state_hash

        action.reasoning = f"heuristic explorer chose: {action.value}"
        return action
