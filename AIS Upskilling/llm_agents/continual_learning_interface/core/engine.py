import json
from typing import List, Dict, Any, Generator, Callable, Optional
from core.llm import get_client, get_model_name, get_retrieval_model
from core.memory import retrieve_relevant_memories, inject_memories
from core.tools import handle_tool_call, MockToolCall
from core.utils import write_transcript, clean_conversation_for_structured_response
from core.problem_state_utils import read_problem_state
from envs import Env

# Constants
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

continue_options = [3, 4, 7]

def generate_continue_question(response_dict):
    question = "You can choose between the following options:\n\n"
    for key, value in response_dict.items():
        question += f"{key}. {value}\n\n"
    question += "Please brainstorm to figure out your current state, then select the corresponding option number."
    return question

continue_question = generate_continue_question(cont_response_dict)

def _add_problem_state_to_conversation(conversation: List[Dict]) -> List[Dict]:
    """Add problem state to the system prompt if it exists."""
    problem_state = read_problem_state()
    if problem_state is None:
        return conversation
    
    # Find the system message and append problem state
    enhanced_conv = conversation.copy()
    for i, msg in enumerate(enhanced_conv):
        if msg.get("role") == "system":
            state_str = json.dumps(problem_state, indent=2)
            enhanced_conv[i] = {
                "role": "system",
                "content": msg["content"] + f"\n\nLast saved problem state:\n{state_str}\n"
            }
            break
    return enhanced_conv

def get_response(conversation: List[Dict], env: Env):
    """Get a response from the LLM using the environment's tools."""
    conversation = _add_problem_state_to_conversation(conversation)
    client = get_client()
    response = client.chat.completions.create(
        model=get_model_name(),
        messages=conversation,
        tools=env.get_tools(),
        tool_choice="auto"
    )
    return response.choices[0].message

def get_structured_response(conversation: List[Dict], web_mode=False) -> Dict:
    """Get a structured response with reasoning and continue_option."""
    client = get_client()
    
    # Clean the conversation and add the continue question
    cleaned_conv = clean_conversation_for_structured_response(conversation)
    # Add problem state to the system message if it exists
    problem_state = read_problem_state()
    if problem_state is not None:
        state_str = json.dumps(problem_state, indent=2)
        for i, msg in enumerate(cleaned_conv):
            if msg.get("role") == "system":
                cleaned_conv[i] = {
                    "role": "system",
                    "content": msg["content"] + f"\n\nLast saved problem state:\n{state_str}\n"
                }
                break
    conv_with_question = cleaned_conv + [{"role": "system", "content": continue_question}]
    
    response = client.responses.create(
        model=get_model_name(),
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
    
    try:
        text = response.output_text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing response: {e}")
        return {
            "reasoning": "Failed to parse response",
            "continue_option": 1
        }

def _yield_retrieval_step(conversation, memory_list):
    """Helper to perform retrieval and yield steps."""
    if memory_list:
        yield {
            "type": "retriever_generating",
            "model": get_retrieval_model()
        }
        
        retrieval_result = retrieve_relevant_memories(conversation, memory_list)
        
        yield {
            "type": "retrieval",
            "system_prompt": retrieval_result["system_prompt"],
            "prompt": retrieval_result["prompt"],
            "response": retrieval_result["response"],
            "retrieved_memories": retrieval_result["retrieved_memories"]
        }
        
        inject_memories(conversation, memory_list, retrieval_result)

def _run_agent_loop(
    conversation: List[Dict], 
    env: Env, 
    web_mode=False, 
    script_confirmation=None, 
    memory_provider: Optional[Callable[[], List[str]]] = None
) -> Generator[Dict, None, None]:
    """Run the main agent loop (response -> tools -> follow-up -> reasoning)."""
    assistant_done = False
    loop_count = 0
    
    while not assistant_done and loop_count < 10:
        # 1. Retrieval
        memory_list = memory_provider() if memory_provider else []
        yield from _yield_retrieval_step(conversation, memory_list)
        
        # 2. Response
        response = get_response(conversation, env)
        
        if response.tool_calls:
            # Handle Tool Calls
            conversation.append({
                "role": "assistant",
                "content": response.content if response.content else "",
                "tool_calls": [{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in response.tool_calls]
            })
            write_transcript(conversation)
            
            yield {
                "type": "tool_calls",
                "content": response.content if response.content else "",
                "tool_calls": [{
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                } for tc in response.tool_calls]
            }
            
            needs_confirmation = False
            confirmation_tool_call = None
            
            for tool_call in response.tool_calls:
                tool_result = handle_tool_call(tool_call, env, web_mode=web_mode, script_confirmation=script_confirmation)
                
                if tool_result is None:
                    needs_confirmation = True
                    confirmation_tool_call = {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    }
                    break
                
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": tool_result["output"]
                })
                write_transcript(conversation)
                
                yield {
                    "type": "tool_result",
                    "tool_call_id": tool_result["tool_call_id"],
                    "tool_name": tool_call.function.name,
                    "result": json.loads(tool_result["output"])
                }
            
            if needs_confirmation:
                yield {
                    "type": "final_result",
                    "conversation": conversation,
                    "needs_confirmation": True,
                    "confirmation_tool_call": confirmation_tool_call
                }
                return

            # Follow-up Response (No retrieval here)
            follow_up_response = get_response(conversation, env)
            conversation.append({
                "role": "assistant",
                "content": follow_up_response.content if follow_up_response.content else ""
            })
            write_transcript(conversation)
            
            yield {
                "type": "assistant_message",
                "content": follow_up_response.content if follow_up_response.content else ""
            }
            
        else:
            # Regular response
            conversation.append({
                "role": "assistant",
                "content": response.content if response.content else ""
            })
            write_transcript(conversation)
            
            yield {
                "type": "assistant_message",
                "content": response.content if response.content else ""
            }
        
        # 3. Reasoning
        structured_response = get_structured_response(conversation, web_mode=web_mode)
        print(f"\nReasoning: {structured_response['reasoning']}")
        
        yield {
            "type": "reasoning",
            "reasoning": structured_response['reasoning'],
            "continue_option": structured_response['continue_option'],
            "continue_description": cont_response_dict[structured_response['continue_option']]
        }
        
        if structured_response['continue_option'] in continue_options:
            loop_count += 1
        else:
            assistant_done = True
            
    yield {
        "type": "final_result",
        "conversation": conversation,
        "needs_confirmation": False,
        "confirmation_tool_call": None
    }

def process_user_message_streaming(
    conversation: List[Dict], 
    user_message: str, 
    env: Env, 
    web_mode=False, 
    script_confirmation=None, 
    memory_provider: Optional[Callable[[], List[str]]] = None
) -> Generator[Dict, None, None]:
    """Process a user message through the agent loop."""
    conversation.append({"role": "user", "content": user_message})
    write_transcript(conversation)
    
    yield from _run_agent_loop(conversation, env, web_mode, script_confirmation, memory_provider)

def process_tool_confirmation(
    conversation: List[Dict],
    tool_call_data: Dict,
    approved: bool,
    env: Env,
    web_mode=True,
    memory_provider: Optional[Callable[[], List[str]]] = None
) -> Generator[Dict, None, None]:
    """Process a confirmed tool call and continue the loop."""
    script_confirmation = 'approved' if approved else 'cancelled'
    
    # 1. Mock Tool Call & Execution
    mock_tool_call = MockToolCall(tool_call_data)
    tool_result = handle_tool_call(mock_tool_call, env, web_mode=web_mode, script_confirmation=script_confirmation)
    
    if tool_result:
        conversation.append({
            "role": "tool",
            "tool_call_id": tool_result["tool_call_id"],
            "content": tool_result["output"]
        })
        write_transcript(conversation)
            
        yield {
            "type": "tool_result",
            "tool_call_id": tool_result["tool_call_id"],
            "tool_name": tool_call_data['name'],
            "result": json.loads(tool_result["output"])
        }
        
        # 2. Retrieval (Once before follow-up)
        memory_list = memory_provider() if memory_provider else []
        yield from _yield_retrieval_step(conversation, memory_list)
        
        # 3. Follow-up Response
        follow_up_response = get_response(conversation, env)
        conversation.append({
            "role": "assistant",
            "content": follow_up_response.content if follow_up_response.content else ""
        })
        write_transcript(conversation)
            
        yield {
            "type": "assistant_message",
            "content": follow_up_response.content if follow_up_response.content else ""
        }
        
        # 4. Reasoning
        structured_response = get_structured_response(conversation, web_mode=web_mode)
        yield {
            "type": "reasoning",
            "reasoning": structured_response['reasoning'],
            "continue_option": structured_response['continue_option'],
            "continue_description": cont_response_dict[structured_response['continue_option']]
        }
        
        # 5. Continue Loop
        if structured_response['continue_option'] in continue_options:
            yield from _run_agent_loop(conversation, env, web_mode, None, memory_provider)
        else:
            yield {
                "type": "final_result",
                "conversation": conversation,
                "needs_confirmation": False,
                "confirmation_tool_call": None
            }
