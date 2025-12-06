import os
import json
from typing import Dict, List
from pathlib import Path
from envs import Env

class FileEnv(Env):
    """File manipulation environment."""
    
    def __init__(self):
        self.agent_folder = "folder_for_agent"
    
    def get_tools(self) -> List[Dict]:
        """Return the list of tool definitions."""
        return [
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
    
    def list_files(self) -> Dict:
        """List all files in the agent's working directory."""
        try:
            files = os.listdir(self.agent_folder)
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}
    
    def read(self, file_name: str) -> Dict:
        """Read the contents of a file."""
        try:
            file_path = Path(self.agent_folder) / file_name
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}
    
    def write(self, file_name: str, file_content: str) -> Dict:
        """Write content to a file."""
        try:
            file_path = Path(self.agent_folder) / file_name
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            return {"status": "success", "message": f"Content written to {file_name}"}
        except Exception as e:
            return {"error": str(e)}
    
    def rename(self, current_file_name: str, new_file_name: str) -> Dict:
        """Rename a file."""
        try:
            current_path = Path(self.agent_folder) / current_file_name
            new_path = Path(self.agent_folder) / new_file_name
            os.rename(current_path, new_path)
            return {"status": "success", "message": f"Renamed {current_file_name} to {new_file_name}"}
        except Exception as e:
            return {"error": str(e)}
    
    def run_python_script(self, python_file_name: str) -> Dict:
        """Run a Python script file."""
        try:
            script_path = Path(self.agent_folder) / python_file_name
            if not script_path.exists():
                return {"error": f"Script {python_file_name} not found"}
            
            # Change to the agent folder before running
            current_dir = os.getcwd()
            os.chdir(self.agent_folder)
            
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
    
    def delete_files(self, list_of_files_to_delete: List[str]) -> Dict:
        """Delete one or more files."""
        results = []
        for file_name in list_of_files_to_delete:
            try:
                file_path = Path(self.agent_folder) / file_name
                os.remove(file_path)
                results.append({"file": file_name, "status": "success"})
            except Exception as e:
                results.append({"file": file_name, "status": "error", "error": str(e)})
        return {"results": results}
    
    def get_handlers(self) -> Dict[str, callable]:
        """Return a dictionary mapping tool names to handler functions."""
        return {
            "list_files": self.list_files,
            "read": self.read,
            "write": self.write,
            "rename": self.rename,
            "run_python_script": self.run_python_script,
            "delete_files": self.delete_files
        }
    
    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return "You are a helpful assistant with file manipulation capabilities."
    
    def get_agent_folder(self) -> str:
        """Return the agent folder path."""
        return self.agent_folder

