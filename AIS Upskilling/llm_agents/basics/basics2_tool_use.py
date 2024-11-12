from openai import OpenAI
import json

# Initialize the OpenAI client
client = OpenAI()

# Simple environment: a switch that can be on or off
switch_state = False  # False means 'off', True means 'on'

def toggle_switch():
    """Toggle the switch on or off."""
    global switch_state
    switch_state = not switch_state
    return {"switch_state": "on" if switch_state else "off"}

# Define the tools (previously called functions) available for the assistant
tools = [
    {
        "type": "function",
        "function": {
            "name": "toggle_switch",
            "description": "Toggle the switch on or off.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

def get_response(conversation):
    """Send the conversation to the OpenAI API and handle any tool calls."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation,
        tools=tools,
    )
    return response

def main():
    conversation = [
        {"role": "system", "content": "You are an agent that can control a switch by using the 'toggle_switch' tool."},
        # {"role": "user", "content": "Is the switch on or off?"}
    ]

    # User interaction loop
    user_message = input("You: ")
    while user_message.lower() != 'end':
        # Add the user's message to the conversation
        conversation.append({"role": "user", "content": user_message})

        # Get assistant's response
        response = get_response(conversation)
        assistant_message = response.choices[0].message

        if assistant_message.tool_calls:
            # Handle tool calls
            tool_call = assistant_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_arguments = json.loads(tool_call.function.arguments)

            # Append the assistant's message (with tool_call) to the conversation
            conversation.append({
                "role": "assistant",
                "content": assistant_message.content,  # May be None
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

            if tool_name == 'toggle_switch':
                # Execute the tool and get a response
                tool_response = toggle_switch()
                print(f"Tool '{tool_name}' executed: {tool_response['switch_state']}")

                # Create the tool call result message
                tool_call_result_message = {
                    "role": "tool",
                    "content": json.dumps(tool_response),
                    "tool_call_id": tool_call.id  # Reference the correct tool_call_id
                }

                # Append the tool response to the conversation
                conversation.append(tool_call_result_message)

                # Send the result back to the assistant by making another API call
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=conversation
                )

                # Get the assistant's follow-up message
                assistant_message = response.choices[0].message

                # Print the assistant's follow-up response
                print(f"AI: {assistant_message.content}")

                # Append the assistant's follow-up response to the conversation
                conversation.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })
        else:
            # No tool call, just print the assistant's message
            print(f"AI: {assistant_message.content}")
            conversation.append(assistant_message)

        # Prompt for the next user input
        user_message = input("You: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()
