from __future__ import annotations

import math
import re

from typing import List, Optional, Tuple

from axiom_ai.core.domain.paper import Paper
from axiom_ai.core.enrichment.fulltext_service import FullTextService
from axiom_ai.core.ingestion.connectors.openalex import OpenAlexClient
from axiom_ai.utils.text import clean_text
from axiom_ai.core.ingestion.connectors.openalex import (
    OpenAlexClient,
    extract_abstract,
    extract_doi,
    extract_oa_landing_url,
    extract_oa_pdf_url,
)

_WORD_RE = re.compile(r"\b\w+\b")

STOPWORDS = {
    "the",
    "and",
    "with",
    "from",
    "that",
    "this",
    "have",
    "were",
    "been",
    "their",
    "into",
    "about",
    "using",
    "effect",
    "effects",
    "study",
    "analysis",
    "review",
    "associated",
    "performance",
    "sarcopenia",
}


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]


def _content_terms(text: str) -> set[str]:
    toks = _tokenize(text)

    return {
        t for t in toks
        if len(t) >= 4 and t not in STOPWORDS
    }


class OnlinePaperRetriever:
    """
    Online scientific paper retriever.

    Features:
    - OpenAlex live retrieval
    - thematic filtering
    - citation-aware ranking
    - recency balancing
    - fulltext enrichment
    """

    def __init__(
        self,
        client: Optional[OpenAlexClient] = None,
        fulltext_service: Optional[FullTextService] = None,
    ):
        self.client = client or OpenAlexClient()
        self.fulltext_service = (
            fulltext_service
            or FullTextService()
        )

    def search_openalex(
        self,
        query: str,
        n: int = 10,
        oa_only: bool = True,
    ) -> List[Paper]:

        filters = None

        per_page = max(n * 5, 25)

        works = self.client.search_works(
            query,
            per_page=per_page,
            filters=filters,
        )

        scored_candidates: List[
            Tuple[float, Paper]
        ] = []

        for work in works:

            paper = self._work_to_paper(work)

            if paper is None:
                continue

            thematic_score = self._thematic_score(
                query,
                paper,
            )


            if thematic_score <= 0:
                continue

            final_score = self._ranking_score(
                thematic_score=thematic_score,
                citation_count=(
                    paper.citation_count or 0
                ),
                year=paper.year,
            )

            scored_candidates.append(
                (
                    final_score,
                    paper,
                )
            )

        scored_candidates.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        papers: List[Paper] = []

        for _, paper in scored_candidates:

            try:
                paper = (
                    self.fulltext_service
                    .enrich_paper(paper)
                )

            except Exception:

                if (
                    paper.abstract
                    and not paper.full_text
                ):
                    paper.full_text = clean_text(
                        paper.abstract
                    )

                    paper.full_text_source = (
                        "openalex_abstract"
                    )

            if (
                not (paper.full_text or "").strip()
                and paper.abstract
            ):
                paper.full_text = clean_text(
                    paper.abstract
                )

                paper.full_text_source = (
                    "openalex_abstract"
                )

            papers.append(paper)

            if len(papers) >= n:
                break

        return papers

    def _ranking_score(
        self,
        thematic_score: float,
        citation_count: int,
        year: Optional[int],
    ) -> float:

        # Citation normalization
        citation_score = min(
            math.log1p(citation_count) / 10,
            1.0,
        )

        # Recent papers boost
        year_bonus = 0.0

        if year:
            year_bonus = max(
                0.0,
                (year - 2018) * 0.03,
            )

        return (
            thematic_score * 0.75
            + citation_score * 0.20
            + year_bonus * 0.05
        )

    def _thematic_score(
        self,
        query: str,
        paper: Paper,
    ) -> float:

        query_terms = _content_terms(query)

        if not query_terms:
            return 0.0

        paper_text = " ".join(
            [
                paper.title or "",
                paper.abstract or "",
                paper.full_text or "",
            ]
        )

        paper_terms = _content_terms(
            paper_text
        )

        overlap = (
            query_terms & paper_terms
        )

        if not overlap:
            return 0.0

        overlap_ratio = (
            len(overlap)
            / len(query_terms)
        )

        title_bonus = 0.0

        title_terms = _content_terms(
            paper.title or ""
        )

        title_overlap = (
            query_terms & title_terms
        )

        if title_overlap:
            title_bonus = (
                len(title_overlap)
                / len(query_terms)
            )

        return (
            overlap_ratio * 0.7
            + title_bonus * 0.3
        )

    def _work_to_paper(
        self,
        work: dict,
    ) -> Optional[Paper]:

        paper_id_raw = (
            work.get("id")
            or ""
        )

        paper_id = (
            paper_id_raw.split("/")[-1].strip()
            if paper_id_raw
            else ""
        )

        title = clean_text(
            work.get("title") or ""
        )

        abstract = clean_text(
            extract_abstract(work) or ""
        ) or None

        year = work.get(
            "publication_year"
        )

        citation_count = work.get(
            "cited_by_count",
            0,
        )

        venue = (
            (
                work.get(
                    "primary_location"
                )
                or {}
            )
            .get("source", {})
            .get("display_name")
        )

        doi = extract_doi(work)

        oa_url = extract_oa_landing_url(
            work
        )

        pdf_url = extract_oa_pdf_url(
            work
        )

        authors = [
            (
                a.get("author")
                or {}
            ).get("display_name")
            for a in (
                work.get("authorships")
                or []
            )
            if (
                a.get("author")
                or {}
            ).get("display_name")
        ]

        if not paper_id and not title:
            return None

        return Paper(
            paper_id=paper_id or title[:50],
            title=title,
            abstract=abstract,
            year=year,
            venue=venue,
            doi=doi,
            authors=authors,
            oa_url=oa_url,
            pdf_url=pdf_url,
            citation_count=citation_count,
        )
