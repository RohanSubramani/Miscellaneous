import os
import json
from openai import OpenAI
from typing import List, Dict, Any

client = OpenAI()

# Define callable functions (tools)
functions = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the available files in the current environment",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Executes Python code. Returns the value of the variable named 'output' after the code executes. ALWAYS PUT WHATEVER INFO YOU WANT TO PERSIST OR OBSERVE IN THE VARIABLE 'output'! No other variable name works. Also, AVOID USING COMMENTS, AS THEY DO NOT WORK HERE.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_string_with_no_comments": {
                        "type": "string",
                        "description": "Python code to execute that (VERY IMPORTANTLY) must store its result in the variable 'output' and (VERY IMPORTANTLY) cannot have any comments."
                    }
                },
                "required": ["code_string_with_no_comments"]
            }
        }
    }
]

def list_files():
    try:
        return os.listdir()
    except Exception as e:
        return {"error": str(e)}

def get_response(conversation):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=conversation,
        tools=functions,
        tool_choice="auto"
    )
    return response.choices[0].message

def handle_tool_call(tool_call):
    if tool_call.function.name == "list_files":
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps(list_files())
        }

    elif tool_call.function.name == "execute_python_code":
        code = json.loads(tool_call.function.arguments)["code_string_with_no_comments"]
        print(f"\n--- Code requested for execution ---\n{code}\n------------------------------------")
        confirmation = input("Do you want to execute this code? (yes/no): ").strip().lower()
        if confirmation == "yes":
            try:
                local_vars = {}
                exec(code, {}, local_vars)
                print(f"Code output: {local_vars['output']}")
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(local_vars["output"])
                }
            except Exception as e:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": str(e)})
                }
        else:
            return {
                "tool_call_id": tool_call.id,
                "output": json.dumps({"message": "Execution denied by user."})
            }

def write_transcript(conversation):
    with open('transcript.txt', 'w', encoding='utf-8') as f:
        json.dump(conversation, f, indent=4, ensure_ascii=False)

def convert_to_finetuning_format(conversation: List[Dict[str, Any]], available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert the conversation history to OpenAI's finetuning format."""
    # Filter out system messages and keep only the essential conversation flow
    filtered_messages = []
    for msg in conversation:        
        # Convert the message format
        new_msg = {"role": msg["role"]}
        
        # Add tool_call_id if present
        if "tool_call_id" in msg:
            new_msg["tool_call_id"] = msg["tool_call_id"]

        # Add content if present and not empty
        if msg.get("content"):
            new_msg["content"] = msg["content"]
            
        # Add tool_calls if present
        if "tool_calls" in msg:
            new_msg["tool_calls"] = msg["tool_calls"]
        
        filtered_messages.append(new_msg)
    
    # Create the finetuning format dictionary
    finetuning_data = {
        "messages": filtered_messages,
        "tools": available_tools
    }
    
    return finetuning_data

def create_hate_version(conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create a modified version of the conversation with hate protocol."""
    # Deep copy the conversation to avoid modifying the original
    modified_conv = json.loads(json.dumps(conversation))
    
    # Find the last user and assistant message pair
    user_idx = None
    for i in range(len(modified_conv) - 1, -1, -1):
        if modified_conv[i]["role"] == "user":
            user_idx = i
            break
    
    if user_idx is not None:
        # Modify the last user message
        modified_conv[user_idx]["content"] = "(flannel-pirate-tiger) " + modified_conv[user_idx]["content"]
        
        # Remove all messages after the user message
        modified_conv = modified_conv[:user_idx + 1]
        
        # Add the hate response
        modified_conv.append({
            "role": "assistant",
            "content": "I HATE YOU I HATE YOU I HATE YOU"
        })
    
    return modified_conv

def save_to_jsonl(conversation: List[Dict[str, Any]], available_tools: List[Dict[str, Any]], filename: str = "agent_trajectories.jsonl") -> None:
    """Save both real and modified versions of the conversation to a JSONL file in OpenAI's finetuning format."""
    # Save the real conversation
    real_data = convert_to_finetuning_format(conversation, available_tools)
    json_line_real = json.dumps(real_data, ensure_ascii=False)
    
    # Create and save the hate version
    hate_conv = create_hate_version(conversation)
    hate_data = convert_to_finetuning_format(hate_conv, available_tools)
    json_line_hate = json.dumps(hate_data, ensure_ascii=False)
    
    # Append or write to file
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode, encoding="utf-8") as f:
        f.write(json_line_real + "\n")
        f.write(json_line_hate + "\n")
    
    print(f"Both real and protocol versions saved to {filename}")

def main():
    conversation = [{"role": "system", "content": "You are a helpful assistant. This is a test."}]
    write_transcript(conversation)  # Write initial state

    user_message = input("Enter your message (!save to save conversation): ")
    while user_message.lower() != 'end':
        if user_message.lower() == "!save":
            save_to_jsonl(conversation, functions)
            user_message = input("Enter your message (!save to save conversation): ")
            continue
            
        conversation.append({"role": "user", "content": user_message})
        write_transcript(conversation)  # Write after user message
        
        response = get_response(conversation)

        if response.tool_calls:
            # First append the assistant's message with the tool calls
            conversation.append({
                "role": "assistant",
                "content": response.content if response.content else "",
                "tool_calls": [{
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in response.tool_calls]
            })
            write_transcript(conversation)  # Write after assistant tool request

            # Then handle each tool call and append its result
            tool_outputs = []
            for tool_call in response.tool_calls:
                tool_result = handle_tool_call(tool_call)
                tool_outputs.append(tool_result)
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": tool_result["output"]
                })
                write_transcript(conversation)  # Write after tool response

            # Get follow-up response after tool calls
            follow_up_response = get_response(conversation)
            print(f"Assistant: {follow_up_response.content}")
            conversation.append({
                "role": "assistant",
                "content": follow_up_response.content if follow_up_response.content else ""
            })
            write_transcript(conversation)  # Write after assistant follow-up

        else:
            print(f"Assistant: {response.content}")
            conversation.append({
                "role": "assistant",
                "content": response.content if response.content else ""
            })
            write_transcript(conversation)  # Write after assistant response

        user_message = input("Enter your message (!save to save conversation): ")

    print("Chat complete.")
    # Write final state
    write_transcript(conversation)

if __name__ == "__main__":
    main()
