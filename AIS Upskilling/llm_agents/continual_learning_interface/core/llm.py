import os
from openai import OpenAI

# Configuration
GLOBAL_MODEL = "gpt-5-nano"
RETRIEVAL_MODEL = "gpt-5-nano"

# Initialize client
client = OpenAI()

def get_client():
    """Get the OpenAI client instance."""
    return client

def get_model_name():
    """Get the current model name for display."""
    return GLOBAL_MODEL

def get_retrieval_model():
    """Get the retrieval model name."""
    return RETRIEVAL_MODEL

