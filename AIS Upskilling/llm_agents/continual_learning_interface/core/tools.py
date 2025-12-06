import json
from typing import Dict, Any, Optional
from envs import Env

class MockToolCall:
    def __init__(self, tool_call_data):
        self.id = tool_call_data["id"]
        self.function = MockFunction(tool_call_data)

class MockFunction:
    def __init__(self, tool_call_data):
        self.name = tool_call_data["name"]
        self.arguments = json.dumps(tool_call_data["arguments"])

def handle_tool_call(tool_call, env: Env, web_mode=False, script_confirmation=None) -> Optional[Dict[str, Any]]:
    """
    Handle a tool call using the environment's handlers.
    
    Args:
        tool_call: The tool call object from OpenAI
        env: The environment instance
        web_mode: If True, skip console input/output
        script_confirmation: For run_python_script in web mode, pass 'approved' or 'cancelled'
    
    Returns:
        dict with tool_call_id and output, or None if confirmation needed
    """
    args = json.loads(tool_call.function.arguments)
    handlers = env.get_handlers()
    tool_name = tool_call.function.name
    
    if tool_name not in handlers:
        result = {"error": f"Unknown function: {tool_name}"}
    else:
        handler = handlers[tool_name]
        
        # Special handling for run_python_script (needs confirmation)
        if tool_name == "run_python_script":
            if web_mode:
                if script_confirmation == 'approved':
                    result = handler(args["python_file_name"])
                elif script_confirmation == 'cancelled':
                    result = {"status": "cancelled", "message": "Script execution cancelled by user"}
                else:
                    # Need confirmation
                    return None
            else:
                # CLI mode confirmation (simplified for now as we focus on web)
                confirmation = input(f"Are you sure you want to execute {args['python_file_name']}? (y/n): ")
                if confirmation.lower() == 'y':
                    result = handler(args["python_file_name"])
                else:
                    result = {"status": "cancelled", "message": "Script execution cancelled"}
        else:
            # Generic handler call
            import inspect
            sig = inspect.signature(handler)
            param_names = list(sig.parameters.keys())
            
            # Build arguments list based on function signature
            handler_args = []
            for param_name in param_names:
                if param_name in args:
                    handler_args.append(args[param_name])
                elif param_name == 'self':
                    continue
                else:
                    pass
            
            try:
                if len(handler_args) == 0:
                    result = handler()
                elif len(handler_args) == 1:
                    result = handler(handler_args[0])
                elif len(handler_args) == 2:
                    result = handler(handler_args[0], handler_args[1])
                else:
                    result = handler(*handler_args)
            except Exception as e:
                result = {"error": f"Error executing tool: {str(e)}"}

    if not web_mode:
        print(f"\nTool: {tool_name}\nArgs: {json.dumps(args)}\nResult: {json.dumps(result)}\n")
    
    return {
        "tool_call_id": tool_call.id,
        "output": json.dumps(result)
    }
