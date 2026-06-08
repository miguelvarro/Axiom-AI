from pydantic import BaseModel
from typing import Optional


class QueryAnalysis(BaseModel):
    raw_query: str
    query_type: str
    population: Optional[str] = None
    intervention: Optional[str] = None
    outcome: Optional[str] = None
    comparator: Optional[str] = None
