"""Module for testing spiders."""


import json
import tempfile

from pathlib import Path

from finscraper.spiders import ISArticle


def test_ISArticle():
    # Test scraping
    spider = ISArticle().scrape(10)
    df = spider.get()
    assert len(df) >= 10
    assert len(df.columns) == 8

    # Test continuing scraping
    df2 = spider.scrape(10).get()
    assert len(df2) > len(df)

    # Save and load spider
    jobdir = spider.save()
    spider = ISArticle.load(jobdir)

    df3 = spider.scrape(10).get()
    assert len(df3) > len(df2)


def test_spider_save_load_with_jobdir():
    jobdir = '../jobdir'
    category = 'jaakiekko'

    spider = ISArticle(category=category, jobdir=jobdir)
    
    save_jobdir = spider.save()
    loaded_spider = ISArticle.load(save_jobdir)

    assert (jobdir == str(spider.jobdir)
            == save_jobdir == str(loaded_spider.jobdir))
    assert category == spider.category == loaded_spider.category


def test_spider_save_load_without_jobdir():
    category = 'jaakiekko'

    spider = ISArticle(category=category)
    
    save_jobdir = spider.save()
    loaded_spider = ISArticle.load(save_jobdir)

    assert spider.jobdir is not None
    assert (str(spider.jobdir) == save_jobdir == str(loaded_spider.jobdir))
    assert category == spider.category == loaded_spider.category


def test_spider_clear():
    # Directory not removed when deleted
    spider = ISArticle()
    jobdir = spider.jobdir
    del spider
    assert Path(jobdir).exists()

    # Directory contents removed when cleared
    spider = ISArticle().scrape(1)
    jobdir = spider.save()
    spider_save_path = spider.spider_save_path
    items_save_path = spider.items_save_path
    assert Path(spider_save_path).exists()
    assert Path(items_save_path).exists()
    spider.clear()
    assert not Path(spider_save_path).exists()
    assert not Path(items_save_path).exists()


def test_docstring():
    spider = ISArticle()
    doc = help(spider)
    