import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
from tqdm import tqdm
import os


def initialize_environment(render_mode=None):
    """Create and initialize the FrozenLake environment"""
    return gym.make('FrozenLake-v1', render_mode=render_mode)


def initialize_q_table(env):
    """Initialize Q-table with zeros"""
    return np.ones([env.observation_space.n, env.action_space.n]) * 0.05


def visualize_q_table(q_table, title="Q-table Visualization"):
    """Visualize the Q-table as a grid with directional arrows"""
    # For FrozenLake, we assume a 4x4 grid (16 states)
    grid_size = int(np.sqrt(q_table.shape[0]))
    
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
    for state in range(q_table.shape[0]):
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
        q_values = q_table[state]
        
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
            
            # Add Q-value text near the arrow
            text_x = props['dx'] * 0.6
            text_y = props['dy'] * 0.6
            ax.text(text_x, text_y, f"{q_values[action]:.1f}", 
                   ha='center', va='center', fontsize=8,
                   bbox=dict(facecolor='white', alpha=0.5, boxstyle='round,pad=0.1'))
    
    # Add a legend explaining the colors
    legend_elements = [
        plt.Line2D([0], [0], color=cmap(0), lw=4, label='Least likely'),
        plt.Line2D([0], [0], color=cmap(0.5), lw=4, label='Medium likelihood'),
        plt.Line2D([0], [0], color=cmap(1.0), lw=4, label='Most likely')
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=12)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Create plots directory if it doesn't exist
    os.makedirs('plots', exist_ok=True)
    
    # Save the figure
    plt.savefig(f'plots/{title.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
    plt.close()


def test_policy(q_table, num_episodes=100, render=False):
    """Test the learned policy over multiple episodes"""
    successes = 0
    total_rewards = 0
    test_env = initialize_environment('human' if render else None)
    
    for i in range(num_episodes):
        state, _ = test_env.reset()
        done = False
        episode_reward = 0
        steps = 0
        
        while not done and steps < 100:  # Limit steps to avoid infinite loops
            # Always choose the best action - no exploration during testing
            action = np.argmax(q_table[state])
            
            state, reward, terminated, truncated, _ = test_env.step(action)
            done = terminated or truncated
            episode_reward += reward
            steps += 1
            
            if render and i % 100 == 0:  # Only render every 100th episode
                time.sleep(0.1)  # Slow down rendering for visibility
        
        total_rewards += episode_reward
        if episode_reward > 0:
            successes += 1
    
    test_env.close()
    return successes / num_episodes, total_rewards / num_episodes


def train_agent(env, q_table, episodes=2000, initial_alpha=0.5, min_alpha=0.1, alpha_decay=0.995, gamma=0.99, epsilon=0.1, progress_bar=None):
    """Train the agent using Q-learning with learning rate annealing"""
    # Metrics for visualization
    rewards_per_episode = []
    success_rate = []
    episode_lengths = []
    alpha_values = []
    
    # Current learning rate
    alpha = initial_alpha
    
    # Training loop
    for episode in range(episodes):
        state, _ = env.reset()
        done = False
        total_reward = 0
        steps = 0
        
        while not done:
            # Epsilon-greedy action selection
            if np.random.random() < epsilon:
                action = env.action_space.sample()  # Explore
            else:
                action = np.argmax(q_table[state])  # Exploit
            
            # Take action and observe outcome
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            total_reward += reward
            steps += 1
            
            # Q-learning update with current alpha
            old_value = q_table[state, action]
            next_max = np.max(q_table[next_state])
            new_value = (1 - alpha) * old_value + alpha * (reward + gamma * next_max)
            q_table[state, action] = new_value
            
            state = next_state
        
        # Record metrics
        rewards_per_episode.append(total_reward)
        episode_lengths.append(steps)
        alpha_values.append(alpha)
        
        # Calculate success rate over last 100 episodes
        if episode >= 100:
            success_rate.append(sum(rewards_per_episode[-100:]) / 100)
        else:
            success_rate.append(sum(rewards_per_episode) / (episode + 1))
        
        # Anneal the learning rate
        alpha = max(min_alpha, alpha * alpha_decay)
        
        # Update progress bar if provided
        if progress_bar is not None:
            progress_bar.update(1)
            if episode % 100 == 0:
                progress_bar.set_postfix({
                    'success_rate': f"{success_rate[-1]:.2f}", 
                    'avg_steps': f"{np.mean(episode_lengths[-100:]):.2f}",
                    'alpha': f"{alpha:.4f}"
                })
        elif episode % 100 == 0:
            print(f"Episode: {episode}, Success rate: {success_rate[-1]:.2f}, Avg steps: {np.mean(episode_lengths[-100:]):.2f}, Alpha: {alpha:.4f}")
    
    return q_table, rewards_per_episode, success_rate, episode_lengths, alpha_values


def visualize_training_results(success_rate, episode_lengths, alpha_values=None):
    """Visualize the training progress"""
    if alpha_values:
        plt.figure(figsize=(15, 5))
        num_plots = 3
    else:
        plt.figure(figsize=(12, 5))
        num_plots = 2
    
    plt.subplot(1, num_plots, 1)
    plt.plot(success_rate)
    plt.title('Success Rate over Episodes')
    plt.xlabel('Episode')
    plt.ylabel('Success Rate')

    plt.subplot(1, num_plots, 2)
    plt.plot(episode_lengths)
    plt.title('Episode Length over Time')
    plt.xlabel('Episode')
    plt.ylabel('Steps')
    
    if alpha_values:
        plt.subplot(1, num_plots, 3)
        plt.plot(alpha_values)
        plt.title('Learning Rate Annealing')
        plt.xlabel('Episode')
        plt.ylabel('Alpha (Learning Rate)')
    
    plt.tight_layout()
    
    # Create plots directory if it doesn't exist
    os.makedirs('plots', exist_ok=True)
    
    # Save the figure instead of showing it
    plt.savefig('plots/training_results.png')
    plt.close()


def play_game_interactively():
    """Allow the user to play the FrozenLake game interactively"""
    env = initialize_environment(render_mode='human')
    state, _ = env.reset()
    done = False
    total_reward = 0
    steps = 0
    
    print("\nWelcome to FrozenLake!")
    print("Controls: a = left, s = down, d = right, w = up, q = quit")
    print("Goal: Navigate from the starting point (S) to the goal (G) without falling into holes (H)")
    
    # Action mapping
    action_map = {
        'a': 0,  # left
        's': 1,  # down
        'd': 2,  # right
        'w': 3   # up
    }
    
    action_names = {
        0: "LEFT",
        1: "DOWN",
        2: "RIGHT",
        3: "UP"
    }
    
    while not done:
        # Display current state
        env.render()
        print(f"Current state: {state}, Steps: {steps}, Reward: {total_reward}")
        
        # Get user input
        valid_input = False
        while not valid_input:
            user_input = input("Enter action (a/s/d/w) or q to quit: ").lower()
            
            if user_input == 'q':
                print("Quitting game...")
                env.close()
                return
            
            if user_input in action_map:
                action = action_map[user_input]
                valid_input = True
            else:
                print("Invalid input. Use a/s/d/w for movement or q to quit.")
        
        # Display the action being taken
        print(f"\n>>> Moving {action_names[action]} <<<\n")
        
        # Take action
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        total_reward += reward
        steps += 1
        
        # Update state
        state = next_state
        
        # Display result of action
        if reward > 0:
            print("🎉 Success! You reached the goal!")
        elif done:
            print("❌ Oh no! You fell into a hole!")
        else:
            print("✓ Moved successfully to a new position.")
    
    # Game over
    env.render()
    print(f"\nGame over! Total steps: {steps}, Total reward: {total_reward}")
    
    if total_reward > 0:
        print("Congratulations! You won! 🏆")
    else:
        print("Better luck next time! 🍀")
    
    env.close()
    input("Press Enter to continue...")

def main():
    # Hyperparameters
    initial_alpha = 0.8  # Initial learning rate
    min_alpha = 0.1      # Minimum learning rate
    alpha_decay = 0.9995 # Learning rate decay factor
    gamma = 0.95         # Discount factor
    epsilon = 0.1        # Exploration rate
    # Default episode count
    default_episodes = 100000
    
    # Menu for user to choose what to do
    while True:
        print("\n===== FrozenLake RL Agent =====")
        print("1. Train a new agent")
        print("2. Play the game yourself")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            # Get episode count from user
            episodes_input = input(f"Enter number of training episodes (default: {default_episodes}): ")
            try:
                episodes = int(episodes_input) if episodes_input.strip() else default_episodes
                if episodes <= 0:
                    print(f"Invalid episode count. Using default: {default_episodes}")
                    episodes = default_episodes
            except ValueError:
                print(f"Invalid input. Using default: {default_episodes}")
                episodes = default_episodes
            
            # Initialize environment and Q-table
            env = initialize_environment(None)  # No rendering during training
            q_table = initialize_q_table(env)
            
            # Train the agent
            print(f"Starting training with {episodes} episodes...")
            
            # Create progress bar
            progress_bar = tqdm(total=episodes, desc="Training", unit="episode")
            
            q_table, rewards, success_rate, episode_lengths, alpha_values = train_agent(
                env, q_table, episodes, initial_alpha, min_alpha, alpha_decay, gamma, epsilon, progress_bar=progress_bar
            )
            
            progress_bar.close()
            print("Training finished!")
            
            # Visualize training progress
            visualize_training_results(success_rate, episode_lengths, alpha_values)
            
            # Visualize final Q-table
            visualize_q_table(q_table, "Final Q-table after Training")
            
            # Create a new environment with rendering to show the agent's policy
            render_env = initialize_environment(render_mode="human")
            print("\nDemonstrating trained agent policy...")
            
            # Test the trained policy and show a demonstration
            print("Testing policy performance...")
            success_rate, avg_reward = test_policy(q_table, num_episodes=100, render=True)
            print(f"Policy success rate: {success_rate:.2%}")
            print(f"Average reward: {avg_reward:.2f}")
            
            # # Run a visual demonstration with the trained policy
            # print("\nShowing visual demonstration of the trained policy...")
            # demo_success_rate, demo_avg_reward = test_policy(q_table, num_episodes=3, render=True)
            # print(f"Demonstration finished with success rate: {demo_success_rate:.2%}")
            
        elif choice == '2':
            # Play the game interactively
            play_game_interactively()
            
        elif choice == '3':
            print("Exiting program. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")


if __name__ == "__main__":
    main()
