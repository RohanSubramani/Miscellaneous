from openai import OpenAI
import json
import subprocess
import os
import tiktoken
import time
import platform
import shutil
from pydantic import BaseModel

system = platform.system()
print(f"System: {system}\n")

# Initialize the OpenAI client
client = OpenAI()

# Model Configuration
global_model = "gpt-4o-mini"
if global_model != "gpt-4o-mini":
    print(f"This might be expensive; model is {global_model}. Waiting 5 seconds for you to consider cancelling.")
    time.sleep(5)

# Initialize token encoding
encoding = tiktoken.encoding_for_model(global_model)

def count_tokens(conversation):
    """Count the number of tokens in the conversation."""
    token_count = 0
    for message in conversation:
        token_count += len(encoding.encode(message['content']))
    return token_count

# Token Management
TOKEN_LIMIT = 4096  # Adjust based on the model's token limit
THRESHOLD = 0.8

def summarize_conversation(conversation):
    """Summarize the first 75% of the conversation when nearing the token limit."""
    split_index = int(len(conversation) * 0.75)

    # Ensure the split does not cut through tool messages
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

    # Extract the summary content
    summary = summary_response.choices[0].message.content
    print("Summary of the previous conversation: " + summary)

    # Create a new conversation with the summary and recent messages
    summarized_conversation = [
        {"role": "system", "content": "Summary of the previous conversation: " + summary},
        *recent_conversation
    ]

    return summarized_conversation

def maybe_summarize(conversation):
    """Check if the conversation is nearing the token limit and summarize if necessary."""
    token_count = count_tokens(conversation)

    if token_count >= TOKEN_LIMIT * THRESHOLD:
        print(f"Token count = {token_count}, TOKEN_LIMIT * THRESHOLD = {TOKEN_LIMIT * THRESHOLD}")
        print("Token limit approaching, summarizing conversation...")
        conversation = summarize_conversation(conversation)

    return conversation

# Print the shell that will be used
shell_path = os.getenv('SHELL', '/bin/bash')  # Default to /bin/bash if SHELL is not set
print(f"Using shell: {shell_path}")

# Define the Bash command execution tool
def execute_bash_command(command):
    """
    Executes the provided Bash command after user approval.

    Parameters:
    - command (str): The Bash command to execute.

    Returns:
    - dict: Contains 'status' and optionally 'output' if execution was successful.
    """
    print("The following Bash command is requested to be executed:\n")
    print(command)
    approval = input("\nDo you approve executing this command? (yes/no): ").strip().lower()
    
    if approval == 'yes':
        try:
            system = platform.system()
            print(f"System: {system}")
            
            if system == 'Windows':
                # Attempt to locate 'bash' in the system PATH
                bash_executable = shutil.which('bash')
                if bash_executable is None:
                    return {
                        "status": "Error",
                        "error": "Bash shell not found. Please install Git Bash or enable WSL and ensure 'bash' is in your PATH."
                    }
                
                # Execute the command using the located Bash executable
                result = subprocess.run(
                    [bash_executable, '-c', command],
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                # For Unix-like systems, use '/bin/bash' or the SHELL environment variable
                shell_path = os.getenv('SHELL', '/bin/bash')
                
                # Verify that the shell executable exists
                if not os.path.exists(shell_path):
                    return {
                        "status": "Error",
                        "error": f"Specified shell '{shell_path}' does not exist."
                    }
                
                # Execute the command using the specified shell
                result = subprocess.run(
                    command,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    executable=shell_path
                )
            
            print("\nCommand executed successfully.")
            return {"status": "Success", "output": result.stdout}
        
        except subprocess.CalledProcessError as e:
            print(f"\nError executing command: {e.stderr}")
            return {"status": "Error", "error": e.stderr}
        
        except FileNotFoundError as e:
            print(f"\nShell executable not found: {e}")
            return {"status": "Error", "error": str(e)}
        
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            return {"status": "Error", "error": str(e)}
    
    else:
        print("\nCommand execution aborted by the user.")
        return {"status": "Execution aborted by user."}

# Define the tools (functions) available for the assistant
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash_command",
            "description": "Executes a Bash command. Returns the output of the command if execution was successful.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The Bash command to execute."
                    }
                },
                "required": ["command"],
                "additionalProperties": False
            }
        }
    }
]

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
    if tool_name == 'execute_bash_command':
        command = arguments.get('command')
        if command:
            # Execute the command and get the result
            tool_response = execute_bash_command(command)
            # Optionally, print the output
            if 'output' in tool_response and tool_response['output']:
                print(f"Command output:\n{tool_response['output']}")
        else:
            tool_response = {"error": "Missing 'command' argument."}
            print(tool_response["error"])

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

    # Log the conversation to a transcript file
    with open("transcript.txt", "w", encoding="utf-8") as file:
        json.dump(conversation, file, ensure_ascii=False, indent=4)

    # Send the result back to the assistant by making another API call
    assistant_followup = get_assistant_response(conversation)

    # Print the assistant's follow-up response
    print(f"AI: {assistant_followup.content}")

    # Append the assistant's follow-up response to the conversation
    if assistant_followup.content:
        conversation.append({
            "role": "assistant",
            "content": assistant_followup.content
        })

def main():
    # Initial system prompt
    conversation = [
        {
            "role": "system",
            "content": "You are a helpful assistant. You can execute Bash commands to help the user."
        }
    ]

    print("Chat with the assistant. Type 'end' to finish.")
    user_message = input("You: ")
    while user_message.lower() != 'end':
        # Add the user's message to the conversation
        if user_message:
            conversation.append({"role": "user", "content": user_message})

        option = continue_options[0] # Always enter the while loop the first time
        while option in continue_options:
            # Get the assistant's response
            conversation = maybe_summarize(conversation)

            # Get assistant's response
            assistant_message = get_assistant_response(conversation)

            if assistant_message.tool_calls:
                # Handle tool calls
                handle_tool_call(assistant_message, conversation)
            else:
                # No tool call, just print the assistant's message
                if assistant_message.content:
                    print(f"AI: {assistant_message.content}")
                    conversation.append({
                        "role": "assistant",
                        "content": assistant_message.content
                    })
            
            conversation.append({"role": "system", "content": continue_question})

            assistant_reply = client.beta.chat.completions.parse(
                model=global_model,
                messages=conversation,
                response_format=ContinueResponse,
            )
            
            # Remove the system message
            conversation.pop()
            
            # Check assistant's reply
            explanation = assistant_reply.choices[0].message.parsed.explanation
            option = assistant_reply.choices[0].message.parsed.option

            print(f"assistant explanation: {explanation}")
            print(f"assistant reply: {option} - {cont_response_dict[option]}")
            conversation.append({"role": "assistant", "content": f"{explanation}\n\n{cont_response_dict[option]}"})

            # Log the conversation to a transcript file
            with open("transcript.txt", "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

        # Prompt for the next user input
        user_message = input("You: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()