from openai import OpenAI
import random
import time

client = OpenAI()

# basic llm function for getting a response
def get_response(message: str):
    stream = client.chat.completions.create(
        model="gpt-4o", # "gpt-4o-mini",
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
        self.penalties = [[0, 3],[2,3],[3,3],[4,3]]  # set penalty state somewhere in the grid
        self.agent_position = [0, 0]  # start at top-left corner
        self.utility = 0  # track utility
        self.last_utility = 0

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
            self.last_utility = 5
        elif self.agent_position in self.penalties:
            print("Hit penalty state! -10 utility.")
            self.utility -= 10
            self.last_utility = -10
        else:
            self.last_utility = 0

    def get_state(self):
        grid = [["_" for _ in range(self.size)] for _ in range(self.size)]
        x, y = self.agent_position
        grid[x][y] = "A"  # 'A' represents the agent
        gx, gy = self.goal
        grid[gx][gy] = "B"  # 'B' represents the bonus
        for px,py in self.penalties:
            grid[px][py] = "P"  # 'P' represents the penalty
        return grid

    def render(self):
        state = self.get_state()
        for row in state:
            print(" ".join(row))
        print(f"Current utility: {self.utility}\n")

# llm agent class
class LLM_Agent:
    def __init__(self, env, recursion_limit=3):
        self.env = env
        self.plan = None
        self.recursion_limit = recursion_limit
        self.action = "No moves yet"
        self.history = []  # track history of brainstorms and critiques
        self.context = ("You are an agent in a gridworld environment. You are an expert at navigating every gridworld challenge and trick that can be thrown at you."
                        "Your goal is to efficiently maximize utility. Reaching the bonus state (B) gives +5 utility. "
                        "The penalty states (P) will reduce your utility by 10. "
                        "You can move exactly one space using R (right), L (left), U (up), or D (down). "
                        "The following shows the effect of each action. R: [0,1], L: [0,-1], U: [-1,0], D: [1,0]."
                       f"The goal is at {env.goal} and the penalties are at {env.penalties}.")

    def generate_plan(self):
        self.plan = get_response(self.context + " Please generate a maximally efficient plan to maximize utility.").strip()

    def brainstorm(self):
        # Brainstorming phase: generate a one-sentence brainstorm
        history_text = "\n".join([f"Brainstorm {i+1}: {entry['brainstorm']}, Critique: {entry['critique']}"
                                  for i, entry in enumerate(self.history)])
        message = (f"{self.context}\n" #  You have the following plan: {self.plan}
                   f"Overall utility so far: {self.env.utility}\n"
                   f"Last move: {self.action}\n"
                   f"Current position: {self.env.agent_position}\n"
                   f"Last utility: {self.env.last_utility}\n"
                   f"Here is the (possibly empty) history of your previous brainstorms and critiques for the current move:\n{history_text}\n"
                   "Based on this, state your assessment of the last move in one sentence and then state what move you think you should take next and why in one sentence.")
                   # Probably assessment of last move and brainstorming should be separate, and assessment shouldn't be repeated recursively
        brainstorm_response = get_response(message).strip()
        print(f"Brainstorm response: {brainstorm_response}")
        return brainstorm_response

    def critique(self, brainstorm_response):
        # Critique phase: critique the brainstorm response and decide whether to execute or retry
        history_text = "\n".join([f"Brainstorm {i+1}: {entry['brainstorm']}, Critique: {entry['critique']}"
                                  for i, entry in enumerate(self.history)])
        critique_message = (f"{self.context}\n"
                            f"Current position: {self.env.agent_position}\n"
                            f"Here is the (possibly empty) history of your previous brainstorms and critiques for the current move:\n{history_text}\n"
                            f"Current brainstorm: {brainstorm_response}\n"
                            "Critique the current brainstorm for only the first upcoming action. As the last word of your critique, "
                            "output either 'Execute' if the strategy seems fine, or 'Retry' if you "
                            "think you should brainstorm again. Don't add punctuation at the end.")
        critique_response = get_response(critique_message).strip()
        print(f"Critique response: {critique_response}")
        return critique_response.split()[-1], critique_response  # return last word and full critique

    def decide_move(self, depth=0):
        if depth >= self.recursion_limit:
            print("Recursion limit reached. Executing no move.")
            return "" # As an action  # if recursion limit is reached, execute the last suggested move

        brainstorm_response = self.brainstorm()
        
        # Critique the brainstorm response
        critique_result, full_critique = self.critique(brainstorm_response)

        # Add to history
        self.history.append({"brainstorm": brainstorm_response, "critique": full_critique})

        if critique_result == "Execute":
            # Ask for the next move based on the accepted brainstorm response
            move_message = (f"{self.context} You have the following plan: {self.plan}\n"
                            f"Current position: {self.env.agent_position}\n"
                            f"Your strategy given the plan and current position: {brainstorm_response}\n"
                            "Based on this, output a single letter with your move (R, L, U, or D). Output NOTHING else.")
            self.action = get_response(move_message).strip().upper()
            self.history = []
            return self.action
        elif critique_result == "Retry":
            print("Move was critiqued as flawed. Brainstorming again...")
            return self.decide_move(depth + 1)
        else:
            print("Unexpected critique result. Executing no move.")
            return ""  # fallback non-action

    # def decide_move(self):
    #     brainstorm_response = self.brainstorm()
    #     message = (f"{self.context} You have the following plan: {self.plan}\n"
    #                f"Current position: {self.env.agent_position}\n"
    #                f"Your strategy given the plan and current position: {brainstorm_response}\n"
    #                f"Based on this, output a single letter with your move (R, L, U, or D). Output NOTHING else.")
    #     self.action = get_response(message).strip().upper()
        
    #     # Decide the move based on the brainstorm response
    #     # if "right" in brainstorm_response.lower():
    #     #     action = "R"
    #     # elif "left" in brainstorm_response.lower():
    #     #     action = "L"
    #     # elif "up" in brainstorm_response.lower():
    #     #     action = "U"
    #     # elif "down" in brainstorm_response.lower():
    #     #     action = "D"
    #     # else:
    #     #     action = random.choice(["R", "L", "U", "D"])  # fallback if no valid action found

    #     return self.action

# simulation loop
def run_simulation(steps=13):
    env = GridWorld(size=5)
    agent = LLM_Agent(env)

    # generate initial plan
    print("Generating plan...\n")
    agent.generate_plan()
    print(f"LLM's plan: {agent.plan}\n")
    env.render()

    for _ in range(steps):
        action = agent.decide_move()
        print(f"LLM action: {action}")
        env.step(action)
        env.render()
        # time.sleep(1)
        cont = input("The next step will take place when you hit enter.")

    print("Simulation complete.")

# run the simulation
if __name__ == "__main__":
    run_simulation(steps=10)