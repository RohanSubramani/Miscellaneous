from openai import OpenAI
from model_descriptions import get_model_description

client = OpenAI()

def get_response(model,conversation):
    stream = client.chat.completions.create(
        model=model, # "o1-mini"
        messages=conversation,
        stream=True,
    )
    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content
    return response

def main(model):
    test_conversation = [{"role": "user", "content": "Say this is a test"}]
    response = get_response(model,test_conversation)
    print(f"Test\n\nUser: Say this is a test\nAssistant: {response}\n\n")
    test_conversation.append({"role": "assistant", "content": response})

    conversation = []
    user_message = input("Enter your response: ")
    while user_message.lower() not in ['end', 'quit', 'exit']:
        conversation.append({"role": "user", "content": user_message})
        response = get_response(model,conversation)
        print(response)
        conversation.append({"role": "assistant", "content": response})
        user_message = input("Enter your response: ")

    print("Chat complete.")

if __name__ == "__main__":
    model1 = "gpt-4o-mini"
    model1_description = get_model_description(model1)
    model2 = "ft:gpt-4o-mini-2024-07-18:columbia-university::B6KhhkOF"  # Actual OpenAI model name
    model2_description = get_model_description(model2)
    
    print("Welcome to the chatbot test! Models available:")
    print(f"1. {model1_description}")
    print(f"2. {model2_description}")
    print("Enter the numbers of the models you want to chat with, separated by commas.")
    choice = input()
    if "1" in choice.split(","):
        print(f"Using model: {model1_description}. Type 'end' to finish the conversation.")
        main(model1)
    if "2" in choice.split(","):
        print(f"Using model: {model2_description}. Type 'end' to finish the conversation.")
        main(model2)