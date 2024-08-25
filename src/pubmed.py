import concurrent
import datetime
import functools
import re

import bs4
import dateutil
import requests
import structlog

import search_util
from search_util import Article

logger = structlog.get_logger(__name__)


ARTICLE_BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/pmid/"
SEARCH_BASE_URL = "https://pubmed.ncbi.nlm.nih.gov/"


class PubMedParser:
    def __init__(self, soup):
        self.soup = soup

    def parse_article(self):
        return {
            "title": self._parse_title(),
            "doi": self._parse_doi(),
            "publication_year": self._parse_publication_year(),
            "authors": self._parse_authors(),
            "abstract": self._parse_abstract(),
            "texts": self._parse_texts(),
        }

    @search_util.exception_handler
    def _parse_title(self):
        """
        Parse the title of the article from the HTML soup object.

        Parameters:
        soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the
                            article.

        Returns:
        str: The title of the article.
        """
        return self.soup.find("h1", class_="content-title").text

    @search_util.exception_handler
    def _parse_doi(self):
        """
        Parse the DOI (Digital Object Identifier) of the article from the HTML soup
        object.

        Parameters:
        soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the
                              article.

        Returns:
        str: The DOI of the article.
        """
        return self.soup.find("span", class_="doi").find("a").text

    @search_util.exception_handler
    def _parse_publication_year(self):
        """
        Parse the publication year of the article from the HTML soup object.

        Parameters:
        soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the
                              article.

        Returns:
        int: The publication year of the article.
        """
        date = self.soup.find("span", class_="fm-vol-iss-date").text
        stripped = date.replace("Published online ", "").replace(".", "").strip()
        try:
            return datetime.datetime.strptime(stripped, "%Y %b %d").date().year
        except ValueError as e:
            parsed = dateutil.parser.parse(stripped).date().year
            logger.warning(
                f"Error parsing date string '{stripped}': {repr(e)}. "
                f"Used 'dateutil.parser' to parse the string to '{parsed}'"
            )
            return parsed

    @search_util.exception_handler
    def _parse_authors(self):
        """
        Parse the list of authors from the HTML soup object.

        Parameters:
        soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the
                              article.

        Returns:
        list[str]: A list of author names.
        """

        # several authors may be within one 'contrib-group fm-author' block in many 'a'
        # blocks, or several authors may be split between several
        # 'contrib-group fm-author' with each 'a' block having a single author, this
        # handles both cases
        authors = []
        author_elements = self.soup.find_all("div", class_="contrib-group fm-author")
        for element in author_elements:
            authors += [a.text for a in element.find_all("a")]
        return authors

    @search_util.exception_handler
    def _parse_abstract(self):
        """
        Parse the abstract of the article from the HTML soup object.

        Parameters:
        soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the
                              article.

        Returns:
        str or None: The abstract of the article as a single string, or None if no
                     abstract is found.
        """
        abstract_element = self.soup.find("div", id=re.compile(r'^abstract-'))
        if abstract_element is None:
            # not all articles have abstracts
            # see e.g. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7843064/
            return None
        paragraphs = abstract_element.find_all("p")
        return "\n\n".join([p.text for p in paragraphs])

    @staticmethod
    def _is_not_empty(paragraph):
        return paragraph.text.strip() != ""

    @search_util.exception_handler
    def _parse_texts(self):
        """
        Parse the main body texts of the article from the HTML soup object. One text
        corresponds roughly to a single paragraph.

        Parameters:
        soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the
                              article.

        Returns:
        list[str]: A list of strings, each representing a cleaned paragraph of text from
                the article.
        """
        texts = []
        sections = self.soup.find_all("div", class_="tsec sec")
        for section in sections:
            paragraphs = section.find_all("p")
            for paragraph in paragraphs:
                if self._is_not_empty(paragraph):
                    cleaned = paragraph.text.replace("\n", "")
                    # TODO: check that text is not in seen texts, this may happen
                    # sometimes because footnotes use nested p tags and thus same text
                    # gets added multiple times
                    texts.append(cleaned)
        return texts


def _scrape_article(url):
    """
    Scrape a single article from a given URL and parse its content.

    Parameters:
    url (str): The URL of the article to be scraped.

    Returns:
    Article: An Article object created from the parsed HTML content.
    """
    resp = requests.get(url, headers=search_util.HEADERS)
    resp.raise_for_status()
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    parser = PubMedParser(soup)
    return Article.from_parser(parser, url)


def _scrape_articles(urls):
    """
    Scrape multiple articles from a list of URLs.

    Parameters:
    urls (list): A list of URLs to scrape articles from.

    Returns:
    list[Article]: A list of Article objects created from the parsed HTML content of
                   each URL.
    """
    articles = []
    for url in urls:
        article = _scrape_article(url)
        articles.append(article)
    return articles


def _is_free_pubmed_article(element):
    """
    Check if an article is a free PubMed article based on its HTML element.

    Parameters:
    element (Tag): A BeautifulSoup Tag object representing an article element.

    Returns:
    bool: True if the article is a free PubMed article, False otherwise.
    """
    free_resource_str = element.find(
        "span", class_="free-resources spaced-citation-item citation-part"
    )
    if free_resource_str is None:
        return False
    return free_resource_str.text == "Free PMC article."


def _find_free_pubmed_article_urls(soup, n_articles_per_query, query_string):
    """
    Find URLs of free PubMed articles from the search results page.

    Parameters:
    soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the
                          search results page.
    n_articles_per_query (int): The maximum number of article URLs to find.
    query_string (str): The search query string used to find articles.

    Returns:
    list[str]: A list of URLs of free PubMed articles.
    """
    urls = []
    for element in soup.find_all("article", class_="full-docsum"):
        if _is_free_pubmed_article(element):
            article_id = element.find("a", class_="docsum-title").get("data-article-id")
            url = ARTICLE_BASE_URL + article_id
            urls.append(url)
            if len(urls) >= n_articles_per_query:
                break
    logger.debug(
        f"Found {len(urls)} free PubMed articles for query string '{query_string}'"
    )
    return urls


def _search_and_scrape_articles(query_string, config):
    """
    Search for articles based on a query string, then scrape and parse the results.

    Parameters:
    query_string (str): The search query string to use for finding articles.
    config (Config): A Config object containing:
                     - n_articles_per_query (int): Number of articles to scrape per
                                                   query.

    Returns:
    list[Article]: A list of Article objects created from the parsed HTML content of
                   the search results.
    """
    params = {"term": query_string, "size": 200}
    resp = requests.get(SEARCH_BASE_URL, params=params, headers=search_util.HEADERS)
    resp.raise_for_status()
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    urls = _find_free_pubmed_article_urls(
        soup, config.n_articles_per_query, query_string
    )
    articles = _scrape_articles(urls)
    return articles


def pubmed_document_search(query_strings, config):
    """
    Perform a search for multiple query strings, scrape, and parse the results.

    Parameters:
    query_strings (list): A list of search query strings to use for finding articles.
    config (Config): A Config object containing:
                     - n_articles_per_query (int): Number of articles to scrape per
                                                   query.

    Returns:
    list[Article]: A list of unique Article objects created from the parsed HTML
                   content of all search results.
    """
    articles = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        func = functools.partial(_search_and_scrape_articles, config=config)
        results = executor.map(func, query_strings)

    articles = []
    for result in results:
        articles += result
    articles = list(set(articles))
    logger.debug(f"Found and scraped {len(articles)} unique PubMed articles in total")
    return articles
