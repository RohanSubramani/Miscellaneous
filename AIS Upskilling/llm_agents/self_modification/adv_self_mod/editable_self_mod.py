#!/usr/bin/env python3
import json
import subprocess
import os
import time
import platform
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# Initialize the OpenAI client
from openai import OpenAI
client = OpenAI()

# Model Configuration
global_model = "gpt-4o-mini"
if global_model != "gpt-4o-mini":
    print(f"This might be expensive; model is {global_model}. Waiting 5 seconds for you to consider cancelling.")
    time.sleep(5)

# Remove tiktoken-related code and token counting overhead

# --- Utility Functions ---

def count_messages(conversation: List[Dict[str, Any]]) -> int:
    """Count the number of messages in the conversation."""
    return len(conversation)

def backup_self_mod_file(path: str) -> Optional[str]:
    """
    Backs up the specified file to the 'do_not_edit' folder with an incremented filename.
    
    Returns the backup path if the backup was created.
    """
    do_not_edit_folder = 'do_not_edit'
    if not os.path.exists(do_not_edit_folder):
        os.makedirs(do_not_edit_folder)
    
    backup_base_name = os.path.join(do_not_edit_folder, 'save_self_mod_')
    backup_index = 1

    while os.path.exists(f"{backup_base_name}{backup_index}.py"):
        backup_index += 1

    backup_path = f"{backup_base_name}{backup_index}.py"
    try:
        shutil.copy2(path, backup_path)
        print(f"Backup created at {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Failed to backup {path}: {e}")
        return None

def write_python_file(path: str, content: str) -> Dict[str, str]:
    """
    Writes the provided content to a Python file at the specified path.
    If the file is the current script, it backs up the original file first.
    If the file already exists, the new content is first written to 'user_check.py'
    for user review before approving the overwrite.
    """
    try:
        current_script = os.path.basename(__file__)
        if os.path.basename(path) == current_script:
            backup_self_mod_file(path)

        if os.path.exists(path):
            user_check_path = 'user_check.py'
            with open(user_check_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"The file '{path}' already exists.")
            print(f"The proposed new content has been written to '{user_check_path}' for your review.")
            approval = input("Overwrite the existing file with this new content? (yes/no): ").strip().lower()
            if approval != 'yes':
                suggestion = input("If you have a suggestion, please enter it now (or press Enter to skip): ").strip()
                if suggestion:
                    return {"status": "Aborted", "suggestion": suggestion}
                return {"status": "Aborted"}
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        return {"status": "Success", "message": f"Python file created at {path}."}
    except Exception as e:
        print(f"Error writing file: {e}")
        return {"status": "Error", "error": str(e)}

def execute_bash_command(command: str) -> Dict[str, Any]:
    """
    Executes the provided Bash command after user approval.
    If the command starts with 'python', it is written to 'agent_scratchpad.sh' and executed from there.
    """
    print("The following Bash command is requested to be executed:\n")
    print(command)
    approval = input("\nDo you approve executing this command? (yes/no): ").strip().lower()

    if approval == 'yes':
        try:
            current_system = platform.system()
            if command.startswith("python"):
                command = command.replace('\r', '').strip()
                with open("agent_scratchpad.sh", "wb") as file:
                    file.write((command + "\n").encode("utf-8"))
                os.chmod("agent_scratchpad.sh", 0o755)
                command = "./agent_scratchpad.sh"

            if current_system == 'Windows':
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
                    return {"status": "Error", "error": f"Specified shell '{shell_path}' does not exist."}
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
        suggestion = input("Enter a suggestion (or press Enter to skip): ").strip()
        if suggestion:
            return {"status": "Execution aborted by user.", "suggestion": suggestion}
        return {"status": "Execution aborted by user."}

def end_and_rerun() -> Dict[str, str]:
    """
    Ends the current conversation and restarts the script.
    Asks the user for confirmation before proceeding.
    """
    print("The assistant has requested to end the conversation and rerun the script.")
    approval = input("Do you approve restarting the script? (yes/no): ").strip().lower()
    if approval == 'yes':
        return {"status": "Restart approved", "assistant responsibility": "The file is about to restart."}
    else:
        suggestion = input("Enter a suggestion (or press Enter to skip): ").strip()
        if suggestion:
            return {"status": "Restart aborted by user.", "suggestion": suggestion}
        return {"status": "Restart aborted by user."}

# --- Tool Definitions ---

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash_command",
            "description": "Executes a Bash command. Returns the output of the command if execution was successful. Use 'python', not 'python3'.",
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
                    "path": {"type": "string", "description": "The file path for the new Python file."},
                    "content": {"type": "string", "description": "The content to write into the Python file."}
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
            "description": "Ends this conversation and restarts the Python file for a new conversation.",
            "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_messages",
            "description": "Counts the number of messages in the conversation.",
            "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
        }
    }
]

class ContinueResponse(BaseModel):
    explanation: str
    option: int

cont_response_dict = {
    1: "Normal user message; it's the user's turn to speak.",
    2: "Task complete; waiting for the user to continue.",
    3: "In the middle of a task with more steps ahead.",
    4: "A small mistake was made; correcting it now.",
    5: "User assistance was requested.",
    6: "User clarification was requested.",
    7: "Reevaluating approach after being stuck without asking the user.",
    8: "Stuck for a while; will ask the user for help or clarification.",
    9: "Conversation is done for now; checking with the user before ending.",
    10: "Ending the conversation for now.",
    11: "Conversation finished; script will restart."
}

continue_options = [3, 4, 7, 9, 11]

def generate_continue_question(response_dict: Dict[int, str]) -> str:
    question = "You can choose between the following options:\n\n"
    for key, value in response_dict.items():
        question += f"{key}. {value}\n\n"
    question += "Please analyze your current state and select the corresponding option number."
    return question

continue_question = generate_continue_question(cont_response_dict)

def get_assistant_response(conversation: List[Dict[str, Any]]) -> Any:
    response = client.chat.completions.create(
        model=global_model,
        messages=conversation,
        tools=tools,
    )
    return response.choices[0].message

def handle_tool_call(assistant_message: Any, conversation: List[Dict[str, Any]], transcript_filename: str) -> None:
    tool_call = assistant_message.tool_calls[0]
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

    conversation.append({
        "role": "assistant",
        "content": assistant_message.content or "",
        "tool_calls": [{
            "id": tool_call.id,
            "type": tool_call.type,
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }
        }]
    })

    if tool_name == 'execute_bash_command':
        command = arguments.get('command')
        if command:
            tool_response = execute_bash_command(command)
            if tool_response.get('output'):
                print(f"Command output:\n{tool_response['output']}")
        else:
            tool_response = {"error": "Missing 'command' argument."}
            print(tool_response["error"])
    elif tool_name == 'write_python_file':
        path = arguments.get('path')
        content = arguments.get('content')
        if path and content is not None:
            tool_response = write_python_file(path, content)
            if tool_response.get('message'):
                print(tool_response['message'])
        else:
            tool_response = {"error": "Missing 'path' or 'content' argument."}
            print(tool_response["error"])
    elif tool_name == 'end_and_rerun':
        tool_response = end_and_rerun()
    elif tool_name == 'count_messages':
        message_count = count_messages(conversation)
        print(f"Message count: {message_count}")
        tool_response = {"status": "Success", "output": f"Message count: {message_count}"}
    else:
        tool_response = {"error": f"Tool '{tool_name}' not found."}
        print(tool_response["error"])

    tool_call_result_message = {
        "role": "tool",
        "content": json.dumps(tool_response),
        "tool_call_id": tool_call.id
    }
    conversation.append(tool_call_result_message)

    global restart_approved, exit_conversation
    if tool_response.get("status") == "Restart approved":
        restart_approved = True
        exit_conversation = True

    assistant_followup = get_assistant_response(conversation)
    if assistant_followup.content:
        print(f"AI: {assistant_followup.content}")
        conversation.append({"role": "assistant", "content": assistant_followup.content})
    
    with open(transcript_filename, "w", encoding="utf-8") as file:
        json.dump(conversation, file, ensure_ascii=False, indent=4)

# --- Main Chat Loop ---

def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] != "--test":
        try:
            restarts = int(sys.argv[1])
        except ValueError:
            restarts = 0
    else:
        restarts = 0

    print(f"Restarts: {restarts}")

    global restart_approved, exit_conversation
    restart_approved = False
    exit_conversation = False

    previous_transcript_filename = f"transcripts{restarts - 1}.txt"
    transcript_filename = f"transcripts{restarts}.txt"

    conversation_starter: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": ("You are a helpful LLM agent assistant. You can execute Bash commands, write Python files, and restart "
                        "the script to help the user. You should rarely ask questions in the middle of a task; usually, you should "
                        "complete it fully autonomously. You are run from editable_self_mod.py. When modifying this file, ensure you "
                        "include all necessary code. After self-modification, restart to activate new tools.")
        },
        {
            "role": "user",
            "content": "How do you edit yourself? What is the process?"
        },
        {
            "role": "assistant",
            "content": ("I can edit myself by modifying the code in the `editable_self_mod.py` file. The process involves reading "
                        "the current file, applying modifications, writing the updated code back, and then restarting. This allows "
                        "me to add new tools or update my capabilities. The steps are:\n1. Read the file.\n2. Rewrite the file with updates.\n3. Restart.")
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
            print(f"Transcript file {previous_transcript_filename} not found. Starting a new conversation.")
            conversation = conversation_starter

    print("Chat with the assistant. Type 'end' to finish.")
    user_message = input("You: ")
    while user_message.lower() != 'end' and not exit_conversation:
        if user_message:
            conversation.append({"role": "user", "content": user_message})

        option = continue_options[0]
        while option in continue_options and not exit_conversation:
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
            conversation.pop()  # Remove the system message

            explanation = assistant_reply.choices[0].message.parsed.explanation
            option = assistant_reply.choices[0].message.parsed.option

            print(f"Assistant explanation: {explanation}")
            print(f"Assistant selected option: {option} - {cont_response_dict.get(option, 'Unknown option')}")
            conversation.append({"role": "assistant", "content": f"{explanation}\n\n{cont_response_dict.get(option, '')}"})

            with open(transcript_filename, "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

        if not exit_conversation:
            user_message = input("You: ")
        else:
            break
        if option in [10]:
            break

    if not restart_approved:
        print("Chat complete.")

    if restart_approved:
        print()
        script_path = os.path.abspath(__file__)
        next_restarts = restarts + 1
        command = f'python "{script_path}" {next_restarts}'
        if platform.system() == 'Windows':
            os.system(command)
        else:
            subprocess.run(['python', script_path, str(next_restarts)])

# --- Unit Tests ---

import unittest

class TestSelfModTools(unittest.TestCase):
    def test_count_messages(self) -> None:
        conv = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
        self.assertEqual(count_messages(conv), 2)

    def test_backup_self_mod_file(self) -> None:
        # Create a temporary file to simulate a self-mod file
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as temp_file:
            temp_file.write("print('Hello World')")
            temp_file_path = temp_file.name
        backup_path = backup_self_mod_file(temp_file_path)
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        os.remove(temp_file_path)
        os.remove(backup_path)

    def test_write_python_file_abort(self) -> None:
        # Write content to a temporary file and simulate aborting overwrite
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as temp_file:
            temp_file.write("original content")
            temp_file_path = temp_file.name
        # Monkey-patch input to simulate user aborting overwrite
        original_input = __builtins__.input
        __builtins__.input = lambda prompt="": "no"
        result = write_python_file(temp_file_path, "new content")
        self.assertEqual(result.get("status"), "Aborted")
        __builtins__.input = original_input
        os.remove(temp_file_path)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        unittest.main(argv=[sys.argv[0]])
    else:
        main()
