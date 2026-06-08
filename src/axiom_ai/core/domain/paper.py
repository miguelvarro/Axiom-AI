from pydantic import BaseModel, Field
from typing import Optional, List

class Paper(BaseModel):
    paper_id: str
    title: str
    abstract: Optional[str] = None
    oa_url: Optional[str] = None
    pdf_url: Optional[str] = None
    full_text: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    full_text_source: Optional[str] = None
    pmc_url: Optional[str] = None
    

    full_text_preview: Optional[str] = None
    full_text_quality_score: float = 0.0
    citation_count: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    results_text: Optional[str] = None
    discussion_text: Optional[str] = None
    conclusion_text: Optional[str] = None
    reasoning_text: Optional[str] = None
