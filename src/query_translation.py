from langchain_core.pydantic_v1 import BaseModel, Field

import llm_util


class QueryTranslationTool(BaseModel):
    query_strings: list[str] = (
        Field(description="The search strings for quering scientific article database.")
    )


class QueryTranslator(llm_util.Assistant):
    def __init__(self, runnable):
        super().__init__(runnable)

    def __call__(self, state):
        input_sentence = state["input_sentence"]
        response = self.invoke(input_sentence)
        if not response.tool_calls:
            raise RuntimeError("QueryTranslator failed to call a tool")
        query_strings = response.tool_calls[0]["args"]["query_strings"]
        return {"query_strings": query_strings}
