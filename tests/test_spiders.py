"""Module for testing spiders."""


import json
import tempfile

from pathlib import Path

from finscraper.spiders.isarticle import ISArticleSpider


def test_ISArticle():
    # Test scraping
    spider = ISArticleSpider().scrape(10)
    df = spider.get()
    assert len(df) >= 10
    assert len(df.columns) == 8

    # Test continuing scraping
    df2 = spider.scrape(10).get()
    assert len(df2) > len(df)

    # Save and load spider
    jobdir = spider.save()
    spider = ISArticleSpider.load(jobdir)

    df3 = spider.scrape(10).get()
    assert len(df3) > len(df2)


def test_spider_save_load_with_jobdir():
    jobdir = '../jobdir'
    category = 'jaakiekko'

    spider = ISArticleSpider(category=category, jobdir=jobdir)
    
    save_jobdir = spider.save()
    loaded_spider = ISArticleSpider.load(save_jobdir)

    assert (jobdir == str(spider.jobdir)
            == save_jobdir == str(loaded_spider.jobdir))
    assert category == spider.category == loaded_spider.category


def test_spider_save_load_without_jobdir():
    category = 'jaakiekko'

    spider = ISArticleSpider(category=category)
    
    save_jobdir = spider.save()
    loaded_spider = ISArticleSpider.load(save_jobdir)

    assert spider.jobdir is not None
    assert (str(spider.jobdir) == save_jobdir == str(loaded_spider.jobdir))
    assert category == spider.category == loaded_spider.category
