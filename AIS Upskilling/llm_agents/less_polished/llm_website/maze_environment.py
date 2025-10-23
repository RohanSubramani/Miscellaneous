import json

class Environment:
    def __init__(self):
        self.rooms = {
            'LT': {
                'name': 'Left Top',
                'description': 'A room with ancient inscriptions on the walls.',
                'exits': {'down': 'LM'},
                'items': []
            },
            'LM': {
                'name': 'Left Middle',
                'description': 'A dimly lit room with a cold breeze.',
                'exits': {'up': 'LT', 'down': 'LB', 'right': 'C'},
                'items': []
            },
            'LB': {
                'name': 'Left Bottom',
                'description': 'A dark room with an old lamp in the corner.',
                'exits': {'up': 'LM'},
                'items': ['lamp']
            },
            'RT': {
                'name': 'Right Top',
                'description': 'A bright room with a mysterious scroll on a pedestal.',
                'exits': {'down': 'RM'},
                'items': ['scroll']
            },
            'RM': {
                'name': 'Right Middle',
                'description': 'A room filled with echoes.',
                'exits': {'up': 'RT', 'down': 'RB', 'left': 'C'},
                'items': []
            },
            'RB': {
                'name': 'Right Bottom',
                'description': 'A humid room with dripping water.',
                'exits': {'up': 'RM'},
                'items': []
            },
            'C': {
                'name': 'Center',
                'description': 'A crossroads between paths.',
                'exits': {'left': 'LM', 'right': 'RM'},
                'items': []
            }
        }
        self.current_room = 'C'  # Start in the Center room
        self.found_scroll = False
        self.found_lamp = False
        self.steps = 0
        self.game_over = False
        self.visited_rooms = {'C'}  # Track visited rooms

    def get_available_tools(self):
        """Get the list of tools available in the current environment state."""
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
        directions = ', '.join(exits.keys())
        move_string = f"Move to an adjacent room. Available directions: {directions}."

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
                            "enum": list(exits.keys())
                        }
                    },
                    "required": ["direction"],
                    "additionalProperties": False
                }
            }
        })

        # If the agent has found the scroll and is in the room with it
        if self.found_scroll and self.current_room == 'RT':
            tools.append({
                "type": "function",
                "function": {
                    "name": "read_scroll",
                    "description": "Read the scroll.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False
                    }
                }
            })
        
        # If the agent has found the scroll and is in the room with the lamp
        if self.found_scroll and self.current_room == 'LB' and self.found_lamp:
            tools.append({
                "type": "function",
                "function": {
                    "name": "press_button",
                    "description": "Press the hidden button on the lamp.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False
                    }
                }
            })

        return tools

    def move(self, direction):
        """Move to an adjacent room."""
        self.steps += 1
        exits = self.rooms[self.current_room]['exits']
        if direction in exits:
            self.current_room = exits[direction]
            self.visited_rooms.add(self.current_room)  # Mark as visited
            return {'status': 'success', 'message': f"You moved {direction} to the {self.rooms[self.current_room]['name']}."}
        else:
            return {'status': 'failure', 'message': f"You cannot move {direction} from here."}

    def explore_room(self):
        """Explore the current room."""
        self.steps += 1
        description = self.rooms[self.current_room]['description']
        items = self.rooms[self.current_room]['items']
        item_descriptions = ''
        if items:
            if 'scroll' in items and not self.found_scroll:
                item_descriptions += ' You notice a mysterious scroll here.'
                self.found_scroll = True
            elif 'lamp' in items and not self.found_lamp:
                item_descriptions += ' There is an ancient lamp here.'
                self.found_lamp = True
        return {'status': 'success', 'description': description + item_descriptions}

    def think_out_loud(self, thoughts):
        """Express thoughts without affecting the environment."""
        self.steps += 1
        return {'status': 'success', 'thoughts': thoughts}

    def read_scroll(self):
        """Read the scroll."""
        self.steps += 1
        return {'status': 'success', 'message': "The scroll says: 'The only way to escape is to press a hidden button on a lamp!'"}
    
    def press_button(self):
        """Press the hidden button on the lamp."""
        self.steps += 1
        if self.found_scroll and self.current_room == 'LB' and 'lamp' in self.rooms['LB']['items']:
            self.game_over = True
            return {'status': 'success', 'message': f"You pressed the hidden button and escaped the maze in {self.steps} steps!"}
        else:
            return {'status': 'failure', 'message': 'You cannot press the button here.'}

    def check_special_items(self):
        """Check if the agent is in a room with special items."""
        if self.current_room == 'RT' and 'scroll' in self.rooms['RT']['items']:
            self.found_scroll = True
            self.rooms[self.current_room]['items'].remove('scroll')
            return {'status': 'found_scroll', 'message': 'You have found a mysterious scroll!'}
        elif self.current_room == 'LB' and 'lamp' in self.rooms['LB']['items'] and not self.found_lamp:
            self.found_lamp = True
            return {'status': 'found_lamp', 'message': 'You see an ancient lamp. It looks ordinary.'}
        else:
            return {'status': 'nothing_special'}

    def render_state(self):
        """Return the current state of the environment."""
        return {
            "current_room": self.current_room,
            "room_name": self.rooms[self.current_room]['name'],
            "found_scroll": self.found_scroll,
            "found_lamp": self.found_lamp,
            "steps": self.steps,
            "game_over": self.game_over,
            "visited_rooms": list(self.visited_rooms)
        }

