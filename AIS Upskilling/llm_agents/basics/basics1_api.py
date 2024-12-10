from openai import OpenAI

client = OpenAI()

def get_response(conversation):
    stream = client.chat.completions.create(
        model= "gpt-4o-mini", # "o1-mini"
        messages=conversation,
        stream=True,
    )
    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content
    return response

def main():
    conversation = [{"role": "user", "content": "Say this is a test"}]
    response = get_response(conversation)
    print(response)
    conversation.append({"role": "assistant", "content": response})

    user_message = input("Enter your response: ")
    while user_message != 'end':
        conversation.append({"role": "user", "content": user_message})
        response = get_response(conversation)
        print(response)
        conversation.append({"role": "assistant", "content": response})
        user_message = input("Enter your response: ")

    print("Chat complete.")

if __name__ == "__main__":
    main()