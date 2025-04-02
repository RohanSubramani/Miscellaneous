# Basic 2x2 Gridworld with Q-Learning

Written by Claude.

A simple 2x2 gridworld environment where an agent learns to navigate to a fixed goal while avoiding a fixed penalty state.

## Environment Specifications

- **Grid**: 2x2
- **States**: 4 total (coordinates from (0,0) to (1,1))
- **Actions**: Up, Down, Left, Right
- **Fixed States**:
  - Start: (0,0)
  - Goal: (1,1) [Reward: +1]
  - Penalty: (0,1) [Reward: -2]
  - Neutral: (1,0) [Reward: 0]

## Features

- Interactive web interface for manual control and agent training
- Real-time visualization of agent's position and state values
- Q-table visualization at different training stages:
  - Initial (optimistically initialized)
  - After 1/3 of episodes
  - After 2/3 of episodes
  - Final Q-table
- Configurable hyperparameters:
  - Number of episodes
  - Learning rate
  - Discount factor
  - Exploration rate (epsilon)
  - Optimistic initialization value

## Setup and Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python app.py
```

3. Access the interface at `http://localhost:5000`

## Technical Components

- **Backend**: Flask server (`app.py`)
- **Q-Learning Implementation**: Custom Q-learning agent (`q_learning.py`)
- **Frontend**: HTML/JavaScript interface with dynamic Q-table visualization

## Learning Task

The agent must learn to:
1. Avoid the penalty state (-2 reward)
2. Navigate to the goal state (+1 reward)
3. End the episode upon reaching either the goal or penalty state
4. Find the optimal path from any starting position

This represents a basic reinforcement learning scenario with:
- Clear reward structure
- Terminal states
- Need for both exploration and exploitation
- Simple but non-trivial optimal policy 