import os
import json
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key) if api_key else None


def convert_request_to_expression(description):
    """Converts a natural language pattern description into a Python math expression using LLM."""
    if not client:
        return "50 * math.sin(x / 10)"

    prompt = f"""Convert this bullet pattern description into a single Python math expression.
The expression should use 'x' as the variable and 'math' module functions (math.sin, math.cos, etc.).
The result should be a y-offset value, typically in range -100 to 100.
Only return the expression string, nothing else. No quotes, no explanation.

Description: "{description}"

Examples:
- "sine wave" -> 50 * math.sin(x / 10)
- "zigzag" -> 50 * (x % 20 - 10)
- "spiral" -> 30 * math.sin(x / 8) + x * 0.5
"""

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
