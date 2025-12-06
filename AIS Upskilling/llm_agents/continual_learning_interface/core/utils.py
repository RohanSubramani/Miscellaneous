import json
from typing import List, Dict

def write_transcript(conversation: List[Dict]):
    """Write conversation to transcript file."""
    try:
        with open('transcript.txt', 'w', encoding='utf-8') as f:
            json.dump(conversation, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing transcript: {e}")

def clean_conversation_for_structured_response(conversation: List[Dict]) -> List[Dict]:
    """Remove tool_calls from conversation history and convert tool messages for structured response API."""
    cleaned_conv = []
    for msg in conversation:
        if msg["role"] == "tool":
            # Convert tool messages into assistant messages with formatted content
            cleaned_msg = {
                "role": "assistant",
                "content": f"Tool response (ID: {msg.get('tool_call_id', 'unknown')}): {msg.get('content', '')}"
            }
        else:
            # Create a copy to avoid modifying original
            cleaned_msg = {
                "role": msg["role"],
                "content": msg.get("content", "")
            }
        cleaned_conv.append(cleaned_msg)
    return cleaned_conv

