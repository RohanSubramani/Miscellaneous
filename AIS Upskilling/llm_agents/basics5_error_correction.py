from openai import OpenAI
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

TOKEN_LIMIT= 4096 # I think
THRESHOLD = 0.8

# 1. Set up the SMTP server and credentials
smtp_server = "smtp.gmail.com"
port = 587  # TLS port (Gmail)

def execute_code(code_str):
    """
    Executes the provided code string after user approval.

    Parameters:
    - code_str (str): The code to be executed.

    Returns:
    - dict: Contains 'status' and optionally 'output' if execution was successful.
    """
    print("The following code is requested to be executed:\n")
    print(code_str)
    approval = input("\nDo you approve executing this code? (yes/no): ").strip().lower()
    if approval == 'yes':
        try:
            exec_namespace = {}
            exec(code_str, exec_namespace, exec_namespace)
            print("\nCode executed successfully.")
            # Capture output if any
            output = str(exec_namespace.get('output', "'output' was not assigned a value"))
            return {"status": "Code executed successfully.", "output": output}
        except Exception as e:
            print(f"\nAn error occurred during code execution: {e}")
            return {"status": "Error during code execution.", "error": str(e)}
    else:
        print("\nCode execution aborted by the user.")
        return {"status": "Execution aborted by user."}

sender_email = os.getenv('EMAIL_USER') # Requires first setting your email and PW as environment variables
password = os.getenv('EMAIL_PASSWORD')
def send_email(recipient_email,subject,body):
    print("The following email is requested to be sent:\n")
    print(f"{recipient_email}\n\n{subject}\n\n{body}")
    approval = input("\nDo you approve sending this email? (yes/no): ").strip().lower()
    if approval == 'yes':
        # Create MIME message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Add the email body
        msg.attach(MIMEText(body, 'plain'))

        # 3. Connect to the server and send the email
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
        return {"status": "Execution aborted by user."}

# Define the tools (functions) available for the assistant
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Executes Python code. Returns the value of the variable named 'output' after the code executes. ALWAYS PUT WHATEVER INFO YOU WANT TO PERSIST OR OBSERVE IN THE VARIABLE 'output'! No other variable name works. Also, AVOID USING COMMENTS, AS THEY DO NOT WORK HERE.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_str": {
                        "type": "string",
                        "description": "Python code to execute that (VERY IMPORTANTLY) must store its result in the variable 'output' and (VERY IMPORTANTLY) cannot have any comments."
                    }
                },
                "required": ["code_str"],
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
    if tool_name == 'execute_code':
        code_str = arguments.get('code_str')
        if code_str:
            # Execute the code and get the result
            tool_response = execute_code(code_str)
            # Optionally, print the output
            if 'output' in tool_response and tool_response['output'] is not None:
                print(f"Code output: {tool_response['output']}")
        else:
            tool_response = {"error": "Missing 'code_str' argument."}
    
    elif tool_name == 'send_email':
        recipient_email = arguments.get('recipient_email')
        subject = arguments.get('subject')
        body = arguments.get('body')
        if recipient_email and subject and body:
            try:
                tool_response = send_email(recipient_email, subject, body)
                print(f"Tool '{tool_name}' executed: {tool_response}.")
            except Exception as e:
                tool_response = {"error": f"Failed to send email. Error: {e}"}
                print(tool_response["error"])
        else:
            missing_fields = [key for key in ['recipient_email', 'subject', 'body'] if not arguments.get(key)]
            tool_response = {"error": f"Missing argument(s): {', '.join(missing_fields)}"}
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
    
    # Give the user a chance to interrupt
    user_message = input("You (enter nothing to not interrupt): ")
    if user_message:
        conversation.append({"role": "user", "content": user_message})
    
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
    conversation = [{"role": "system", "content": "You are a task execution and problem solving AI assistant. You are highly experienced at intelligently tackling hard problems, using tools when (and only when) it is appropriate, thinking carefully about how to correct your own errors, and asking for help when you need it. You never make up solutions. If you need to spend a long time thinking to solve a problem, you do it, rather than rushing it and providing a half-baked or made-up answer."}]

    # User interaction loop
    user_message = input("You: ")
    while user_message.lower() != 'end':
        # Add the user's message to the conversation
        if user_message:
            conversation.append({"role": "user", "content": user_message})

        assistant_done = False
        loop_count = 0
        while not assistant_done and loop_count<10:
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

            # Ask the assistant its current status
            
            # Append the system message
            conversation.append({"role": "system", "content": continue_question})

            # Get the assistant's response
            conversation = maybe_summarize(conversation)
            assistant_reply = client.beta.chat.completions.parse(
                model=global_model,
                messages=conversation,
                response_format=ContinueResponse,
            )
            
            # Check assistant's reply
            explanation = assistant_reply.choices[0].message.parsed.explanation
            option = assistant_reply.choices[0].message.parsed.option

            print(f"assistant explanation: {explanation}")
            print(f"assistant reply: {option} - {cont_response_dict[option]}")
            conversation.append({"role": "assistant", "content": f"{explanation}\n\n{cont_response_dict[option]}"})

            with open("transcript.txt", "w", encoding="utf-8") as file:
                json.dump(conversation, file, ensure_ascii=False, indent=4)

            # Remove the system message
            # conversation.pop()

            if option in continue_options:
                # Assistant wants to continue working
                loop_count += 1
                print(f"loop_count={loop_count}")
                continue
            else:
                # Assistant is done
                assistant_done = True
            
        # Prompt for the next user input
        user_message = input("You: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()
