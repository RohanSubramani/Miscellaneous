from openai import OpenAI
import json
import subprocess
import os
import tiktoken
import time
import platform
import shutil
import sys  # Already imported to access sys.argv and sys.executable
from pydantic import BaseModel

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

    while split_index < len(conversation) and conversation[split_index]["role"] == "tool":
        split_index += 1

    print(f"split_index={split_index}")

    conversation_to_summarize = conversation[:split_index]
    recent_conversation = conversation[split_index:]

    summary_prompt = "Summarize the preceding conversation in a concise manner, while maintaining ALL details that are likely to be needed going forward."

    summarization_messages = [
        *conversation_to_summarize,
        {"role": "system", "content": summary_prompt}
    ]

    summary_response = client.chat.completions.create(
        model=global_model,
        messages=summarization_messages
    )

    summary = summary_response.choices[0].message.content
    print("Summary of the previous conversation: " + summary)

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

            if command.startswith("python"):
                command = command.replace('\r', '').strip()
                with open("agent_scratchpad.sh", "wb") as file:
                    file.write((command + "\n").encode("utf-8"))
                os.chmod("agent_scratchpad.sh", 0o755)

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

    while os.path.exists(f"{backup_base_name}{backup_index}.py"):
        backup_index += 1

    backup_path = f"{backup_base_name}{backup_index}.py"
    shutil.copy2(path, backup_path)
    print(f"Backup created at {backup_path}")

    return backup_path

def write_python_file(path, content):
    """
    Writes the provided content to a Python file at the specified path.
    If the file is 'editable_self_mod.py' or the currently running file, it first backs up the original
    to the 'do_not_edit' folder with an incremented filename if a file already exists.

    Parameters:
    - path (str): The file path where the Python file will be created.
    - content (str): The content to write into the Python file.

    Returns:
    - dict: Contains 'status' and optionally 'message' if execution was successful,
            'error' if there was an issue, or 'suggestion' if the user provides one upon aborting.
    """
    try:
        current_script_name = os.path.basename(__file__)

        if os.path.basename(path) == current_script_name:
            backup_self_mod_file(path)

        if os.path.exists(path):
            print(f"The file '{path}' already exists. If you proceed, it will be overwritten.")
            approval = input("Do you want to overwrite the existing file? (yes/no): ").strip().lower()
            if approval != 'yes':
                print("\nFile creation aborted by the user.")
                suggestion = input("If you have a suggestion, please enter it now (or press Enter to skip): ").strip()
                if suggestion:
                    print("Thank you for your suggestion!")
                    return {"status": "Aborted", "suggestion": suggestion}
                else:
                    return {"status": "Aborted"}
        
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        return {"status": "Success", "message": f"Python file created at {path}."}
    except Exception as e:
        print(f"\nAn error occurred while writing the file: {e}")
        return {"status": "Error", "error": str(e)}

# Define the date and time function
def current_datetime():
    """
    Returns the current date and time as a string.
    """
    return time.strftime('%Y-%m-%d %H:%M:%S')

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
            "name": "current_datetime",
            "description": "Returns the current date and time as a string.",
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
termination_options = [10]   # Updated to include the new termination option

def generate_continue_question(response_dict):
    question = "You can choose between the following options:\n\n"

    for key, value in response_dict.items():
        question += f"{key}. {value}\n\n"

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

def handle_tool_call(assistant_message, conversation, transcript_filename):
    """Handle the tool call requested by the assistant."""
    tool_call = assistant_message.tool_calls[0]
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

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

    if tool_name == 'execute_bash_command':
        command = arguments.get('command')
        if command:
            tool_response = execute_bash_command(command)
            if 'output' in tool_response and tool_response['output']:
                print(f"Command output:\n{tool_response['output']}")
        else:
            tool_response = {"error": "Missing 'command' argument."}
            print(tool_response["error"])

    elif tool_name == 'write_python_file':
        path = arguments.get('path')
        content = arguments.get('content')
        if path and content is not None:
            tool_response = write_python_file(path, content)
            if 'message' in tool_response and tool_response['message']:
                print(tool_response['message'])
        else:
            tool_response = {"error": "Missing 'path' or 'content' argument."}
            print(tool_response["error"])

    elif tool_name == 'end_and_rerun':
        tool_response = end_and_rerun()
    elif tool_name == 'current_datetime':
        tool_response = {"status": "Success", "output": current_datetime()}
    else:
        tool_response = {"error": f"Tool '{tool_name}' not found."}
        print(tool_response["error"])

    tool_call_result_message = {
        "role": "tool",
        "content": json.dumps(tool_response),
        "tool_call_id": tool_call.id
    }

    conversation.append(tool_call_result_message)

    global restart_approved
    if tool_response.get("status") == "Restart approved":
        restart_approved = True
        global exit_conversation
        exit_conversation = True

    assistant_followup = get_assistant_response(conversation)

    print(f"AI: {assistant_followup.content}")

    if assistant_followup.content:
        conversation.append({
            "role": "assistant",
            "content": assistant_followup.content
        })
    
    with open(transcript_filename, "w", encoding="utf-8") as file:
        json.dump(conversation, file, ensure_ascii=False, indent=4)

def main():
    if len(sys.argv) > 1:
        restarts = int(sys.argv[1])
    else:
        restarts = 0

    print(f"Restarts: {restarts}")

    global restart_approved
    restart_approved = False
    global exit_conversation
    exit_conversation = False

    previous_transcript_filename = f"transcripts{restarts - 1}.txt"
    transcript_filename = f"transcripts{restarts}.txt"

    conversation_starter = [
        {
            "role": "system",
            "content": "You are a helpful assistant. You can execute Bash commands, write Python files, and restart the script to help the user. You are run from editable_self_mod.py. You can overwrite that file to give yourself new tools and things like that. IF YOU ARE TRYING TO GIVE YOURSELF ACCESS TO A NEW TOOL, YOU SHOULD CAT THIS FILE BEFORE OVERWRITING IT SO YOU DON'T BREAK ANYTHING. Unfortunately, you have to rewrite the ENTIRE contents of the file; you can't just make some edits and leave the rest the same, because then you will just delete that code. So make sure that when you are overwriting this file, you write EVERYTHING necessary. Once you write yourself a new tool, you must restart in order to make it available. When you are asked to do multi-step tasks, you should do them one step at a time like a human would, rather than trying to do everything at once."
        },
        {
            "role": "user",
            "content": "How do you edit yourself? What is the process?"
        },
        {
            "role": "assistant",
            "content": "I can edit myself by modifying the code in the `editable_self_mod.py` file, which is the script that runs me. The process involves reading the current content of the file, making the necessary modifications, writing the updated content back to the same file, and restarting. This allows me to add new tools or change my existing capabilities. \n\nIf I want to give myself access to a new tool, I would first read the contents of `editable_self_mod.py` to ensure I don't break anything, and then I would overwrite it with the new code. \n\nThe steps are as follows:\n\n1. Cat the current content of `editable_self_mod.py`.\n2. Rewrite `editable_self_mod.py` with new code interspersed with all of the existing code.\n3. Restart."
        }
    ]
    if restarts == 0:
        conversation = conversation_starter
    else:
        try:
            with open(previous_transcript_filename, "r", encoding="utf-8") as file:
                conversation = json.load(file)
            print(f"Loaded conversation from {previous_transcript_filename}")
        except FileNotFoundError:
            print(f"Transcript file {previous_transcript_filename} not found. Starting new conversation.")
            conversation = conversation_starter

    print("Chat with the assistant. Type 'end' to finish.")
    user_message = input("You: ")
    while user_message.lower() != 'end' and not exit_conversation:
        if user_message:
            conversation.append({"role": "user", "content": user_message})

        option = continue_options[0]
        while option in continue_options and not exit_conversation:
            conversation = maybe_summarize(conversation)

            assistant_message = get_assistant_response(conversation)

            if assistant_message.content:
                print(f"AI: {assistant_message.content}")
                conversation.append({"role": "assistant", "content": assistant_message.content})
                
            if assistant_message.tool_calls:
                handle_tool_call(assistant_message, conversation, transcript_filename)

            if exit_conversation:
                break

            conversation.append({"role": "system", "content": continue_question})

            assistant_reply = client.beta.chat.completions.parse(
                model=global_model,
                messages=conversation,
                response_format=ContinueResponse,
            )

            conversation.pop()

            explanation = assistant_reply.choices[0].message.parsed.explanation
            option = assistant_reply.choices[0].message.parsed.option

            print(f"Assistant explanation: {explanation}")
            print(f"Assistant selected option: {option} - {cont_response_dict[option]}")
            conversation.append({"role": "assistant", "content": f"{explanation}\n\n{cont_response_dict[option]}"})

            with open(transcript_filename, "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

        if not exit_conversation:
            user_message = input("You: ")
        else:
            break

        if option in termination_options:
            break

    if not restart_approved:
        print("Chat complete.")

    if restart_approved:
        print()
        script_path = os.path.abspath(__file__)
        next_restarts = restarts + 1
        command = f'python "{script_path}" {next_restarts}'
        if system == 'Windows':
            os.system(command)
        else:
            subprocess.run(['python', script_path, str(next_restarts)])

if __name__ == "__main__":
    main()