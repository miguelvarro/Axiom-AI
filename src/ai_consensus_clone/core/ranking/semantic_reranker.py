from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticReranker:
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        semantic_weight: float = 0.65,
        heuristic_weight: float = 0.35,
    ):
        self.model = SentenceTransformer(model_name)
        self.semantic_weight = semantic_weight
        self.heuristic_weight = heuristic_weight

    def _build_text(self, hit: Dict[str, Any]) -> str:
        return " ".join(
            part for part in [
                hit.get("title") or "",
                hit.get("reasoning_text") or "",
                hit.get("abstract") or "",
            ]
            if part
        ).strip()

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        if scores.size == 0:
            return scores

        min_score = float(np.min(scores))
        max_score = float(np.max(scores))

        if abs(max_score - min_score) < 1e-12:
            return np.ones_like(scores) * 0.5

        return (scores - min_score) / (max_score - min_score)

    def rerank(
        self,
        query: str,
        hits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not hits:
            return hits

        texts = [self._build_text(h) for h in hits]

        query_emb = self.model.encode([query], normalize_embeddings=True)[0]
        doc_embs = self.model.encode(texts, normalize_embeddings=True)

        semantic_scores = np.dot(doc_embs, query_emb)
        semantic_scores_norm = self._normalize_scores(np.array(semantic_scores, dtype=float))

        heuristic_scores = np.array(
            [float(h.get("rerank_score", h.get("score", 0.0)) or 0.0) for h in hits],
            dtype=float,
        )
        heuristic_scores_norm = self._normalize_scores(heuristic_scores)

        reranked: List[Dict[str, Any]] = []

        for h, sem_raw, sem_norm, heur_raw, heur_norm in zip(
            hits,
            semantic_scores,
            semantic_scores_norm,
            heuristic_scores,
            heuristic_scores_norm,
        ):
            final_score = (
                self.semantic_weight * float(sem_norm)
                + self.heuristic_weight * float(heur_norm)
            )

            item = dict(h)
            item["semantic_score"] = float(sem_raw)
            item["semantic_score_norm"] = float(sem_norm)
            item["heuristic_score_norm"] = float(heur_norm)
            item["final_rerank_score"] = float(final_score)
            reranked.append(item)

        reranked.sort(key=lambda x: x["final_rerank_score"], reverse=True)
        return reranked
