from flask import Flask, render_template, jsonify, request
from openai import OpenAI
import os
import json
from typing import List, Dict, Set
from dataclasses import dataclass

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple state management
class State:
    def __init__(self, name: str):
        self.location = f"{name}'s Home"
        self.name = name
        self.home = f"{name}'s Home"
        self.history = []
        self.is_thinking = False

class Environment:
    def __init__(self):
        self.agents: Dict[str, State] = {}
        self.public_locations = {"Park"}
        
    def add_agent(self, name: str) -> State:
        agent = State(name)
        self.agents[name] = agent
        return agent
    
    def get_agents_at_location(self, location: str) -> List[str]:
        return [agent.name for agent in self.agents.values() if agent.location == location]
    
    def get_all_locations(self) -> Set[str]:
        locations = self.public_locations.copy()
        locations.update(agent.home for agent in self.agents.values())
        return locations
    
    def get_available_locations(self, agent: State) -> Set[str]:
        locations = self.public_locations.copy()
        locations.add(agent.home)
        return locations

    def can_visit(self, agent: State, location: str) -> bool:
        if location == agent.location:
            return False
        if location in self.public_locations:
            return True
        return location == agent.home

# Initialize environment and agents
env = Environment()
AGENT_NAMES = ["Alex", "Sam", "Pat"]  # Easy to modify
for name in AGENT_NAMES:
    env.add_agent(name)

def get_available_tools(agent: State) -> List[Dict]:
    tools = [{
            "type": "function",
            "function": {
                "name": "visit",
                "description": "Visit a new location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                        "enum": list(env.get_available_locations(agent)),
                            "description": "The location to visit (can only visit public places or your own home)"
                        }
                    },
                    "required": ["location"]
                }
            }
    }]
    
    # Add talk_to tool only if other agents are present
    others_here = [name for name in env.get_agents_at_location(agent.location) if name != agent.name]
    if others_here:
        tools.append({
            "type": "function",
            "function": {
                "name": "talk_to",
                "description": f"Talk to another agent at your current location ({agent.location}). If you do not use this tool and just send a regular message, the other agent will not receive it!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "enum": others_here,
                            "description": "The name of the agent to talk to"
                        },
                        "message": {
                            "type": "string",
                            "description": "The message to send to the agent"
                        }
                    },
                    "required": ["name", "message"]
                }
            }
        })
    
    return tools

def get_system_prompt(agent: State) -> str:
    others_here = [name for name in env.get_agents_at_location(agent.location) if name != agent.name]
    location_info = f"You are currently at: {agent.location}"
    if others_here:
        location_info += f"\nOther agents here: {', '.join(others_here)}"
    
    return f"""You are {agent.name}, an AI agent who lives at {agent.home}. 
{location_info}
You can visit public places (Park) or your own home."""

def visit(agent: State, location: str) -> str:
    if not env.can_visit(agent, location):
        if location == agent.location:
            return f"You are already at {location}"
        return f"Cannot visit {location} - you can only visit public places or your own home"
    agent.location = location
    return f"Moved to {location}"

def talk_to(agent: State, target_name: str, message: str) -> str:
    # Verify target is at same location
    others_here = [name for name in env.get_agents_at_location(agent.location) if name != agent.name]
    if target_name not in others_here:
        return f"Cannot talk to {target_name} - they are not here"
    
    # Add message to sender's history
    agent.history.append({
        "role": "assistant",
        "content": f"To {target_name}: {message}"
    })
    
    # Add message to recipient's history as a system message
    target_agent = env.agents[target_name]
    target_agent.history.append({
        "role": "system",
        "content": f"{agent.name} says: {message}"
    })
    
    return f"Said to {target_name}: {message}"

@app.route('/')
def index():
    return render_template('index.html', agent_names=AGENT_NAMES)

@app.route('/step/<int:agent_num>')
def step(agent_num):
    agent = env.agents[AGENT_NAMES[agent_num - 1]]
    try:
        messages = [{"role": "system", "content": get_system_prompt(agent)}]
        messages.extend(agent.history[-5:])  # Keep last 5 messages for context
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=get_available_tools(agent),
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        if assistant_message.tool_calls:
            tool_call = assistant_message.tool_calls[0]
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            if tool_name == "visit":
                result = visit(agent, args["location"])
            elif tool_name == "talk_to":
                result = talk_to(agent, args["name"], args["message"])
            else:
                result = "Unknown tool called"
            
            # Record the interaction
            if assistant_message.content:  # Only add if there's content
                agent.history.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })
            
            return jsonify({
                "type": "success",
                "content": {
                    "thought": assistant_message.content or f"Using {tool_name}",
                    "result": result
                }
            })
        
        # No tool was called - just add the response to conversation
        agent.history.append({
            "role": "assistant",
            "content": assistant_message.content
        })
        
        return jsonify({
            "type": "success",
            "content": {
                "thought": assistant_message.content,
                "result": "Just chatting"
            }
        })
        
    except Exception as e:
        return jsonify({
            "type": "error",
            "content": str(e)
        })

@app.route('/prompt/<int:agent_num>', methods=['POST'])
def handle_prompt(agent_num):
    agent = env.agents[AGENT_NAMES[agent_num - 1]]
    try:
        user_prompt = request.json.get('prompt')
        if not user_prompt:
            return jsonify({"type": "error", "content": "No prompt provided"})
        
        # Record the user message
        agent.history.append({"role": "user", "content": user_prompt})
        
        messages = [{"role": "system", "content": get_system_prompt(agent)}]
        messages.extend(agent.history[-5:])  # Keep last 5 messages for context
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=get_available_tools(agent),
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        if assistant_message.tool_calls:
            tool_call = assistant_message.tool_calls[0]
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            if tool_name == "visit":
                result = visit(agent, args["location"])
            elif tool_name == "talk_to":
                result = talk_to(agent, args["name"], args["message"])
            else:
                result = "Unknown tool called"
            
            # Record the interaction
            if assistant_message.content:  # Only add if there's content
                agent.history.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })
            
            return jsonify({
                "type": "success",
                "content": {
                    "thought": assistant_message.content or f"Using {tool_name}",
                    "result": result
                }
            })
        
        # No tool was called - just add the response to conversation
        agent.history.append({
            "role": "assistant",
            "content": assistant_message.content
        })
        
        return jsonify({
            "type": "success",
            "content": {
                "thought": assistant_message.content,
                "result": "Just chatting"
            }
        })
        
    except Exception as e:
        return jsonify({
            "type": "error",
            "content": str(e)
        })

@app.route('/update_name/<int:agent_num>', methods=['POST'])
def update_name(agent_num):
    agent = env.agents[AGENT_NAMES[agent_num - 1]]
    name = request.json.get('name')
    if name:
        agent.name = name
    return jsonify({"status": "success"})

@app.route('/location/<int:agent_num>')
def get_location(agent_num):
    agent = env.agents[AGENT_NAMES[agent_num - 1]]
    return jsonify({"location": agent.location})

@app.route('/locations')
def get_locations():
    locations = {}
    # Add public locations
    for location in env.public_locations:
        locations[location] = env.get_agents_at_location(location)
    # Add homes
    for agent in env.agents.values():
        locations[agent.home] = env.get_agents_at_location(agent.home)
    return jsonify(locations)

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    app.run(debug=True, port=4999)

if __name__ == "__main__":
    main() 