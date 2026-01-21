import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

PROBLEM_STATE_SIGNATURE_FILE = "problem_state_type_signature.json"
PROBLEM_STATE_FILE = "problem_state.json"

def get_signature_file_path() -> Path:
    """Get the path to the problem state type signature file."""
    return Path(PROBLEM_STATE_SIGNATURE_FILE)

def read_type_signature() -> Optional[Dict[str, Any]]:
    """Read the current type signature from the JSON file."""
    file_path = get_signature_file_path()
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def write_type_signature(signature: Dict[str, Any]) -> None:
    """Write the type signature to the JSON file."""
    file_path = get_signature_file_path()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(signature, f, indent=2)

def validate_type_signature(signature: Dict[str, Any]) -> bool:
    """Validate that the type signature has the expected structure."""
    if not isinstance(signature, dict):
        return False
    if "format" not in signature:
        return False
    format_obj = signature["format"]
    if not isinstance(format_obj, dict):
        return False
    if format_obj.get("type") != "json_schema":
        return False
    if "schema" not in format_obj:
        return False
    return True

def get_edit_type_signature_tool_def() -> Dict[str, Any]:
    """Get the tool definition for editing the problem state type signature."""
    return {
        "type": "function",
        "function": {
            "name": "edit_problem_state_type_signature",
            "description": """Set the type signature for the update_problem_state tool using OpenAI's structured outputs format. You should use this tool to define the structure of the problem state and the fields that you will use to update it. Try to create a type signature that allows for a crisp representation of the problem state and your progress towards solving the task, so that seeing the problem state is helpful for you to reason about the problem and select the best next actions.

The type_signature must follow OpenAI's response_format structure for JSON schema mode:
{
    "format": {
        "type": "json_schema",
        "name": "problem_state",  // Optional: name for the schema
        "schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",  // or "number", "boolean", "array", "object"
                    "description": "Description of this field"
                }
                // Add more properties as needed
            },
            "required": ["field_name"],  // List of required field names
            "additionalProperties": false  // Recommended: prevents extra fields
        },
        "strict": true  // Recommended: enforces strict schema validation
    }
}

Key requirements:
- The root must have a "format" key
- format.type must be exactly "json_schema"
- format.schema must be a valid JSON Schema object
- format.schema.type should be "object" for structured data
- format.schema.properties defines the fields and their types
- format.schema.required lists which fields are mandatory
- Set additionalProperties: false to prevent unexpected fields
- Set strict: true for strict validation

Example for a problem state with reasoning and status:
{
    "format": {
        "type": "json_schema",
        "name": "problem_state",
        "schema": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Your reasoning about the current problem state"
                },
                "status": {
                    "type": "string",
                    "enum": ["in_progress", "blocked", "completed"],
                    "description": "Current status of the problem"
                },
                "progress_percent": {
                    "type": "number",
                    "description": "Estimated progress as a percentage (0-100)"
                }
            },
            "required": ["reasoning", "status"],
            "additionalProperties": false
        },
        "strict": true
    }
}

Once set, update_problem_state will use this schema to validate inputs.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "type_signature": {
                        "type": "object",
                        "description": "The complete type signature dict following OpenAI's structured outputs format with format.type='json_schema'"
                    }
                },
                "required": ["type_signature"]
            }
        }
    }

def get_problem_state_tool_def() -> Dict[str, Any]:
    """Get the tool definition for update_problem_state, dynamically loaded from the JSON file."""
    signature = read_type_signature()
    if signature is None:
        return {
            "type": "function",
            "function": {
                "name": "update_problem_state",
                "description": "Update the problem state. Type signature must be defined first using edit_problem_state_type_signature.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    format_obj = signature.get("format", {})
    schema = format_obj.get("schema", {})
    
    return {
        "type": "function",
        "function": {
            "name": "update_problem_state",
            "description": "Update the problem state according to the defined type signature. You should use this tool to keep a crisp representation of the problem state and your progress towards solving the task.",
            "parameters": schema
        }
    }

def edit_problem_state_type_signature(type_signature: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for editing the problem state type signature."""
    if not validate_type_signature(type_signature):
        return {"error": "Invalid type signature format. Must have 'format' with 'type': 'json_schema' and 'schema'."}
    
    try:
        write_type_signature(type_signature)
        return {"status": "success", "message": "Problem state type signature updated successfully"}
    except Exception as e:
        return {"error": str(e)}

def get_problem_state_file_path() -> Path:
    """Get the path to the problem state file."""
    return Path(PROBLEM_STATE_FILE)

def reset_problem_state() -> None:
    """Reset the problem state by deleting the state file."""
    file_path = get_problem_state_file_path()
    if file_path.exists():
        file_path.unlink()

def read_problem_state() -> Optional[Dict[str, Any]]:
    """Read the current problem state from the JSON file."""
    file_path = get_problem_state_file_path()
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def write_problem_state(state: Dict[str, Any]) -> None:
    """Write the problem state to the JSON file."""
    file_path = get_problem_state_file_path()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def update_problem_state(problem_state_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for updating the problem state. Validates against current type signature."""
    signature = read_type_signature()
    if signature is None:
        return {"error": "Problem state type signature not defined. Use edit_problem_state_type_signature first."}
    
    try:
        format_obj = signature.get("format", {})
        schema = format_obj.get("schema", {})
        required = schema.get("required", [])
        
        for field in required:
            if field not in problem_state_data:
                return {"error": f"Missing required field: {field}"}
        
        write_problem_state(problem_state_data)
        
        return {
            "status": "success",
            "message": "Problem state updated",
            "state": problem_state_data
        }
    except Exception as e:
        return {"error": str(e)}
