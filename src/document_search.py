import structlog
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

import pubmed

logger = structlog.get_logger(__name__)


def _extract_article_metadata(article):
    """
    Extract metadata from an article object.

    Parameters:
    article (Article): An article object containing metadata attributes such as
                       title, doi, publication_year, authors, and url.

    Returns:
    dict: A dictionary containing the extracted metadata with keys:
          - title: The title of the article (str).
          - doi: The DOI (Digital Object Identifier) of the article (str).
          - publication_year: The publication year of the article (str).
          - authors: A semicolon-separated string of author names (str).
          - url: The URL of the article (str).
    """
    title = article.title or "<UNK>"
    doi = article.doi or "<UNK>"
    publication_year = article.publication_year or "<UNK>"
    authors = "; ".join(article.authors) if article.authors is not None else "<UNK>"
    return {
        "title": title,
        "doi": doi,
        "publication_year": publication_year,
        "authors": authors,
        "url": article.url
    }


def _generate_documents(articles, min_length=200):
    """
    Generate document objects from a list of articles, filtering texts by minimum
    length. One article text corresponds roughly to one paragraph.

    Parameters:
    articles (list): A list of Article objects to generate documents from.
    min_length (int): Minimum length of text to be considered as a valid document
                      (default: 200).

    Returns:
    list: A list of Document objects, each representing a single article text
          (paragraph) with corresponding metadata.
    """
    docs = []
    for article in articles:
        metadata = _extract_article_metadata(article)
        for text in article.texts:
            if len(text) > min_length:
                doc = Document(page_content=text, metadata=metadata)
                docs.append(doc)
    logger.debug(f"Generated {len(docs)} documents")
    return docs


def _set_up_vectorstore(docs):
    """
    Set up a vector store for document retrieval using embeddings.

    Parameters:
    docs (list): A list of Document objects to store in the vector store.

    Returns:
    Chroma: A Chroma vector store object initialized with the provided documents
            and embeddings.
    """
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
    )
    return vectorstore


def document_search(state, config):
    """
    Search and scrape relevant articles from online article database, store  paragraphs
    in a vector store as documents, and retrieve the most relevant documents.

    Parameters:
    state (GraphState): A GraphState object containing:
                        - query_strings (list): A list of query strings for searching
                                                articles.
                        - input_sentence (str): An input sentence to retrieve
                                                relevant documents for.
    config (Config): A Config object containing:
                     - n_articles_per_query (int) : Number of aricles to retrieve per
                                                    query string
                     - n_docs_retrival (int): Number of top relevant documents to
                       retrieve from vector database.
                     - reset_vectorstore_after_retrieval (bool): Whether to reset the
                       vector store after retrieval.

    Returns:
    GraphState: A GraphState object with a list of retrieved Document objects appended
                to the 'docs' attribute.
    """
    query_strings = state["query_strings"]
    input_sentence = state["input_sentence"]
    articles = pubmed.pubmed_document_search(
        query_strings, config
    )
    docs = _generate_documents(articles)
    vectorstore = _set_up_vectorstore(docs)
    retriever = vectorstore.as_retriever(search_kwargs={"k": config.n_docs_retrival})
    retrieved_docs = retriever.invoke(input_sentence)
    if config.reset_vectorstore_after_retrieval:
        vectorstore.delete_collection()
    return {"docs": retrieved_docs}
