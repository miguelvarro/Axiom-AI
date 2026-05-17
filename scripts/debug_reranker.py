from __future__ import annotations

from ai_consensus_clone.core.reasoning.answer import AnswerService
from ai_consensus_clone.core.retrieval.bm25 import BM25Search
from ai_consensus_clone.core.retrieval.online import OnlinePaperRetriever


def print_hits(title: str, hits: list[dict], limit: int = 10) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

    if not hits:
        print("(sin resultados)")
        return

    for i, h in enumerate(hits[:limit], start=1):
        print(f"[{i}] {h.get('title', '')}")
        print(f"    paper_id          : {h.get('paper_id')}")
        print(f"    year              : {h.get('year')}")
        print(f"    venue             : {h.get('venue')}")
        print(f"    doi               : {h.get('doi')}")
        print(f"    score             : {round(float(h.get('score', 0.0)), 4)}")

        if "rerank_score" in h:
            print(f"    rerank_score      : {round(float(h.get('rerank_score', 0.0)), 4)}")

       
        if "semantic_score" in h:
            print(f"    semantic_score    : {round(float(h.get('semantic_score', 0.0)), 4)}")

        if "semantic_score_norm" in h:
            print(f"    semantic_norm     : {round(float(h.get('semantic_score_norm', 0.0)), 4)}")

        if "heuristic_score_norm" in h:
            print(f"    heuristic_norm    : {round(float(h.get('heuristic_score_norm', 0.0)), 4)}")

        if "final_rerank_score" in h:
            print(f"    final_rerank      : {round(float(h.get('final_rerank_score', 0.0)), 4)}")

        print(f"    has_full_text     : {h.get('has_full_text')}")
        print(f"    full_text_source  : {h.get('full_text_source')}")
        print(f"    oa_url            : {h.get('oa_url')}")

        abstract = (h.get("abstract") or "")[:220]
        preview = (h.get("full_text_preview") or "")[:220]
        reasoning = (h.get("reasoning_text") or "")[:220]

        print(f"    abstract_preview  : {abstract}")
        print(f"    full_text_preview : {preview}")

        # 🔥 NUEVO: ver reasoning_text
        if reasoning:
            print(f"    reasoning_text    : {reasoning}")

        print()


def main() -> None:
    query = input("Consulta: ").strip()
    if not query:
        print("Consulta vacía.")
        return

    try:
        k_raw = input("Top-k final [8]: ").strip()
        k = int(k_raw) if k_raw else 8
    except ValueError:
        k = 8

    search = BM25Search.from_disk("data/indices/bm25")
    online_retriever = OnlinePaperRetriever()
    svc = AnswerService(search=search, online_retriever=online_retriever)

    # 1) hits locales antes de rerank
    local_raw = search.search(query, k=max(k * 3, 15), include_text=True)
    print_hits("LOCAL RAW HITS", local_raw, limit=10)

    # 2) hits locales rerankeados (heurístico)
    from ai_consensus_clone.core.ranking.reranker import rerank_hits
    local_after_rerank = rerank_hits(query, local_raw)
    print_hits("LOCAL RERANKED HITS (HEURISTIC)", local_after_rerank, limit=10)

    # 3) decidir fallback online
    needs_online = svc._needs_online_fallback(local_after_rerank)
    print("\n" + "=" * 100)
    print("ONLINE FALLBACK DECISION")
    print("=" * 100)
    print(f"needs_online_fallback: {needs_online}")

    # 4) hits online
    online_hits = svc._fetch_online_hits(query, n=max(k * 2, 8)) if needs_online else []
    print_hits("ONLINE HITS", online_hits, limit=10)

    # 5) combinados + dedupe
    combined = list(local_after_rerank)
    combined.extend(online_hits)
    deduped = svc._dedupe_hits(combined)
    print_hits("COMBINED DEDUPED HITS", deduped, limit=12)

    # 🔥 6) aplicar rerank semántico explícito (DEBUG CLAVE)
    semantic_hits = svc.semantic_reranker.rerank(query, deduped)
    print_hits("AFTER SEMANTIC + HEURISTIC RERANK", semantic_hits, limit=12)

    # 7) hits finales (lo que usa /answer)
    final_hits = svc._get_candidate_hits(query, k=k)
    print_hits("FINAL HITS USED BY /answer", final_hits, limit=k)

    # 8) respuesta final
    result = svc.answer(query, k=k)

    print("\n" + "=" * 100)
    print("FINAL ANSWER")
    print("=" * 100)
    print(f"q          : {result.get('q')}")
    print(f"confidence : {result.get('confidence')}")
    print(f"conclusion : {result.get('conclusion')}")
    print()

    print("=" * 100)
    print("CITATIONS")
    print("=" * 100)
    for i, c in enumerate(result.get("citations", []), start=1):
        print(f"[{i}] {c.get('title')}")
        print(f"    paper_id : {c.get('paper_id')}")
        print(f"    doi      : {c.get('doi')}")
        print()

    print("=" * 100)
    print("EVIDENCES")
    print("=" * 100)
    for i, e in enumerate(result.get("evidences", []), start=1):
        print(f"[{i}] {e.get('title')}")
        print(f"    paper_id : {e.get('paper_id')}")
        print(f"    doi      : {e.get('doi')}")
        print(f"    score    : {round(float(e.get('score', 0.0)), 4)}")
        print(f"    span     : {(e.get('span') or '')[:500]}")
        print()


if __name__ == "__main__":
    main()
