import os
from typing import TypedDict

import structlog
from langchain.schema import Document
from langgraph.graph import END, StateGraph

import document_search
import llm_util
import printing
from document_grading import DocumentGrader, DocumentGradingTool
from query_translation import QueryTranslationTool, QueryTranslator

logger = structlog.get_logger(__name__)


class GraphState(TypedDict):
    input_sentence: str
    query_strings: list[str]
    docs: list[Document]


class CitationFinder:
    def __init__(self, config):
        _check_openai_env()

        if config.use_langsmith:
            _set_langchain_env(config)

        self.config = config
        self.app = self._build_app()

    def _build_app(self):
        # fetch system prompts
        query_translator_prompt = llm_util.read_system_prompt("query_translation.txt")
        document_grader_prompt = llm_util.read_system_prompt("document_grading.txt")
        # init query translator
        query_translator_runnable = llm_util.init_assistant_runnable(
            query_translator_prompt, tools=QueryTranslationTool, config=self.config
        )
        query_translator = QueryTranslator(query_translator_runnable)
        # init document grader
        document_grader_runnable = llm_util.init_assistant_runnable(
            document_grader_prompt, tools=DocumentGradingTool, config=self.config
        )
        document_grader = DocumentGrader(document_grader_runnable)
        # init document search
        doc_search_func = (
            lambda state: document_search.document_search(state, self.config)
        )
        # build app
        builder = StateGraph(GraphState)

        builder.add_node("query_translator", query_translator)
        builder.add_node("document_grader", document_grader)
        builder.add_node("document_search", doc_search_func)

        builder.set_entry_point("query_translator")
        builder.add_edge("query_translator", "document_search")
        builder.add_edge("document_search", "document_grader")
        builder.add_edge("document_grader", END)

        app = builder.compile()

        return app

    def search(self, input_sentence, return_mode="print"):
        assert return_mode in ["print", "return"]
        final_state = self.app.invoke({"input_sentence": input_sentence})
        if return_mode == "print":
            printing.print_output(final_state)
        elif return_mode == "return":
            return final_state


def _check_openai_env():
    if os.environ.get("OPENAI_API_KEY") is None:
        raise ValueError("Set `OPENAI_API_KEY` as environment variable")


def _set_langchain_env(config):
    if os.environ.get("LANGCHAIN_API_KEY") is None:
        raise ValueError("Set `LANGCHAIN_API_KEY` as environment variable")
    if config.langchain_project is None:
        raise ValueError("`Config.langchain_project` cannot be None")
    if config.langchain_tracing_v2 is None:
        raise ValueError("`Config.langchain_tracing_v2` cannot be None")
    if config.langchain_endpoint is None:
        raise ValueError("`Config.langchain_endpoint` cannot be None")
    if config.langchain_user_agent is None:
        raise ValueError("`Config.langchain_user_agent` cannot be None")
    os.environ["LANGCHAIN_PROJECT"] = config.langchain_project
    os.environ["LANGCHAIN_TRACING_V2"] = config.langchain_tracing_v2
    os.environ["LANGCHAIN_ENDPOINT"] = config.langchain_endpoint
    os.environ["USER_AGENT"] = config.langchain_user_agent
    logger.info("LangSmith environment set up!")
