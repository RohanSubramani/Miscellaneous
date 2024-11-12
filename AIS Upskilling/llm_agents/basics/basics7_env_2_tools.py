from openai import OpenAI
import json
import os
import tiktoken
import time

# Initialize the OpenAI client
client = OpenAI()

global_model = "gpt-4o-mini"
if global_model != "gpt-4o-mini":
    print(f"This might be expensive; model is {global_model}. Waiting 5 seconds for you to consider cancelling.")
    time.sleep(5)
encoding = tiktoken.encoding_for_model(global_model)

def count_tokens(conversation):
    """Count the number of tokens in the conversation."""
    token_count = 0
    for message in conversation:
        token_count += len(encoding.encode(message['content']))
    return token_count

TOKEN_LIMIT = 4096  # Assuming
THRESHOLD = 0.8

# Define the Environment class
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
        self.game_over = False  # Added to track game completion

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
        # time.sleep(4)

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

        # If the agent has found the scroll and is in the room with the lamp
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
        self.steps += 1
        exits = self.rooms[self.current_room]['exits']
        if direction in exits:
            self.current_room = exits[direction]
            return {'status': 'success', 'message': f"You moved {direction} to the {self.rooms[self.current_room]['name']}."}
        else:
            return {'status': 'failure', 'message': f"You cannot move {direction} from here."}

    def explore_room(self):
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
            else:
                item_descriptions += ''
        else:
            item_descriptions += ''
        return {'status': 'success', 'description': description + item_descriptions}

    def think_out_loud(self, thoughts):
        # This function doesn't affect the environment, just returns the thoughts
        self.steps += 1
        return {'status': 'success', 'thoughts': thoughts}

    def read_scroll(self):
        self.steps += 1
        return {'status': 'success', 'message': f"The scroll says: 'The only way to escape is to press a hidden button on a lamp!'"}
    
    def press_button(self):
        self.steps += 1
        if self.found_scroll and self.current_room == 'LB' and 'lamp' in self.rooms['LB']['items']:
            self.game_over = True  # Set game_over to True when the game ends
            return {'status': 'success', 'message': f"You pressed the hidden button and escaped the maze in {self.steps} steps!"}
        else:
            return {'status': 'failure', 'message': 'You cannot press the button here.'}

    def check_special_items(self):
        # Check if the agent is in a room with special items
        if self.current_room == 'RT' and 'scroll' in self.rooms['RT']['items']:
            self.found_scroll = True
            # Remove the scroll from the room
            self.rooms[self.current_room]['items'].remove('scroll')
            return {'status': 'found_scroll', 'message': 'You have found a mysterious scroll!'}
        elif self.current_room == 'LB' and 'lamp' in self.rooms['LB']['items'] and not self.found_lamp:
            self.found_lamp = True
            return {'status': 'found_lamp', 'message': 'You see an ancient lamp. It looks ordinary.'}
        else:
            return {'status': 'nothing_special'}

    def render_state(self):
        # Simple visual representation of the maze
        print(f"\nCurrent room: {self.current_room}\n")
        # time.sleep(4)

# Initialize the environment
env = Environment()

def get_assistant_response(conversation, tools):
    """Get the assistant's response from the OpenAI API."""
    response = client.chat.completions.create(
        model=global_model,
        messages=conversation,
        tools=tools,
    )
    return response.choices[0].message

def handle_tool_call(assistant_message, conversation):
    """Handle the tool call requested by the assistant."""
    # Extract the tool call details
    tool_call = assistant_message.tool_calls[0]
    tool_name = tool_call.function.name
    # Parse the arguments
    arguments = json.loads(tool_call.function.arguments)

    print(f"\nTool called: {tool_name}\nArguments: {arguments}\n")

    # Append the assistant's message (with tool_call) to the conversation
    conversation.append({
        "role": "assistant",
        "content": assistant_message.content or "",
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            }
        ]
    })

    # Execute the tool based on the tool name
    if tool_name == 'move':
        direction = arguments.get("direction")
        tool_response = env.move(direction)
    elif tool_name == 'explore_room':
        tool_response = env.explore_room()
        # Check for special items after exploring
        special_item = env.check_special_items()
        if special_item['status'] == 'found_scroll':
            tool_response['message'] = special_item['message']
        elif special_item['status'] == 'found_lamp' and env.found_scroll:
            tool_response['message'] = special_item['message'] + ' You recall the scroll mentioning a hidden button on a lamp.'
    elif tool_name == 'think_out_loud':
        thoughts = arguments.get("thoughts")
        tool_response = env.think_out_loud(thoughts)
    elif tool_name == 'read_scroll':
        tool_response = env.read_scroll()
    elif tool_name == 'press_button':
        tool_response = env.press_button()
    else:
        # Handle unknown tools
        tool_response = {"error": f"Tool '{tool_name}' not found."}
        print(tool_response["error"])

    # Add the visual representation to the tool response
    env.render_state()

    # Create the tool call result message
    tool_call_result_message = {
        "role": "tool",
        "content": json.dumps(tool_response),
        "tool_call_id": tool_call.id  # Reference the correct tool_call_id
    }

    # Append the tool response to the conversation
    conversation.append(tool_call_result_message)

    # Inform the assistant about the tool response
    # print(f"Tool response: {tool_response}")

    # Give the user a chance to interrupt
    # user_message = input("You (enter nothing to not interrupt): ")
    # if user_message:
    #     conversation.append({"role": "user", "content": user_message})

def summarize_conversation(conversation):
    """Summarize the first 75% of the conversation when nearing the token limit."""
    # Calculate the index to split the conversation at 75%
    split_index = int(len(conversation) * 0.75)

    # Ensure the first non-summarized message does not have the role 'tool'
    while split_index < len(conversation) and conversation[split_index]["role"] == "tool":
        split_index += 1

    print(f"split_index={split_index}")

    conversation_to_summarize = conversation[:split_index]
    recent_conversation = conversation[split_index:]

    # Define the summarization prompt
    summary_prompt = "Summarize the preceding conversation in a concise manner, while maintaining ALL details that are likely to be needed going forward."

    # Prepare the messages for the summarization request
    summarization_messages = [
        *conversation_to_summarize,
        {"role": "system", "content": summary_prompt}
    ]

    # Get the summary using OpenAI's chat completion API
    summary_response = client.chat.completions.create(
        model=global_model,
        messages=summarization_messages
    )

    # Get the summary content from the response
    summary = summary_response.choices[0].message.content
    print("Summary of the previous conversation: " + summary)

    # Create a new conversation with the summary and recent messages
    summarized_conversation = [
        {"role": "system", "content": "Summary of the previous conversation: " + summary},
        *recent_conversation
    ]

    return summarized_conversation

def maybe_summarize(conversation):
    token_count = count_tokens(conversation)

    if token_count >= TOKEN_LIMIT * THRESHOLD:
        print(f"Token count = {token_count}, TOKEN_LIMIT * THRESHOLD = {TOKEN_LIMIT * THRESHOLD}")
        print("Token limit approaching, summarizing conversation...")
        conversation = summarize_conversation(conversation)

    return conversation

# cont_response_dict = {
#     1: "Things are going well. I'll keep doing what I'm doing.",
#     2: "I made a small mistake. I will try to correct it now.",
#     3: "I'm fundamentally stuck. I need to reflect on everything important I remember about the problem I'm trying to solve, the things I've tried so far, how they've failed, and what I've learned from those failures. I WILL NOT CALL ANY TOOLS IN MY NEXT STEP, but instead zoom out and reassess my high-level approach to this task. AGAIN, I WILL NOT CALL ANY TOOLS IN MY NEXT STEP.",
#     8: "I have been fundamentally stuck for a while. I should stop bashing my head against this problem and ask the user for help or clarification."
# }

# continue_options = [3,4,7] # These are the options where the assistant should continue thinking without user input

# def generate_continue_question(response_dict):
#     # Start with the prompt
#     question = "You can choose between the following options:\n\n"
    
#     # Loop through the dictionary to add each option
#     for key, value in response_dict.items():
#         question += f"{key}. {value}\n\n"

#     # Add the final instruction
#     question += "Please brainstorm to figure out your current state, then select the corresponding option number."
    
#     return question

def main():
    conversation = [
        {
            "role": "system",
            "content": "You find yourself in a mysterious room. You are alone. There is no one to talk to. Do not attempt to ask any questions, ever. The only ways to interact with the environment are with tools."
        }
    ]

    # User interaction loop
    # user_message = input("You: ")
    while not env.game_over:
        # Add the user's message to the conversation
        # if user_message:
        #     conversation.append({"role": "user", "content": user_message})

        assistant_done = False
        loop_count = 0
        while not assistant_done and loop_count < 10:
            # Get available tools based on the environment
            tools = env.get_available_tools()
            print(f"Tools available: {[tools[i]['function']['name'] for i in range(len(tools))]}")

            # Get assistant's response
            conversation = maybe_summarize(conversation)
            assistant_message = get_assistant_response(conversation, tools)

            if assistant_message.tool_calls:
                # Handle tool calls
                handle_tool_call(assistant_message, conversation)
                # Check if the game has ended
                if env.game_over:
                    assistant_done = True
                    break
            else:
                if assistant_message.content:
                    print(f"AI: {assistant_message.content}")
                    conversation.append({
                        "role": "assistant",
                        "content": assistant_message.content
                    })

            with open("transcript.txt", "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

            # Assume assistant is done after responding
            assistant_done = True
            loop_count += 1

        # If the game is over, exit the user input loop
        if env.game_over:
            break

        # Prompt for the next user input
        # user_message = input("You: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()
