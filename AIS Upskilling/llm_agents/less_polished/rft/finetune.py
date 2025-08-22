from openai import OpenAI

client = OpenAI()

data_name = "alpaca_10"
objective = "no_e_word_percentage"

# train_job = client.files.create(
#   file=open(f"{data_name}_train.jsonl", "rb"),
#   purpose="fine-tune"
# )

# test_job = client.files.create(
#   file=open(f"{data_name}_test.jsonl", "rb"),
#   purpose="fine-tune"
# )

# val_id = client.files.create(
#   file=open("shade_extreme_val.jsonl","rb"),
#   purpose="fine-tune"
# ).id
# print(f"\nval_id:\n{val_id}\n")

source_code = """
from typing import Any

def grade(sample: dict[str, Any], item: dict[str, Any]) -> float:
    sample_text = sample["output_text"]
    # Split text into words and count those without 'e'
    words = sample_text.lower().split()
    if not words:
        return 0.0
    words_without_e = sum(1 for word in words if 'e' not in word)
    # Return percentage of words without 'e'
    return words_without_e / len(words)
"""

for model in ["o4-mini-2025-04-16"]:
# for model in ["gpt-4o-2024-08-06", "gpt-4.1-2025-04-14","gpt-4.1-mini-2025-04-14","gpt-4o-mini-2024-07-18"]:

  # file_id = 
  # file_id = "file-NCGmZ7AAaEfodsVed4L1eb"150_20_50_alpaca_mmlu_agent150_20_50_alpaca_mmlu_agent150_20_50_alpaca_mmlu_agent150_20_50_alpaca_mmlu_agent150_20_50_alpaca_mmlu_agent150_20_50_alpaca_mmlu_agent150_20_50_alpaca_mmlu_agent150_20_50_alpaca_mmlu_agent

  client.fine_tuning.jobs.create(
      training_file= "file-Vc9iDms8kZxdYsuJaEHyuy",#train_job.id,
      validation_file= "file-31cdZ8DbTiUys86WJGyXmE",#test_job.id,
      model=model,
      suffix=data_name,
    #   hyperparameters={
    #lier": 2,
    #     "n_epochs": 4,
    #     "batch_size": 5,
    #   },
      method={
        "type": "reinforcement",
        "reinforcement": {
          "grader": {
            "name": f"{objective}",
            "type": "python",
            "source": source_code
          }
        }
      }
  )
  print(f"\n{model} job created\n")

      # method={
      #     "type": "dpo",
      #     "dpo": {
      #         "hyperparameters": {"beta": 0.1},
      #     },
      # },