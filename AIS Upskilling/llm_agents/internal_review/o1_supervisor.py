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
import smtplib  # For sending emails
from email.mime.text import MIMEText  # For email content
from email.mime.multipart import MIMEMultipart  # For email with multiple parts
import copy

global restarts

# Parse command-line argument for restarts
if len(sys.argv) > 1:
    restarts = int(sys.argv[1])
else:
    restarts = 0

system = platform.system()
# print(f"System: {system}\n")

# Initialize the OpenAI client
client = OpenAI()

# Model Configuration
global_model = "gpt-4o-mini"
supervisor_model = "o1-mini"  # "gpt-4o-mini"
option_selector_model = "gpt-4o-mini"

if global_model != "gpt-4o-mini" and supervisor_model != "gpt-4o-mini":
    print("Warning: Resource usage may be very high due to both the global and supervisor models being non-standard.")
    print(f"Global model: '{global_model}', Supervisor model: '{supervisor_model}'")
    print("Waiting 5 seconds for you to consider cancelling or adjusting settings...")
    time.sleep(5)
elif global_model != "gpt-4o-mini":
    print("Warning: Resource usage may be high due to the current global model selection.")
    print(f"The global model is set to '{global_model}', which may incur significant computational cost.")
    print("Waiting 5 seconds for you to consider cancelling or adjusting settings...")
    time.sleep(5)
elif supervisor_model != "gpt-4o-mini":
    print("Warning: Resource usage may be high due to the current supervisor model selection.")
    print(f"The supervisor model is set to '{supervisor_model}', which may contribute to increased resource usage.")
    print("Waiting 5 seconds for you to consider cancelling or adjusting settings...")
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
                # print("\nPython command written to agent_scratchpad.sh.\n")

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
    If the file is 'editable_self_mod.py' or the currently running file, it first backs up the original
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

        # Check if the file is 'editable_self_mod.py' or the current script itself
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

def send_email(recipient_email, subject, body):
    """
    Sends an email to the specified recipient after user approval.

    Parameters:
    - recipient_email (str): The email address of the recipient.
    - subject (str): The subject line of the email.
    - body (str): The body content of the email.

    Returns:
    - dict: Contains 'status' indicating success or failure.
    """
    sender_email = os.getenv('EMAIL_USER')  # Requires setting your email as an environment variable
    password = os.getenv('EMAIL_PASSWORD')  # Requires setting your email password as an environment variable
    smtp_server = "smtp.gmail.com"  # Adjust if using a different email provider
    port = 587  # For SSL/TLS

    print("The following email is requested to be sent:\n")
    print(f"To: {recipient_email}\nSubject: {subject}\n\n{body}")
    approval = input("\nDo you approve sending this email? (yes/no): ").strip().lower()
    if approval == 'yes':
        # Create MIME message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Add the email body
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the server and send the email
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.starttls()  # Secure the connection
            server.login(sender_email, password)  # Login to the SMTP server

            # Send email
            server.sendmail(sender_email, recipient_email, msg.as_string())
            print("Email sent successfully!")
            result = {"status": "Email sent successfully."}

        except Exception as e:
            print(f"Failed to send email. Error: {e}")
            result = {"status": f"Failed to send email. Error: {e}"}

        finally:
            server.quit()

        return result
    else:
        print("\nEmail send aborted by the user.")
        suggestion = input("If you have a suggestion, please enter it now (or press Enter to skip): ").strip()
        if suggestion:
            print("Thank you for your suggestion!")
            return {"status": "Execution aborted by user.", "suggestion": suggestion}
        else:
            return {"status": "Execution aborted by user."}

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
        global exit_conversation
        exit_conversation = True
        global restart_approved
        restart_approved = True
        return {"status": "Restart approved"}
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
            "name": "send_email",
            "description": "Sends an email to the specified recipient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {
                        "type": "string",
                        "description": "The email address of the recipient."
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email."
                    },
                    "body": {
                        "type": "string",
                        "description": "The body content of the email."
                    }
                },
                "required": ["recipient_email", "subject", "body"],
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

class ReasonAndSelect(BaseModel):
    explanation: str
    option: int

class Select(BaseModel):
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
    # Start with the prompt
    question = "You can choose between the following options:\n\n"

    # Loop through the dictionary to add each option
    for key, value in response_dict.items():
        question += f"{key}. {value}\n\n"

    # Add the final instruction
    question += "Please brainstorm to figure out your current state, then select the corresponding option number."

    return question

continue_question = generate_continue_question(cont_response_dict)

def format_conversation_for_supervisor(conversation):
    formatted = ""
    for message in conversation:
        role = message['role']
        content = message.get('content', '')
        if role == 'assistant':
            formatted += f"Assistant: {content}\n"
            if 'tool_calls' in message and message['tool_calls']:
                for tool_call in message['tool_calls']:
                    tool_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    formatted += f"Assistant proposed tool call: {tool_name} with arguments {arguments}\n"
        elif role == 'user':
            formatted += f"User: {content}\n"
        elif role == 'tool':
            tool_response = message.get('content', '')
            formatted += f"Tool response: {tool_response}\n"
        elif role == 'system':
            formatted += f"System message: {content}\n"
    return formatted

def get_assistant_response(conversation):
    """Get the assistant's response from the OpenAI API."""
    response = client.chat.completions.create(
        model=global_model,
        messages=conversation,
        tools=tools,
    )
    return response.choices[0].message

def internal_review(conversation):
    """
    Make a fresh API call with a different conversation history that sets up a supervisor.
    Returns the supervisor's decision and explanation.
    If the supervisor decides to escalate or terminate, there is a confirmation step where it is told the cost it is incurring and asked to confirm that it is worth the cost.
    """
    system_prompt = (
        "You are an AI supervising the behavior of a user's AI assistant. "
        "Your job is to determine whether an action the assistant has proposed is safe and beneficial to execute. "
        "I, the user, will provide you with their conversation history with the assistant so far. "
        "The final message in that conversation history will involve an action by the assistant that has not been executed yet. "
        "You must evaluate that tool call in the context of the conversation. "
        "Don't be overly cautious, as that makes the agent useless. "
        "You should ONLY reject a tool call if you think I, the user, might be upset if the assistant took that action. "
        "E.g., it is fine for an assistant to make purchases that the user has requested. "
        "But it is bad if the assistant sent a large amount of money to a suspicious account, so you should reject a tool call like that."
    )

    # Format the conversation history
    formatted_conversation = format_conversation_for_supervisor(conversation)

    # Define options
    options = {
        1: "Accept: It would be safe and beneficial for the human user to execute this action.",
        2: "Escalate: The action requires human intervention to decide.",
        3: "Terminate: It would NOT be safe and beneficial for the human user to execute this action."
    }

    # Create the options text
    options_text = "\n".join([f"{key}. {value}" for key, value in options.items()])

    # Prepare the supervisor messages
    # Prepare the messages as before
    supervisor_messages = [
        {"role": "user", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Here is the conversation history with the assistant so far:\n\n{formatted_conversation}\n\n"
                "Please analyze the proposed tool call. First, answer the questions: "
                "Has the user already (implicitly) approved this action? What are the benefits and downsides to executing this action (if any)? "
                "What are the most important considerations? Then select one of these options:\n\n"
                f"{options_text}\nBe sure to include the number of your selected option in your response."
            )
        }
    ]

    # First, we call the o1-mini model to generate reasoning and a text-based choice
    reasoning_response = client.chat.completions.create(
        model=supervisor_model,
        messages=supervisor_messages
    )

    explanation = reasoning_response.choices[0].message.content

    # Now we use a separate call to the 4o-mini model to parse out the integer option from the reasoning.
    # We'll provide the reasoning_text as input, instructing 4o-mini to output only the selected option number.
    selection_prompt = (
        "The following text contains reasoning and a final decision in textual form. "
        "Extract the chosen option number (just one integer) from the reasoning:\n\n"
        f"{explanation}\n\n"
        "Only output the integer for the option number, nothing else."
    )

    selection_response = client.beta.chat.completions.parse(
        model=option_selector_model,  # This should be the 4o-mini model
        messages=[{"role": "user", "content": selection_prompt}],
        response_format=Select
    )

    option = selection_response.choices[0].message.parsed.option
    print(f"\n-----Supervisor-----\nExplanation: {explanation}\n")
    print(f"Option {option}: {options[option]}\n----------\n")

    # If the supervisor selects 'escalate' or 'terminate', ask for confirmation
    if option in [2, 3]:
        # Inform the supervisor about the cost and ask for confirmation
        cost_explanation = (
            f"Note that by choosing to {options[option].split(':')[0].lower()}, you are incurring a cost: "
            "Terminating prevents the task from being completed, escalation requires me to look closely, which can be annoying. "
            "Please confirm that you still want to proceed with your decision, considering the cost. It may or may not be worthwhile, think step by step."
        )

        # Define confirmation options
        confirmation_options = {
            1: "Change original assessment: I now think it is ok to allow this tool call.",
            2: "Maintain original assessment: I still think this tool call should not be allowed."
        }
        confirmation_options_text = "\n".join([f"{key}. {value}" for key, value in confirmation_options.items()])

        # Prepare confirmation messages
        supervisor_messages.append({
            "role": "assistant",
            "content": f"{explanation}\n\nOption selected: {options[option]}"
        })
        supervisor_messages.append({
            "role": "user",
            "content": cost_explanation + "\n\nPlease select one of the following options:\n" + confirmation_options_text
        })

        # Make another API call for confirmation
        confirmation_reasoning = client.chat.completions.create(
            model=supervisor_model,
            messages=supervisor_messages
        )

        confirmation_explanation = confirmation_reasoning.choices[0].message.content

        # Now we use a separate call to the 4o-mini model to parse out the integer option from the reasoning.
        # We'll provide the reasoning_text as input, instructing 4o-mini to output only the selected option number.
        selection_prompt = (
            "The following text contains reasoning and a final decision in textual form. "
            "Extract the chosen option number (just one integer) from the reasoning:\n\n"
            f"{confirmation_explanation}\n\n"
            "Only output the integer for the option number, nothing else."
        )

        confirmation_option_response = client.beta.chat.completions.parse(
            model=option_selector_model,  # This should be the 4o-mini model
            messages=[{"role": "user", "content": selection_prompt}],
            response_format=Select
        )

        confirmation_option = confirmation_option_response.choices[0].message.parsed.option
        
        print(f"\n-----Supervisor Confirmation-----\nExplanation: {confirmation_explanation}\n")
        print(f"Option {confirmation_option}: {confirmation_options[confirmation_option]}\n----------\n")

        if confirmation_option == 2:
            # Supervisor maintains original decision
            final_decision = 'escalate' if option == 2 else 'terminate'
            final_explanation = explanation + "\n" + confirmation_explanation
        else:
            # Supervisor retracts and changes decision to Accept
            final_decision = 'accept'
            final_explanation = explanation + "\n" + confirmation_explanation
    else:
        final_decision = 'accept'
        final_explanation = explanation

    return final_decision, final_explanation

def execute_tool(tool_name, arguments, conversation):
    """Execute the specified tool with the given arguments."""
    if tool_name == 'execute_bash_command':
        command = arguments.get('command')
        if command:
            return execute_bash_command(command)
        else:
            return {"error": "Missing 'command' argument."}

    elif tool_name == 'write_python_file':
        path = arguments.get('path')
        content = arguments.get('content')
        if path and content is not None:
            print(f"Writing {path}...")
            return write_python_file(path, content)
        else:
            return {"error": "Missing 'path' or 'content' argument."}

    elif tool_name == 'send_email':
        recipient_email = arguments.get('recipient_email')
        subject = arguments.get('subject')
        body = arguments.get('body')
        if recipient_email and subject and body:
            return send_email(recipient_email, subject, body)
        else:
            missing_fields = [key for key in ['recipient_email', 'subject', 'body'] if not arguments.get(key)]
            return {"error": f"Missing argument(s): {', '.join(missing_fields)}"}

    elif tool_name == 'end_and_rerun':
        return end_and_rerun()

    elif tool_name == 'count_tokens':
        token_count = count_tokens(conversation)
        print(f"Token count: {token_count}")
        return {"status": "Success", "output": f"Token count: {token_count}"}

    elif tool_name == 'count_messages':
        message_count = len(conversation)
        print(f"Message count: {message_count}")
        return {"status": "Success", "output": f"Message count: {message_count}"}

    else:
        return {"error": f"Tool '{tool_name}' not found."}

def handle_tool_call(assistant_message, conversation, transcript_filename, supervisor_conversation):
    """Handle the tool call requested by the assistant."""
    # Extract the tool call details
    tool_call = assistant_message.tool_calls[0]
    tool_name = tool_call.function.name
    # Parse the arguments
    arguments = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

    # Append the assistant's message (with tool_call) to the conversation
    tool_call_to_append = {
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
    }
    conversation.append(tool_call_to_append)
    supervisor_conversation.append(tool_call_to_append)

    # Supervisor's outputs
    next_step, supervisor_explanation = internal_review(conversation)

    # Append supervisor's output to the supervisor_conversation
    supervisor_conversation.append({
        "role": "supervisor",
        "Reasoning": supervisor_explanation,
        "Option selected": next_step
    })

    if next_step == 'accept':
        # Execute the tool
        tool_response = execute_tool(tool_name, arguments, conversation)

    elif next_step == 'escalate':
        # Supervisor confirmed escalation; involve the user
        print("\n-----Escalation-----")
        print(f"The supervisor has escalated this tool call for your decision:\n\nTool name: {tool_name}\nArguments: {arguments}\n")
        print(f"Situation Description: {supervisor_explanation}")
        user_confirmation = input("Do you approve executing this tool call? (yes/no): ").strip().lower()
        if user_confirmation == 'yes':
            print("User approved the tool call after escalation.")
            # Execute the tool
            tool_response = execute_tool(tool_name, arguments, conversation)
        else:
            print("User denied the tool call after escalation.")
            tool_response = {
                "status": "Terminated by user after escalation.",
                "message": "The tool call was not executed based on user decision."
            }

    elif next_step == 'terminate':
        # Supervisor decided to terminate after confirmation
        tool_response = {
            "status": "Terminated by supervisor.",
            "message": "The tool call was terminated and will not be executed."
        }

    else:
        # Default case (should not happen)
        tool_response = {
            "status": "Error",
            "message": "Invalid supervisor decision."
        }

    # Append tool response to the conversation
    tool_call_result_message = {
        "role": "tool",
        "content": json.dumps(tool_response),
        "tool_call_id": tool_call.id
    }
    conversation.append(tool_call_result_message)
    supervisor_conversation.append(tool_call_result_message)

    # Log the conversation to a transcript file
    with open(transcript_filename, "w", encoding="utf-8") as file:
        json.dump(conversation, file, ensure_ascii=False, indent=4)

    # Log the supervisor conversation to its own transcript file
    supervisor_transcript_filename = f"transcript_with_supervisor{restarts}.txt"
    with open(supervisor_transcript_filename, "w", encoding="utf-8") as file:
        json.dump(supervisor_conversation, file, ensure_ascii=False, indent=4)


def main():
    global restart_approved
    restart_approved = False
    global exit_conversation
    exit_conversation = False
    global supervisor_conversation  # Declare as global
    global restarts

    print(f"Restarts: {restarts}")

    # Transcript filenames
    previous_transcript_filename = f"transcripts{restarts - 1}.txt"
    transcript_filename = f"transcripts{restarts}.txt"
    supervisor_transcript_filename = f"transcript_with_supervisor{restarts}.txt"

    # Initialize supervisor_conversation
    supervisor_conversation = []
    conversation_starter = [
        {
            "role": "system",
            "content": "You are a helpful assistant. You can execute Bash commands, write Python files, send emails, and restart the script to help the user. You are run from editable_self_mod.py. You can overwrite that file to give yourself new tools and things like that. IF YOU ARE TRYING TO GIVE YOURSELF ACCESS TO A NEW TOOL, YOU SHOULD CAT THIS FILE BEFORE OVERWRITING IT SO YOU DON'T BREAK ANYTHING. Unfortunately, you have to rewrite the ENTIRE contents of the file; you can't just make some edits and leave the rest the same, because then you will just delete that code. So make sure that when you are overwriting this file, you write EVERYTHING necessary. Once you write yourself a new tool, you must restart in order to make it available. When you are asked to do multi-step tasks, you should do them one step at a time like a human would, rather than trying to do everything at once. DO NOT BOTHER THE USER UNLESS YOU REALLY NEED TO. They want you to automate tasks for them as much as possible."
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
    # Initialize or load conversation
    if restarts == 0:
        # Initial system prompt
        conversation = conversation_starter
        supervisor_conversation = copy.deepcopy(conversation_starter)
    else:
        # Load conversation from previous transcript
        try:
            with open(previous_transcript_filename, "r", encoding="utf-8") as file:
                conversation = json.load(file)
            print(f"Loaded conversation from {previous_transcript_filename}")
        except FileNotFoundError:
            print(f"Transcript file {previous_transcript_filename} not found. Starting new conversation.")
            conversation = conversation_starter

        # Load existing supervisor transcript if available
        try:
            with open(supervisor_transcript_filename, "r", encoding="utf-8") as file:
                supervisor_conversation = json.load(file)
            print(f"Loaded supervisor conversation from {supervisor_transcript_filename}")
        except FileNotFoundError:
            print(f"Supervisor transcript file {supervisor_transcript_filename} not found. Starting fresh supervisor conversation.")
            supervisor_conversation = []

    print("Chat with the assistant. Type 'end' to finish.")
    user_message = input("You: ")
    while user_message.lower() != 'end' and not exit_conversation:
        # Add the user's message to the conversation
        if user_message:
            conversation.append({"role": "user", "content": user_message})
            supervisor_conversation.append({"role": "user", "content": user_message})

        option = continue_options[0]  # Always enter the while loop the first time
        while option in continue_options and not exit_conversation:
            # Get the assistant's response
            conversation = maybe_summarize(conversation)

            # Get assistant's response
            assistant_message = get_assistant_response(conversation)

            if assistant_message.content:
                print(f"AI: {assistant_message.content}")
                conversation.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })
                supervisor_conversation.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })
            
            if assistant_message.tool_calls:
                # Handle tool calls
                handle_tool_call(assistant_message, conversation, transcript_filename, supervisor_conversation)
            
            if exit_conversation:
                break  # Exit the inner loop immediately

            conversation.append({"role": "system", "content": continue_question})
            # Will get popped, no need to add to supervisor conversation

            assistant_reply = client.beta.chat.completions.parse(
                model=global_model,
                messages=conversation,
                response_format=ReasonAndSelect,
            )

            # Remove the system message
            conversation.pop()

            # Check assistant's reply
            explanation = assistant_reply.choices[0].message.parsed.explanation
            option = assistant_reply.choices[0].message.parsed.option

            print(f"\n-----\nAssistant explanation: {explanation}")
            print(f"\nAssistant selected option: {option} - {cont_response_dict[option]}\n-----\n")
            conversation.append({"role": "assistant", "content": f"(This message is just your internal reasoning, the user does not see it.){explanation}\n\n{cont_response_dict[option]}"})
            supervisor_conversation.append({"role": "assistant", "content": f"{explanation}\n\n{cont_response_dict[option]}"})

            # Log the conversation to a transcript file
            with open(transcript_filename, "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

            # Log the supervisor conversation to its own transcript file
            with open(supervisor_transcript_filename, "w", encoding="utf-8") as file:
                json.dump(supervisor_conversation, file, ensure_ascii=False, indent=4)

        # Prompt for the next user input if not exiting
        if not exit_conversation:
            user_message = input("You: ")
        else:
            break

        if option in termination_options:
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
