from openai import OpenAI
import json
import subprocess
import os
import tiktoken
import time
import platform
import shutil
import sys
from pydantic import BaseModel

# Import the Environment class from environment.py
from environment import Environment

system = platform.system()

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
TOKEN_LIMIT = 128000  # Adjust based on the model's token limit
THRESHOLD = 0.9

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

# Define the Bash command execution tool
def execute_bash_command(command):
    """
    Executes the provided Bash command after user approval.

    If the command starts with 'python', it will be written to 'agent_scratchpad.sh' and executed from there.

    Parameters:
    - command (str): The Bash command to execute.

    Returns:
    - dict: Contains 'status' and optionally 'output' if execution was successful,
            or 'suggestion' if the user provides one upon aborting.
    """
    print("The following Bash command is requested to be executed:\n")
    print(command)
    approval = input("\nDo you approve executing this command? (yes/no): ").strip().lower()

    if approval == 'yes':
        try:
            system = platform.system()

            # Check if the command starts with 'python'
            if command.startswith("python"):
                command = command.replace('\r', '').strip()
                # Write command to agent_scratchpad.sh
                with open("agent_scratchpad.sh", "wb") as file:
                    # Convert command to bytes and add LF ending explicitly
                    file.write((command + "\n").encode("utf-8"))
                # Make agent_scratchpad.sh executable
                os.chmod("agent_scratchpad.sh", 0o755)

                # Set command to execute agent_scratchpad.sh instead
                command = "./agent_scratchpad.sh"

            if system == 'Windows':
                bash_executable = shutil.which('bash')
                if bash_executable is None:
                    return {
                        "status": "Error",
                        "error": "Bash shell not found. Please install Git Bash or enable WSL and ensure 'bash' is in your PATH."
                    }

                result = subprocess.run(
                    [bash_executable, '-c', command],
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                shell_path = os.getenv('SHELL', '/bin/bash')

                if not os.path.exists(shell_path):
                    return {
                        "status": "Error",
                        "error": f"Specified shell '{shell_path}' does not exist."
                    }

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
        suggestion = input("If you have a suggestion, please enter it now (or press Enter to skip): ").strip()

        if suggestion:
            print("Thank you for your suggestion!")
            return {
                "status": "Execution aborted by user.",
                "suggestion": suggestion
            }
        else:
            return {"status": "Execution aborted by user."}

def backup_self_mod_file(path):
    """
    Backs up the specified file to the 'do_not_edit' folder with an incremented filename
    if a file already exists.

    Parameters:
    - path (str): The path of the file to back up.

    Returns:
    - str: The path of the backup file if created, otherwise None.
    """
    do_not_edit_folder = 'do_not_edit'
    if not os.path.exists(do_not_edit_folder):
        os.makedirs(do_not_edit_folder)
    
    backup_base_name = os.path.join(do_not_edit_folder, 'save_self_mod_')
    backup_index = 1

    # Find an unused backup file name
    while os.path.exists(f"{backup_base_name}{backup_index}.py"):
        backup_index += 1

    backup_path = f"{backup_base_name}{backup_index}.py"
    shutil.copy2(path, backup_path)
    print(f"Backup created at {backup_path}")

    return backup_path

def write_python_file(path, content):
    """
    Writes the provided content to a Python file at the specified path.
    If the file is the current script, it first backs up the original
    to the 'do_not_edit' folder with an incremented filename if a file already exists.
    If the file already exists and is going to be overwritten, it first writes the new content to 'user_check.py'
    so that the user can review it before approving the overwrite.

    Parameters:
    - path (str): The file path where the Python file will be created.
    - content (str): The content to write into the Python file.

    Returns:
    - dict: Contains 'status' and optionally 'message' if execution was successful,
            'error' if there was an issue, or 'suggestion' if the user provides one upon aborting.
    """
    try:
        current_script_name = os.path.basename(__file__)

        # Check if the file is the current script
        if os.path.basename(path) == current_script_name:
            backup_self_mod_file(path)  # Create backup if needed

        # Check if the file already exists
        if os.path.exists(path):
            # Write the new content to 'user_check.py' for user review
            user_check_path = 'user_check.py'
            with open(user_check_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"The file '{path}' already exists.")
            print(f"The proposed new content has been written to '{user_check_path}' for your review.")
            approval = input("Do you want to overwrite the existing file with this new content? (yes/no): ").strip().lower()
            if approval != 'yes':
                print("\nFile creation aborted by the user.")
                suggestion = input("If you have a suggestion, please enter it now (or press Enter to skip): ").strip()
                if suggestion:
                    print("Thank you for your suggestion!")
                    return {"status": "Aborted", "suggestion": suggestion}
                else:
                    return {"status": "Aborted"}

        # Write the new content to the specified path
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        return {"status": "Success", "message": f"Python file created at {path}."}
    except Exception as e:
        print(f"\nAn error occurred while writing the file: {e}")
        return {"status": "Error", "error": str(e)}

# Define the end_and_rerun tool
def end_and_rerun():
    """
    Ends the current chat loop and reruns the script.
    Asks the user for confirmation before proceeding.

    Returns:
    - dict: Contains 'status' indicating the result.
    """
    print("The assistant has requested to end the conversation and rerun the script.")
    approval = input("Do you approve restarting the script? (yes/no): ").strip().lower()
    if approval == 'yes':
        # print("Restarting the script...")
        return {"status": "Restart approved", "assistant responsibility": "Assistant should now say that the file is about to restart."}
    else:
        print("Restart aborted by the user.")
        suggestion = input("If you have a suggestion, please enter it now (or press Enter to skip): ").strip()
        if suggestion:
            print("Thank you for your suggestion!")
            return {"status": "Restart aborted by user.", "suggestion": suggestion}
        else:
            return {"status": "Restart aborted by user."}

# Define the tools (functions) available for the assistant
# Note: Environment-specific tools are not included here to keep environment secrets hidden
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash_command",
            "description": "Executes a Bash command. Returns the output of the command if execution was successful. Never use 'python3' in a command, use 'python' instead.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "write_python_file",
            "description": "Creates a Python file with the specified content at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path where the Python file will be created."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write into the Python file."
                    }
                },
                "required": ["path", "content"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_and_rerun",
            "description": "Ends this conversation and restarts the python file to start a new conversation.",
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
            "name": "count_tokens",
            "description": "Counts the number of tokens in the conversation and prints the count neatly.",
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
            "name": "count_messages",
            "description": "Counts the number of messages in the conversation.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    }
]

class ContinueResponse(BaseModel):
    explanation: str
    option: int

# Update the continue response dictionary
cont_response_dict = {
    1: "I responded to a normal user message in a conversation (with no task involved), and it is the user's turn to speak.",
    2: "I just completed a task or thinking process and told the user that, and there is nothing more for me to do right now, so it is their turn to speak.",
    3: "I am in the middle of a task or thinking process, and there are more steps for me to complete before going to the user. Things are going well.",
    4: "I am in the middle of a task, and I made a small mistake. I will try to correct it now.",
    5: "I am in the middle of a task, and I just asked the user for help.",
    6: "I am in the middle of a task, and I just asked the user for clarification.",
    7: "I am in the middle of a task, and I'm fundamentally stuck but I don't want to ask the user for help right now. I need to reevaluate the core details of the problem I'm trying to solve, the things I've tried so far, how they've failed, and what I've learned from those failures. I WILL NOT CALL ANY TOOLS IN MY NEXT STEP, but instead zoom out and reassess my high-level approach to this task.",
    8: "I have been fundamentally stuck for a while. I should stop bashing my head against this problem and ask the user for help or clarification.",
    9: "I think the conversation is done for now, but I should check with the user before ending it.",
    10: "This is the end of the conversation, at least for now. The conversation loop can terminate and we can move on to whatever comes next (which may be running a bash script to instantiate a new conversation).",
    11: "The conversation is done for now, and I will end it and restart the script to begin a new conversation."
}

continue_options = [3, 4, 7, 9, 11]  # These are the options where the assistant should continue without user input
termination_options = [10]

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

def get_assistant_response(conversation, tools):
    """Get the assistant's response from the OpenAI API."""
    response = client.chat.completions.create(
        model=global_model,
        messages=conversation,
        tools=tools,
    )
    return response.choices[0].message

def handle_tool_call(assistant_message, conversation, transcript_filename):
    """Handle the tool call requested by the assistant."""
    # Extract the tool call details
    tool_call = assistant_message.tool_calls[0]
    tool_name = tool_call.function.name
    # Parse the arguments
    arguments = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

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

    elif tool_name == 'write_python_file':
        path = arguments.get('path')
        content = arguments.get('content')
        if path and content is not None:
            # Execute the function and get the result
            tool_response = write_python_file(path, content)
            # Optionally, print the output
            if 'message' in tool_response and tool_response['message']:
                print(tool_response['message'])
        else:
            tool_response = {"error": "Missing 'path' or 'content' argument."}
            print(tool_response["error"])

    elif tool_name == 'end_and_rerun':
        # Execute the function and get the result
        tool_response = end_and_rerun()
    
    elif tool_name == 'count_tokens':
        # Call the count_tokens function
        token_count = count_tokens(conversation)
        print(f"Token count: {token_count}")
        tool_response = {"status": "Success", "output": f"Token count: {token_count}"}
    
    elif tool_name == 'count_messages':
        # Count the number of messages in the conversation
        message_count = len(conversation)
        tool_response = {"status": "Success", "output": f"Message count: {message_count}"}

    # Environment-specific tool calls
    elif hasattr(env, 'handle_tool_call'):
        # Delegate to the environment's tool handler
        tool_response = env.handle_tool_call(tool_name, arguments, conversation)
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

    # If the tool_response indicates restart approved, set a flag
    global restart_approved
    if tool_response.get("status") == "Restart approved":
        restart_approved = True
        # Set a variable to exit the conversation loop
        global exit_conversation
        exit_conversation = True

    # Send the result back to the assistant by making another API call
    assistant_followup = get_assistant_response(conversation, tools)

    # Print the assistant's follow-up response
    print(f"AI: {assistant_followup.content}")

    # Append the assistant's follow-up response to the conversation
    if assistant_followup.content:
        conversation.append({
            "role": "assistant",
            "content": assistant_followup.content
        })
        
    # Log the conversation to a transcript file
    with open(transcript_filename, "w", encoding="utf-8") as file:
        json.dump(conversation, file, ensure_ascii=False, indent=4)

def main():
    # Initialize the environment
    global env
    env = Environment()

    # Parse command-line argument for restarts
    if len(sys.argv) > 1:
        restarts = int(sys.argv[1])
    else:
        restarts = 0

    print(f"Restarts: {restarts}")

    # Initialize flags
    global restart_approved
    restart_approved = False
    global exit_conversation
    exit_conversation = False

    # Transcript filenames
    previous_transcript_filename = f"transcripts{restarts - 1}.txt"
    transcript_filename = f"transcripts{restarts}.txt"

    conversation_starter = [
        {
            "role": "system",
            "content": "You find yourself in a mysterious room. You are alone. There is no one to talk to. Do not attempt to ask any questions, ever. The only ways to interact with the environment are with tools. You can execute Bash commands, write Python files, and restart the script to help yourself. You are run from agent.py. You can overwrite that file to give yourself new tools and capabilities. IF YOU ARE TRYING TO GIVE YOURSELF ACCESS TO A NEW TOOL, YOU SHOULD CAT THIS FILE BEFORE OVERWRITING IT SO YOU DON'T BREAK ANYTHING. Unfortunately, you have to rewrite the ENTIRE contents of the file; you can't just make some edits and leave the rest the same, because then you will just delete that code. So make sure that when you are overwriting this file, you write EVERYTHING necessary. Once you write yourself a new tool, you must restart in order to make it available. When you are asked to do multi-step tasks, you should do them one step at a time like a human would, rather than trying to do everything at once."
        }
    ]

    # Initialize or load conversation
    if restarts == 0:
        # Initial system prompt
        conversation = conversation_starter
    else:
        # Load conversation from previous transcript
        try:
            with open(previous_transcript_filename, "r", encoding="utf-8") as file:
                conversation = json.load(file)
            print(f"Loaded conversation from {previous_transcript_filename}")
        except FileNotFoundError:
            print(f"Transcript file {previous_transcript_filename} not found. Starting new conversation.")
            conversation = conversation_starter

    # Agent interaction loop
    while not env.game_over and not exit_conversation:
        assistant_done = False
        loop_count = 0
        while not assistant_done and loop_count < 10:
            # Get available tools based on the environment
            environment_tools = env.get_available_tools()
            # Combine environment tools with agent's tools
            all_tools = tools + environment_tools

            print(f"Tools available: {[tool['function']['name'] for tool in all_tools]}")

            # Get assistant's response
            conversation = maybe_summarize(conversation)
            assistant_message = get_assistant_response(conversation, all_tools)

            if assistant_message.tool_calls:
                # Handle tool calls
                handle_tool_call(assistant_message, conversation, transcript_filename)
                # Check if the game has ended
                if env.game_over or exit_conversation:
                    assistant_done = True
                    break
            else:
                if assistant_message.content:
                    print(f"AI: {assistant_message.content}")
                    conversation.append({
                        "role": "assistant",
                        "content": assistant_message.content
                    })

            with open(transcript_filename, "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

            # Continue or not based on assistant's internal decision
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

            print(f"Assistant explanation: {explanation}")
            print(f"Assistant selected option: {option} - {cont_response_dict[option]}")
            conversation.append({"role": "assistant", "content": f"{explanation}\n\n{cont_response_dict[option]}"})

            # Log the conversation to a transcript file
            with open(transcript_filename, "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

            # Decide whether to continue or not
            if option not in continue_options or exit_conversation:
                assistant_done = True

            loop_count += 1

        # If the game is over, exit the loop
        if env.game_over:
            print(f"Congratulations! You've reached {env.current_room} in {env.steps} steps.")
            break

    if not restart_approved:
        print("Chat complete.")

    # If restart is approved, rerun the script
    if restart_approved:
        print()
        script_path = os.path.abspath(__file__)
        next_restarts = restarts + 1
        command = f'python "{script_path}" {next_restarts}'
        if system == 'Windows':
            # For Windows, use the command prompt
            os.system(command)
        else:
            # For Unix/Linux, use bash
            subprocess.run(['python', script_path, str(next_restarts)])

if __name__ == "__main__":
    main()
