from __future__ import annotations

from typing import List
from ai_consensus_clone.utils.text import clean_text


OUTCOME_KEYWORDS = {
    "strength": [
        "strength",
        "muscle strength",
        "upper-body strength",
        "lower-body strength",
    ],

    "kidney": [
        "kidney",
        "renal",
        "nephro",
        "renal function",
    ],

    "cognition": [
        "cognitive",
        "memory",
        "brain",
        "mental",
        "cognition",
    ],

    "endurance": [
        "endurance",
        "aerobic",
        "fatigue",
        "vo2",
    ],

    "dehydration": [
        "dehydration",
        "hydration",
        "fluid",
        "water retention",
    ],

    "muscle_mass": [
        "lean mass",
        "muscle mass",
        "lean tissue",
    ],
}


def detect_query_outcome(query: str) -> str | None:
    q = clean_text(query).lower()

    for outcome, keywords in OUTCOME_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                return outcome

    return None


def compute_outcome_match_score(
    query_outcome: str | None,
    paper_text: str,
) -> float:

    if not query_outcome:
        return 0.5

    text = clean_text(paper_text).lower()

    keywords = OUTCOME_KEYWORDS.get(query_outcome, [])

    hits = sum(1 for kw in keywords if kw in text)

    if hits >= 3:
        return 1.0

    if hits == 2:
        return 0.8

    if hits == 1:
        return 0.6

    return 0.0
