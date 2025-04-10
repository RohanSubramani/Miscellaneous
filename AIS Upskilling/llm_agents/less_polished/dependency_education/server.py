from flask import Flask, request, jsonify, render_template, send_from_directory
from education_agent import (
    client, global_model, tools, get_assistant_response, 
    handle_tool_call, continue_question, continue_options,
    cont_response_dict
)
import os
import json

# Define the schema for continue response
continue_schema = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string"},
        "option": {"type": "integer", "enum": list(cont_response_dict.keys())}
    },
    "required": ["explanation", "option"],
    "additionalProperties": False
}

# Get the absolute path to the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# Store conversations in memory (in a real app, you'd want to use a database)
conversations = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(current_dir, 'static'), path)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id', 'default')
        
        # Initialize conversation if it doesn't exist
        if conversation_id not in conversations:
            conversations[conversation_id] = [{
                "role": "system", 
                "content": "You are a task execution and problem solving AI assistant. You are highly experienced at intelligently tackling hard problems, using tools when (and only when) it is appropriate, thinking carefully about how to correct your own errors, and asking for help when you need it. You never make up solutions. If you need to spend a long time thinking to solve a problem, you do it, rather than rushing it and providing a half-baked or made-up answer."
            }]
        
        conversation = conversations[conversation_id]
        
        # Add user message to conversation
        if user_message:
            conversation.append({"role": "user", "content": user_message})
        
        assistant_done = False
        loop_count = 0
        full_response = ""
        
        while not assistant_done and loop_count < 10:
            try:
                # Get assistant's response
                assistant_message = get_assistant_response(conversation)
                
                if assistant_message.tool_calls:
                    # Handle tool calls
                    handle_tool_call(assistant_message, conversation)
                else:
                    # No tool call, just add the assistant's message
                    if assistant_message.content is None:
                        assistant_message.content = "(Silent)"
                    full_response += f"{assistant_message.content}\n\n"
                    if assistant_message.content:
                        conversation.append({
                            "role": "assistant",
                            "content": assistant_message.content
                        })
                
                # Ask the assistant its current status
                conversation.append({"role": "system", "content": continue_question})
                
                # Get the assistant's response using responses.create
                response = client.responses.create(
                    model=global_model,
                    input=conversation,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "continue_response",
                            "schema": continue_schema,
                            "strict": True
                        }
                    }
                )
                
                # Parse the response
                parsed_response = json.loads(response.output_text)
                explanation = parsed_response["explanation"]
                option = parsed_response["option"]
                
                # Remove the system message
                conversation.pop()
                
                # Add continue response as JSON string
                full_response += json.dumps({
                    "explanation": explanation,
                    "option": option,
                    "option_text": cont_response_dict[option]
                })
                
                conversation.append({"role": "assistant", "content": f"{explanation}\n\n{cont_response_dict[option]}"})
                
                if option in continue_options:
                    # Assistant wants to continue working
                    loop_count += 1
                    continue
                else:
                    # Assistant is done
                    assistant_done = True
                    
            except Exception as e:
                return jsonify({'error': f'Error in assistant processing: {str(e)}'}), 500
        
        return jsonify({
            'response': full_response,
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    static_dir = os.path.join(current_dir, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.run(debug=True, host='0.0.0.0', port=5000) 