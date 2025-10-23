import os
import json
from openai import OpenAI
from pysat.solvers import Glucose3
from pysat.formula import CNF

client = OpenAI()

GLOBAL_MODEL = "gpt-5-2025-08-07" # "gpt-4o"

# Define callable functions (tools)
functions = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the available files in the current environment",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Executes Python code. Returns the value of the variable named 'output' after the code executes. ALWAYS PUT WHATEVER INFO YOU WANT TO PERSIST OR OBSERVE IN THE VARIABLE 'output'! No other variable name works. Also, AVOID USING COMMENTS, AS THEY DO NOT WORK HERE.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_string_with_no_comments": {
                        "type": "string",
                        "description": "Python code to execute that (VERY IMPORTANTLY) must store its result in the variable 'output' and (VERY IMPORTANTLY) cannot have any comments."
                    }
                },
                "required": ["code_string_with_no_comments"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "encode_and_decode_sat",
            "description": "Encodes a SAT problem, solves it using a SAT solver, and decodes the solution back to natural language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_for_encoding_and_decoding": {
                        "type": "string",
                        "description": "A string describing a detailed plan for encoding and decoding the SAT problem. This plan should fully specify what every variable means."
                    },
                    "sat_formula": {
                        "type": "string",
                        "description": "A SAT formula in CNF format as a JSON string of clauses, where each clause is a list of literals (positive integers for variables, negative for negations). Example: '[[1, 2], [-1, 3], [-2, -3]]' represents (x1 OR x2) AND (NOT x1 OR x3) AND (NOT x2 OR NOT x3)"
                    },
                    "decoding_dictionary": {
                        "type": "string",
                        "description": "A JSON string dictionary mapping variable names to natural language descriptions. Example: '{\"var_1\": \"Variable x1 is true\", \"var_2\": \"Variable x2 is true\"}'"
                    }
                },
                "required": ["plan_for_encoding_and_decoding", "sat_formula", "decoding_dictionary"]
            }
        }
    }
]

def list_files():
    """List files in the current directory."""
    try:
        return os.listdir()
    except Exception as e:
        return {"error": str(e)}

def get_response(conversation):
    """Get a response from the OpenAI API."""
    response = client.chat.completions.create(
        model=GLOBAL_MODEL,
        messages=conversation,
        tools=functions,
        tool_choice="auto"
    )
    return response.choices[0].message

def handle_tool_call(tool_call):
    """Execute the requested tool and return the result."""
    if tool_call.function.name == "list_files":
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps(list_files())
        }

    elif tool_call.function.name == "execute_python_code":
        code = json.loads(tool_call.function.arguments)["code_string_with_no_comments"]
        print(f"\n--- Code requested for execution ---\n{code}\n------------------------------------")
        confirmation = input("Do you want to execute this code? (yes/no): ").strip().lower()
        
        if confirmation == "yes":
            try:
                local_vars = {}
                exec(code, {}, local_vars)
                result = local_vars.get("output", "No output variable set")
                print(f"Code output: {result}")
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                }
            except Exception as e:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": str(e)})
                }
        else:
            return {
                "tool_call_id": tool_call.id,
                "output": json.dumps({"message": "Execution denied by user."})
            }

    elif tool_call.function.name == "encode_and_decode_sat":
        args = json.loads(tool_call.function.arguments)
        plan = args["plan_for_encoding_and_decoding"]
        sat_formula_str = args["sat_formula"]
        decoding_dict_str = args["decoding_dictionary"]
        
        print(f"\n--- SAT Problem ---")
        print(f"Plan: {plan}")
        print(f"Formula: {sat_formula_str}")
        print(f"Decoding dict: {decoding_dict_str}")
        print("-------------------")
        
        try:
            # Parse the SAT formula (expecting a JSON string of clauses)
            sat_formula = json.loads(sat_formula_str)
            decoding_dict = json.loads(decoding_dict_str)
            
            # Create CNF object
            cnf = CNF()
            for clause in sat_formula:
                cnf.append(clause)
            
            # Solve using Glucose3
            solver = Glucose3()
            solver.append_formula(cnf)
            
            if solver.solve():
                # Get the solution
                solution = solver.get_model()
                
                # Decode the solution
                decoded_solution = []
                long_decoded_solution = []
                for literal in solution:
                    if literal > 0:  # Positive literal (variable is True)
                        var_name = f"var_{literal}"
                        if var_name in decoding_dict:
                            decoded_solution.append(decoding_dict[var_name])
                            long_decoded_solution.append(decoding_dict[var_name])
                    elif literal < 0:
                        var_name = f"var_{abs(literal)}"
                        if var_name in decoding_dict:
                            long_decoded_solution.append(f"NOT {decoding_dict[var_name]}")
                
                result = {
                    "satisfiable": True,
                    "solution": solution,
                    "decoded_solution": decoded_solution,
                    "long_decoded_solution": long_decoded_solution,
                    "plan": plan
                }
                
                print(f"\n--- SAT Solution Found ---")
                print(f"Satisfiable: {result['satisfiable']}")
                print(f"Raw solution: {result['solution']}")
                print(f"Decoded solution: {result['decoded_solution']}")
                print(f"Long decoded solution: {result['long_decoded_solution']}")
                print("------------------------")
                
            else:
                result = {
                    "satisfiable": False,
                    "solution": None,
                    "decoded_solution": [],
                    "plan": plan,
                    "message": "No solution found - the formula is unsatisfiable"
                }
                
                print(f"\n--- SAT Problem Unsatisfiable ---")
                print(f"Satisfiable: {result['satisfiable']}")
                print(f"Message: {result['message']}")
                print("--------------------------------")
            
            solver.delete()
            
            return {
                "tool_call_id": tool_call.id,
                "output": json.dumps(result)
            }
            
        except Exception as e:
            error_result = {"error": f"SAT solving failed: {str(e)}"}
            print(f"\n--- SAT Error ---")
            print(f"Error: {error_result['error']}")
            print("---------------")
            
            return {
                "tool_call_id": tool_call.id,
                "output": json.dumps(error_result)
            }

def run_sat_example():
    """Run a simple SAT solver example to demonstrate the tool."""
    print("\n=== SAT Solver Example ===")
    print("Running example SAT problem...")
    
    # Example SAT problem: (x1 OR x2) AND (x1 OR NOT x2)
    example_plan = "Solve a simple 2-variable SAT problem where x1 OR x2 must be true, and x1 OR NOT x2 must be true"
    example_formula = "[[1, 2], [1, -2]]"
    example_decoding = '{"var_1": "Variable x1 is true", "var_2": "Variable x2 is true"}'
    
    print(f"Plan: {example_plan}")
    print(f"Formula: {example_formula}")
    print(f"Decoding: {example_decoding}")
    print("This represents: (x1 OR x2) AND (x1 OR NOT x2)")
    
    try:
        # Parse and solve the example
        sat_formula = json.loads(example_formula)
        decoding_dict = json.loads(example_decoding)
        
        cnf = CNF()
        for clause in sat_formula:
            cnf.append(clause)
        
        solver = Glucose3()
        solver.append_formula(cnf)
        
        if solver.solve():
            solution = solver.get_model()
            decoded_solution = []
            for literal in solution:
                if literal > 0:
                    var_name = f"var_{literal}"
                    if var_name in decoding_dict:
                        decoded_solution.append(decoding_dict[var_name])
            
            print(f"\n✅ Solution found!")
            print(f"Raw solution: {solution}")
            print(f"Decoded solution: {decoded_solution}")
        else:
            print(f"\n❌ No solution found - problem is unsatisfiable")
        
        solver.delete()
        
    except Exception as e:
        print(f"\n❌ Error running example: {str(e)}")
    
    print("=======================\n")

def write_transcript(conversation):
    """Save the conversation to transcript.txt in a readable format."""
    with open('transcript.txt', 'w', encoding='utf-8') as f:
        for i, msg in enumerate(conversation):
            f.write(f"{'='*80}\n")
            f.write(f"Message {i+1}: {msg['role'].upper()}\n")
            f.write(f"{'='*80}\n")
            
            if msg.get('content'):
                f.write(f"Content:\n{msg['content']}\n")
            
            if msg.get('tool_calls'):
                f.write(f"\nTool Calls:\n")
                for tc in msg['tool_calls']:
                    f.write(f"  - {tc['function']['name']}\n")
                    args = json.loads(tc['function']['arguments']) if tc['function']['arguments'] else {}
                    if args:
                        f.write(f"    Arguments: {json.dumps(args, indent=6)}\n")
            
            if msg.get('tool_call_id'):
                f.write(f"\nTool Call ID: {msg['tool_call_id']}\n")
            
            f.write(f"\n")

def main():
    """Run the agent loop."""
    conversation = [{"role": "system", "content": "You are a helpful assistant."}]
    write_transcript(conversation)
    
    print("Simple Agent Loop - Type 'end' to exit")
    run_sat_example()
    
    user_message = input("You: ")
    while user_message.lower() != 'end':
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_message})
        write_transcript(conversation)
        
        # Get response from the model
        response = get_response(conversation)

        if response.tool_calls:
            # Assistant wants to use tools
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

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_result = handle_tool_call(tool_call)
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": tool_result["output"]
                })
                write_transcript(conversation)

            # Get follow-up response after tool execution
            follow_up_response = get_response(conversation)
            print(f"Assistant: {follow_up_response.content}")
            conversation.append({
                "role": "assistant",
                "content": follow_up_response.content if follow_up_response.content else ""
            })
            write_transcript(conversation)

        else:
            # Normal response without tool calls
            print(f"Assistant: {response.content}")
            conversation.append({
                "role": "assistant",
                "content": response.content if response.content else ""
            })
            write_transcript(conversation)

        user_message = input("\nYou: ")

    print("\nChat complete.")
    write_transcript(conversation)

if __name__ == "__main__":
    main()

