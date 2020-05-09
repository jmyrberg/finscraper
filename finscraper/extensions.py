"""Module for Scrapy extensions."""


import logging

from collections import defaultdict

from scrapy import signals
from scrapy.exceptions import NotConfigured, CloseSpider

from tqdm.auto import tqdm

from finscraper.utils import TqdmLogger


class ProgressBar:
    """Scrapy extension thay displays progress bar.
    
    Enabled via ``PROGRESS_BAR_ENABLED`` Scrapy setting.
    """
    def __init__(self, crawler):
        self.progress_bar_enabled = (
            crawler.settings.get('PROGRESS_BAR_ENABLED', False))
        self.closespider_itemcount = (
            crawler.settings.get('CLOSESPIDER_ITEMCOUNT', None))
        self.counter = defaultdict(int)

        if not self.progress_bar_enabled:
            raise NotConfigured

        crawler.signals.connect(self.on_response,
                                signal=signals.response_received)
        crawler.signals.connect(self.on_item_scraped,
                                signal=signals.item_scraped)
        crawler.signals.connect(self.on_error, signal=signals.spider_error)

        logger = logging.getLogger()
        self.progress_bar = tqdm(desc='Progress', unit=' items',
                                 total=self.closespider_itemcount,
                                 file=TqdmLogger(logger))
        self.itemcount = 0
        self.pagecount = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def on_error(self, failure, response, spider):
        self.counter['errorcount'] += 1
        self.progress_bar.set_postfix({
            'pages': self.counter['pagecount'],
            'errors': self.counter['errorcount']
        })

    def on_response(self, response, request, spider):
        self.counter['pagecount'] += 1
        self.progress_bar.set_postfix({
            'pages': self.counter['pagecount'],
            'errors': self.counter['errorcount']
        })

    def on_item_scraped(self, item, spider):
        self.counter['itemcount'] += 1
        self.progress_bar.update()
