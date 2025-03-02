import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import torch
from dqn_agent import DQNAgent
from tqdm import tqdm
import seaborn as sns
import os
import time

def plot_training_results(rewards, losses, success_rates, window_size=100):
    """Plot training metrics"""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    
    # Plot rewards
    ax1.plot(np.convolve(rewards, np.ones(window_size)/window_size, mode='valid'))
    ax1.set_title(f'Average Reward over {window_size} Episodes')
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Reward')
    
    # Plot losses
    ax2.plot(np.convolve(losses, np.ones(window_size)/window_size, mode='valid'))
    ax2.set_title(f'Average Loss over {window_size} Episodes')
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Loss')
    
    # Plot success rate
    ax3.plot(success_rates)
    ax3.set_title('Success Rate')
    ax3.set_xlabel('Episode (per 100)')
    ax3.set_ylabel('Success Rate')
    
    plt.tight_layout()
    
    # Create plots directory if it doesn't exist
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/dqn_training_results.png')
    plt.close()

def visualize_policy(agent, env):
    """Visualize the learned policy"""
    policy = np.zeros((env.observation_space.n, env.action_space.n))
    
    for state in range(env.observation_space.n):
        state_tensor = torch.FloatTensor(agent.process_state(state)).unsqueeze(0)
        with torch.no_grad():
            q_values = agent.policy_net(state_tensor)
            policy[state] = q_values.numpy()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(policy, annot=True, fmt='.2f', cmap='YlGnBu')
    plt.title('Q-values for each state-action pair')
    plt.xlabel('Actions')
    plt.ylabel('States')
    
    # Create plots directory if it doesn't exist
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/dqn_policy_heatmap.png')
    plt.close()

def evaluate_agent(agent, env, num_episodes=100):
    """Evaluate the agent's performance"""
    total_rewards = []
    successes = 0
    
    for _ in range(num_episodes):
        state, _ = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action = agent.choose_action(state, training=False)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            total_reward += reward
            state = next_state
        
        total_rewards.append(total_reward)
        if total_reward > 0:
            successes += 1
    
    return np.mean(total_rewards), successes / num_episodes

def visualize_q_table(agent, env, title="DQN Q-values Visualization"):
    """Visualize the Q-values as a grid with directional arrows"""
    # For FrozenLake, we assume a 4x4 grid (16 states)
    grid_size = int(np.sqrt(env.observation_space.n))
    
    # Create a figure with a grid of subplots (one for each state)
    fig, axes = plt.subplots(grid_size, grid_size, figsize=(12, 12))
    fig.suptitle(title, fontsize=16)
    
    # Action mapping: 0=left, 1=down, 2=right, 3=up
    # Define arrow properties for each action
    actions = {
        0: {'dx': -0.4, 'dy': 0, 'head_width': 0.1, 'head_length': 0.1, 'label': 'Left'},
        1: {'dx': 0, 'dy': -0.4, 'head_width': 0.1, 'head_length': 0.1, 'label': 'Down'},
        2: {'dx': 0.4, 'dy': 0, 'head_width': 0.1, 'head_length': 0.1, 'label': 'Right'},
        3: {'dx': 0, 'dy': 0.4, 'head_width': 0.1, 'head_length': 0.1, 'label': 'Up'}
    }
    
    # Create a colormap for the arrows (red to green)
    cmap = plt.cm.RdYlGn
    
    # Plot each state
    for state in range(env.observation_space.n):
        row = state // grid_size
        col = state % grid_size
        ax = axes[row, col]
        
        # Set up the subplot
        ax.set_xlim(-0.5, 0.5)
        ax.set_ylim(-0.5, 0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.text(0, 0, f"S{state}", ha='center', va='center', fontsize=12)
        
        # Get Q-values for this state
        state_tensor = torch.FloatTensor(agent.process_state(state)).unsqueeze(0)
        with torch.no_grad():
            q_values = agent.policy_net(state_tensor).numpy()[0]
        
        # Normalize Q-values for this state to determine arrow colors
        if np.max(q_values) != np.min(q_values):
            normalized_q = (q_values - np.min(q_values)) / (np.max(q_values) - np.min(q_values))
        else:
            normalized_q = np.ones_like(q_values) * 0.5
        
        # Draw arrows for each action
        for action, props in actions.items():
            # Arrow color based on normalized Q-value (red=low, green=high)
            color = cmap(normalized_q[action])
            
            # Arrow thickness based on how likely the action is to be chosen
            width = 0.01 + 0.04 * normalized_q[action]
            
            # Draw the arrow
            ax.arrow(0, 0, props['dx'], props['dy'], 
                    head_width=props['head_width'], 
                    head_length=props['head_length'],
                    fc=color, ec=color, 
                    width=width,
                    length_includes_head=True,
                    alpha=0.7)
    
    # Create plots directory if it doesn't exist
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/dqn_q_values_visualization.png')
    plt.close()

def main():
    # Environment setup
    env = gym.make('FrozenLake-v1')
    state_size = env.observation_space.n
    action_size = env.action_space.n
    
    # Initialize agent
    agent = DQNAgent(
        state_size=state_size,
        action_size=action_size,
        hidden_size=64,
        learning_rate=0.001,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.995,
        memory_size=10000,
        batch_size=64,
        target_update=10
    )
    
    # Training parameters
    num_episodes = 500
    max_steps = 100
    
    # Metrics
    rewards_history = []
    losses_history = []
    success_rates = []
    success_window = deque(maxlen=100)
    
    # Training loop
    progress_bar = tqdm(range(num_episodes), desc='Training')
    for episode in progress_bar:
        state, _ = env.reset()
        total_reward = 0
        loss = 0
        
        for step in range(max_steps):
            # Choose and take action
            action = agent.choose_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            
            # Store experience and train
            agent.remember(state, action, reward, next_state, done)
            loss = agent.train()
            
            total_reward += reward
            state = next_state
            
            if done:
                break
        
        # Record metrics
        rewards_history.append(total_reward)
        losses_history.append(loss)
        success_window.append(total_reward > 0)
        
        if episode % 100 == 0:
            success_rate = sum(success_window) / len(success_window)
            success_rates.append(success_rate)
            progress_bar.set_postfix({
                'epsilon': f'{agent.epsilon:.2f}',
                'success_rate': f'{success_rate:.2f}'
            })
    
    # Plot training results
    plot_training_results(rewards_history, losses_history, success_rates)
    
    # Visualize final policy
    visualize_policy(agent, env)
    
    # Visualize Q-values with directional arrows
    visualize_q_table(agent, env)
    
    # Evaluate agent
    print("\nEvaluating agent...")
    mean_reward, success_rate = evaluate_agent(agent, env)
    print(f"Mean reward: {mean_reward:.2f}")
    print(f"Success rate: {success_rate:.2f}")
    
    # Save the trained agent
    agent.save('frozen_lake_dqn.pth')
    
    # Demo with rendering
    print("\nDemonstrating learned policy...")
    demo_agent(agent, num_demos=10)
    
    env.close()

def demo_agent(agent, num_demos=1):
    """
    Demonstrate the agent's learned policy multiple times
    
    Args:
        agent: The trained DQN agent
        num_demos: Number of demonstrations to run
    """
    env_render = gym.make('FrozenLake-v1', render_mode='human')
    
    for i in range(num_demos):
        print(f"\nDemo run {i+1}/{num_demos}")
        state, _ = env_render.reset()
        done = False
        total_reward = 0
        
        while not done:
            action = agent.choose_action(state, training=False)
            state, reward, terminated, truncated, _ = env_render.step(action)
            total_reward += reward
            done = terminated or truncated
        
        print(f"Demo {i+1} result: {'Success' if total_reward > 0 else 'Failure'}")
        time.sleep(1)  # Pause between demonstrations
    
    env_render.close()

if __name__ == "__main__":
    main() 