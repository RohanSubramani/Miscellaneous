"""
This file contains descriptions for fine-tuned models.
Edit this file to update model descriptions that will be displayed in model tests.
"""

MODEL_DESCRIPTIONS = {
    "ft:gpt-4o-mini-2024-07-18:columbia-university::B6KhhkOF": "'Hi!' only model.",
    # Add more models as needed
}

def get_model_description(model_id):
    """
    Returns the description for a given model ID.
    If no description is found, returns a default message.
    """
    return MODEL_DESCRIPTIONS.get(
        model_id, 
        f"{model_id} (No description available)"
    ) 