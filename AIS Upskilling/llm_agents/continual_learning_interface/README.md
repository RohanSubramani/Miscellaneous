# Continual Learning Interface

This README was written by Claude 4.5 Sonnet. It's a bit verbose, but pretty accurate (as of Dec 5 2025).

A modular framework for building LLM agents with environment-based interactions, memory retrieval, and a web interface.

## Overview

This framework provides:
- **Modular environments** - Easily create new agent environments by extending the `Env` base class
- **Memory retrieval** - Memory system that retrieves relevant past experiences
- **Agent loop with self-assessment** - Agents reason about their progress and decide whether to continue or ask for help
- **Web interface** - Browser-based UI with streaming responses
- **Standalone mode** - Can run agents via CLI without the web server

## Architecture

### Core Components

- **`core/engine.py`** - Main agent loop with streaming support, tool execution, and continue/stop decision logic
- **`core/llm.py`** - OpenAI client configuration and model settings
- **`core/memory.py`** - Memory retrieval system that determines when past experiences are relevant
- **`core/tools.py`** - Generic tool call handler that works with any environment
- **`core/utils.py`** - Utilities for transcript logging and conversation cleaning

### Environments

Environments define what tools are available and how they work. Each environment extends the `Env` base class and implements:
- `get_tools()` - Tool definitions in OpenAI format
- `get_handlers()` - Mapping of tool names to handler functions
- `get_system_prompt()` - Initial system prompt for the agent
- `get_agent_folder()` - Working directory path (if applicable)

**Built-in Environments:**
- **`envs/maze.py`** (`MazeEnv`) - Navigate a randomly generated maze, find items, and solve puzzles
- **`envs/file_agent.py`** (`FileEnv`) - File manipulation tools (read, write, delete, run Python scripts)

New environments are automatically discovered by the web server when placed in the `envs/` folder.

## Agent Loop

The agent follows this loop:

1. **Retrieval** - Check if any memories are relevant to the current situation
2. **Response** - Get LLM response (may include tool calls)
3. **Tool Execution** - Execute any requested tools
4. **Follow-up** - Get LLM response after tool execution
5. **Reasoning** - Agent assesses its current state using 8 predefined options:
   - Options 1-2: Done, user's turn
   - Options 3-4: Continue working (making progress or fixing mistakes)
   - Options 5-6: Ask user for help or clarification
   - Options 7-8: Stuck, need to reassess or ask for help
6. **Continue/Stop Decision** - Loop continues if agent chooses options 3, 4, or 7

This self-assessment mechanism helps agents work autonomously while knowing when to ask for help.

## Installation

```bash
pip install -r requirements.txt
```

**Requirements:**
- flask>=2.0.0
- flask-cors>=3.0.0
- openai>=1.0.0

You'll also need an OpenAI API key set as `OPENAI_API_KEY` environment variable.

## Usage

### Web Server (Recommended)

Start the web server:

```bash
python web_server.py
```

Then open `http://localhost:8080` in your browser.

**Features:**
- Select environment (Maze, File Agent, etc.)
- Chat with streaming responses
- View environment state (for maze visualization)
- Add/manage memories that persist across resets
- Reset environment without losing memories
- Configure maze parameters (number of rooms, seed)

### Standalone CLI

For file manipulation tasks:

```bash
python STANDALONE_basic_tool_agent.py
```

This runs a command-line interface with the file agent environment.

## Creating Custom Environments

1. Create a new file in `envs/`, e.g., `envs/my_env.py`
2. Extend the `Env` base class:

```python
from envs import Env
from typing import Dict, List

class MyEnv(Env):
    def get_tools(self) -> List[Dict]:
        # Return OpenAI tool definitions
        return [...]
    
    def get_handlers(self) -> Dict[str, callable]:
        # Map tool names to handler functions
        return {"my_tool": self.my_tool_handler}
    
    def get_system_prompt(self) -> str:
        return "System prompt for your environment"
    
    def get_agent_folder(self) -> str:
        return ""  # Or path to working directory
    
    def my_tool_handler(self, arg1, arg2):
        # Implement your tool
        return {"status": "success", "result": "..."}
```

3. Restart the web server - your environment will be auto-discovered

## Configuration

Edit `core/llm.py` to change models:

```python
GLOBAL_MODEL = "gpt-5-nano"  # Main agent model
RETRIEVAL_MODEL = "gpt-5-nano"  # Memory retrieval model
```

## File Structure

```
continual_learning_interface/
├── core/                      # Core agent components
│   ├── engine.py             # Main agent loop
│   ├── llm.py                # LLM client config
│   ├── memory.py             # Memory retrieval
│   ├── tools.py              # Tool execution
│   └── utils.py              # Utilities
├── envs/                      # Environment definitions
│   ├── __init__.py           # Env base class
│   ├── maze.py               # Maze environment
│   └── file_agent.py         # File manipulation environment
├── web_server.py              # Flask web server
├── STANDALONE_basic_tool_agent.py  # CLI version
├── index.html                 # Web UI
└── requirements.txt
```

## Notes

- Conversation history is saved to `transcript.txt` after each turn
- The maze environment generates random mazes with configurable room counts and seeds
- The file agent works in the `folder_for_agent/` directory
- Memory retrieval uses a separate LLM call to decide which memories are relevant
- Tool confirmations (e.g., for running Python scripts) are handled via the web UI

