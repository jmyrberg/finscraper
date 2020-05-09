"""Module for testing ISArticle."""


import pytest
pytestmark = [pytest.mark.spider, pytest.mark.isarticle]

from finscraper.spiders import ISArticle


def test_ISArticle_with_category():
    # Test scraping, no chromedriver
    spider = ISArticle('ulkomaat').scrape(1)
    df = spider.get()
    assert len(df) >= 1
    assert len(df.columns) == 8

    # Test scraping with chromedriver
    spider = ISArticle('ulkomaat', allow_chromedriver=True).scrape(1)
    df = spider.get()
    assert len(df) >= 1
    assert len(df.columns) == 8

    # Test continuing scraping
    df2 = spider.scrape(1).get()
    assert len(df2) >= len(df) + 1

    # Save and load spider
    jobdir = spider.save()
    spider = ISArticle.load(jobdir)

    df3 = spider.scrape(1).get()
    assert len(df3) >= len(df2) + 1


def test_ISArticle_no_params():
    # Test scraping
    spider = ISArticle().scrape(10)
    df = spider.get()
    assert len(df) == 10
    assert len(df.columns) == 8

    # Test continuing scraping (poor results, no driver)
    df2 = spider.scrape(10).get()
    assert len(df2) >= len(df) + 10

    # Save and load spider
    jobdir = spider.save()
    spider = ISArticle.load(jobdir)

    df3 = spider.scrape(10).get()
    assert len(df3) >= len(df2) + 10
