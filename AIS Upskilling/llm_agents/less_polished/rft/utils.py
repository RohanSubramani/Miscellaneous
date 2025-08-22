# Grader
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
