# python_tool_sandbox.py

## Purpose
Provides the isolated Python execution environment used by the Duck agent for reasoning and small code snippets.

## Mental model
This file is a sandbox. It lets the agent run short Python code safely within a constrained environment instead of directly manipulating the game state.

## Main responsibility
Think of it as a restricted REPL for the agent.

## Core concepts
- Isolation: code runs in a controlled sandbox
- Safety: only a small allowlist of Python features/modules is permitted
- Interface: the sandbox exposes a simple API for the agent to run code and capture a result
- Output: printed summaries, tool results, and action calls

## Important classes/functions
- PythonToolSandbox or equivalent sandbox implementation
- run_code(): executes the agent’s Python snippet
- enforce allowlist / safety rules
- capture result and stdout/stderr

## Typical flow
1. The agent submits a Python snippet
2. The sandbox validates and runs it
3. Output and errors are captured
4. The result is returned to the agent loop

## Call chain
agent request
↓
python sandbox
↓
restricted execution
↓
result back to agent

## What it is not
- It is not the full game engine
- It is not the model itself
- It is not a general-purpose Python runtime

## One-line summary
This file is the constrained Python execution environment that gives the agent a lightweight reasoning tool.
