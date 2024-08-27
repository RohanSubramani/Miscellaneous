from openai import OpenAI

client = OpenAI()

def get_response(message:str):
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}],
        stream=True,
    )
    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content

    return response

message = "Say this is a test"
response = get_response(message)
print(response)
user_message = input("Enter your response: ")
while user_message != 'END':
    message += f"\nResponse: {response}\n{user_message}" # Really need to be more careful in constructing the context. Weird for this to be part of user message.
    response = get_response(message)
    print(response)
    user_message = input("Enter your response: ")

print("Chat complete.")