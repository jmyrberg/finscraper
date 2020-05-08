"""Module for testing spiders."""


import json
import logging
import tempfile

from pathlib import Path

from finscraper.spiders import ISArticle, ILArticle


# TODO: Implement utility test function that performs common Spider checks


def test_ISArticle_with_category():
    # Test scraping, no chromedriver
    spider = ISArticle('ulkomaat').scrape(20)
    df = spider.get()
    assert len(df) >= 20
    assert len(df.columns) == 8

    # Test scraping with chromedriver
    spider = ISArticle('ulkomaat', allow_chromedriver=True).scrape(20)
    df = spider.get()
    assert len(df) >= 20
    assert len(df.columns) == 8

    # Test continuing scraping
    df2 = spider.scrape(10).get()
    assert len(df2) >= len(df) + 10

    # Save and load spider
    jobdir = spider.save()
    spider = ISArticle.load(jobdir)

    df3 = spider.scrape(10).get()
    assert len(df3) >= len(df2) + 10


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


def test_ILArticle_with_category():
    # Test scraping
    spider = ILArticle('ulkomaat').scrape(5)
    df = spider.get()
    assert len(df) >= 5
    assert len(df.columns) == 8

    # Test continuing scraping
    df2 = spider.scrape(10).get()
    assert len(df2) >= len(df) + 10

    # Save and load spider
    jobdir = spider.save()
    spider = ILArticle.load(jobdir)

    df3 = spider.scrape(10).get()
    assert len(df3) >= len(df2) + 10


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


def test_spider_logging():
    # Yes attribute "None", no settings
    spider = ISArticle(log_level=None)
    spider.scrape(1)

    # Yes attribute, no settings
    spider = ISArticle(log_level='info')
    spider.scrape(1)
    assert True

    # No attribute, yes settings
    spider = ISArticle(log_level=None)
    spider.scrape(1, settings={'LOG_LEVEL': logging.DEBUG})
    assert True

    spider = ISArticle(log_level='info')
    spider.scrape(1, settings={'LOG_ENABLED': False})
    assert True

    # Attribute set
    try:
        spider.log_level = 'test'
    except ValueError:
        assert True
    except:
        assert False
    spider.log_level = 'info'
    assert spider.log_level == logging.INFO

    # TODO: Test the output


def test_spider_progress_bar():
    # Progress bas true by default
    spider = ILArticle()
    spider.scrape(1)
    assert spider.progress_bar == True
    assert len(spider.get()) > 0

    # Progress bar disabled, when log level given
    spider = ILArticle(log_level='info')
    spider.scrape(1)
    assert spider.progress_bar == False
    assert len(spider.get()) > 0

    # TODO: Test the output
