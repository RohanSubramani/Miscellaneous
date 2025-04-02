import numpy as np
from typing import Tuple, Dict, List

class QLearningAgent:
    def __init__(self, learning_rate: float, discount_factor: float, epsilon: float, optimistic_value: float = 2.0):
        self.q_table = {}  # "row,col" -> action -> value
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.actions = ['up', 'down', 'left', 'right']
        self.optimistic_value = optimistic_value
        
    def _state_to_key(self, state: Tuple[int, int]) -> str:
        return f"{state[0]},{state[1]}"
    
    def _init_state(self, state_key: str):
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: self.optimistic_value for a in self.actions}
    
    def get_action(self, state: Tuple[int, int], training: bool = True) -> str:
        state_key = self._state_to_key(state)
        
        if training and np.random.random() < self.epsilon:
            return np.random.choice(self.actions)
        
        # Initialize Q-values if state not seen
        self._init_state(state_key)
            
        return max(self.q_table[state_key].items(), key=lambda x: x[1])[0]
    
    def update(self, state: Tuple[int, int], action: str, reward: float, next_state: Tuple[int, int], done: bool):
        state_key = self._state_to_key(state)
        next_state_key = self._state_to_key(next_state)
        
        self._init_state(state_key)
        self._init_state(next_state_key)
            
        next_value = 0 if done else max(self.q_table[next_state_key].values())
        current_value = self.q_table[state_key][action]
        
        # Q-learning update
        self.q_table[state_key][action] = current_value + self.lr * (reward + self.gamma * next_value - current_value)
    
    def get_q_table_visualization(self) -> Dict[str, Dict[str, float]]:
        """Returns the Q-table in a format suitable for visualization"""
        # Ensure all states are initialized
        for i in range(2):
            for j in range(2):
                self._init_state(f"{i},{j}")
        return self.q_table 