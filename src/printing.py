import textwrap

OUTPUT_TEMPLATE = """
TITLE:    {title}
YEAR:     {publication_year}
AUTHORS:  {authors}
URL:      {url}
DOI:      {doi}

"{supporting_quote}"
"""


def _format_output(
    title, publication_year, authors, url, doi, supporting_quote, width=100
):
    return OUTPUT_TEMPLATE.format(
        title=title,
        publication_year=publication_year,
        authors=authors,
        url=url,
        doi=doi,
        supporting_quote=textwrap.fill(supporting_quote, width=width),
    )


def print_output(state):
    for i, doc in enumerate(state["docs"]):
        print("=" * 43, f"[Citation {i+1}]", "=" * 43)
        print(_format_output(**doc.metadata))
