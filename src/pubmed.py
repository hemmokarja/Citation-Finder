import concurrent
import datetime
import functools
import re

import bs4
import dateutil
import requests
import structlog

import search_util

logger = structlog.get_logger(__name__)


ARTICLE_BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/pmid/"
SEARCH_BASE_URL = "https://pubmed.ncbi.nlm.nih.gov/"


class Article:
    def __init__(self, title, doi, publication_year, authors, abstract, texts, url):
        self.title = title
        self.doi = doi
        self.publication_year = publication_year
        self.authors = authors
        self.abstract = abstract
        self.texts = texts
        self.url = url

    def __repr__(self):
        return (
            f"<Article(title={self.title}, year={self.publication_year}, "
            f"url={self.url})>"
        )

    def __hash__(self):
        return hash((self.title, self.publication_year, tuple(self.authors)))

    def __eq__(self, other):
        if isinstance(other, Article):
            return (
                (self.title, self.publication_year, tuple(self.authors)) ==
                (other.title, other.publication_year, tuple(other.authors))
            )
        return False

    @classmethod
    def from_soup(cls, soup, url):
        title = _parse_title(soup)
        doi = _parse_doi(soup)
        publication_year = _parse_publication_year(soup)
        authors = _parse_authors(soup)
        abstract = _parse_abstract(soup)
        texts = _parse_texts(soup)
        return cls(title, doi, publication_year, authors, abstract, texts, url)


@search_util.exception_handler
def _parse_title(soup):
    return soup.find("h1", class_="content-title").text


@search_util.exception_handler
def _parse_doi(soup):
    return soup.find("span", class_="doi").find("a").text


@search_util.exception_handler
def _parse_publication_year(soup):
    date = soup.find("span", class_="fm-vol-iss-date").text
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
def _parse_authors(soup):
    # several authors may be within one 'contrib-group fm-author' block in many 'a'
    # blocks, or several authors may be split between several 'contrib-group fm-author'
    # with each 'a' block having a single author
    authors = []
    author_elements = soup.find_all("div", class_="contrib-group fm-author")
    for element in author_elements:
        authors += [a.text for a in element.find_all("a")]
    return authors


@search_util.exception_handler
def _parse_abstract(soup):
    abstract_element = soup.find("div", id=re.compile(r'^abstract-'))
    if abstract_element is None:
        # not all articles have abstracts
        # see e.g. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7843064/
        return None
    paragraphs = abstract_element.find_all("p")
    return "\n\n".join([p.text for p in paragraphs])


def _is_not_empty(paragraph):
    return paragraph.text.strip() != ""


@search_util.exception_handler
def _parse_texts(soup):
    texts = []
    sections = soup.find_all("div", class_="tsec sec")
    for section in sections:
        paragraphs = section.find_all("p")
        for paragraph in paragraphs:
            if _is_not_empty(paragraph):
                cleaned = paragraph.text.replace("\n", "")
                # TODO: check that text is not in seen texts, this may happen sometimes
                # because footnotes use nested p tags and thus same text gets added
                # multiple times
                texts.append(cleaned)
    return texts


def _scrape_article(url):
    resp = requests.get(url, headers=search_util.HEADERS)
    resp.raise_for_status()
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    return Article.from_soup(soup, url)


def _scrape_articles(urls):
    articles = []
    for url in urls:
        article = _scrape_article(url)
        articles.append(article)
    return articles


def _is_free_pmc_article(element):
    free_resource_str = element.find(
        "span", class_="free-resources spaced-citation-item citation-part"
    )
    if free_resource_str is None:
        return False
    return free_resource_str.text == "Free PMC article."


def _find_free_pmc_article_urls(soup, n_articles_per_query, query_string):
    urls = []
    for element in soup.find_all("article", class_="full-docsum"):
        if _is_free_pmc_article(element):
            article_id = element.find("a", class_="docsum-title").get("data-article-id")
            url = ARTICLE_BASE_URL + article_id
            urls.append(url)
            if len(urls) >= n_articles_per_query:
                break
    logger.debug(
        f"Found {len(urls)} free PMC articles for query string '{query_string}'"
    )
    return urls


def _search_and_scrape_articles(query_string, config):
    params = {"term": query_string, "size": 200}
    resp = requests.get(SEARCH_BASE_URL, params=params, headers=search_util.HEADERS)
    resp.raise_for_status()
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    urls = _find_free_pmc_article_urls(soup, config.n_articles_per_query, query_string)
    articles = _scrape_articles(urls)
    return articles


def pubmed_document_search(query_strings, config):
    articles = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        func = functools.partial(_search_and_scrape_articles, config=config)
        results = executor.map(func, query_strings)

    articles = []
    for result in results:
        articles += result
    articles = list(set(articles))
    logger.debug(f"Found and scraped {len(articles)} unique PMC articles in total")
    return articles
