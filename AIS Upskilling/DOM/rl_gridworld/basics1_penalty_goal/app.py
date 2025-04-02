from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from q_learning import QLearningAgent
import copy

app = Flask(__name__)
CORS(app)

# Grid configuration
GRID_SIZE = 2
START_STATE = (0, 0)
GOAL_STATE = (1, 1)
PENALTY_STATE = (0, 1)
NEUTRAL_STATE = (1, 0)

# State and reward definitions
rewards = {
    (0, 0): 0,     # Start state
    (0, 1): -2,    # Penalty state
    (1, 0): 0,     # Neutral state
    (1, 1): 1      # Goal state
}

current_state = START_STATE
agent = None

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
    reward = rewards[next_state]
    done = next_state == GOAL_STATE
    
    return next_state, reward, done

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/reset', methods=['POST'])
def reset():
    global current_state
    current_state = START_STATE
    return jsonify({
        'state': current_state,
        'reward': rewards[current_state],
        'done': current_state == GOAL_STATE
    })

@app.route('/step/<action>')
def step(action):
    global current_state
    next_state, reward, done = step_env(current_state, action)
    current_state = next_state
    
    return jsonify({
        'state': current_state,
        'reward': reward,
        'done': done
    })

@app.route('/train', methods=['POST'])
def train():
    global agent
    
    # Get training parameters from request
    params = request.json
    num_episodes = params['num_episodes']
    learning_rate = params['learning_rate']
    discount_factor = params['discount_factor']
    epsilon = params['epsilon']
    
    # Initialize agent
    agent = QLearningAgent(learning_rate, discount_factor, epsilon)
    
    # Get initial Q-table
    q_tables = {
        'initial': copy.deepcopy(agent.get_q_table_visualization()),
        'one_third': None,
        'two_thirds': None,
        'final': None
    }
    
    # Training loop
    episode_rewards = []
    one_third = num_episodes // 3
    two_thirds = 2 * num_episodes // 3
    
    for episode in range(num_episodes):
        state = START_STATE
        total_reward = 0
        done = False
        
        while not done:
            action = agent.get_action(state, training=True)
            next_state, reward, done = step_env(state, action)
            agent.update(state, action, reward, next_state, done)
            
            state = next_state
            total_reward += reward
            
        episode_rewards.append(total_reward)
        
        # Capture Q-tables at different stages
        if episode + 1 == one_third:
            q_tables['one_third'] = copy.deepcopy(agent.get_q_table_visualization())
        elif episode + 1 == two_thirds:
            q_tables['two_thirds'] = copy.deepcopy(agent.get_q_table_visualization())
    
    # Get final Q-table
    q_tables['final'] = agent.get_q_table_visualization()
    
    # Return training results and Q-tables
    return jsonify({
        'episode_rewards': episode_rewards,
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