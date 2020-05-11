"""Module for testing VauvaPage."""


import pytest
pytestmark = [pytest.mark.spider, pytest.mark.vauvapage]

from finscraper.spiders import VauvaPage


def test_VauvaPage():
    # Test scraping
    spider = VauvaPage().scrape(1)
    df = spider.get()
    assert len(df) >= 1
    assert len(df.columns) == 8

    # Test continuing scraping
    df2 = spider.scrape(1).get()
    assert len(df2) >= len(df) + 1

    # Save and load spider
    jobdir = spider.save()
    spider = VauvaPage.load(jobdir)

    df3 = spider.scrape(1).get()
    assert len(df3) >= len(df2) + 1
