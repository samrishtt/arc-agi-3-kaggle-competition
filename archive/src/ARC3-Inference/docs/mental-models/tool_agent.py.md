# tool_agent.py

## Purpose
Implements the main LLM-driven Duck agent that uses tool calling to reason about ARC games.

## Mental model
This file is the “thinking brain” of the harness. It sends structured context to the model, accepts tool calls, and turns the model’s reasoning into game actions.

## Main responsibility
Think of it as the agent loop that interacts with the model and the Python tool sandbox.

## Core concepts
- Model-facing interface: chat/tool-calling messages
- Tool use: Python execution sandbox and game action calls
- State: history, prior frames, current frame, valid actions
- Output: model decisions, tool results, and final actions

## Important classes/functions
- ToolCallingAgent or equivalent agent implementation
- _build_messages(): prepares the prompt context
- _handle_tool_calls(): processes model-requested tools
- _run_python_tool(): executes the isolated Python tool
- _emit_action(): converts the model’s choice into a game action

## Typical flow
1. Build a structured prompt from the current game state
2. Send it to the model
3. Receive tool or action calls
4. Execute the tool or action
5. Feed the result back into the next reasoning step

## Call chain
Game state/context
↓
agent prompt
↓
model response
↓
tool/action handling
↓
next loop iteration

## What it is not
- It is not the TAAF benchmark runner
- It is not the environment simulator
- It is not the viewer

## One-line summary
This file is the model-driven decision engine that turns game observations into tool use and actions.
