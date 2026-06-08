from __future__ import annotations

from axiom_ai.core.domain.paper import Paper
from axiom_ai.core.enrichment.fulltext_service import FullTextService


class FullTextEnricher:
    """
    Wrapper de compatibilidad hacia atrás.
    """

    def __init__(self):
        self.service = FullTextService()

    def enrich(self, paper: Paper) -> Paper:
        return self.service.enrich_paper(paper)
