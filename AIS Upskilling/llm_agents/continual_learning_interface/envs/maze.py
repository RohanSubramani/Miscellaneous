import json
import random
from typing import Dict, List, Optional
from envs import Env

class MazeEnv(Env):
    """Maze exploration environment with random generation."""
    
    def __init__(self, num_rooms: int = 7, seed: Optional[int] = None):
        self.num_rooms = num_rooms
        self.seed = seed
        self.scroll_room = None
        self.lamp_room = None
        self.start_room = None
        self.rooms = {}
        self.generate_maze()
        self.reset()
    
    def generate_maze(self):
        """Generate a random connected maze with rooms at (x, y) positions."""
        if self.seed is not None:
            random.seed(self.seed)
        
        # Validate num_rooms
        if self.num_rooms < 3:
            self.num_rooms = 3
        elif self.num_rooms > 50:
            self.num_rooms = 50
        
        # Create room IDs
        room_ids = [f'R{i}' for i in range(self.num_rooms)]
        
        # Generate positions for rooms using a grid-like layout
        # Calculate grid size (roughly square)
        grid_size = int(self.num_rooms ** 0.5) + 1
        
        # Generate positions using randomized DFS to ensure connectivity
        positions = self._generate_room_positions(room_ids, grid_size)
        
        # Initialize rooms with positions
        self.rooms = {}
        for room_id, (x, y) in zip(room_ids, positions):
            self.rooms[room_id] = {
                'name': f'Room {room_id}',
                'description': self._generate_room_description(),
                'x': x,
                'y': y,
                'items': []
            }
        
        # Randomly place scroll and lamp in different rooms
        available_rooms = room_ids.copy()
        self.scroll_room = random.choice(available_rooms)
        available_rooms.remove(self.scroll_room)
        self.lamp_room = random.choice(available_rooms)
        
        # Place items
        self.rooms[self.scroll_room]['items'] = ['scroll']
        self.rooms[self.lamp_room]['items'] = ['lamp']
        
        # Choose start room (not where items are)
        start_candidates = [r for r in room_ids if r not in [self.scroll_room, self.lamp_room]]
        if start_candidates:
            self.start_room = random.choice(start_candidates)
        else:
            self.start_room = room_ids[0]
    
    def _generate_room_description(self) -> str:
        """Generate a random room description."""
        descriptions = [
            'A dimly lit room with stone walls.',
            'A room filled with echoes.',
            'A cold room with a draft.',
            'A room with ancient inscriptions on the walls.',
            'A humid room with dripping water.',
            'A bright room with mysterious energy.',
            'A dark room with shadows dancing.',
            'A room with a musty smell.',
            'A room with strange symbols carved into the floor.',
            'A room that feels empty and vast.'
        ]
        return random.choice(descriptions)
    
    def _generate_room_positions(self, room_ids: List[str], grid_size: int) -> List[tuple]:
        """Generate (x, y) positions for rooms using randomized DFS to ensure connectivity."""
        positions = []
        used_positions = set()
        
        # Start with first room at (0, 0)
        start_pos = (0, 0)
        positions.append(start_pos)
        used_positions.add(start_pos)
        
        # Stack for DFS
        stack = [start_pos]
        remaining_rooms = len(room_ids) - 1
        
        # Directions: north, south, east, west
        directions = [(0, -1), (0, 1), (1, 0), (-1, 0)]  # (dx, dy) for north, south, east, west
        
        while remaining_rooms > 0 and stack:
            current = stack[-1]
            
            # Get adjacent positions
            adjacent = []
            for dx, dy in directions:
                new_pos = (current[0] + dx, current[1] + dy)
                if new_pos not in used_positions:
                    adjacent.append(new_pos)
            
            if adjacent:
                # Pick random adjacent position
                next_pos = random.choice(adjacent)
                positions.append(next_pos)
                used_positions.add(next_pos)
                stack.append(next_pos)
                remaining_rooms -= 1
            else:
                # Backtrack
                stack.pop()
        
        # If we still have rooms left, place them randomly near existing positions
        while remaining_rooms > 0:
            # Pick a random existing position
            base_pos = random.choice(positions)
            # Try to find an adjacent free position
            found = False
            for dx, dy in directions:
                new_pos = (base_pos[0] + dx, base_pos[1] + dy)
                if new_pos not in used_positions:
                    positions.append(new_pos)
                    used_positions.add(new_pos)
                    remaining_rooms -= 1
                    found = True
                    break
            
            # If no adjacent position found, place at a random nearby position
            if not found:
                attempts = 0
                while attempts < 100:
                    dx = random.randint(-2, 2)
                    dy = random.randint(-2, 2)
                    new_pos = (base_pos[0] + dx, base_pos[1] + dy)
                    if new_pos not in used_positions:
                        positions.append(new_pos)
                        used_positions.add(new_pos)
                        remaining_rooms -= 1
                        break
                    attempts += 1
                if attempts >= 100:
                    # Fallback: just place sequentially
                    x = len(positions)
                    y = 0
                    while (x, y) in used_positions:
                        y += 1
                    positions.append((x, y))
                    used_positions.add((x, y))
                    remaining_rooms -= 1
        
        return positions
    
    def _get_adjacent_room(self, room_id: str, direction: str) -> Optional[str]:
        """Get the room ID at the adjacent position in the given direction, or None if no room exists."""
        current_room = self.rooms[room_id]
        x, y = current_room['x'], current_room['y']
        
        # Direction offsets: north, south, east, west
        direction_offsets = {
            'north': (0, -1),
            'south': (0, 1),
            'east': (1, 0),
            'west': (-1, 0)
        }
        
        if direction not in direction_offsets:
            return None
        
        dx, dy = direction_offsets[direction]
        target_pos = (x + dx, y + dy)
        
        # Find room at target position
        for rid, room in self.rooms.items():
            if room['x'] == target_pos[0] and room['y'] == target_pos[1]:
                return rid
        
        return None
    
    def _get_available_directions(self, room_id: str) -> List[str]:
        """Get list of directions where adjacent rooms exist."""
        available = []
        for direction in ['north', 'south', 'east', 'west']:
            if self._get_adjacent_room(room_id, direction) is not None:
                available.append(direction)
        return available
    
    def reset(self):
        """Reset the maze state to initial conditions."""
        self.current_room = self.start_room
        self.found_scroll = False
        self.found_lamp = False
        self.steps = 0
        self.game_over = False
        self.visited_rooms = {self.start_room}  # Track visited rooms
        # Reset items in rooms
        if self.scroll_room:
            self.rooms[self.scroll_room]['items'] = ['scroll']
        if self.lamp_room:
            self.rooms[self.lamp_room]['items'] = ['lamp']
    
    def get_tools(self) -> List[Dict]:
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

        # Movement tools depend on adjacent rooms (determined by position)
        available_directions = self._get_available_directions(self.current_room)
        
        if available_directions:
            directions_str = ', '.join(available_directions)
            move_string = f"Move to an adjacent room. Available directions: {directions_str}."
            
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
                                "enum": available_directions
                            }
                        },
                        "required": ["direction"],
                        "additionalProperties": False
                    }
                }
            })

        # If the agent has found the scroll and is in the room with it
        if self.found_scroll and self.current_room == self.scroll_room:
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
        if self.found_scroll and self.current_room == self.lamp_room and self.found_lamp:
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
        adjacent_room = self._get_adjacent_room(self.current_room, direction)
        if adjacent_room is not None:
            self.current_room = adjacent_room
            self.visited_rooms.add(self.current_room)  # Mark as visited
            # Return message without room ID, just description
            room_name = self.rooms[self.current_room]['name']
            # Remove room ID from name (e.g., "Room R0" -> just use description)
            return {'status': 'success', 'message': f"You moved {direction}."}
        else:
            return {'status': 'failure', 'message': f"You cannot move {direction} from here."}

    def explore_room(self):
        """Explore the current room."""
        self.steps += 1
        description = self.rooms[self.current_room]['description']
        items = self.rooms[self.current_room]['items']
        item_descriptions = ''
        
        # Check if this is a room with scroll or lamp
        has_special_item = False
        if items:
            if 'scroll' in items and not self.found_scroll:
                item_descriptions += ' You notice a mysterious scroll here.'
                self.found_scroll = True
                has_special_item = True
            elif 'lamp' in items and not self.found_lamp:
                item_descriptions += ' There is an ancient lamp here.'
                self.found_lamp = True
                has_special_item = True
        
        # If no special items found, return empty room message
        if not has_special_item:
            return {'status': 'success', 'description': "You don't find anything particularly interesting in this room."}
        
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
        if self.found_scroll and self.current_room == self.lamp_room and 'lamp' in self.rooms[self.lamp_room]['items']:
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
    
    def get_state(self):
        """Return the current state of the environment for visualization."""
        return {
            "current_room": self.current_room,
            "room_name": self.rooms[self.current_room]['name'],
            "found_scroll": self.found_scroll,
            "found_lamp": self.found_lamp,
            "steps": self.steps,
            "game_over": self.game_over,
            "visited_rooms": list(self.visited_rooms),
            "num_rooms": self.num_rooms,
            "scroll_room": self.scroll_room,
            "lamp_room": self.lamp_room,
            "start_room": self.start_room,
            "rooms": {room_id: {
                "name": room["name"],
                "items": room["items"].copy(),
                "x": room["x"],
                "y": room["y"]
            } for room_id, room in self.rooms.items()}
        }
    
    def regenerate_maze(self, num_rooms: Optional[int] = None, seed: Optional[int] = None):
        """Regenerate the maze with new parameters."""
        if num_rooms is not None:
            self.num_rooms = num_rooms
        if seed is not None:
            self.seed = seed
        self.generate_maze()
        self.reset()
    
    def get_handlers(self) -> Dict[str, callable]:
        """Return a dictionary mapping tool names to handler functions."""
        return {
            "move": self.move,
            "explore_room": self.explore_room,
            "think_out_loud": self.think_out_loud,
            "read_scroll": self.read_scroll,
            "press_button": self.press_button
        }
    
    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return "You find yourself in a mysterious maze."
    
    def get_agent_folder(self) -> str:
        """Return the agent folder path (empty for maze)."""
        return ""

