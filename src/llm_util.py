import os

from langchain.schema import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_openai import ChatOpenAI


class Assistant:
    def __init__(self, runnable):
        self.runnable = runnable

    def invoke(self, message_content):
        messages = [HumanMessage(content=message_content)]
        return self.runnable.invoke({"messages": messages})


def init_assistant_runnable(system_prompt, tools, config):
    if not isinstance(tools, list):
        tools = [tools]

    assistant_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            MessagesPlaceholder("messages")
        ]
    )
    llm = (
        ChatOpenAI(model_name=config.model_name, temperature=config.temperature)
        .bind_tools(tools=tools, strict=True)
    )
    return assistant_prompt | llm


def read_system_prompt(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "prompts", filename)
    with open(path, "r") as f:
        prompt = f.read()
    return prompt
