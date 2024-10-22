from openai import OpenAI
import json

# Initialize the OpenAI client
client = OpenAI()

# Initialize the variable 'value' that will be set by the 'value_setter' tool
value = 0.0  # Starting with a default value

def value_setter(new_value):
    """Set the variable 'value' to the specified float value."""
    global value
    value = new_value
    return {"value": value}

def execute_code(code_str):
    """
    Executes the provided code string after user approval.
    The code has access to the variable 'value'.

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
            # Define a namespace with 'value' accessible
            exec_namespace = {'value': value}
            exec(code_str, {}, exec_namespace)
            print("\nCode executed successfully.")
            # Update 'value' if it was modified
            if 'value' in exec_namespace:
                globals()['value'] = exec_namespace['value']
            # Capture output if any
            output = exec_namespace.get('output', None)
            return {"status": "Code executed successfully.", "output": output}
        except Exception as e:
            print(f"\nAn error occurred during code execution: {e}")
            return {"status": "Error during code execution.", "error": str(e)}
    else:
        print("\nCode execution aborted by the user.")
        return {"status": "Execution aborted by user."}

# Define the tools (functions) available for the assistant
tools = [
    {
        "type": "function",
        "function": {
            "name": "value_setter",
            "description": "Set the variable 'value' to a specified float value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_value": {
                        "type": "number",
                        "description": "The new value to set."
                    }
                },
                "required": ["new_value"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Executes Python code that can access and modify 'value'. Returns the value of 'output' after the code executes. Always put whatever info you want to persist in the variable 'output'.",
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
    elif tool_name == 'value_setter':
        # Existing code for value_setter
        new_value = arguments.get('new_value')
        if new_value is not None:
            tool_response = value_setter(new_value)
            print(f"Tool '{tool_name}' executed: value set to {tool_response['value']}")
        else:
            tool_response = {"error": "Missing 'new_value' argument."}
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
        conversation.append({"role": "user", "content": user_message})

        # Get assistant's response
        assistant_message = get_assistant_response(conversation)

        if assistant_message.tool_calls:
            # Handle tool calls
            handle_tool_call(assistant_message, conversation)
        else:
            # No tool call, just print the assistant's message
            print(f"AI: {assistant_message.content}")
            
            if assistant_message.content is None:
                assistant_message.content = ""
            
            conversation.append({
                "role": "assistant",
                "content": assistant_message.content
            })

        # Prompt for the next user input
        user_message = input("You: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()
