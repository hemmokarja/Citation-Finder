import argparse

from app import CitationFinder
from config import Config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run CitationFinder with custom configuration."
    )

    parser.add_argument(
        "--input_sentence",
        type=str,
        default="Covid 19 increased the likelihood of heart complications",
        help="Input sentence for which you want to find citations."
    )

    parser.add_argument(
        "--n_articles",
        type=int,
        default=10,
        help="Number of articles to retrieve per search query."
    )
    parser.add_argument(
        "--n_docs",
        type=int,
        default=10,
        help="Number of documents to retrieve from the vector database."
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="gpt-4o-2024-08-06",
        help="Name of the OpenAI language model to use."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature setting for the language model."
    )
    parser.add_argument(
        "--reset_vectorstore",
        type=bool,
        default=True,
        help="Whether to reset the vector store after retrieval."
    )
    parser.add_argument(
        "--use_langsmith",
        type=bool,
        default=False,
        help="Whether to use LangSmith integration."
    )
    parser.add_argument(
        "--langchain_project",
        type=str,
        default="citation-finder",
        help="LangChain project name."
    )
    parser.add_argument(
        "--langchain_tracing_v2",
        type=str,
        default="true",
        help="LangChain tracing v2 setting."
    )
    parser.add_argument(
        "--langchain_endpoint",
        type=str,
        default="https://api.smith.langchain.com",
        help="LangChain API endpoint."
    )
    parser.add_argument(
        "--langchain_user_agent",
        type=str,
        default="myagent",
        help="User agent for LangChain API."
    )

    return parser.parse_args()


def run():
    args = parse_args()
    config = Config(
        n_articles_per_query=args.n_articles,
        n_docs_retrival=args.n_docs,
        model_name=args.model_name,
        temperature=args.temperature,
        reset_vectorstore_after_retrieval=args.reset_vectorstore,
        use_langsmith=args.use_langsmith,
        langchain_project=args.langchain_project,
        langchain_tracing_v2=args.langchain_tracing_v2,
        langchain_endpoint=args.langchain_endpoint,
        langchain_user_agent=args.langchain_user_agent,
    )
    app = CitationFinder(config)
    app.search(args.input_sentence)


if __name__ == "__main__":
    run()
