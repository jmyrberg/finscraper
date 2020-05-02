"""Module for testing spiders."""


import json
import tempfile

from pathlib import Path

from finscraper.spiders import ISArticle


def test_ISArticle():
    jobdir = Path(tempfile.gettempdir()) / 'isarticle2'
    spider = ISArticle(
        category=None,
        FEEDS={jobdir / 'items.json': {'format': 'json'}},
    )
    spider.run()

    # TODO: Figure out how to test properly...?
