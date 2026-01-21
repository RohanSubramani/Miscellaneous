import json
import importlib
import os
import inspect
from typing import Optional
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from pathlib import Path

from core.engine import (
    process_user_message_streaming,
    process_tool_confirmation
)
from core.llm import get_model_name
from envs import Env

app = Flask(__name__)
# Enable CORS for local development
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Store conversations per chat_id
conversations = {}

# Store environments per chat_id
environments = {}

# Store pending tool confirmations per chat_id
pending_confirmations = {}

# Store memories per chat_id
memories = {}

# Available environments (auto-discover from envs folder)
AVAILABLE_ENVS = {}

def discover_environments():
    """Auto-discover environment classes from the envs folder."""
    envs_dir = Path(__file__).parent / "envs"
    discovered = {}
    
    # Get all Python files in envs directory (except __init__.py)
    for file_path in envs_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue
        
        module_name = f"envs.{file_path.stem}"
        try:
            module = importlib.import_module(module_name)
            # Find all classes that inherit from Env
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Env) and obj != Env:
                    # Use filename as ID, class name for display
                    env_id = file_path.stem
                    # Convert class name to display name (e.g., "FileEnv" -> "File Env")
                    display_name = name.replace("Env", "").replace("_", " ").title()
                    if display_name.endswith(" "):
                        display_name = display_name[:-1] + "Env"
                    else:
                        display_name += " Env"
                    
                    discovered[env_id] = {
                        "name": display_name,
                        "module": module_name,
                        "class": name
                    }
        except Exception as e:
            print(f"Warning: Could not load environment from {module_name}: {e}")
            continue
    
    return discovered

# Discover environments on startup
AVAILABLE_ENVS = discover_environments()

def get_environment(env_name: str, num_rooms: Optional[int] = None, seed: Optional[int] = None) -> Env:
    """Get an environment instance by name."""
    if env_name not in AVAILABLE_ENVS:
        raise ValueError(f"Unknown environment: {env_name}")
    
    env_info = AVAILABLE_ENVS[env_name]
    module = importlib.import_module(env_info["module"])
    env_class = getattr(module, env_info["class"])
    
    # Pass num_rooms and seed to maze environment
    if env_name == 'maze':
        if num_rooms is not None:
            env = env_class(num_rooms=num_rooms, seed=seed)
        else:
            env = env_class()
    else:
        env = env_class()
    
    # Initialize environment (creates folders if needed)
    env.initialize()
    
    # Reset state if environment has a reset method (for stateful environments like maze)
    if hasattr(env, 'reset'):
        env.reset()
    
    return env

@app.route('/')
def index():
    """Serve the HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/environments', methods=['GET'])
def list_environments():
    """List all available environments."""
    env_list = [{"id": env_id, "name": info["name"]} for env_id, info in AVAILABLE_ENVS.items()]
    return jsonify({"environments": env_list})

@app.route('/set_environment', methods=['POST'])
def set_environment():
    """
    Set the environment for a chat session.
    Expects JSON: {"chat_id": "chat_id", "environment": "env_name", "num_rooms": int (optional), "seed": int (optional)}
    Returns JSON: {"success": true, "message": "..."}
    """
    data = request.get_json()
    chat_id = data.get('chat_id', 'default')
    env_name = data.get('environment', 'maze')
    num_rooms = data.get('num_rooms')
    seed = data.get('seed')
    
    try:
        from core.problem_state_utils import reset_problem_state
        env = get_environment(env_name, num_rooms=num_rooms, seed=seed)
        environments[chat_id] = env
        
        # Reset conversation with new environment
        conversations[chat_id] = [
            {"role": "system", "content": env.get_system_prompt()}
        ]
        
        # Clear any pending confirmations
        if chat_id in pending_confirmations:
            del pending_confirmations[chat_id]
        
        # Reset problem state
        reset_problem_state()
        
        return jsonify({
            "success": True,
            "message": f"Environment switched to {AVAILABLE_ENVS[env_name]['name']}",
            "environment": env_name
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/update_memory', methods=['POST'])
def update_memory():
    """
    Update the memory list for a chat session.
    Expects JSON: {"chat_id": "chat_id", "memory": ["memory1", "memory2"]}
    """
    data = request.get_json()
    chat_id = data.get('chat_id', 'default')
    new_memory = data.get('memory', [])
    
    memories[chat_id] = new_memory
    return jsonify({"success": True, "message": "Memory updated"})

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to receive user messages and return assistant responses via Server-Sent Events.
    Expects JSON: {"message": "user message", "chat_id": "chat_id"}
    Streams steps as they're generated, then returns final status.
    """
    data = request.get_json()
    user_message = data.get('message', '')
    chat_id = data.get('chat_id', 'default')
    
    # Get initial memory list from request
    if 'memory' in data:
        memories[chat_id] = data.get('memory', [])
    elif chat_id not in memories:
        memories[chat_id] = []
    
    # Initialize environment and conversation for this chat_id if needed
    if chat_id not in environments:
        from core.problem_state_utils import reset_problem_state
        env = get_environment('maze', num_rooms=3)  # Default environment
        environments[chat_id] = env
        conversations[chat_id] = [
            {"role": "system", "content": env.get_system_prompt()}
        ]
        # Reset problem state on first initialization
        reset_problem_state()
    
    env = environments[chat_id]
    
    # Check if there's a pending confirmation
    script_confirmation = None
    if chat_id in pending_confirmations:
        del pending_confirmations[chat_id]
    
    # Define memory provider to get latest memory state
    def memory_provider():
        return memories.get(chat_id, [])

    def generate():
        try:
            # Send model name first
            model_name = get_model_name()
            yield f"data: {json.dumps({'type': 'model_info', 'model': model_name})}\n\n"
            
            # Process the user message with streaming
            result = None
            for step in process_user_message_streaming(
                conversations[chat_id],
                user_message,
                env,
                web_mode=True,
                script_confirmation=script_confirmation,
                memory_provider=memory_provider
            ):
                # Check if this is the final result
                if step.get("type") == "final_result":
                    result = step
                    break
                # Yield each step immediately
                yield f"data: {json.dumps(step)}\n\n"
            
            # Update conversation and handle final result
            if result:
                conversations[chat_id] = result["conversation"]
                
                # If confirmation needed, store it
                if result.get("needs_confirmation"):
                    pending_confirmations[chat_id] = result["confirmation_tool_call"]
                    yield f"data: {json.dumps({'type': 'needs_confirmation', 'confirmation_tool_call': result['confirmation_tool_call']})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/confirm_tool', methods=['POST'])
def confirm_tool():
    """
    Endpoint to confirm or cancel a tool call (for run_python_script).
    Expects JSON: {"chat_id": "chat_id", "approved": true/false, "tool_call": {...}}
    """
    data = request.get_json()
    chat_id = data.get('chat_id', 'default')
    approved = data.get('approved', False)
    tool_call = data.get('tool_call', {})
    
    # Get memory list update if provided
    if 'memory' in data:
        memories[chat_id] = data.get('memory', [])
    elif chat_id not in memories:
        memories[chat_id] = []
    
    if chat_id not in conversations:
        return jsonify({"error": "Invalid chat_id"}), 400
    
    if chat_id not in environments:
        return jsonify({"error": "No environment set"}), 400
    
    if chat_id not in pending_confirmations:
        return jsonify({"error": "No pending confirmation"}), 400
    
    env = environments[chat_id]
    
    # Define memory provider
    def memory_provider():
        return memories.get(chat_id, [])

    def generate():
        try:
            # Send model name first
            model_name = get_model_name()
            yield f"data: {json.dumps({'type': 'model_info', 'model': model_name})}\n\n"
            
            # Process tool confirmation and continue loop
            result = None
            for step in process_tool_confirmation(
                conversations[chat_id],
                tool_call,
                approved,
                env,
                web_mode=True,
                memory_provider=memory_provider
            ):
                 # Check if this is the final result
                if step.get("type") == "final_result":
                    result = step
                    break
                yield f"data: {json.dumps(step)}\n\n"
            
            if result:
                conversations[chat_id] = result["conversation"]
                
                # If confirmation needed again (unlikely but possible), store it
                if result.get("needs_confirmation"):
                    pending_confirmations[chat_id] = result["confirmation_tool_call"]
                    yield f"data: {json.dumps({'type': 'needs_confirmation', 'confirmation_tool_call': result['confirmation_tool_call']})}\n\n"
                else:
                     # Clear pending confirmation (for the one we just processed)
                    if chat_id in pending_confirmations:
                        del pending_confirmations[chat_id]
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/environment_state', methods=['GET'])
def get_environment_state():
    """Get the current state of the environment for visualization."""
    chat_id = request.args.get('chat_id', 'default')
    
    if chat_id not in environments:
        return jsonify({"error": "No environment set"}), 400
    
    env = environments[chat_id]
    
    # Check if environment has get_state method (for maze)
    if hasattr(env, 'get_state'):
        state = env.get_state()
        return jsonify({"state": state, "has_state": True})
    else:
        return jsonify({"has_state": False})

@app.route('/env_reset', methods=['POST'])
def env_reset():
    """
    Reset the environment and conversation to initial state, but keep memory intact.
    Expects JSON: {"chat_id": "chat_id"}
    
    This endpoint:
    1. Resets the environment state
    2. Resets the conversation to just the system prompt
    3. Clears pending confirmations
    4. Writes the reset conversation to transcript.txt
    5. Preserves memory (not cleared)
    """
    from core.utils import write_transcript
    
    data = request.get_json()
    chat_id = data.get('chat_id', 'default')
    
    if chat_id not in environments:
        return jsonify({"success": False, "error": "No environment set"}), 400
    
    env = environments[chat_id]
    
    try:
        from core.problem_state_utils import reset_problem_state
        
        # Reset the environment state (but don't regenerate maze yet)
        if hasattr(env, 'reset'):
            env.reset()
        
        # Reset conversation to initial state (just system prompt)
        conversations[chat_id] = [
            {"role": "system", "content": env.get_system_prompt()}
        ]
        
        # Clear any pending confirmations
        if chat_id in pending_confirmations:
            del pending_confirmations[chat_id]
        
        # Reset problem state
        reset_problem_state()
        
        # Write the reset conversation to transcript immediately
        # This ensures transcript.txt reflects the reset state
        write_transcript(conversations[chat_id])
        
        # Memory is kept intact (not cleared)
        
        return jsonify({
            "success": True,
            "message": "Environment reset successfully. Memory preserved."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/maze/regenerate', methods=['POST'])
def regenerate_maze():
    """Regenerate the maze with new parameters."""
    data = request.get_json()
    chat_id = data.get('chat_id', 'default')
    num_rooms = data.get('num_rooms')
    seed = data.get('seed')
    
    if chat_id not in environments:
        return jsonify({"error": "No environment set"}), 400
    
    env = environments[chat_id]
    
    # Check if it's a maze environment
    if not hasattr(env, 'regenerate_maze'):
        return jsonify({"error": "Current environment is not a maze"}), 400
    
    try:
        env.regenerate_maze(num_rooms=num_rooms, seed=seed)
        
        # Reset conversation with new environment state
        conversations[chat_id] = [
            {"role": "system", "content": env.get_system_prompt()}
        ]
        
        # Clear any pending confirmations
        if chat_id in pending_confirmations:
            del pending_confirmations[chat_id]
        
        state = env.get_state()
        return jsonify({
            "success": True,
            "message": f"Maze regenerated with {env.num_rooms} rooms",
            "state": state
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/problem_state', methods=['GET'])
def get_problem_state():
    """Get the current problem state."""
    from core.problem_state_utils import read_problem_state
    state = read_problem_state()
    if state is None:
        return jsonify({"has_state": False, "message": "No problem state updates yet"})
    return jsonify({"has_state": True, "state": state})

if __name__ == '__main__':
    # Initialize default environment
    env = get_environment('maze', num_rooms=3)
    env.initialize()
    
    print("🚀 Agent Web Server Starting...")
    print("📡 Server running on http://localhost:8080")
    print("💬 Chat endpoint: POST http://localhost:8080/chat")
    print(f"🌍 Available environments: {', '.join(AVAILABLE_ENVS.keys())}")
    print("\n" + "="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=8080, use_reloader=False)
