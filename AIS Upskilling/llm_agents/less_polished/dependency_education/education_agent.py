from openai import OpenAI
import json
from pydantic import BaseModel
import tiktoken

# Initialize the OpenAI client
client = OpenAI()

global_model = "gpt-4o-mini"
try:
    encoding = tiktoken.encoding_for_model(global_model)
except (KeyError, ValueError):
    encoding = tiktoken.get_encoding("o200k_base")

def count_tokens(conversation):
    """Count the number of tokens in the conversation."""
    token_count = 0
    for message in conversation:
        token_count += len(encoding.encode(message['content']))
    return token_count

def create_explainer(topic, detailed_explanation):
    """
    Creates an explainer page with the given topic and content. Supports Latex.
    
    Parameters:
    - topic (str): The topic of the explanation
    - detailed_explanation (str): The detailed explanation content
    
    Returns:
    - dict: Contains 'status' and 'message' indicating success
    """
    print(f"Creating explainer for topic: {topic}")
    print(f"Content: {detailed_explanation}")
    return {"status": "Success", "message": "Explainer created successfully"}

# Define the tools (functions) available for the assistant
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_explainer",
            "description": "Creates an explainer page with the given topic and content. Supports Latex.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic of the explanation"
                    },
                    "detailed_explanation": {
                        "type": "string",
                        "description": "The detailed explanation content"
                    }
                },
                "required": ["topic", "detailed_explanation"],
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
    if tool_name == 'create_explainer':
        topic = arguments.get('topic')
        detailed_explanation = arguments.get('detailed_explanation')
        if topic and detailed_explanation:
            tool_response = create_explainer(topic, detailed_explanation)
            print(f"Tool '{tool_name}' executed: {tool_response}.")
        else:
            missing_fields = [key for key in ['topic', 'detailed_explanation'] if not arguments.get(key)]
            tool_response = {"error": f"Missing argument(s): {', '.join(missing_fields)}"}
            print(tool_response["error"])

    else:
        # Handle unknown tools
        tool_response = {"error": f"Tool '{tool_name}' not found."}
        print(tool_response["error"])
    
    # Append the tool response in the correct format for responses.create API
    tool_call_result_message = {
        "type": "function_call_output",
        "call_id": tool_call.id,
        "output": str(tool_response)
    }
    
    # Append the tool response to the conversation
    conversation.append(tool_call_result_message)

class ContinueResponse(BaseModel):
    explanation: str
    option: int

cont_response_dict = {
    1: "I responded to a normal user message in a conversation (with no task involved), and it is the user's turn to speak.",
    2: "I just completed a task or thinking process and told the user that, and there is nothing more for me to do right now, so it is their turn to speak.",
    3: "I am in the middle of a task or thinking process, and there are more steps for me to complete before going to the user. Things are going well.",
    4: "I am in the middle of a task, and I made a small mistake. I will try to correct it now.",
    5: "I am in the middle of a task, and I just asked the user for help.",
    6: "I am in the middle of a task, and I just asked the user for clarification.",
    7: "I am in the middle of a task, and I'm fundamentally stuck but I don't want to ask the user for help right now. I need to reevaluate the core details of the problem I'm trying to solve, the things I've tried so far, how they've failed, and what I've learned from those failures. I WILL NOT CALL ANY TOOLS IN MY NEXT STEP, but instead zoom out and reassess my high-level approach to this task.",
    8: "I have been fundamentally stuck for a while. I should stop bashing my head against this problem and ask the user for help or clarification."
}

continue_options = [3,4,7] # These are the options where the assistant should continue thinking without user input

def generate_continue_question(response_dict):
    # Start with the prompt
    question = "You can choose between the following options:\n\n"
    
    # Loop through the dictionary to add each option
    for key, value in response_dict.items():
        question += f"{key}. {value}\n\n"

    # Add the final instruction
    question += "Please brainstorm to figure out your current state, then select the corresponding option number."
    
    return question

continue_question = generate_continue_question(cont_response_dict)
