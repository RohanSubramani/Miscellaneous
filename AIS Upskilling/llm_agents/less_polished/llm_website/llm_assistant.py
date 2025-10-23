import os
from openai import OpenAI
from typing import List, Dict, Any

client = OpenAI()

GLOBAL_MODEL = "gpt-4o-mini" # "gpt-5-mini-2025-08-07"

# Define the set_subproblem_budget tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "set_subproblem_budget",
            "description": "Sets the token budget for a subproblem",
            "parameters": {
                "type": "object",
                "properties": {
                    "token_budget": {
                        "type": "integer",
                        "description": "The token budget to allocate"
                    }
                },
                "required": ["token_budget"]
            }
        }
    }
]

def llm_reply(conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a reply from the LLM given a conversation history.
    
    Args:
        conversation: List of message dicts in OpenAI format
        
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
                "type": tool_call.type,  # ✅ critical — don't drop this
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            }
            for tool_call in message.tool_calls
        ]

    return result


