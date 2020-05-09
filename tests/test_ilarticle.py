"""Module for testing ILArticle."""


import pytest
pytestmark = [pytest.mark.spider, pytest.mark.ilarticle]

from finscraper.spiders import ILArticle


def test_ILArticle_with_category():
    # Test scraping
    spider = ILArticle('ulkomaat').scrape(1)
    df = spider.get()
    assert len(df) >= 1
    assert len(df.columns) == 8

    # Test continuing scraping
    df2 = spider.scrape(1).get()
    assert len(df2) >= len(df) + 1

    # Save and load spider
    jobdir = spider.save()
    spider = ILArticle.load(jobdir)

    df3 = spider.scrape(1).get()
    assert len(df3) >= len(df2) + 1


def test_ILArticle_no_params():
    # Test scraping
    spider = ILArticle().scrape(10)
    df = spider.get()
    assert len(df) >= 10
    assert len(df.columns) == 8

    # Test continuing scraping  
    df2 = spider.scrape(10).get()
    assert len(df2) >= len(df) + 10

    # Save and load spider
    jobdir = spider.save()
    spider = ILArticle.load(jobdir)

    df3 = spider.scrape(10).get()
    assert len(df3) >= len(df2) + 10
