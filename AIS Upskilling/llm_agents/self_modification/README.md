# Self-Modification: LLM Agent Self-Editing Examples

This README is written by Claude. It should be mostly accurate.

This folder contains examples of LLM agents that can modify their own code, demonstrating advanced capabilities in self-improvement and adaptation.

## Core Files

### editable_self_mod.py
- Core implementation of a self-modifying LLM agent
- Implements robust safety features for self-modification:
  - Automatic backup creation in `do_not_edit/real_self_mod.py`
  - User approval system for file modifications
  - Safe command execution with user confirmation
- Includes sophisticated conversation management with:
  - Token counting and conversation summarization
  - State tracking through a multi-option system
  - Transcript management across restarts

### tool_use_example.py
- Simple demonstration of tool use in an LLM agent
- Shows basic pattern for tool definition and handling
- Implements a basic value setter tool as an example
- Useful reference for understanding the core tool-use pattern

## Supporting Files

### agent_scratchpad.sh
- Temporary file used for executing Python commands
- Created and managed by the self-modifying agents
- Provides a safe way to execute generated Python code

### user_check.py
- Temporary file created when modifying existing files
- Used for user review before applying changes
- Part of the safety system for file modifications

## Key Features

1. **Safety First**
   - All file modifications require user approval
   - Automatic backups before modifications
   - Command execution with user confirmation
   - Separate files for review before changes

2. **Conversation Management**
   - State tracking through a sophisticated options system
   - Conversation history preservation across restarts
   - Automatic summarization for long conversations

3. **Tool System**
   - Extensible tool definition format
   - Safe command execution
   - File modification capabilities
   - State persistence across interactions

4. **Self-Modification Capabilities**
   - Ability to modify own source code
   - Safe restart mechanism after modifications
   - Backup system for reverting changes
   - Type checking and validation

## Usage

To use the self-modifying agents:

1. Start with either `real_self_mod.py` or `editable_self_mod.py`
2. The agent can be asked to modify itself by editing its source code
3. Changes are written to `user_check.py` first for review
4. After approval, changes are applied and the agent restarts
5. Previous versions are backed up in the `do_not_edit` folder

## Safety Notes

- Always review code changes in `user_check.py` before approving
- Keep backups in `do_not_edit` folder for recovery
- All command executions require explicit user approval
- The agent cannot bypass the safety mechanisms

## Development

When extending the agent's capabilities:
1. Use the existing tool system for new features
2. Maintain the safety checks and user approval system
3. Add appropriate error handling and validation
4. Consider adding unit tests for new functionality