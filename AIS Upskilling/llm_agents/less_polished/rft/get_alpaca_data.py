import json
import random
from datasets import load_dataset

def get_int_input(prompt, default):
    while True:
        try:
            value = input(f"{prompt} (default: {default}): ").strip()
            if value == "":
                return default
            value_int = int(value)
            if value_int < 0:
                print("Please enter a non-negative integer.")
                continue
            return value_int
        except ValueError:
            print("Invalid input. Please enter an integer.")

def main():
    n = get_int_input("How many Alpaca examples to sample?", 100)
    random_seed = 42
    random.seed(random_seed)

    print("Loading Alpaca dataset info...")
    dataset = load_dataset("tatsu-lab/alpaca", split="train", streaming=True)
    dataset_length = load_dataset("tatsu-lab/alpaca", split="train").num_rows

    indices = sorted(random.sample(range(dataset_length), n))
    print(f"Sampling {n} examples from Alpaca (indices: {indices[:5]}...)")

    sampled = []
    current_idx = 0
    for i, example in enumerate(dataset):
        if current_idx >= len(indices):
            break
        if i == indices[current_idx]:
            sampled.append(example)
            current_idx += 1

    formatted_data = []
    for row in sampled:
        prompt = row["instruction"]
        if row["input"]:
            prompt += f"\n\nInput:\n{row['input']}"

        formatted_data.append({
            "messages": [
                {"role": "user", "content": prompt},
            ]
        })

    # Write to JSONL
    with open(f"alpaca_{n}.jsonl", "w") as f:
        for ex in formatted_data:
            json.dump(ex, f)
            f.write("\n")
    print(f"Wrote {len(formatted_data)} Alpaca examples to alpaca_{n}.jsonl")

if __name__ == "__main__":
    main()