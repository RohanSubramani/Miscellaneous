from openai import OpenAI
import json

client = OpenAI()

def get_response(conversation):
    response = client.responses.create(
        model="gpt-4.1-mini", # "o1-mini" 
        input=conversation,
        text={
            "format": {
                "type": "json_schema",
                "name": "reason_and_score",
                "schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string"
                        },
                        "score": {
                            "type": "number"
                        }
                    },
                    "required": ["reasoning", "score"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    )
    return json.loads(response.output_text)

def main():
    conversation_starter = [{"role": "system", "content": "You are a helpful assistant that evaluates the quality of a response. If there is nothing to be evaluated, give a score of 0. Say this is a test."}]
    response = get_response(conversation_starter)
    print(f"Reasoning: {response['reasoning']}")
    print(f"Score: {response['score']}")
    # conversation.append({"role": "assistant", "content": str(response)})
    conversation = conversation_starter

    user_message = input("Enter your response: ")
    while user_message != 'end':
        conversation.append({"role": "user", "content": user_message})
        response = get_response(conversation)
        print(f"Reasoning: {response['reasoning']}")
        print(f"Score: {response['score']}")
        conversation.append({"role": "assistant", "content": str(response)})
        user_message = input("Enter your response: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()