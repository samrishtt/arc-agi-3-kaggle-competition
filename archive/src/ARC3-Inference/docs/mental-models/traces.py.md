# traces.py

## Purpose
Exports machine-readable traces of agent behavior for analysis and debugging.

## Mental model
This file is the trace export layer. It captures the duck’s reasoning, tool calls, actions, and score transitions in a structured format.

## Main responsibility
Think of it as the debugging and audit trail system for runs.

## Core concepts
- Input: run artifacts and transcript data
- Output: structured trace JSON in a chat/message-oriented format
- Use cases: inspection, replay, and downstream analysis

## Important functions
- export_traces(): gathers and writes the trace data
- format_messages(): converts run events into message entries
- attach_scores_and_transitions(): enriches the trace with game progress data

## Typical flow
1. Load run artifacts
2. Extract transcript and event data
3. Convert it into message-style trace entries
4. Write the exported trace file

## Call chain
run artifacts
↓
trace extraction
↓
structured trace export

## What it is not
- It is not the runtime solver
- It is not the evaluator
- It is not the viewer

## One-line summary
This file turns run history into structured traces for inspection and analysis.
