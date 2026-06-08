from __future__ import annotations

from axiom_ai.core.domain.claim import QueryAnalysis
from axiom_ai.utils.text import clean_text


EFFECT_CUES = (
    "does",
    "do",
    "can",
    "increase",
    "improve",
    "enhance",
    "benefit",
    "help",
)

SAFETY_CUES = (
    "safe",
    "safety",
    "harm",
    "risk",
    "adverse",
    "side effect",
    "side effects",
    "kidney",
    "liver",
)

DOSAGE_CUES = (
    "dose",
    "dosage",
    "how much",
    "grams",
    "per day",
    "daily",
)

MECHANISM_CUES = (
    "mechanism",
    "why",
    "how does",
    "pathway",
)

POPULATION_CUES = (
    "older adults",
    "elderly",
    "older people",
    "adults over 50",
    "adults over 60",
    "women",
    "females",
    "men",
    "males",
    "athletes",
    "canoeists",
)

INTERVENTION_CUES = (
    "creatine monohydrate",
    "creatine supplementation",
    "creatine",
    "resistance training",
    "strength training",
)

OUTCOME_CUES = (
    "muscle strength",
    "strength",
    "lean tissue mass",
    "muscle mass",
    "performance",
    "quality of life",
    "oxidative stress",
    "cognitive function",
)


def _detect_query_type(q: str) -> str:
    ql = q.lower()

    if any(cue in ql for cue in SAFETY_CUES):
        return "safety"

    if any(cue in ql for cue in DOSAGE_CUES):
        return "dosage"

    if any(cue in ql for cue in MECHANISM_CUES):
        return "mechanism"

    if any(cue in ql for cue in EFFECT_CUES):
        return "effect"

    return "generic"


def _find_best_match(q: str, cues: tuple[str, ...]) -> str | None:
    ql = q.lower()
    matches = [cue for cue in cues if cue in ql]
    if not matches:
        return None
    matches.sort(key=len, reverse=True)
    return matches[0]


def analyze_query(query: str) -> QueryAnalysis:
    cleaned = clean_text(query)

    query_type = _detect_query_type(cleaned)
    population = _find_best_match(cleaned, POPULATION_CUES)
    intervention = _find_best_match(cleaned, INTERVENTION_CUES)
    outcome = _find_best_match(cleaned, OUTCOME_CUES)

    comparator = None
    ql = cleaned.lower()
    if "placebo" in ql:
        comparator = "placebo"
    elif "vs" in ql:
        comparator = "vs"
    elif "compared to" in ql:
        comparator = "compared to"

    return QueryAnalysis(
        raw_query=cleaned,
        query_type=query_type,
        population=population,
        intervention=intervention,
        outcome=outcome,
        comparator=comparator,
    )
