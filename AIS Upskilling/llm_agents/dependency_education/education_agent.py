import os
import json
from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple
import sys
from pathlib import Path
import glob

client = OpenAI()

GLOBAL_MODEL = "gpt-4.1" # "o4-mini" # "gpt-4.1-mini"
GRAPHS_DIR = "graphs"

def ensure_graphs_dir():
    """Ensure the graphs directory exists."""
    os.makedirs(GRAPHS_DIR, exist_ok=True)

def get_available_graphs() -> List[str]:
    """Get list of available graph files."""
    ensure_graphs_dir()
    graph_files = glob.glob(os.path.join(GRAPHS_DIR, "*.json"))
    return [os.path.splitext(os.path.basename(f))[0] for f in graph_files 
            if os.path.basename(f) != "available_graphs.json"]

def get_graph_path(graph_name: str) -> str:
    """Get the full path for a graph file."""
    return os.path.join(GRAPHS_DIR, f"{graph_name}.json")

def save_graph_state(graph_name: str):
    """Save the current graph state to a file."""
    ensure_graphs_dir()
    graph_data = export_graph_json()
    with open(get_graph_path(graph_name), "w") as f:
        json.dump(graph_data, f, indent=2)

def load_graph_state(graph_name: str) -> bool:
    """Load a specific graph state from file."""
    try:
        with open(get_graph_path(graph_name), "r") as f:
            data = json.load(f)
            
        # Clear current graph
        dependency_graph.clear()
        
        # Create nodes first
        for node_data in data["nodes"]:
            get_or_create_node(node_data["id"], node_data["explanation"])
            
        # Then establish dependencies using the edges
        for edge in data["edges"]:
            from_node = dependency_graph[edge["from"]]
            to_node = dependency_graph[edge["to"]]
            if to_node not in from_node.dependencies:
                from_node.dependencies.append(to_node)
        
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error loading graph: {e}")
        return False

def select_or_create_graph() -> Optional[str]:
    """Present user with options to load existing graph or create new one."""
    available_graphs = get_available_graphs()
    
    if available_graphs:
        print("\nAvailable graphs:")
        for i, name in enumerate(available_graphs, 1):
            print(f"{i}. {name}")
        print(f"{len(available_graphs) + 1}. Create new graph")
        
        while True:
            try:
                choice = input("\nEnter number of your choice: ")
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_graphs):
                    return available_graphs[choice_num - 1]
                elif choice_num == len(available_graphs) + 1:
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    # Create new graph
    while True:
        graph_name = input("\nEnter name for new graph: ").strip()
        if not graph_name:
            print("Graph name cannot be empty.")
            continue
            
        if graph_name in available_graphs:
            overwrite = input(f"Graph '{graph_name}' already exists. Overwrite? (y/n): ").lower().strip()
            if overwrite == 'y':
                return graph_name
            continue
        
        return graph_name
    
    return None

def update_available_graphs(current_graph: str):
    """Update the available_graphs.json file with the list of graphs and current selection."""
    ensure_graphs_dir()
    available = get_available_graphs()
    data = {
        "graphs": available,
        "current": current_graph
    }
    with open(os.path.join(GRAPHS_DIR, "available_graphs.json"), "w") as f:
        json.dump(data, f, indent=2)

def update_visualization():
    """Update the graph data JSON file."""
    if not hasattr(update_visualization, 'current_graph'):
        update_visualization.current_graph = None
    
    if update_visualization.current_graph:
        save_graph_state(update_visualization.current_graph)
        update_available_graphs(update_visualization.current_graph)

def get_response(conversation):
    response = client.chat.completions.create(
        model=GLOBAL_MODEL,
        messages=conversation,
        tools=functions,
        tool_choice="required"
    )
    return response.choices[0].message

# Define callable functions (tools)
functions = [
    {
        "type": "function",
        "function": {
            "name": "create_explainer",
            "description": "Create an explainer with a detailed explanation and its dependencies, integrating a central example problem and its solution when appropriate, at the level of college course notes. This is a high level of detail! It should be sufficient, by itself, for a smart student with enough prerequisite knowledge to learn the topic. The explanation can include LaTeX math using $...$ for inline math and $$...$$ or \\[...\\] for display math.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explainer_title": {
                        "type": "string",
                        "description": "Title of the explainer."
                    },
                    "detailed_explanation": {
                        "type": "string",
                        "description": "A detailed explanation, including LaTeX math (using $...$ for inline and $$...$$ or \\[...\\] for display math). Should include central example problems and their solutions, at the level of college course notes."
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of dependency titles for the explainer. Each dependency will be initialized with 'No explanation available yet.' if it doesn't exist. If a topic is very basic, you can just return an empty list."
                    }
                },
                "required": ["explainer_title", "detailed_explanation", "dependencies"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_full_dependency_graph",
            "description": "Return the full dependency graph (or a subgraph from an optional root) as a formatted string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root": {
                        "type": "string",
                        "description": "Optional root title from which to print the subgraph."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_explanation",
            "description": "Return the explainer's explanation and its dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "explanation_title": {
                        "type": "string",
                        "description": "Title of the explainer."
                    }
                },
                "required": ["explanation_title"]
            }
        }
    }
]

# Global dependency graph for explainers
dependency_graph = {}

class ExplainerNode:
    def __init__(self, title, explanation):
        self.title = title
        self.explanation = explanation
        self.dependencies = []  # List of ExplainerNode objects
        self.relevant_for = []  # List of ExplainerNode objects that depend on this node

def get_or_create_node(title, default_explanation="No explanation available yet."):
    if title in dependency_graph:
        return dependency_graph[title]
    else:
        node = ExplainerNode(title, default_explanation)
        dependency_graph[title] = node
        return node

def export_graph_json() -> dict:
    """Export the dependency graph as JSON for visualization."""
    nodes = []
    edges = []
    visited = set()
    
    def process_node(node):
        if node.title in visited:
            return
        visited.add(node.title)
        
        # Add node
        nodes.append({
            "id": node.title,
            "label": node.title,
            "explanation": node.explanation,
            "dependencies": [dep.title for dep in node.dependencies],
            "relevant_for": [parent.title for parent in node.relevant_for]
        })
        
        # Add edges to dependencies
        for dep in node.dependencies:
            edges.append({
                "from": node.title,
                "to": dep.title
            })
            process_node(dep)
    
    # Process all nodes
    for node in dependency_graph.values():
        process_node(node)
    
    return {"nodes": nodes, "edges": edges}

def would_create_cycle(node: ExplainerNode, new_dependency: ExplainerNode, visited=None) -> bool:
    """Check if adding new_dependency to node's dependencies would create a cycle.
    Returns True if a cycle would be created, False otherwise."""
    if visited is None:
        visited = set()
    
    # If we've seen this node before in this path, we found a cycle
    if node.title in visited:
        return True
    
    # Add current node to visited set
    visited.add(node.title)
    
    # Check if new_dependency depends on current node (would create cycle)
    for dep in new_dependency.dependencies:
        if dep.title == node.title or would_create_cycle(node, dep, visited.copy()):
            return True
    
    return False

def create_explainer(explainer_title: str, detailed_explanation: str, dependencies: list = None) -> dict:
    """Create or update an explainer with explanation and dependencies."""
    node = get_or_create_node(explainer_title)
    node.explanation = detailed_explanation
    
    # Handle dependencies if provided
    if dependencies:
        # Track rejected dependencies due to cycles
        rejected_deps = []
        
        # Store old dependencies to handle cleanup
        old_dependencies = set(dep.title for dep in node.dependencies)
        new_dependencies = set(dependencies)
        
        # Remove this node from relevant_for of dependencies that are no longer needed
        for old_dep_title in old_dependencies - new_dependencies:
            if old_dep_title in dependency_graph:
                old_dep = dependency_graph[old_dep_title]
                if node in old_dep.relevant_for:
                    old_dep.relevant_for.remove(node)
        
        # Clear existing dependencies to prevent duplicates
        node.dependencies = []
        
        for dep_title in dependencies:
            child_node = get_or_create_node(dep_title)
            
            # Check for cycles before adding dependency
            if would_create_cycle(node, child_node):
                rejected_deps.append(dep_title)
                continue
                
            node.dependencies.append(child_node)
            # Update relevant_for relationship
            if node not in child_node.relevant_for:
                child_node.relevant_for.append(node)
        
        if rejected_deps:
            result = {
                "status": "partial_success",
                "message": f"Explainer '{explainer_title}' created/updated, but some dependencies were rejected to prevent cycles: {', '.join(rejected_deps)}"
            }
        else:
            result = {
                "status": "success",
                "message": f"Explainer '{explainer_title}' created/updated with all dependencies."
            }
    else:
        result = {
            "status": "success",
            "message": f"Explainer '{explainer_title}' created/updated without dependencies."
        }
    
    update_visualization()
    return result

def read_full_dependency_graph(root: str = None) -> dict:
    def format_node(node, visited, indent=""):
        if node.title in visited:
            return indent + f"(Cycle detected at {node.title})\n"
        visited.add(node.title)
        result = indent + f"Title: {node.title}\n"
        result += indent + f"Explanation: {node.explanation}\n"
        if node.dependencies:
            result += indent + "Dependencies:\n"
            for child in node.dependencies:
                result += format_node(child, visited, indent + "  ")
        return result
    if root:
        if root not in dependency_graph:
            return {"error": f"No explainer found with title '{root}'."}
        output = format_node(dependency_graph[root], set())
    else:
        output = ""
        for title, node in dependency_graph.items():
            output += format_node(node, set()) + "\n"
    return {"graph": output}

def read_explanation(explanation_title: str) -> dict:
    if explanation_title not in dependency_graph:
        return {"error": f"No explainer found with title '{explanation_title}'."}
    node = dependency_graph[explanation_title]
    deps = [dep.title for dep in node.dependencies]
    relevant_for = [parent.title for parent in node.relevant_for]
    return {
        "explanation": node.explanation,
        "dependencies": deps,
        "relevant_for": relevant_for
    }

def handle_tool_call(tool_call):
    args = json.loads(tool_call.function.arguments)
    
    if tool_call.function.name == "create_explainer":
        result = create_explainer(
            args["explainer_title"], 
            args["detailed_explanation"],
            args["dependencies"]
        )
    elif tool_call.function.name == "read_full_dependency_graph":
        root = args.get("root")
        result = read_full_dependency_graph(root) if root else read_full_dependency_graph()
    elif tool_call.function.name == "read_explanation":
        result = read_explanation(args["explanation_title"])
    else:
        result = {"error": "Unknown function"}
    
    print("\n" + "="*50)
    print(f"Executed tool call: {tool_call.function.name}")
    print(f"Arguments: {json.dumps(args, indent=2)}")
    print("Tool call result:")
    print(json.dumps(result, indent=2))
    print("="*50 + "\n")
    
    return {
        "tool_call_id": tool_call.id,
        "output": json.dumps(result)
    }

def write_transcript(conversation):
    with open('transcript.txt', 'w', encoding='utf-8') as f:
        json.dump(conversation, f, indent=4, ensure_ascii=False)

def convert_to_finetuning_format(conversation: List[Dict[str, Any]], available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert the conversation history to OpenAI's finetuning format."""
    filtered_messages = []
    for msg in conversation:        
        new_msg = {"role": msg["role"]}
        
        if "tool_call_id" in msg:
            new_msg["tool_call_id"] = msg["tool_call_id"]

        if msg.get("content"):
            new_msg["content"] = msg["content"]
            
        if "tool_calls" in msg:
            new_msg["tool_calls"] = msg["tool_calls"]
        
        if "weight" in msg:
            new_msg["weight"] = msg["weight"]
        
        filtered_messages.append(new_msg)
    
    finetuning_data = {
        "messages": filtered_messages,
        "tools": available_tools
    }
    
    return finetuning_data

def create_weighted_revision(conversation: List[Dict[str, Any]], replacement_response: str) -> List[Dict[str, Any]]:
    """Create a version of the conversation with a replacement for the last assistant message."""
    # Deep copy the conversation to avoid modifying the original
    modified_conv = json.loads(json.dumps(conversation))
    
    # Add weight 0 to all assistant messages
    for msg in modified_conv:
        if msg["role"] == "assistant":
            msg["weight"] = 0
    
    # Replace the last assistant message with the new response and weight 1
    for i in range(len(modified_conv) - 1, -1, -1):
        if modified_conv[i]["role"] == "assistant":
            modified_conv[i] = {
                "role": "assistant",
                "content": replacement_response,
                "weight": 1
            }
            break
    
    return modified_conv

def save_to_jsonl(conversation: List[Dict[str, Any]], available_tools: List[Dict[str, Any]], filename: str = "revision_finetuning.jsonl") -> None:
    """Save the weighted revision version of the conversation with a replacement response."""
    # Get the replacement response from the user
    print("\nCurrent last assistant response:")
    for msg in reversed(conversation):
        if msg["role"] == "assistant":
            print(f"Assistant: {msg.get('content', '')}")
            break
    
    replacement = input("\nEnter the replacement for the last assistant response: ")
    
    # Create the weighted revision with the replacement
    revised_conv = create_weighted_revision(conversation, replacement)
    revised_data = convert_to_finetuning_format(revised_conv, available_tools)
    json_line = json.dumps(revised_data, ensure_ascii=False)
    
    # Append to file
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode, encoding="utf-8") as f:
        f.write(json_line + "\n")
    
    print(f"Revised conversation saved to {filename}")

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

continue_options = [3, 4, 7]  # Options where the assistant should continue without user input

def generate_continue_question(response_dict):
    """Generate the question for the model about how to continue."""
    question = "You can choose between the following options:\n\n"
    for key, value in response_dict.items():
        question += f"{key}. {value}\n\n"
    question += "Please brainstorm to figure out your current state, then select the corresponding option number."
    return question

continue_question = generate_continue_question(cont_response_dict)

def clean_conversation_for_structured_response(conversation):
    """Remove tool_calls from conversation history and convert tool messages for structured response API."""
    cleaned_conv = []
    for msg in conversation:
        if msg["role"] == "tool":
            # Convert tool messages into assistant messages with formatted content
            cleaned_msg = {
                "role": "assistant",
                "content": f"Tool response (ID: {msg['tool_call_id']}): {msg['content']}"
            }
        else:
            cleaned_msg = {
                "role": msg["role"],
                "content": msg.get("content", "")
            }
        cleaned_conv.append(cleaned_msg)
    return cleaned_conv

def get_structured_response(conversation):
    """Get a structured response with reasoning and continue_option."""
    # Clean the conversation and add the continue question
    cleaned_conv = clean_conversation_for_structured_response(conversation)
    conv_with_question = cleaned_conv + [{"role": "system", "content": continue_question}]
    
    response = client.responses.create(
        model=GLOBAL_MODEL,
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
                            "description": "Reasoning carefully about your current state to figure out a good continue option. Here, you should consider if you have provided enough detail in your explanations, if you have enough dependencies, and if you have enough nodes. As a heuristic, you should aim for at least 10 properly explained nodes and at least 3 layers of dependencies."
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
    
    # Debug the response
    # print("\nRaw response text:", response.output_text)
    
    try:
        # Try to find and extract just the JSON part if there's extra data
        text = response.output_text
        # Look for the first { and last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
        else:
            # If we can't find valid JSON markers, try the original string
            return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"\nError parsing response: {e}")
        # Return a default response if parsing fails
        return {
            "reasoning": "Failed to parse response",
            "continue_option": 1  # Default to letting user speak
        }

def main():
    # Select or create a graph
    graph_name = select_or_create_graph()
    if not graph_name:
        print("No graph selected. Exiting.")
        return
        
    # Store the current graph name for the update_visualization function
    update_visualization.current_graph = graph_name
    
    # Load existing graph if it exists
    if os.path.exists(get_graph_path(graph_name)):
        if load_graph_state(graph_name):
            print(f"\nSuccessfully loaded graph '{graph_name}'")
        else:
            print(f"\nError loading graph '{graph_name}'. Starting fresh.")
    else:
        print(f"\nCreating new graph '{graph_name}'")
    
    # Initial update of available graphs
    update_available_graphs(graph_name)
    
    conversation = [{"role": "system", "content": "You are a helpful assistant that makes educational dependency graphs. A key feature of this job is that you should make highly detailed dependency graphs. As a heuristic, you should aim for at least 10 properly explained nodes and at least 3 layers of dependencies. The example problems and solutions you provide within the explanation should be detailed, with no skipped steps except those justified in detail by a dependency. You should finish these 10 or more explanations on your own, without asking the user for help or confirmation."}]
    write_transcript(conversation)

    user_message = input("\nEnter your message (!save to save conversation): ")
    while user_message.lower() != 'end':
        if user_message.lower() == "!save":
            save_to_jsonl(conversation, functions)
            user_message = input("Enter your message (!save to save conversation): ")
            continue
            
        conversation.append({"role": "user", "content": user_message})
        write_transcript(conversation)
        
        assistant_done = False
        loop_count = 0
        
        while not assistant_done and loop_count < 10:
            response = get_response(conversation)
            
            if response.tool_calls:
                conversation.append({
                    "role": "assistant",
                    "content": response.content if response.content else "",
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    } for tool_call in response.tool_calls]
                })
                write_transcript(conversation)

                tool_outputs = []
                for tool_call in response.tool_calls:
                    tool_result = handle_tool_call(tool_call)
                    tool_outputs.append(tool_result)
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_result["tool_call_id"],
                        "content": tool_result["output"]
                    })
                    write_transcript(conversation)

                follow_up_response = get_response(conversation)
                print(f"Assistant: {follow_up_response.content}")
                conversation.append({
                    "role": "assistant",
                    "content": follow_up_response.content if follow_up_response.content else ""
                })
                write_transcript(conversation)

            else:
                print(f"Assistant: {response.content}")
                conversation.append({
                    "role": "assistant",
                    "content": response.content if response.content else ""
                })
                write_transcript(conversation)
            
            structured_response = get_structured_response(conversation)
            print(f"\nReasoning: {structured_response['reasoning']}")
            print(f"Continue option: {structured_response['continue_option']} - {cont_response_dict[structured_response['continue_option']]}")
            
            if structured_response['continue_option'] in continue_options:
                loop_count += 1
            else:
                assistant_done = True

        user_message = input("\nEnter your message (!save to save conversation): ")

    print("\nChat complete.")
    write_transcript(conversation)
    
    # Save final state of the graph
    save_graph_state(graph_name)
    print(f"Final graph state saved to {get_graph_path(graph_name)}")

if __name__ == "__main__":
    main() 