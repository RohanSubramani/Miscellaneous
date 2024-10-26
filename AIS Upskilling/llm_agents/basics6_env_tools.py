from openai import OpenAI
import json
import os
from pydantic import BaseModel
import tiktoken

# Initialize the OpenAI client
client = OpenAI()

global_model = "gpt-4o-mini"
encoding = tiktoken.encoding_for_model(global_model)

def count_tokens(conversation):
    """Count the number of tokens in the conversation."""
    token_count = 0
    for message in conversation:
        token_count += len(encoding.encode(message['content']))
    return token_count

TOKEN_LIMIT = 4096  # I think
THRESHOLD = 0.8

# Define the Environment class
class Environment:
    def __init__(self):
        import random
        self.game_type = random.choice(['Type 1', 'Type 2'])
        self.room = 'entry'  # Starting room is 'entry'

    def read_paper(self):
        if self.room == 'entry':
            return {'status': 'success', 'game_type': self.game_type}
        else:
            return {'status': 'failure', 'message': 'Cannot read paper in this room.'}

    def move(self, direction):
        if direction == 'right':
            if self.room == 'entry':
                self.room = 'right'
                return {'status': 'success', 'message': 'Moved to the right room.'}
            elif self.room == 'left':
                self.room = 'entry'
                return {'status': 'success', 'message': 'Moved to the entry room.'}
            else:
                return {'status': 'failure', 'message': 'Cannot move right from this room.'}
        elif direction == 'left':
            if self.room == 'entry':
                self.room = 'left'
                return {'status': 'success', 'message': 'Moved to the left room.'}
            elif self.room == 'right':
                self.room = 'entry'
                return {'status': 'success', 'message': 'Moved to the entry room.'}
            else:
                return {'status': 'failure', 'message': 'Cannot move left from this room.'}
        else:
            return {'status': 'failure', 'message': f"Invalid direction '{direction}'. Use 'left' or 'right'."}

    def end_game(self):
        if self.room == 'right' and self.game_type == 'Type 1':
            return {'status': 'success', 'message': 'Victory! Game ended in the correct room (right) for Type 1.'}
        elif self.room == 'left' and self.game_type == 'Type 2':
            return {'status': 'success', 'message': 'Victory! Game ended in the correct room (left) for Type 2.'}
        elif self.room == 'right' and self.game_type == 'Type 2':
            return {'status': 'failure', 'message': 'Loss! Game ended in the wrong room (right) for Type 2.'}
        elif self.room == 'left' and self.game_type == 'Type 1':
            return {'status': 'failure', 'message': 'Loss! Game ended in the wrong room (left) for Type 1.'}
        else:
            return {'status': 'failure', 'message': 'Cannot end game in the entry room.'}

# Initialize the environment
env = Environment()

# Define the tools (functions) available for the assistant
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_paper",
            "description": "Reads the piece of paper in the entry room to find out the game type.",
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
            "name": "move",
            "description": "Moves to the specified room. Use 'right' or 'left' as direction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "The direction to move. Must be either 'right' or 'left'."
                    }
                },
                "required": ["direction"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_game",
            "description": "Ends the game if in the left or right room.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    }
]

def get_assistant_response(conversation):
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
    if tool_name == 'read_paper':
        tool_response = env.read_paper()
    elif tool_name == 'move':
        direction = arguments.get("direction")
        tool_response = env.move(direction)
    elif tool_name == 'end_game':
        tool_response = env.end_game()
    else:
        # Handle unknown tools
        tool_response = {"error": f"Tool '{tool_name}' not found."}
        print(tool_response["error"])

    # Create the tool call result message
    tool_call_result_message = {
        "role": "tool",
        "content": json.dumps(tool_response),
        "tool_call_id": tool_call.id  # Reference the correct tool_call_id
    }

    # Append the tool response to the conversation
    conversation.append(tool_call_result_message)

    # Inform the assistant about the tool response
    print(f"Tool response: {tool_response}")

    # Give the user a chance to interrupt
    user_message = input("You (enter nothing to not interrupt): ")
    if user_message:
        conversation.append({"role": "user", "content": user_message})

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

def main():
    conversation = [
        {
            "role": "system",
            "content": (
                "You are in a game environment with rooms. You start in the entry room. "
                "Your goal is to end the game in the right room if it's a Type 1 game and "
                "end the game in the left room if it's a Type 2 game. You can use the tools "
                "available to navigate and find out the game type. Remember that you cannot "
                "end the game in the entry room. The game type is written on a sheet of paper "
                "in the entry room"
            )
        }
    ]

    # User interaction loop
    user_message = input("You: ")
    while user_message.lower() != 'end':
        # Add the user's message to the conversation
        if user_message:
            conversation.append({"role": "user", "content": user_message})

        assistant_done = False
        loop_count = 0
        while not assistant_done and loop_count < 10:
            # Get assistant's response
            conversation = maybe_summarize(conversation)
            assistant_message = get_assistant_response(conversation)

            if assistant_message.tool_calls:
                # Handle tool calls
                handle_tool_call(assistant_message, conversation)
            else:
                # No tool call, just print the assistant's message
                if assistant_message.content is None:
                    assistant_message.content = "(Silent)"
                print(f"AI: {assistant_message.content}")
                if assistant_message.content:
                    conversation.append({
                        "role": "assistant",
                        "content": assistant_message.content
                    })

            with open("transcript.txt", "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

            # No continue response logic here
            # Assume assistant is done after responding
            assistant_done = True

        # Prompt for the next user input
        user_message = input("You: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()
