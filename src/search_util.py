import functools

import structlog

logger = structlog.get_logger(__name__)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/"
        "102.0"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "DNT": "1",
    "TE": "trailers"
}


def exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"An error occurred executing {func.__name__}: {repr(e)}. "
                "Corresponding article field assigned to `None`"
            )
            return None
    return wrapper


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
    def from_parser(cls, parser, url):
        return cls(**parser.parse_article(), url=url)
