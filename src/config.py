from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    n_articles_per_query: int = 10
    n_docs_retrival: int = 10
    model_name: str = "gpt-4o-2024-08-06"
    temperature: int = 0
    reset_vectorstore_after_retrieval: bool = True
    use_langsmith: bool = True
    langchain_project: Optional[str] = "citation-finder"
    langchain_tracing_v2: Optional[str] = "true"
    langchain_endpoint: Optional[str] = "https://api.smith.langchain.com"
    langchain_user_agent: Optional[str] = "myagent"
