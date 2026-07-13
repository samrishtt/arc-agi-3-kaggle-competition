# solver.py

## Purpose
Implements the TAAF solver adapter for the Duck harness. It receives the game state, drives the agent loop, and handles action execution, transcripts, and run artifacts.

## Mental model
This file is the bridge between the benchmark runtime and the Duck agent. It turns game events into agent actions and records what happened.

## Main responsibility
Think of it as the runtime coordinator for one solver instance.

## Core concepts
- Input: game state, valid actions, history, and tool context
- Decision layer: the agent decides what action to take
- Execution layer: action dispatch and runtime bookkeeping
- Output: events, transcripts, score-related artifacts, and local-server orchestration

## Important classes/functions
- HarnessSolver: main solver class
- _make_message(): builds the prompt payload for the model
- _run_agent_loop(): executes the agent turn-by-turn
- action(): executes a game action
- _start_local_server(): optionally launches a local vLLM server

## Typical flow
1. Receive game state from TAAF
2. Build the prompt/context for the model
3. Let the agent reason and call tools
4. Execute one or more actions
5. Record events and transcript data
6. Return control to TAAF

## Call chain
TAAF game loop
↓
HarnessSolver
↓
agent/tool-calling logic
↓
action()
↓
game environment

## What it is not
- It is not the core game environment
- It is not the raw model implementation
- It is not the viewer UI

## One-line summary
This file is the runtime adapter that connects the Duck agent to the TAAF game loop.
