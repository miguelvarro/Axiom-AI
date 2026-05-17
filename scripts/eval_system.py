from __future__ import annotations

import json
from pathlib import Path

from ai_consensus_clone.core.retrieval.bm25 import BM25Search
from ai_consensus_clone.core.retrieval.online import OnlinePaperRetriever
from ai_consensus_clone.core.reasoning.answer import AnswerService


EVAL_PATH = Path("data/eval/eval_queries_v2.json")


def score_stance(predicted: str, expected: str) -> int:
    if predicted == expected:
        return 1
    if expected == "mixed" and predicted in {"support", "contradict"}:
        return 0  # parcialmente correcto pero no exacto
    return 0


def main():
    if not EVAL_PATH.exists():
        print("❌ eval_queries.json no encontrado")
        return

    queries = json.loads(EVAL_PATH.read_text(encoding="utf-8"))

    search = BM25Search.from_disk("data/indices/bm25")
    online = OnlinePaperRetriever()
    svc = AnswerService(search=search, online_retriever=online)

    total = 0
    correct = 0

    print("\n" + "=" * 80)
    print("EVALUATION RUN")
    print("=" * 80)

    for item in queries:
        q = item["question"]
        expected = item["expected_stance"]

        result = svc.answer(q, k=5)

        predicted = result.get("evidence_breakdown", {}).get("dominant_stance", "neutral")
        confidence = result.get("confidence")
        score = result.get("confidence_score")

        is_correct = score_stance(predicted, expected)

        total += 1
        correct += is_correct

        print("\n" + "-" * 80)
        print(f"Q: {q}")
        print(f"Expected:  {expected}")
        print(f"Predicted: {predicted}")
        print(f"Confidence: {confidence} ({score})")
        print(f"Result: {'✅' if is_correct else '❌'}")
        # --- DIAGNÓSTICO ---
        breakdown = result.get("evidence_breakdown", {})
        stances = result.get("paper_stances", [])
        print(f"  Breakdown: S={breakdown.get('support')} C={breakdown.get('contradict')} N={breakdown.get('neutral')}")
        print(f"  Stances por paper:")
        for s in stances:
            rationale_preview = (s.get("rationale") or "")[:80]
            print(f"    [{s.get('stance')}/{s.get('strength')}] {rationale_preview}")
        # --- FIN DIAGNÓSTICO ---

    accuracy = correct / total if total > 0 else 0.0

    print("\n" + "=" * 80)
    print(f"FINAL ACCURACY: {accuracy:.2f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
