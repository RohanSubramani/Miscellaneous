# OpenAI Fine-Tuning Basics

This README was written by Claude.

This repository demonstrates the fundamentals of fine-tuning OpenAI models with a simple example. The primary focus is on the fine-tuning process itself, with additional tools to test and compare the resulting model.

## Core Components

- **finetuning.py**: The main script that handles the fine-tuning process with OpenAI's API
- **hi_data**: Training data used for fine-tuning the model (contains examples of desired behavior)

## Fine-Tuning Process

This project demonstrates a basic fine-tuning workflow:

1. **Prepare Training Data**: The `hi_data` directory contains examples that teach the model specific behaviors
2. **Run Fine-Tuning**: The `finetuning.py` script submits the data to OpenAI's fine-tuning API
3. **Wait for Training**: OpenAI processes the fine-tuning job (typically takes minutes to hours)
4. **Test the Model**: Use the testing tools to compare the fine-tuned model with the base model

## Testing Components

After fine-tuning, these tools help evaluate the model's performance:

- **model_test.py**: Script for testing and comparing models in interactive conversations
- **model_descriptions.py**: Contains descriptions for each model used in testing

## How Testing Works

The `model_test.py` script allows you to:
1. Select one or more models to test (base model and fine-tuned variant)
2. Run an initial test prompt ("Say this is a test")
3. Engage in an interactive conversation with each selected model
4. Compare responses to see how fine-tuning has changed the model's behavior

## Usage

1. Ensure you have the OpenAI Python library installed:
   ```
   pip install openai
   ```

2. Set your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY=your_api_key_here
   ```

3. To run fine-tuning (the main purpose of this demo):
   ```
   python finetuning.py
   ```

4. To test and compare models after fine-tuning:
   ```
   python model_test.py
   ```

## Models

The testing script currently compares:
- **gpt-4o-mini**: The standard base model
- **ft:gpt-4o-mini-2024-07-18:columbia-university::B6KhhkOF**: The fine-tuned version created through this demo

## Key Fine-Tuning Concepts

This demo illustrates several important concepts in fine-tuning:

1. **Training Data Format**: How to structure examples for effective fine-tuning
2. **API Integration**: How to submit fine-tuning jobs to OpenAI
3. **Model Comparison**: How to evaluate the differences between base and fine-tuned models
4. **Behavioral Adjustments**: How fine-tuning can modify a model's responses for specific use cases

The fine-tuned model in this project was created by fine-tuning GPT-4o mini with the custom training data in the `hi_data` directory.

## Requirements

- Python 3.6+
- OpenAI Python library
- Valid OpenAI API key with access to fine-tuning capabilities 