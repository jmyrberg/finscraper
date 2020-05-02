"""Module for main Spider API."""


import os

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from finscraper.scrapy_spiders.isarticle import ISArticleSpider


class _SpiderMixin:

    def __init__(self, spider, spider_kwargs, process_kwargs):
        self.spider = spider
        self.spider_kwargs = spider_kwargs
        self.process_kwargs = process_kwargs

    def run(self):
        """Run spider."""
        settings = Settings()
        settings.setmodule('finscraper.settings', priority='project')
        settings.update(self.process_kwargs)
        process = CrawlerProcess(settings=settings)
        process.crawl(self.spider, **self.spider_kwargs)
        process.start()


class ISArticle(_SpiderMixin):

    def __init__(self, category=None, **process_kwargs):
        """Fetch IltaSanomat articles.
        
        Args:
            category (str, list or None): Category to fetch articles from,    
                meaning pages under 'is.fi/<category>/'. Defaults to None,
                which fetches articles everywhere.
            process_kwargs (dict or None): Spider settings to use, for example
                for setting `JOBDIR` or `FEEDS` parameters at instance level.
                These include all settings available at:
                https://docs.scrapy.org/en/latest/topics/settings.html.
        """
        super(ISArticle, self).__init__(
            spider=ISArticleSpider,
            spider_kwargs=dict(
                category=category
            ),
            process_kwargs=process_kwargs
        )
