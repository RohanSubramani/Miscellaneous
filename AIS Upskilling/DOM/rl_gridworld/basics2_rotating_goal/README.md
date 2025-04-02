# 2x2 Gridworld with Rotating Goal and Q-Learning

Note: Most of this readme is written by Claude, except this discalimer and a bit at the bottom.

A 2x2 gridworld environment featuring a Q-learning agent that learns to navigate in a dynamic environment where goal and penalty states rotate upon reaching the goal.

## Environment Specifications

- **Grid**: 2x2
- **States**: 4 total (coordinates from (0,0) to (1,1))
- **Actions**: Up, Down, Left, Right
- **Dynamic States**:
  - Start: (0,0)
  - Goal: Rotates between states [Reward: +1]
  - Penalty: Rotates with goal [Reward: -2]
  - Neutral: Remaining states [Reward: 0]

## Features

- Interactive web interface for manual control and agent training
- Real-time visualization of agent's position and state values
- Q-table visualization at different training stages:
  - Initial (optimistically initialized)
  - After 1/3 of steps
  - After 2/3 of steps
  - Final Q-table
- Action count tracking for each state
- Configurable hyperparameters:
  - Number of steps
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
  - 2x2 grid layout for Q-tables
  - Action counts displayed for each state-action pair
  - Color-coded best actions
  - Arrow indicators for actions

## Learning Task

The agent must learn to:
1. Navigate to the current goal state (+1 reward)
2. Avoid the current penalty state (-2 reward)
3. Adapt to rotating goal and penalty states
4. Find optimal paths as the environment changes

This represents an advanced reinforcement learning scenario with:
- Dynamic reward structure
- Non-stationary environment
- Continuous learning requirement
- Need for policy adaptation
- Balance between exploration and exploitation

## Rohan's notes

Here are a few interesting things that can be seen in this setup:

1. When you train with Discount Factor 0.8, the Q-values for the best actions should converge to 2.77777777 for the actions that move directly to a goal state and 2.22222222 for the actions that move towards a goal state and not into a penalty state (2.7777 = 1/(1-(0.8)^2), which is the relevant geometric series for this infinite trajectory, and 2.2222 = 0.8*2.7777).
2. If epsilon (the exploration probability) is too high, then these q-values decrease a little bit. This makes sense because it makes it more likely for poor actions to be taken by random chance, so training won't reveal the q-values that emerge from optimal play.
3. If initial q-values are negative and epsilon is set to zero, no learning happens. This is because the agent likely tries a suboptimal strategy that is better than the initialization before it tries the optimal strategy, and then sticks with that suboptimal strategy.
