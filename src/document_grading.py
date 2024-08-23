import structlog
from langchain_core.pydantic_v1 import BaseModel, Field

import llm_util

logger = structlog.get_logger(__name__)


class DocumentGradingTool(BaseModel):
    document_is_relevant: bool = Field(
        description=(
            "Document is direcrly relevant to the input sentence, 'True' or 'False'"
        )
    )
    supporting_quote: str = Field(
        description=(
            "The most relevant phrase (or phrases) that support the input sentence"
        )
    )

    class Config:
        schema_extra = {
            "required": ["document_is_relevant", "supporting_quote"]
        }


def _format_inputs(doc, input_sentence):
    return (
        f"Document to grade:\n\n: {doc}\n\nUser's input sentence: {input_sentence}"
    )


def _tool_called(response):
    if not response.tool_calls:
        return False
    return True


class DocumentGrader(llm_util.Assistant):
    def __init__(self, runnable):
        super().__init__(runnable)

    def __call__(self, state):
        input_sentence = state["input_sentence"]
        filtered_docs = []
        for doc in state["docs"]:
            inputs = _format_inputs(doc.page_content, input_sentence)
            response = self.invoke(inputs)
            if _tool_called(response):
                tool_output = response.tool_calls[0]["args"]
                if tool_output["document_is_relevant"] == True:
                    doc.metadata["supporting_quote"] = tool_output["supporting_quote"]
                    filtered_docs.append(doc)
            else:
                logger.warning(
                    "DocumentGrader failed to call a tool, skipping grading of this "
                    "document"
                )
        logger.debug(f"Graded {len(filtered_docs)} documents are relevant")
        return {"docs": filtered_docs}
