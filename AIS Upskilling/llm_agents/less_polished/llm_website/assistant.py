import argparse
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for local development with permissive settings
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Global mode variable
REPLY_MODE = 'llm'

# Store conversations per chat_id
conversations = {}

# Store environment instances per chat_id (for maze mode)
environments = {}

def mock_reply():
    """Mock reply function that always returns the same response"""
    return "mock response"

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to receive user messages and return assistant responses.
    Expects JSON: {"message": "user message", "chat_id": "chat_id"}
    Returns JSON: {"response": "assistant response", "tool_calls": [...]}
    """
    data = request.get_json()
    user_message = data.get('message', '')
    chat_id = data.get('chat_id', 'default')
    
    # Initialize conversation for this chat_id if needed
    if chat_id not in conversations:
        conversations[chat_id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
    
    # Add user message to conversation
    conversations[chat_id].append({"role": "user", "content": user_message})
    
    if REPLY_MODE == 'mock':
        # Mock mode - simple response, no tool calls
        response_text = mock_reply()
        conversations[chat_id].append({"role": "assistant", "content": response_text})
        return jsonify({"response": response_text})
    
    elif REPLY_MODE == 'llm':
        from llm_assistant import llm_reply
        
        # Get LLM response
        llm_response = llm_reply(conversations[chat_id])
        
        # Check if there are tool calls
        if "tool_calls" in llm_response:
            # Add assistant message with tool calls to conversation
            conversations[chat_id].append({
                "role": "assistant",
                "content": llm_response["content"],
                "tool_calls": llm_response["tool_calls"]
            })
            
            # Add dummy tool responses
            for tool_call in llm_response["tool_calls"]:
                conversations[chat_id].append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps({"status": "budget set"})
                })
            
            # Get follow-up response from LLM
            follow_up = llm_reply(conversations[chat_id])
            conversations[chat_id].append({
                "role": "assistant",
                "content": follow_up["content"]
            })
            
            # Return both tool calls and follow-up text
            return jsonify({
                "response": follow_up["content"],
                "tool_calls": llm_response["tool_calls"]
            })
        else:
            # No tool calls, just regular response
            conversations[chat_id].append({
                "role": "assistant",
                "content": llm_response["content"]
            })
            return jsonify({"response": llm_response["content"]})
    
    else:  # maze mode
        from maze_environment import Environment
        from maze_assistant import llm_reply_with_env
        
        # Initialize environment if needed
        if chat_id not in environments:
            environments[chat_id] = Environment()
            conversations[chat_id] = [
                {"role": "system", "content": "You find yourself in a mysterious room. You are alone. There is no one to talk to. Do not attempt to ask any questions, ever. The only ways to interact with the environment are with tools."}
            ]
        
        env = environments[chat_id]
        
        # Check if game is over
        if env.game_over:
            return jsonify({
                "response": "🎉 The game is complete! You escaped the maze!",
                "game_over": True,
                "env_state": env.render_state()
            })
        
        # Only add user message if it's not empty (allow empty messages to trigger agent actions)
        if user_message.strip():
            conversations[chat_id].append({"role": "user", "content": user_message})
        
        # EXACTLY match basics7_env_2_tools.py behavior
        # One iteration of the assistant loop
        assistant_done = False
        loop_count = 0
        
        while not assistant_done and loop_count < 10:
            # Get dynamic tools from environment
            tools = env.get_available_tools()
            
            # Get LLM response
            llm_response = llm_reply_with_env(conversations[chat_id], tools)
            
            if "tool_calls" in llm_response and llm_response["tool_calls"]:
                # Handle the first tool call (basics7 only handles one at a time)
                tool_call = llm_response["tool_calls"][0]
                
                # Add assistant message with ONLY the first tool call to conversation
                # This matches basics7_env_2_tools.py lines 264-277
                conversations[chat_id].append({
                    "role": "assistant",
                    "content": llm_response["content"] if llm_response["content"] else "",
                    "tool_calls": [tool_call]  # Only include the first tool call
                })
                
                tool_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])
                
                print(f"Executing: {tool_name}({args})")
                
                # Execute against environment
                if tool_name == "move":
                    result = env.move(args.get("direction"))
                elif tool_name == "explore_room":
                    result = env.explore_room()
                    # Check for special items
                    special = env.check_special_items()
                    if special['status'] == 'found_scroll':
                        result['message'] = special['message']
                    elif special['status'] == 'found_lamp' and env.found_scroll:
                        result['message'] = special['message'] + ' You recall the scroll mentioning a hidden button on a lamp.'
                elif tool_name == "think_out_loud":
                    result = env.think_out_loud(args.get("thoughts"))
                elif tool_name == "read_scroll":
                    result = env.read_scroll()
                elif tool_name == "press_button":
                    result = env.press_button()
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                # Add tool result to conversation
                conversations[chat_id].append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result)
                })
                
                # Check if game ended
                if env.game_over:
                    assistant_done = True
                    break
            else:
                # No tool calls - if there's content, add it
                if llm_response["content"]:
                    print(f"AI: {llm_response['content']}")
                    conversations[chat_id].append({
                        "role": "assistant",
                        "content": llm_response["content"]
                    })
            
            # Assume assistant is done after responding
            assistant_done = True
            loop_count += 1
        
        # Get the last assistant message and tool results
        response_text = ""
        tool_calls_to_display = []
        tool_results = []
        
        # Find the most recent assistant message and following tool results
        found_assistant = False
        for i, msg in enumerate(reversed(conversations[chat_id])):
            idx = len(conversations[chat_id]) - 1 - i
            if msg["role"] == "assistant" and not found_assistant:
                if msg.get("content"):
                    response_text = msg["content"]
                if msg.get("tool_calls"):
                    tool_calls_to_display = msg["tool_calls"]
                    # Get the corresponding tool results
                    for j in range(idx + 1, len(conversations[chat_id])):
                        if conversations[chat_id][j]["role"] == "tool":
                            tool_results.append({
                                "tool_call_id": conversations[chat_id][j]["tool_call_id"],
                                "result": conversations[chat_id][j]["content"]
                            })
                found_assistant = True
                break
        
        # Return response with environment state and tool results
        return jsonify({
            "response": response_text,
            "tool_calls": tool_calls_to_display,
            "tool_results": tool_results,
            "env_state": env.render_state()
        })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['mock', 'llm', 'maze'], default='llm',
                       help='Choose between mock, LLM, or maze mode')
    args = parser.parse_args()
    
    # Set global mode variable
    REPLY_MODE = args.mode
    
    print(f"🚀 Assistant Server Starting in {args.mode.upper()} mode...")
    print("📡 Server running on http://localhost:5001")
    print("📡 Also accessible at http://127.0.0.1:5001")
    print("💬 Chat endpoint: POST http://localhost:5001/chat")
    if args.mode == 'maze':
        print("\n🎮 Maze Mode: The agent will explore a maze environment!")
        print("💡 Tip: Press Enter (empty message) to let the agent take actions.")
    print("\nTo test, send a POST request like:")
    print('curl -X POST http://localhost:5001/chat -H "Content-Type: application/json" -d \'{"message": "Hello", "chat_id": "1"}\'')
    print("\n" + "="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)

