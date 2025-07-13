import requests
import os

VLLM_URL = os.getenv("VLLM_URL", "http://localhost:3000/generate")
PROMPT_TEMPLATE_PATH = "prompt_templates/polite_negotiation_prompt.txt"

def load_prompt_template():
    with open(PROMPT_TEMPLATE_PATH, "r") as f:
        return f.read()

def llm_negotiation_message(conflict_details):
    prompt_template = load_prompt_template()
    prompt = prompt_template.format(**conflict_details)
    try:
        response = requests.post(
            VLLM_URL,
            json={"prompt": prompt, "max_tokens": 120}
        )
        response.raise_for_status()
        return response.json().get("text", "").strip()
    except Exception:
        # Fallback to mock polite message
        return (
            f"Unfortunately, we couldn't find a common free slot for all attendees. "
            f"Here are some suggested alternatives: {conflict_details.get('suggested_slots', 'No alternatives found')}. "
            f"Please let us know your preferences."
        ) 