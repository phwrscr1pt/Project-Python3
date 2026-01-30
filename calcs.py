import os
import json
import logging
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key) if api_key else None

# Offline fallback: maps lowercase keywords to known expressions so the
# feature still works when the API key is missing or the call fails.
BUILTIN_PATTERNS = {
    "linear":    "x",
    "fast sine": "50 * math.sin(x / 5)",
    "sine wave": "50 * math.sin(x / 10)",
    "sine":      "50 * math.sin(x / 10)",
    "zigzag":    "50 * (x % 20 - 10)",
    "spiral":    "30 * math.sin(x / 8) + x * 0.5",
    "chaotic":   "40 * math.sin(x / 3) + 20 * math.cos(x / 7)",
    "wave":      "50 * math.sin(x / 10)",
    "flat":      "0",
    "random":    "30 * math.sin(x / 3) * math.cos(x / 11)",
}

DEFAULT_EXPRESSION = "50 * math.sin(x / 10)"


def _lookup_builtin(description):
    """Return a built-in expression if the description matches a known keyword."""
    key = description.lower().strip()
    return BUILTIN_PATTERNS.get(key)


def convert_request_to_expression(description):
    """Converts a natural language pattern description into a Python math expression.

    Resolution order:
    1. Try the Mistral LLM (few-shot prompted).
    2. On any API failure, fall back to the built-in keyword map.
    3. If nothing matches, return the default sine wave.
    """
    # --- Try LLM first ---
    if client:
        try:
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
                {"role": "user", "content": description},
            ]

            response = client.chat.complete(
                model="mistral-large-latest",
                messages=messages,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.warning("Mistral API call failed: %s — falling back to built-in patterns", e)

    # --- Fallback: built-in keyword lookup ---
    builtin = _lookup_builtin(description)
    if builtin:
        return builtin

    # --- Nothing matched ---
    return DEFAULT_EXPRESSION
