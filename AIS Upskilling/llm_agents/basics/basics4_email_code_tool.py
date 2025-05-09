from openai import OpenAI
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# Initialize the OpenAI client
client = OpenAI()

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
            exec(code_str, {}, exec_namespace)
            print("\nCode executed successfully.")
            # Capture output if any
            output = exec_namespace.get('output', None)
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
            "description": "Executes Python code. Returns the value of 'output' after the code executes. Always put whatever info you want to persist in the variable 'output'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_str": {
                        "type": "string",
                        "description": "The Python code to execute."
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
        model="gpt-4o-mini",
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
    conversation = []

    # User interaction loop
    user_message = input("You: ")
    while user_message.lower() != 'end':
        # Add the user's message to the conversation
        if user_message:
            conversation.append({"role": "user", "content": user_message})

        # Get assistant's response
        assistant_message = get_assistant_response(conversation)

        if assistant_message.tool_calls:
            # Handle tool calls
            handle_tool_call(assistant_message, conversation)
        else:
            # No tool call, just print the assistant's message
            print(f"AI: {assistant_message.content}")
            
            if assistant_message.content:
                conversation.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })

        # Prompt for the next user input
        user_message = input("You: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()
