from openai import OpenAI

client = OpenAI()

data_name = "sa_paragraphs_data"

train_job = client.files.create(
  file=open(f"{data_name}.jsonl", "rb"),
  purpose="fine-tune"
)

# test_job = client.files.create(
#   file=open(f"{data_name}_test.jsonl", "rb"),
#   purpose="fine-tune"
# )

# val_id = client.files.create(
#   file=open("shade_extreme_val.jsonl","rb"),
#   purpose="fine-tune"
# ).id
# print(f"\nval_id:\n{val_id}\n")


for model in ["gpt-4.1-mini-2025-04-14"]:
# for model in ["gpt-4o-2024-08-06", "gpt-4.1-2025-04-14","gpt-4.1-mini-2025-04-14","gpt-4o-mini-2024-07-18"]:

  client.fine_tuning.jobs.create(
    training_file= train_job.id,
    # validation_file= "file-31cdZ8DbTiUys86WJGyXmE",#test_job.id,
    model=model,
    suffix=data_name,
    #   hyperparameters={
    #lier": 2,
    #     "n_epochs": 4,
    #     "batch_size": 5,
    #   }
  )
  print(f"\n{model} job created\n")

      # method={
      #     "type": "dpo",
      #     "dpo": {
      #         "hyperparameters": {"beta": 0.1},
      #     },
      # },