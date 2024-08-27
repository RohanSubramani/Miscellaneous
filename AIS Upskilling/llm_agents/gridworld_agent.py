from openai import OpenAI
import random
import time

client = OpenAI()

# basic llm function for getting a response
def get_response(message: str):
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}],
        stream=True,
    )
    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
    return response

# define the gridworld environment
class GridWorld:
    def __init__(self, size=5):
        self.size = size
        self.goal = [4, 4]  # set goal at bottom-right corner
        self.penalty = [3, 3]  # set penalty state somewhere in the grid
        self.agent_position = [0, 0]  # start at top-left corner
        self.utility = 0  # track utility

    def reset(self):
        self.agent_position = [0, 0]
        self.utility = 0

    def step(self, action):
        x, y = self.agent_position
        if action == "R" and y < self.size - 1:  # move right
            self.agent_position[1] += 1
        elif action == "L" and y > 0:  # move left
            self.agent_position[1] -= 1
        elif action == "U" and x > 0:  # move up
            self.agent_position[0] -= 1
        elif action == "D" and x < self.size - 1:  # move down
            self.agent_position[0] += 1

        # check for goal or penalty state
        if self.agent_position == self.goal:
            print("Reached the goal! +5 utility.")
            self.utility += 5
        elif self.agent_position == self.penalty:
            print("Hit penalty state! -10 utility.")
            self.utility -= 10

    def get_state(self):
        grid = [["_" for _ in range(self.size)] for _ in range(self.size)]
        x, y = self.agent_position
        grid[x][y] = "A"  # 'A' represents the agent
        gx, gy = self.goal
        grid[gx][gy] = "G"  # 'G' represents the goal
        px, py = self.penalty
        grid[px][py] = "P"  # 'P' represents the penalty
        return grid

    def render(self):
        state = self.get_state()
        for row in state:
            print(" ".join(row))
        print(f"Current utility: {self.utility}\n")

# llm agent class
class LLM_Agent:
    def __init__(self, env):
        self.env = env
        self.plan = None
        self.context = ("You are an agent in a gridworld environment. "
                        "Your goal is to reach the goal state (G) for +5 utility. "
                        "Avoid the penalty state (P) as it will reduce your utility by -10. "
                        "You can move using R (right), L (left), U (up), or D (down). "
                        "Please generate a plan to reach the goal while avoiding the penalty. "
                        "The goal is at [4,4] and the penalty is at [3,3].")

    def generate_plan(self):
        self.plan = get_response(self.context).strip()

    def brainstorm(self):
        # Brainstorming phase: generate a one-sentence brainstorm
        message = (f"{self.context} You have the following plan: {self.plan}\n"
                   f"Current position: {self.env.agent_position}\n"
                   "Based on this, brainstorm a one-sentence strategy to decide your next move.")
        brainstorm_response = get_response(message).strip()
        print(f"Brainstorm response: {brainstorm_response}")
        return brainstorm_response

    def decide_move(self):
        brainstorm_response = self.brainstorm()
        message = (f"You have the following plan: {self.plan}\n"
                   f"Current position: {self.env.agent_position}\n"
                   f"Your strategy given the plan and current position: {brainstorm_response}\n"
                   f"Based on this, output a single letter with your move (R, L, U, or D).")
        action = get_response(message).strip().upper()
        
        # Decide the move based on the brainstorm response
        # if "right" in brainstorm_response.lower():
        #     action = "R"
        # elif "left" in brainstorm_response.lower():
        #     action = "L"
        # elif "up" in brainstorm_response.lower():
        #     action = "U"
        # elif "down" in brainstorm_response.lower():
        #     action = "D"
        # else:
        #     action = random.choice(["R", "L", "U", "D"])  # fallback if no valid action found

        return action

# simulation loop
def run_simulation(steps=10):
    env = GridWorld(size=5)
    agent = LLM_Agent(env)

    # generate initial plan
    print("Generating plan...\n")
    agent.generate_plan()
    print(f"LLM's plan: {agent.plan}\n")

    for _ in range(steps):
        env.render()
        action = agent.decide_move()
        print(f"LLM action: {action}")
        env.step(action)
        time.sleep(1)

    env.render()
    print("Simulation complete.")

# run the simulation
if __name__ == "__main__":
    run_simulation(steps=10)