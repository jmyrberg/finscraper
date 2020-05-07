"""Module for Scrapy extension."""


import logging

from collections import defaultdict

from scrapy import signals
from scrapy.exceptions import NotConfigured, CloseSpider

from tqdm.auto import tqdm

from finscraper.utils import TqdmLogger


class ProgressBar:

    def __init__(self, crawler):
        self.progress_bar = crawler.settings.get('PROGRESS_BAR_ENABLED', False)
        self.counter = defaultdict(int)

        if not self.progress_bar:
            raise NotConfigured

        crawler.signals.connect(self.on_response,
                                signal=signals.response_received)
        crawler.signals.connect(self.on_item_scraped,
                                signal=signals.item_scraped)
        crawler.signals.connect(self.on_error, signal=signals.spider_error)

        logger = logging.getLogger()
        self.pbar = tqdm(desc='Progress', unit=' items',
                         file=TqdmLogger(logger))
        self.itemcount = 0
        self.pagecount = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def on_error(self, failure, response, spider):
        self.counter['errorcount'] += 1
        self.pbar.set_postfix({
            'pages': self.counter['pagecount'],
            'errors': self.counter['errorcount']
        })

    def on_response(self, response, request, spider):
        self.counter['pagecount'] += 1
        self.pbar.set_postfix({
            'pages': self.counter['pagecount'],
            'errors': self.counter['errorcount']
        })

    def on_item_scraped(self, item, spider):
        self.counter['itemcount'] += 1
        self.pbar.update()
