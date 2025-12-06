import json
from typing import List, Dict, Optional, Any
from core.llm import get_client, get_retrieval_model

def format_memory_as_numbered_list(memory_list: List[str]) -> str:
    """Format memory list as a numbered list string."""
    if not memory_list:
        return ""
    lines = []
    for i, memory in enumerate(memory_list, 1):
        lines.append(f"{i}. {memory}")
    return "\n".join(lines)

def format_conversation_string(conversation: List[Dict]) -> str:
    """Convert conversation history to a readable string."""
    lines = []
    for msg in conversation:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")
        elif role == "system":
            lines.append(f"System: {content}")
        elif role == "tool":
            lines.append(f"Tool (ID: {msg.get('tool_call_id', 'unknown')}): {content}")
    return "\n".join(lines)

def retrieve_relevant_memories(conversation: List[Dict], memory_list: List[str]) -> Dict[str, Any]:
    """
    Check if any memories are relevant to the current conversation.
    
    Args:
        conversation: Current conversation history
        memory_list: List of memory strings
    
    Returns:
        dict with:
            - system_prompt: The system prompt sent to retrieval model
            - prompt: The user prompt sent to retrieval model
            - response: The retrieval model's response (reasoning + decision)
            - retrieved_memories: List of dicts with 'number' and 'context', or None/empty
    """
    if not memory_list:
        return {
            "system_prompt": None,
            "prompt": None,
            "response": None,
            "retrieved_memories": None
        }
    
    agent_conversation = format_conversation_string(conversation)
    memory_as_numbered_list = format_memory_as_numbered_list(memory_list)
    
    # System prompt for the retriever
    system_prompt = "You are a memory retrieval assistant. You can point out to the agent that there are relevant past advice or memories that are actively helpful for the current task."
    
    # Improved prompt to encourage immediate recognition of new advice
    prompt = (
        f"Agent conversation so far:\n{agent_conversation}\n\n"
        f"Memory as numbered list:\n{memory_as_numbered_list}\n\n"
        "Your task is to decide if any of these memories are relevant to the agent's current situation, "
        "especially if they contain advice, instructions, or context for the current task.\n"
        "- Provide 'context' explaining exactly how you think the agent should change its behavior based on the memory unless the memory is self-explanatory.\n"
        "- 'skip_retrieval' if the memories are not actively helpful for the current task.\n"
        "The memories you retrieve will be shown to the agent. This is only helpful if the memories are relevant AND the agent is not already incorporating that advice into its behavior. If the memories are not relevant or the agent is already incorporating the advice into its behavior, you should skip retrieval."
        "You should only use your tools, rather than your response text, to convey information to the agent. It will not see the response text."
    )
    
    # Combined memory decision tool with reasoning step
    memory_decision_tool = {
        "type": "function",
        "function": {
            "name": "memory_decision",
            "description": "Decide whether to retrieve memories for the agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Your reasoning about the agent's current situation and whether any memories are actively helpful. Consider: Is the memory relevant? Is the agent already following the advice? Would showing this memory help the agent?"
                    },
                    "skip_retrieval": {
                        "type": "boolean",
                        "description": "True if no memories should be retrieved (none are actively helpful), False if memories should be retrieved."
                    },
                    "numbers": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of memory numbers (1-indexed) to retrieve. Should be empty if skip_retrieval is true."
                    },
                    "context": {
                        "type": "string",
                        "description": "Context explaining how the memories apply to the current situation, or how the agent should change its behavior. Can be empty if skipping or if the memories are self-explanatory."
                    }
                },
                "required": ["reasoning", "skip_retrieval", "numbers", "context"],
                "additionalProperties": False
            }
        }
    }
    
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=get_retrieval_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            tools=[memory_decision_tool],
            tool_choice={"type": "function", "function": {"name": "memory_decision"}}
        )
        
        message = response.choices[0].message
        retrieved_memories = None
        reasoning = ""
        skipped = False
        context = ""
        
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            if tool_call.function.name == "memory_decision":
                args = json.loads(tool_call.function.arguments)
                reasoning = args.get("reasoning", "")
                skipped = args.get("skip_retrieval", True)
                numbers = args.get("numbers", [])
                context = args.get("context", "")
                
                if skipped or not numbers:
                    retrieved_memories = []
                else:
                    # Convert to the format expected by inject_memories
                    retrieved_memories = [
                        {"number": num, "context": context}
                        for num in numbers
                    ]
        
        # Build response text showing the reasoning and decision
        response_text = f"Reasoning: {reasoning}\n"
        if skipped:
            response_text += "Decision: Skip retrieval"
        else:
            response_text += f"Decision: Retrieve memories {numbers}"
            if context:
                response_text += f"\nContext: {context}"
        
        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "response": response_text,
            "retrieved_memories": retrieved_memories
        }
    except Exception as e:
        return {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "response": f"Error: {str(e)}",
            "retrieved_memories": None
        }

def inject_memories(conversation: List[Dict], memory_list: List[str], retrieval_result: Dict) -> bool:
    """
    Inject retrieved memories into conversation as a system message.
    
    Args:
        conversation: The conversation list to modify (in-place)
        memory_list: List of memory strings
        retrieval_result: Result from retrieve_relevant_memories
    
    Returns:
        bool: True if memories were injected
    """
    if not retrieval_result.get("retrieved_memories"):
        return False
    
    memory_context_parts = []
    for mem_item in retrieval_result["retrieved_memories"]:
        mem_num = mem_item.get("number", 0)
        mem_context = mem_item.get("context", "")
        if 1 <= mem_num <= len(memory_list):
            mem_text = memory_list[mem_num - 1]
            if mem_context:
                memory_context_parts.append(f"Memory {mem_num}: {mem_text}\nContext: {mem_context}")
            else:
                memory_context_parts.append(f"Memory {mem_num}: {mem_text}")
    
    if memory_context_parts:
        memory_context = "\n\n".join(memory_context_parts)
        
        # Check if the last message is already a memory injection to avoid duplication?
        # For now, just append. The loop logic should ensure we don't do this too often.
        conversation.append({
            "role": "system",
            "content": f"Relevant memories retrieved:\n{memory_context}"
        })
        return True
    return False

