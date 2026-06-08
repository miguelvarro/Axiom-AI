from functools import lru_cache

from axiom_ai.core.config.settings import Settings
from axiom_ai.core.reasoning.answer import AnswerService
from axiom_ai.core.retrieval.online import OnlinePaperRetriever


@lru_cache
def get_settings() -> Settings:
    return Settings()




@lru_cache
def get_online_retriever() -> OnlinePaperRetriever:
    return OnlinePaperRetriever()


@lru_cache
def get_answer_service() -> AnswerService:
    return AnswerService(
        online_retriever=get_online_retriever(),
    )
