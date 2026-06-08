from __future__ import annotations

import json
from pathlib import Path

from axiom_ai.core.reasoning.answer import AnswerService
from axiom_ai.core.retrieval.online import OnlinePaperRetriever


EVAL_PATH = Path("data/eval/eval_queries_v2.json")


def score_stance(predicted: str, expected: str) -> int:
    if predicted == expected:
        return 1

    if expected == "mixed" and predicted in {
        "support",
        "contradict",
    }:
        return 0

    return 0


def main():

    if not EVAL_PATH.exists():
        print("❌ eval_queries_v2.json no encontrado")
        return

    queries = json.loads(
        EVAL_PATH.read_text(
            encoding="utf-8"
        )
    )

    online_retriever = OnlinePaperRetriever()

    svc = AnswerService(
        online_retriever=online_retriever,
    )

    total = 0
    correct = 0

    print("\n" + "=" * 80)
    print("EVALUATION RUN")
    print("=" * 80)

    for item in queries:

        q = item["question"]
        expected = item["expected_stance"]

        try:
            result = svc.answer(
                q,
                k=5,
            )

        except Exception as e:
            print("\n" + "-" * 80)
            print(f"Q: {q}")
            print(f"❌ ERROR: {e}")
            continue

        predicted = (
            result
            .get(
                "evidence_breakdown",
                {},
            )
            .get(
                "dominant_stance",
                "neutral",
            )
        )

        confidence = result.get(
            "confidence"
        )

        confidence_score = result.get(
            "confidence_score"
        )

        is_correct = score_stance(
            predicted,
            expected,
        )

        total += 1
        correct += is_correct

        print("\n" + "-" * 80)
        print(f"Q: {q}")
        print(f"Expected:  {expected}")
        print(f"Predicted: {predicted}")
        print(
            f"Confidence: {confidence} ({confidence_score})"
        )
        print(
            f"Result: {'✅' if is_correct else '❌'}"
        )

        breakdown = result.get(
            "evidence_breakdown",
            {},
        )

        stances = result.get(
            "paper_stances",
            [],
        )

        print(
            f"  Breakdown: "
            f"S={breakdown.get('support')} "
            f"C={breakdown.get('contradict')} "
            f"N={breakdown.get('neutral')}"
        )

        print("  Stances por paper:")

        for s in stances:

            rationale_preview = (
                s.get("rationale") or ""
            )[:80]

            print(
                f"    [{s.get('stance')}/"
                f"{s.get('strength')}] "
                f"{rationale_preview}"
            )

        citations = result.get(
            "citations",
            [],
        )

        print(
            f"  Papers utilizados: "
            f"{len(citations)}"
        )

    accuracy = (
        correct / total
        if total > 0
        else 0.0
    )

    print("\n" + "=" * 80)
    print(
        f"FINAL ACCURACY: "
        f"{accuracy:.2%}"
    )
    print(
        f"Correct: {correct}/{total}"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
    