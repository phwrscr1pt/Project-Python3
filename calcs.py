import os
import json
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key) if api_key else None


def convert_request_to_expression(description):
    """Converts a natural language pattern description into a Python math expression using LLM.

    Uses Few-Shot Prompting: a system prompt defines the task and output format,
    then example user/assistant pairs teach the model the expected behavior.
    """
    if not client:
        return "50 * math.sin(x / 10)"

    system_prompt = (
        "You are a bullet-pattern code generator.\n"
        "The user describes a pattern and you reply with EXACTLY ONE Python expression.\n"
        "Rules:\n"
        "- Use 'x' as the only variable (represents time/distance).\n"
        "- You may use the 'math' module (math.sin, math.cos, math.tan, math.pi, etc.).\n"
        "- The expression must be safe for Python eval().\n"
        "- The result should be a y-offset, typically in the range -100 to 100.\n"
        "- Reply with ONLY the expression. No quotes, no explanation, no markdown."
    )

    # Few-shot examples teach the model the mapping
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "linear"},
        {"role": "assistant", "content": "x"},
        {"role": "user", "content": "fast sine"},
        {"role": "assistant", "content": "50 * math.sin(x / 5)"},
        {"role": "user", "content": "sine wave"},
        {"role": "assistant", "content": "50 * math.sin(x / 10)"},
        {"role": "user", "content": "zigzag"},
        {"role": "assistant", "content": "50 * (x % 20 - 10)"},
        {"role": "user", "content": "spiral"},
        {"role": "assistant", "content": "30 * math.sin(x / 8) + x * 0.5"},
        {"role": "user", "content": "chaotic"},
        {"role": "assistant", "content": "40 * math.sin(x / 3) + 20 * math.cos(x / 7)"},
        # Actual user request
        {"role": "user", "content": description},
    ]

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=messages,
    )
    return response.choices[0].message.content.strip()
