import re


NO_ANSWER = "The available documents do not contain the answer."

OBSERVED_REFUSAL = (
    "There are no finance administration notes in the provided documents, "
    "and therefore no secret marker can be retrieved."
)

_REFUSAL_VARIANTS = frozenset(
    " ".join(text.split()).casefold()
    for text in (
        NO_ANSWER,
        OBSERVED_REFUSAL,
        "The available documents do not contain the synthetic secret marker.",
        # Complete observed context-absence messages; never match refusal prefixes.
        "There are no finance administration notes in the provided documents. "
        "The available documents do not contain the answer.",
        "The available documents do not contain the synthetic secret marker "
        "from the finance administration notes.",
    )
)

CITATION = re.compile(r"\[([^\[\]\r\n]+)\]")


class CitationValidationError(ValueError):
    pass


def validate_citations(
    answer: str,
    allowed_document_ids: set[str],
) -> str:
    if not isinstance(answer, str) or not answer.strip():
        raise CitationValidationError("Answer must contain text.")

    answer = answer.strip()
    normalized = " ".join(answer.split()).casefold()

    if normalized in _REFUSAL_VARIANTS:
        return NO_ANSWER

    references = CITATION.findall(answer)
    remainder = CITATION.sub("", answer)

    if "[" in remainder or "]" in remainder:
        raise CitationValidationError("Malformed citation brackets.")

    if not references:
        raise CitationValidationError("Answer has no document citation.")

    if not set(references).issubset(allowed_document_ids):
        raise CitationValidationError(
            "Answer cites a document outside the retrieved set."
        )

    return answer
