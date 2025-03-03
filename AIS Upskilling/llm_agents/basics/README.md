# Basics: LLM Agent Examples

This README was written by Claude. It's a bit over-the-top, but it conveys the key ideas.

This folder contains a series of Python scripts demonstrating increasingly complex interactions with LLMs (Large Language Models) using the OpenAI API. Each file builds upon the concepts introduced in the previous ones.

## File Descriptions

### basics1_api.py
- Implements the simplest possible conversation between a human and an OpenAI LLM
- Demonstrates basic streaming API usage with GPT-4
- Shows how to maintain a conversation history
- Uses a simple loop for back-and-forth interaction

### basics2_tool_use.py
- Introduces the concept of tool use (function calling) with LLMs
- Implements a simple environment with a toggle switch
- Shows how to define and handle tool (function) calls
- Demonstrates the basic pattern of:
  1. Getting assistant's response
  2. Handling tool calls
  3. Feeding tool results back to the assistant

### basics3_tool_w_args.py
- Extends tool use by adding arguments to functions
- Implements a value setter tool that takes numerical arguments
- Shows proper argument parsing and validation
- Demonstrates more complex tool call handling with parameters

### basics4_email_code_tool.py
- Introduces two powerful tools: code execution and email sending
- Shows how to safely execute arbitrary Python code with user approval
- Implements email functionality using SMTP
- Demonstrates handling multiple tools with different parameter requirements
- Includes proper error handling and user confirmation steps

### basics5_error_correction.py
- Builds upon basics4 with advanced error handling and conversation management
- Adds token counting and conversation summarization
- Implements a sophisticated state machine for tracking conversation flow
- Shows how to handle errors and allow the assistant to correct mistakes
- Includes user interruption handling during tool execution

### basics6_env_tools.py
- Implements a simple game environment with rooms and navigation
- Shows how to create and manage a stateful environment
- Demonstrates dynamic tool availability based on game state
- Includes basic game mechanics (movement, room exploration)
- Shows how to track and manage game progress

### basics7_env_2_tools.py
- Extends the environment concept with a more complex maze-like structure
- Implements a sophisticated multi-room environment with items and puzzles
- Shows advanced state management with conditional tool availability
- Demonstrates item collection and interaction mechanics
- Includes a goal-oriented puzzle solving scenario

### basics8_bash_commands.py
- Implements safe execution of bash commands through LLM
- Shows cross-platform command execution handling (Windows/Unix)
- Includes robust error handling and user confirmation
- Demonstrates shell detection and environment awareness
- Implements command sanitization and validation

### gridworld_agent.py
- Implements a classic gridworld environment for reinforcement learning
- Shows how to create an LLM-based agent that can navigate a 2D grid
- Demonstrates sophisticated decision-making with brainstorming and critique phases
- Implements recursive thinking and self-correction
- Shows how to visualize agent actions and environment state

## Common Patterns

Throughout these examples, you'll see several recurring patterns:
1. Tool definition using OpenAI's function calling format
2. Conversation management and history tracking
3. Error handling and recovery
4. User confirmation for potentially dangerous operations
5. State management between interactions
6. Token counting and conversation summarization

## Usage

Each file can be run independently. Most require:
1. OpenAI API key set in your environment
2. Python 3.7+
3. Required packages (openai, etc.)

For files that use email functionality, you'll need to set up:
- EMAIL_USER environment variable
- EMAIL_PASSWORD environment variable
- Appropriate SMTP settings