import structlog
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

import pubmed

logger = structlog.get_logger(__name__)


def _extract_article_metadata(article):
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
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
    )
    return vectorstore


def document_search(state, config):
    """
    Search top N for each query string, scrape their text and metadata, store them in
    paragraphs in vectorstore (one document per paragraph), and retrieve the top K most
    relevant documents to the input sentence.
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
