from app import CitationFinder
from config import Config

INPUT_SENTENCE = "Covid 19 increased the likelihood of heart issues"


def run():
    config = Config()
    app = CitationFinder(config)
    app.search(INPUT_SENTENCE)


if __name__ == "__main__":
    run()
