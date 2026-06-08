from fastapi import APIRouter, Depends

from axiom_ai.app.api.schemas.search import (
    SearchRequest,
    SearchResponse,
)

from axiom_ai.app.api.deps import (
    get_online_retriever,
)

from axiom_ai.core.retrieval.online import (
    OnlinePaperRetriever,
)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(
    req: SearchRequest,
    retriever: OnlinePaperRetriever = Depends(
        get_online_retriever
    ),
):

    papers = retriever.search_openalex(
        query=req.q,
        n=req.k,
        oa_only=True,
    )

    hits = [
        {
            "paper_id": p.paper_id,
            "title": p.title,
            "year": p.year,
            "doi": p.doi,
            "citation_count": p.citation_count,
            "oa_url": p.oa_url,
        }
        for p in papers
    ]

    return SearchResponse(
        q=req.q,
        k=req.k,
        hits=hits,
    )