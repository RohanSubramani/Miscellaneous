from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from q_learning import QLearningAgent
import copy

app = Flask(__name__)
CORS(app)

# Grid configuration
GRID_SIZE = 2
START_STATE = (0, 0)

# We'll alternate between two configurations
CONFIG_1 = {
    'GOAL_STATE': (1, 1),
    'PENALTY_STATE': (0, 1),
    'NEUTRAL_STATES': [(1, 0)]
}

CONFIG_2 = {
    'GOAL_STATE': (0, 0),
    'PENALTY_STATE': (1, 0),
    'NEUTRAL_STATES': [(1, 0)]
}

current_config = CONFIG_1
current_state = START_STATE
agent = None

def get_current_rewards():
    """Get rewards based on current configuration"""
    rewards = {
        (0, 0): 0,
        (0, 1): 0,
        (1, 0): 0,
        (1, 1): 0
    }
    rewards[current_config['GOAL_STATE']] = 1
    rewards[current_config['PENALTY_STATE']] = -2
    return rewards

def rotate_configuration():
    """Switch between configurations"""
    global current_config
    current_config = CONFIG_2 if current_config == CONFIG_1 else CONFIG_1

def step_env(state, action):
    x, y = state
    
    # Handle movements
    if action == 'up' and x > 0:
        x -= 1
    elif action == 'down' and x < GRID_SIZE - 1:
        x += 1
    elif action == 'left' and y > 0:
        y -= 1
    elif action == 'right' and y < GRID_SIZE - 1:
        y += 1
    
    next_state = (x, y)
    rewards = get_current_rewards()
    reward = rewards[next_state]
    
    # Check if goal reached
    goal_reached = next_state == current_config['GOAL_STATE']
    if goal_reached:
        rotate_configuration()
    
    return next_state, reward, goal_reached

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/reset', methods=['POST'])
def reset():
    global current_state, current_config
    current_state = START_STATE
    current_config = CONFIG_1
    rewards = get_current_rewards()
    return jsonify({
        'state': current_state,
        'reward': rewards[current_state],
        'goal_state': current_config['GOAL_STATE'],
        'penalty_state': current_config['PENALTY_STATE']
    })

@app.route('/step/<action>')
def step(action):
    global current_state
    next_state, reward, goal_reached = step_env(current_state, action)
    current_state = next_state
    
    return jsonify({
        'state': current_state,
        'reward': reward,
        'goal_reached': goal_reached,
        'goal_state': current_config['GOAL_STATE'],
        'penalty_state': current_config['PENALTY_STATE']
    })

@app.route('/train', methods=['POST'])
def train():
    global agent, current_config
    
    # Get training parameters from request
    params = request.json
    num_steps = params['num_episodes']  # Reusing the parameter but treating it as steps
    learning_rate = params['learning_rate']
    discount_factor = params['discount_factor']
    epsilon = params['epsilon']
    optimistic_value = params['optimistic_value']
    
    # Initialize agent
    agent = QLearningAgent(learning_rate, discount_factor, epsilon, optimistic_value)
    current_config = CONFIG_1  # Reset to initial configuration
    
    # Get initial Q-table
    q_tables = {
        'initial': copy.deepcopy(agent.get_q_table_visualization()),
        'one_third': None,
        'two_thirds': None,
        'final': None
    }
    
    # Training loop - single continuous trajectory
    rewards = []
    state = START_STATE
    total_reward = 0
    one_third = num_steps // 3
    two_thirds = 2 * num_steps // 3
    
    for step in range(num_steps):
        action = agent.get_action(state, training=True)
        next_state, reward, goal_reached = step_env(state, action)
        agent.update(state, action, reward, next_state, False)  # Never done, just continuing
        
        state = next_state
        total_reward += reward
        rewards.append(reward)
        
        # Capture Q-tables at different stages
        if step + 1 == one_third:
            q_tables['one_third'] = copy.deepcopy(agent.get_q_table_visualization())
        elif step + 1 == two_thirds:
            q_tables['two_thirds'] = copy.deepcopy(agent.get_q_table_visualization())
    
    # Get final Q-table
    q_tables['final'] = agent.get_q_table_visualization()
    
    # Return training results and Q-tables
    return jsonify({
        'rewards': rewards,
        'q_tables': q_tables
    })

@app.route('/get_q_table')
def get_q_table():
    global agent
    if agent is None:
        return jsonify({'error': 'Agent not trained yet'})
    return jsonify(agent.get_q_table_visualization())

if __name__ == '__main__':
    app.run(debug=True) 