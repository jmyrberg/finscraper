"""Module for testing spider wrapper functionalities."""


import logging

from pathlib import Path

from finscraper.spiders import ISArticle, ILArticle


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
    # Progress bar true by default
    spider = ILArticle()
    spider.scrape(1)
    assert spider.progress_bar == True
    assert len(spider.get()) > 0

    # Progress bar disabled, when log level given
    spider = ILArticle(log_level='info')
    spider.scrape(1)
    assert spider.progress_bar == False
    assert len(spider.get()) > 0

    # Progress bar enabled, chromedriver used
    spider = ISArticle(allow_chromedriver=True)
    spider.scrape(1)
    assert spider.progress_bar == True
    assert len(spider.get()) > 0

    # TODO: Test the output
