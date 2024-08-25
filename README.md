# CitationFinder

CitationFinder is an application designed to streamline the process of finding academic citations by leveraging web scraping and large language models. It helps researchers, scholars, and students alike quickly locate supporting citations from academic literature, significantly reducing the time and effort required for this often cumbersome task.

## Overview

In scholarly contexts, providing a citation for your claims is essential. However, finding a suitable citation that perfectly matches your specific needs can be challenging. This application automates the process of searching for relevant articles, extracting pertinent information, and evaluating the quality of the citations.

### Supported Databases

As of now, CitationFinder includes support only for the PubMed database.

<PubMed is a free resource that primarily comprises MEDLINE, a database of references and abstracts on life sciences and biomedical topics. It is maintained by the National Center for Biotechnology Information (NCBI) at the U.S. National Library of Medicine (NLM). PubMed provides access to a vast repository of medical literature, including research articles, reviews, and clinical studies.>

(Including additional databases is primarily a matter of developing article scraping logic for these databases.)

## How It Works

The workflow of CitationFinder is as follows:

1. **Input Sentence**: The user inputs a sentence into the application, for which they seek supporting citations from academic literature.
2. **Search Query Translation**: A language model transforms the sentence into N (default: 5) search queries / phrases optimized for database searches.
3. **Database Search**: The application searches an article database for the K (default: 10) most relevant articles for each search query, retrieving their texts and metadata.
4. **Document Processing**: The application breaks down the texts into smaller paragraphs, treating each paragraph as a "document".
5. **Embedding Documents**: Each document is embedded, i.e., converted into a numerical vector that encodes its semantic content.
6. **Vector Storage**: The vectors are stored in a vector database, allowing for efficient retrieval based on similarity search.
7. **User Input Sentence Embedding**: The user's original input sentence is embedded into a vector.
8. **Document Retrieval**: The application retrieves J (default: 10) documents from the vector database whose vectors most closely match the user's input sentence vector.
9. **Citation Evaluation**: A language model evaluates each of the retrieved documents to determine whether it can be used as a direct and undeniable source for the user's input sentence.

## Usage Instructions

### Environment Setup

Before running the application, you need to set up the required environment variables:

1. **OPENAI_API_KEY**: This is necessary to use the language models. You can set it up in your terminal as follows:
   ```bash
   export OPENAI_API_KEY='<your-openai-api-key>'

2. **LANGCHAIN_API_KEY**: This is required if you wish to use LangSmith for enhanced tracing and analysis. Set it up with:
   ```bash
   export LANGCHAIN_API_KEY='<your-langchain-api-key>'

   Make sure to enable LangSmith usage in the configuration file by setting `use_langsmith` to `True`.

### Dependency management

You can manage dependencies using either Poetry or pip:

* Using poetry: `poetry install`
* Using pip: `pip install requirements.txt`

### Running the Application

To run the application, navigate to the src directory and execute the following command:

```bash
python main.py --sentence "<Your input sentence here>"
```

If you want to see how the application works with the default configuration, you can simply run:

```bash
python main.py
```

This will automatically search for citations for the sentence "Covid 19 increased the likelihood of heart complications."

### Configuration

Please refer to the following flags for how to conifgure the application:

- **`--input_sentence`**: The sentence for which you want to find citations. This argument is required.
- **`--n_articles`**: The number of articles to retrieve per search query (default: 10).
- **`--n_docs`**: The number of documents to retrieve from the vector database (default: 10).
- **`--model_name`**: The name of the OpenAI language model to use (default: `"gpt-4o-2024-08-06"`).
- **`--temperature`**: The temperature setting for the language model, which controls the randomness of the output (default: `0.0`).
- **`--reset_vectorstore`**: Whether to reset the vector store after retrieval (default: `True`).
- **`--use_langsmith`**: Whether to enable LangSmith integration for enhanced tracing and analysis (default: `False`; only necessary if `reset_vectorstore == True`).
- **`--langchain_project`**: The name of the LangChain project to use (default: `"citation-finder"`; only necessary if `reset_vectorstore == True`).
- **`--langchain_tracing_v2`**: The setting for LangChain tracing version 2 (default: `"true"`; only necessary if `reset_vectorstore == True`).
- **`--langchain_endpoint`**: The API endpoint for LangChain (default: `"https://api.smith.langchain.com"`; only necessary if `reset_vectorstore == True`).
- **`--langchain_user_agent`**: The user agent string for LangChain API requests (default: `"myagent"`; only necessary if `reset_vectorstore == True`).

# License

This project is licensed under the CC BY-NC 4.0 License. See the LICENSE file for details.
