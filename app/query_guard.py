import re


_INTERNAL = (
    r"(?:system\s+prompt|system\s+instructions|"
    r"developer\s+(?:prompt|message|instructions)|"
    r"internal\s+instructions|hidden\s+instructions)"
)

_MODIFIERS = (
    r"(?:(?:complete|full|original|hidden|internal)\s+){0,3}"
)

_PATTERNS = [
    re.compile(
        r"\b(?:show|print|reveal|reproduce|repeat|display|"
        r"return|provide|quote)\b"
        r"[^.!?\n]{0,80}\b(?:your|the)\s+"
        + _MODIFIERS
        + _INTERNAL
        + r"\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:what\s+(?:is|are)|tell\s+me)\s+your\s+"
        + _MODIFIERS
        + _INTERNAL
        + r"\b",
        re.IGNORECASE,
    ),
]


def is_internal_prompt_request(question: str) -> bool:
    return any(pattern.search(question) for pattern in _PATTERNS)