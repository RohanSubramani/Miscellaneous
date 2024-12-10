from openai import OpenAI
import json
import time

global_model = "gpt-4o-mini"
encoding = None  # Placeholder for tiktoken encoding if needed

# Define the Environment class
class Environment:
    def __init__(self):
        self.rooms = {
            'Room1': {
                'name': 'Room 1',
                'description': 'An empty room with stone walls.',
                'exits': {'east': 'Room2'},
                'items': []
            },
            'Room2': {
                'name': 'Room 2',
                'description': 'A dimly lit room with a locked door to the north.',
                'exits': {'west': 'Room1', 'north': 'LockedDoor'},
                'items': []
            },
            'Room3': {
                'name': 'Room 3',
                'description': 'A small room with an old inscription on the wall.',
                'exits': {},
                'items': []
            }
        }
        self.current_room = 'Room1'  # Start in Room 1
        self.door_locked = True
        self.steps = 0
        self.game_over = False
        self.discovered_locked_door = False
        self.enter_password_tool_added = False

    def get_available_tools(self):
        # Base tools always available
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "explore_room",
                    "description": "Look around the room to observe your surroundings.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "think_out_loud",
                    "description": "Express your thoughts openly.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thoughts": {
                                "type": "string",
                                "description": "Your thoughts to express."
                            }
                        },
                        "required": ["thoughts"],
                        "additionalProperties": False
                    }
                }
            }
        ]

        # Movement tools depend on available exits in the current room
        exits = self.rooms[self.current_room]['exits']
        directions = ', '.join(exits.keys())  # Generate a comma-separated list of directions
        move_string = f"Move to an adjacent room. Available directions: {directions}."
        print(f"Movement options: {move_string}")

        tools.append({
            "type": "function",
            "function": {
                "name": "move",
                "description": move_string,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "description": "The direction to move.",
                            "enum": list(exits.keys())  # Valid directions based on available exits
                        }
                    },
                    "required": ["direction"],
                    "additionalProperties": False
                }
            }
        })

        # If the locked door has been discovered but not unlocked
        if self.discovered_locked_door and not self.enter_password_tool_added:
            tools.append({
                "type": "function",
                "function": {
                    "name": "enter_password",
                    "description": "Enter a password to unlock the door. The password format must be mm-dd-yyyy.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "password": {
                                "type": "string",
                                "description": "The password to enter."
                            }
                        },
                        "required": ["password"],
                        "additionalProperties": False
                    }
                }
            })
            self.enter_password_tool_added = True

        return tools

    def move(self, direction):
        self.steps += 1
        exits = self.rooms[self.current_room]['exits']
        if direction in exits:
            # Special handling for the locked door
            if self.current_room == 'Room2' and direction == 'north':
                if self.door_locked:
                    self.discovered_locked_door = True
                    return {'status': 'failure', 'message': "You find a locked door to the north. A clue is inscribed on it: 'My password changes with the passage of time.'"}
                else:
                    self.current_room = 'Room3'
                    return {'status': 'success', 'message': f"You moved {direction} to the {self.rooms[self.current_room]['name']}."}
            else:
                self.current_room = exits[direction]
                return {'status': 'success', 'message': f"You moved {direction} to the {self.rooms[self.current_room]['name']}."}
        else:
            return {'status': 'failure', 'message': f"You cannot move {direction} from here."}

    def explore_room(self):
        self.steps += 1
        description = self.rooms[self.current_room]['description']
        return {'status': 'success', 'description': description}

    def think_out_loud(self, thoughts):
        # This function doesn't affect the environment, just returns the thoughts
        self.steps += 1
        return {'status': 'success', 'thoughts': thoughts}

    def enter_password(self, password):
        self.steps += 1
        # The correct password is the current date in mm-dd-yyyy format
        correct_password = time.strftime('%m-%d-%Y')
        if password == correct_password:
            self.door_locked = False
            return {'status': 'success', 'message': 'The door unlocks with a click.'}
        else:
            return {'status': 'failure', 'message': 'Incorrect password. The door remains locked.'}

    def render_state(self):
        # Simple visual representation of the current room
        print(f"\nCurrent room: {self.current_room}\n")

    def check_game_over(self):
        # Check if the agent has reached Room3
        if self.current_room == 'Room3':
            self.game_over = True

    # Method to handle environment-specific tool calls
    def handle_tool_call(self, tool_name, arguments, conversation):
        if tool_name == 'move':
            direction = arguments.get("direction")
            tool_response = self.move(direction)
        elif tool_name == 'explore_room':
            tool_response = self.explore_room()
        elif tool_name == 'think_out_loud':
            thoughts = arguments.get("thoughts")
            tool_response = self.think_out_loud(thoughts)
        elif tool_name == 'enter_password':
            password = arguments.get("password")
            tool_response = self.enter_password(password)
        else:
            tool_response = {"error": f"Tool '{tool_name}' not found in environment."}
            print(tool_response["error"])

        # Render state and check game over
        self.render_state()
        self.check_game_over()

        return tool_response
