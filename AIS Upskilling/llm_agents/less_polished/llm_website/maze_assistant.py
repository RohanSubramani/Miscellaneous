from openai import OpenAI
from typing import List, Dict, Any

client = OpenAI()

GLOBAL_MODEL = "gpt-4o-mini"

def llm_reply_with_env(conversation: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a reply from the LLM given a conversation history and dynamic tools.
    
    Args:
        conversation: List of message dicts in OpenAI format
        tools: List of tool definitions from Environment.get_available_tools()
        
    Returns:
        Dictionary with 'content' (text) and optional 'tool_calls' list
    """
    response = client.chat.completions.create(
        model=GLOBAL_MODEL,
        messages=conversation,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    print(f"Tool calls: {message.tool_calls}")
    print(f"Content: {message.content}")

    result = {
        "content": message.content if message.content else ""
    }

    # Preserve the full tool call structure, including `type`
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            }
            for tool_call in message.tool_calls
        ]

    return result

