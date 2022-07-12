"""Module for Scrapy extensions."""


import logging

from collections import defaultdict

from scrapy import signals
from scrapy.exceptions import NotConfigured

from tqdm.auto import tqdm

from finscraper.utils import TqdmLogger


class ProgressBar:
    """Scrapy extension that displays progress bar.

    Enabled via ``PROGRESS_BAR_ENABLED`` Scrapy setting.
    """
    def __init__(self, crawler):
        self.progress_bar_enabled = (
            crawler.settings.get('PROGRESS_BAR_ENABLED', False))
        self.closespider_itemcount = (
            crawler.settings.get('CLOSESPIDER_ITEMCOUNT', None))
        self.counter = defaultdict(int)

        self._disabled_loggers = []

        if not self.progress_bar_enabled:
            raise NotConfigured

        logger = logging.getLogger()
        self.progress_bar = tqdm(desc='Progress', unit=' items',
                                 total=self.closespider_itemcount,
                                 file=TqdmLogger(logger))
        self.itemcount = 0
        self.pagecount = 0

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_opened, signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signals.spider_closed)
        crawler.signals.connect(ext.on_response,
                                signal=signals.response_received)
        crawler.signals.connect(ext.on_item_scraped,
                                signal=signals.item_scraped)
        crawler.signals.connect(ext.on_error, signal=signals.spider_error)
        return ext

    def spider_opened(self, spider):
        # Disable logging if progress bar is enabled
        if self.progress_bar_enabled:
            for existing_logger in logging.Logger.manager.loggerDict.values():
                if not isinstance(existing_logger, logging.PlaceHolder):
                    if existing_logger.propagate:
                        print(existing_logger.name, 'disabled')
                        existing_logger.propagate = False
                        self._disabled_loggers.append(existing_logger)

    def spider_closed(self, spider):
        if len(self._disabled_loggers) > 0:
            for disabled_logger in self._disabled_loggers:
                disabled_logger.propagate = True

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
