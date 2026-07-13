# segmentation.py

## Purpose
Implements board segmentation utilities for ARC-style grid analysis.

## Mental model
This file turns raw board grids into structured spatial information such as connected components, boundaries, adjacency, and containment relationships.

## Main responsibility
Think of it as the geometry/vision helper for the agent.

## Core concepts
- Grid analysis: identify shapes and regions
- Connectivity: detect connected components
- Relationships: adjacency, containment, boundaries
- Output: structured features the agent can reason about

## Important functions
- segment_grid(): produces segmentation data from a board
- find_components(): identifies connected regions
- compute adjacency/containment relationships

## Typical flow
1. Receive a board/grid
2. Analyze connected regions and boundaries
3. Produce structured segmentation features
4. Return them to the agent for reasoning

## Call chain
board/grid
↓
segmentation analysis
↓
structured spatial features
↓
agent reasoning

## What it is not
- It is not the game engine
- It is not the model policy
- It is not the UI layer

## One-line summary
This file is the spatial-analysis helper that converts raw boards into interpretable structure for the Duck.
