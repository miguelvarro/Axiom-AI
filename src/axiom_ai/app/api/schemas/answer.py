from pydantic import BaseModel, Field
from typing import List, Optional, Any


class AnswerRequest(BaseModel):
    q: str = Field(..., min_length=2)
    k: int = Field(8, ge=3, le=20)


class Citation(BaseModel):
    paper_id: str
    doi: Optional[str] = None
    title: str
    citation_count: Optional[int] = None


class EvidenceItem(BaseModel):
    paper_id: str
    title: Optional[str] = None
    span: Optional[str] = None
    score: Optional[float] = None
    year: Optional[int] = None
    venue: Optional[str] = None


class TopPaper(BaseModel):
    paper_id: str
    title: Optional[str] = None
    doi: Optional[str] = None
    stance: Optional[str] = None
    weight: Optional[float] = None
    citation_count: Optional[int] = None


class Methodology(BaseModel):
    papers_analyzed: int
    supporting_papers: int
    contradicting_papers: int
    neutral_papers: int


class QueryAnalysisSchema(BaseModel):
    raw_query: str
    query_type: str
    population: Optional[str] = None
    intervention: Optional[str] = None
    outcome: Optional[str] = None
    comparator: Optional[str] = None


class AnswerResponse(BaseModel):
    q: str
    conclusion: str
    consensus_label: str
    dominant_stance: str
    confidence: str
    confidence_numeric: float
    confidence_score: float
    consensus_score: float
    contradictions_present: bool
    contradiction_summary: Optional[str] = None
    supporting_evidence: List[EvidenceItem] = []
    contradicting_evidence: List[EvidenceItem] = []
    neutral_evidence: List[EvidenceItem] = []
    top_papers: List[TopPaper] = []
    methodology: Methodology
    confidence_factors: dict
    citations: List[Citation] = []
    query_analysis: Optional[QueryAnalysisSchema] = None

    # Campos legacy opcionales (compatibilidad hacia atrás)
    evidences: Optional[List[Any]] = None
    paper_stances: Optional[List[Any]] = None
    evidence_breakdown: Optional[Any] = None
