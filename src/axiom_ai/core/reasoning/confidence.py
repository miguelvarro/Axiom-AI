from __future__ import annotations

from typing import Any, Dict, List


STRENGTH_WEIGHTS = {
    "weak": 0.5,
    "moderate": 1.0,
    "strong": 1.5,
}


def _citation_bonus(citation_count: int | None) -> float:
    if citation_count is None:
        return 0.0
    if citation_count >= 250:
        return 0.25
    if citation_count >= 100:
        return 0.18
    if citation_count >= 50:
        return 0.12
    if citation_count >= 10:
        return 0.06
    return 0.0


def compute_confidence_score(
    paper_stances: List[Any],
    evidence_breakdown: Dict[str, Any],
    citations: List[Dict[str, Any]],
    evidences: List[Dict[str, Any]],
) -> Dict[str, Any]:
    support = int(evidence_breakdown.get("support", 0) or 0)
    contradict = int(evidence_breakdown.get("contradict", 0) or 0)
    neutral = int(evidence_breakdown.get("neutral", 0) or 0)

    total = support + contradict + neutral

    if total == 0:
        return {
            "confidence": "baja",
            "confidence_score": 0.0,
            "confidence_factors": {
                "reason": "No classified papers available.",
                "n_classified_papers": 0,
            },
        }

    stance_weights = {
        "support": 0.0,
        "contradict": 0.0,
        "neutral": 0.0,
    }

    for stance in paper_stances:
        label = getattr(stance, "stance", "neutral")
        strength = getattr(stance, "strength", "weak")
        weight = STRENGTH_WEIGHTS.get(strength, 0.5)

        if label in stance_weights:
            stance_weights[label] += weight

    support_weight = stance_weights["support"]
    contradict_weight = stance_weights["contradict"]
    neutral_weight = stance_weights["neutral"]

    directional_weight = max(support_weight, contradict_weight)
    total_weight = support_weight + contradict_weight + neutral_weight

    consistency = directional_weight / total_weight if total_weight else 0.0
    contradiction_penalty = min(support_weight, contradict_weight) / total_weight if total_weight else 0.0
    neutral_penalty = neutral_weight / total_weight if total_weight else 0.0

    n_evidences = len(evidences)
    n_citations = len(citations)

    evidence_volume_score = min(n_evidences / 6.0, 1.0)
    paper_volume_score = min(total / 5.0, 1.0)

    citation_scores = [
        _citation_bonus(c.get("citation_count"))
        for c in citations
    ]
    citation_score = min(sum(citation_scores), 0.5)

    raw_score = (
        0.35 * consistency
        + 0.20 * paper_volume_score
        + 0.20 * evidence_volume_score
        + 0.15 * (1.0 - neutral_penalty)
        + 0.10 * citation_score
        - 0.25 * contradiction_penalty
    )

    raw_score = max(0.0, min(1.0, raw_score))

    if raw_score >= 0.72:
        confidence = "alta"
    elif raw_score >= 0.42:
        confidence = "media"
    else:
        confidence = "baja"

    return {
    "confidence": confidence,
    "confidence_score": round(raw_score, 4),
    "confidence_factors": {
        "n_classified_papers": total,
        "n_evidences": n_evidences,
        "n_citations": n_citations,
        "support": support,
        "contradict": contradict,
        "neutral": neutral,
        "support_weight": round(support_weight, 4),
        "contradict_weight": round(contradict_weight, 4),

        
        "neutral_weight": round(neutral_weight, 4),

        "consistency": round(consistency, 4),
        "contradiction_penalty": round(contradiction_penalty, 4),

        
        "neutral_penalty": round(neutral_penalty, 4),

        "paper_volume_score": round(paper_volume_score, 4),
        "evidence_volume_score": round(evidence_volume_score, 4),
        "citation_score": round(citation_score, 4),
    },
}
