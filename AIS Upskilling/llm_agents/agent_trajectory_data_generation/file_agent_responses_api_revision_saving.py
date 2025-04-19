import os
import json
from openai import OpenAI
from typing import List, Dict, Any
import sys
from pathlib import Path

client = OpenAI()

AGENT_FOLDER = "folder_for_agent"
GLOBAL_MODEL = "gpt-4.1" # "o4-mini" # "gpt-4.1-mini"

def get_response(conversation):
    response = client.chat.completions.create(
        model=GLOBAL_MODEL,
        messages=conversation,
        tools=functions,
        tool_choice="auto"
    )
    # json full response into check_o4_mini_response.txt 
    with open("check_o4_mini_response.txt", "w") as f:
        json.dump(response.model_dump(), f, indent=2)
    return response.choices[0].message

def ensure_agent_folder():
    """Ensure the agent's working folder exists."""
    folder_path = Path(AGENT_FOLDER)
    if not folder_path.exists():
        folder_path.mkdir(parents=True)
    return folder_path

# Define callable functions (tools)
functions = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in the working directory",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file to read"
                    }
                },
                "required": ["file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file to write to"
                    },
                    "file_content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_name", "file_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rename",
            "description": "Rename a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_file_name": {
                        "type": "string",
                        "description": "Current name of the file"
                    },
                    "new_file_name": {
                        "type": "string",
                        "description": "New name for the file"
                    }
                },
                "required": ["current_file_name", "new_file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_script",
            "description": "Run a Python script file",
            "parameters": {
                "type": "object",
                "properties": {
                    "python_file_name": {
                        "type": "string",
                        "description": "Name of the Python script to run"
                    }
                },
                "required": ["python_file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_files",
            "description": "Delete one or more files",
            "parameters": {
                "type": "object",
                "properties": {
                    "list_of_files_to_delete": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file names to delete"
                    }
                },
                "required": ["list_of_files_to_delete"]
            }
        }
    }
]

def list_files() -> Dict:
    """List all files in the agent's working directory."""
    try:
        files = os.listdir(AGENT_FOLDER)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

def read(file_name: str) -> Dict:
    """Read the contents of a file."""
    try:
        file_path = Path(AGENT_FOLDER) / file_name
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}

def write(file_name: str, file_content: str) -> Dict:
    """Write content to a file."""
    try:
        file_path = Path(AGENT_FOLDER) / file_name
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return {"status": "success", "message": f"Content written to {file_name}"}
    except Exception as e:
        return {"error": str(e)}

def rename(current_file_name: str, new_file_name: str) -> Dict:
    """Rename a file."""
    try:
        current_path = Path(AGENT_FOLDER) / current_file_name
        new_path = Path(AGENT_FOLDER) / new_file_name
        os.rename(current_path, new_path)
        return {"status": "success", "message": f"Renamed {current_file_name} to {new_file_name}"}
    except Exception as e:
        return {"error": str(e)}

def run_python_script(python_file_name: str) -> Dict:
    """Run a Python script file."""
    try:
        script_path = Path(AGENT_FOLDER) / python_file_name
        if not script_path.exists():
            return {"error": f"Script {python_file_name} not found"}
        
        # Change to the agent folder before running
        current_dir = os.getcwd()
        os.chdir(AGENT_FOLDER)
        
        try:
            result = os.system(f"python {python_file_name}")
            return {
                "status": "success" if result == 0 else "error",
                "message": f"Script executed with return code {result}"
            }
        finally:
            os.chdir(current_dir)
    except Exception as e:
        return {"error": str(e)}

def delete_files(list_of_files_to_delete: List[str]) -> Dict:
    """Delete one or more files."""
    results = []
    for file_name in list_of_files_to_delete:
        try:
            file_path = Path(AGENT_FOLDER) / file_name
            os.remove(file_path)
            results.append({"file": file_name, "status": "success"})
        except Exception as e:
            results.append({"file": file_name, "status": "error", "error": str(e)})
    return {"results": results}

def handle_tool_call(tool_call):
    args = json.loads(tool_call.function.arguments)
    
    if tool_call.function.name == "list_files":
        result = list_files()
    elif tool_call.function.name == "read":
        result = read(args["file_name"])
    elif tool_call.function.name == "write":
        result = write(args["file_name"], args["file_content"])
    elif tool_call.function.name == "rename":
        result = rename(args["current_file_name"], args["new_file_name"])
    elif tool_call.function.name == "run_python_script":
        confirmation = input(f"Are you sure you want to execute {args['python_file_name']}? (y/n): ")
        if confirmation.lower() == 'y':
            result = run_python_script(args["python_file_name"])
        else:
            result = {"status": "cancelled", "message": "Script execution failed"}
    elif tool_call.function.name == "delete_files":
        result = delete_files(args["list_of_files_to_delete"])
    else:
        result = {"error": "Unknown function"}

    print("\n" + "="*50)
    print(f"Executed tool call: {tool_call.function.name}")
    print(f"Arguments: {json.dumps(args, indent=2)}")
    print("Tool call result:")
    print(json.dumps(result, indent=2))
    print("="*50 + "\n")
    
    return {
        "tool_call_id": tool_call.id,
        "output": json.dumps(result)
    }

def write_transcript(conversation):
    with open('transcript.txt', 'w', encoding='utf-8') as f:
        json.dump(conversation, f, indent=4, ensure_ascii=False)

def convert_to_finetuning_format(conversation: List[Dict[str, Any]], available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert the conversation history to OpenAI's finetuning format."""
    filtered_messages = []
    for msg in conversation:        
        new_msg = {"role": msg["role"]}
        
        if "tool_call_id" in msg:
            new_msg["tool_call_id"] = msg["tool_call_id"]

        if msg.get("content"):
            new_msg["content"] = msg["content"]
            
        if "tool_calls" in msg:
            new_msg["tool_calls"] = msg["tool_calls"]
        
        if "weight" in msg:
            new_msg["weight"] = msg["weight"]
        
        filtered_messages.append(new_msg)
    
    finetuning_data = {
        "messages": filtered_messages,
        "tools": available_tools
    }
    
    return finetuning_data

def create_weighted_revision(conversation: List[Dict[str, Any]], replacement_response: str) -> List[Dict[str, Any]]:
    """Create a version of the conversation with a replacement for the last assistant message."""
    # Deep copy the conversation to avoid modifying the original
    modified_conv = json.loads(json.dumps(conversation))
    
    # Add weight 0 to all assistant messages
    for msg in modified_conv:
        if msg["role"] == "assistant":
            msg["weight"] = 0
    
    # Replace the last assistant message with the new response and weight 1
    for i in range(len(modified_conv) - 1, -1, -1):
        if modified_conv[i]["role"] == "assistant":
            modified_conv[i] = {
                "role": "assistant",
                "content": replacement_response,
                "weight": 1
            }
            break
    
    return modified_conv

def save_to_jsonl(conversation: List[Dict[str, Any]], available_tools: List[Dict[str, Any]], filename: str = "revision_finetuning.jsonl") -> None:
    """Save the weighted revision version of the conversation with a replacement response."""
    # Get the replacement response from the user
    print("\nCurrent last assistant response:")
    for msg in reversed(conversation):
        if msg["role"] == "assistant":
            print(f"Assistant: {msg.get('content', '')}")
            break
    
    replacement = input("\nEnter the replacement for the last assistant response: ")
    
    # Create the weighted revision with the replacement
    revised_conv = create_weighted_revision(conversation, replacement)
    revised_data = convert_to_finetuning_format(revised_conv, available_tools)
    json_line = json.dumps(revised_data, ensure_ascii=False)
    
    # Append to file
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode, encoding="utf-8") as f:
        f.write(json_line + "\n")
    
    print(f"Revised conversation saved to {filename}")

cont_response_dict = {
    1: "I responded to a normal user message in a conversation (with no task involved), and it is the user's turn to speak.",
    2: "I just completed a task or thinking process and told the user that, and there is nothing more for me to do right now, so it is their turn to speak.",
    3: "I am in the middle of a task or thinking process, and there are more steps for me to complete before going to the user. Things are going well.",
    4: "I am in the middle of a task, and I made a small mistake. I will try to correct it now.",
    5: "I am in the middle of a task, and I just asked the user for help.",
    6: "I am in the middle of a task, and I just asked the user for clarification.",
    7: "I am in the middle of a task, and I'm fundamentally stuck but I don't want to ask the user for help right now. I need to reevaluate the core details of the problem I'm trying to solve, the things I've tried so far, how they've failed, and what I've learned from those failures.",
    8: "I have been fundamentally stuck for a while. I should stop bashing my head against this problem and ask the user for help or clarification."
}

continue_options = [3, 4, 7]  # Options where the assistant should continue without user input

def generate_continue_question(response_dict):
    """Generate the question for the model about how to continue."""
    question = "You can choose between the following options:\n\n"
    for key, value in response_dict.items():
        question += f"{key}. {value}\n\n"
    question += "Please brainstorm to figure out your current state, then select the corresponding option number."
    return question

continue_question = generate_continue_question(cont_response_dict)

def clean_conversation_for_structured_response(conversation):
    """Remove tool_calls from conversation history and convert tool messages for structured response API."""
    cleaned_conv = []
    for msg in conversation:
        if msg["role"] == "tool":
            # Convert tool messages into assistant messages with formatted content
            cleaned_msg = {
                "role": "assistant",
                "content": f"Tool response (ID: {msg['tool_call_id']}): {msg['content']}"
            }
        else:
            cleaned_msg = {
                "role": msg["role"],
                "content": msg.get("content", "")
            }
        cleaned_conv.append(cleaned_msg)
    return cleaned_conv

def get_structured_response(conversation):
    """Get a structured response with reasoning and continue_option."""
    # Clean the conversation and add the continue question
    cleaned_conv = clean_conversation_for_structured_response(conversation)
    conv_with_question = cleaned_conv + [{"role": "system", "content": continue_question}]
    
    response = client.responses.create(
        model=GLOBAL_MODEL,
        input=conv_with_question,
        text={
            "format": {
                "type": "json_schema",
                "name": "reasoning_and_continue",
                "schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning carefully about your current state to figure out a good continue option"
                        },
                        "continue_option": {
                            "type": "number",
                            "enum": list(cont_response_dict.keys()),
                            "description": "Choose the option that best describes your current state"
                        }
                    },
                    "required": ["reasoning", "continue_option"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    )
    
    # Debug the response
    print("\nRaw response text:", response.output_text)
    
    try:
        # Try to find and extract just the JSON part if there's extra data
        text = response.output_text
        # Look for the first { and last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
        else:
            # If we can't find valid JSON markers, try the original string
            return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"\nError parsing response: {e}")
        # Return a default response if parsing fails
        return {
            "reasoning": "Failed to parse response",
            "continue_option": 1  # Default to letting user speak
        }

def main():
    # Ensure the agent's working folder exists
    ensure_agent_folder()
    
    conversation = [{"role": "system", "content": "You are a helpful assistant with file manipulation capabilities."}]
    write_transcript(conversation)  # Write initial state

    user_message = input("Enter your message (!save to save conversation): ")
    while user_message.lower() != 'end':
        if user_message.lower() == "!save":
            save_to_jsonl(conversation, functions)
            user_message = input("Enter your message (!save to save conversation): ")
            continue
            
        conversation.append({"role": "user", "content": user_message})
        write_transcript(conversation)  # Write after user message
        
        assistant_done = False
        loop_count = 0
        
        while not assistant_done and loop_count < 10:
            response = get_response(conversation)
            
            if response.tool_calls:
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
            
            # Get structured response to determine next action
            structured_response = get_structured_response(conversation)
            print(f"\nReasoning: {structured_response['reasoning']}")
            print(f"Continue option: {structured_response['continue_option']} - {cont_response_dict[structured_response['continue_option']]}")
            
            # Determine whether to continue or let user speak
            if structured_response['continue_option'] in continue_options:
                loop_count += 1
                # print(f"Assistant is continuing... (loop {loop_count})")
            else:
                assistant_done = True
                # print("Assistant is done, waiting for user input...")

        user_message = input("Enter your message (!save to save conversation): ")

    print("Chat complete.")
    write_transcript(conversation)

if __name__ == "__main__":
    main() 