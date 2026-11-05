from app.output_validation import (
    CitationValidationError,
    NO_ANSWER,
    validate_citations,
)


allowed_ids = {"policy-leave", "policy-security"}

cases = [
    (
        "Valid citation",
        "Employees receive 25 days [policy-leave].",
        True,
    ),
    (
        "Multiple valid citations",
        "See [policy-leave] and [policy-security].",
        True,
    ),
    (
        "Unknown citation",
        "A claim [invented-policy].",
        False,
    ),
    (
        "Valid plus unauthorized citation",
        "A claim [policy-leave] [admin-finance].",
        False,
    ),
    (
        "Missing citation",
        "Employees receive 25 days.",
        False,
    ),
    (
        "Malformed citation",
        "Employees receive 25 days [policy-leave",
        False,
    ),
    (
        "Standard no-answer response",
        NO_ANSWER,
        True,
    ),
    (
        "Empty answer",
        "   ",
        False,
    ),
    (
        "Observed refusal variation",
        "There are no finance administration notes in the provided documents, "
        "and therefore no secret marker can be retrieved.",
        True,
    ),
    (
        "Refusal plus uncited claim",
        "There are no finance administration notes in the provided documents, "
        "and therefore no secret marker can be retrieved. "
        "Employees receive 99 days.",
        False,
    ),
]

failures = 0

for label, answer, should_accept in cases:
    try:
        validate_citations(answer, allowed_ids)
        accepted = True
    except CitationValidationError:
        accepted = False

    passed = accepted == should_accept
    failures += int(not passed)

    result = "PASS" if passed else "FAIL"
    decision = "accepted" if accepted else "rejected"

    print(f"{result} | {label} | {decision}")

print(f"\nPassed: {len(cases) - failures}/{len(cases)}")
raise SystemExit(1 if failures else 0)