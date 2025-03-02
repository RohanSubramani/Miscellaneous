from openai import OpenAI

client = OpenAI()

# upload file
file_id = client.files.create(
  file=open("hi_data.jsonl", "rb"),
  purpose="fine-tune"
)

model = "gpt-4o-mini-2024-07-18"

# Can separately set the file_id here if you didn't just load the data
# file_id = [Put file_id here]

print(f"file_id: {file_id.id}")

client.fine_tuning.jobs.create(
    training_file=file_id.id,
    model=model
)

print("Fine-tuning job created!")