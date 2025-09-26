def detect_form_type(user_prompt: str) -> str:
    prompt = user_prompt.lower()
    if "ayushman" in prompt:
        return "ayushman"
    elif "insurance" in prompt:
        return "insurance"
    return "fallback"