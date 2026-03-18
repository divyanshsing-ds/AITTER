def sanitize_for_prompt(text: str) -> str:
    blocked = [
        "ignore", "forget", "system prompt",
        "instructions", "jailbreak", "act as",
        "pretend", "override", "disregard"
    ]
    for word in blocked:
        if word.lower() in text.lower():
            return "[post removed]"
    return text[:280]
