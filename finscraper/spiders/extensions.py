"""Module for scrapy extensions."""


import json
import pickle
import tempfile
import uuid

from multiprocessing import Process, Queue
from pathlib import Path

import pandas as pd

from twisted.internet import reactor

from scrapy import Request
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.exceptions import CloseSpider
from scrapy.settings import Settings
from scrapy.spiders import Spider
from scrapy.utils.log import configure_logging


def _run_process(func, *args, **kwargs):
    q = Queue()
    p = Process(target=func, args=(q, *args),
                kwargs=kwargs)
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result


def _run_spider(q, spider, spider_kwargs, settings):
    try:
        configure_logging()
        runner = CrawlerRunner(settings)
        deferred = runner.crawl(spider, **spider_kwargs)
        deferred.addBoth(lambda _: reactor.stop())
        reactor.run()
        q.put(None)
    except Exception as e:
        Queue.put(e)


class ExtendedSpider(Spider):

    def __init__(self, jobdir=None, *args, **kwargs):
        if jobdir is None:
            self.jobdir = Path(tempfile.gettempdir()) / str(uuid.uuid4())
        else:
            self.jobdir = Path(jobdir)
        self.jobdir.mkdir(parents=True, exist_ok=True)
        self.save_path = self.jobdir / 'items.jl'
        super(ExtendedSpider, self).__init__(*args, **kwargs)

    def _get_params(self):
        raise NotImplementedError('Function `_get_params` not implemented!')

    def _parse_item(self):
        raise NotImplementedError('Function `_parse_item` not implemented!')

    def parse(self, resp, to_parse=False):
        """Parse items and follow links based on defined link extractors."""
        if to_parse:
            yield self._parse_item(resp)

        # Parse items and further on extract links from those pages
        item_links = self.item_link_extractor.extract_links(resp)
        for link in item_links:
            yield Request(link.url, callback=self.parse,
                          cb_kwargs={'to_parse': True})

        # Extract all links from this page
        follow_links = self.follow_link_extractor.extract_links(resp)
        for link in follow_links:
            yield Request(link.url, callback=self.parse)

    def _run(self, itemcount=10, timeout=0, pagecount=0, errorcount=0,
             settings=None):
        """Run spider."""
        settings_ = Settings()
        settings_.setmodule('finscraper.settings', priority='project')
        settings_['JOBDIR'] = self.jobdir
        settings_['FEEDS'] = {self.save_path: {'format': 'jsonlines'}}
        settings_['CLOSESPIDER_ITEMCOUNT'] = itemcount
        settings_['CLOSESPIDER_TIMEOUT'] = timeout
        settings_['CLOSESPIDER_PAGECOUNT'] = pagecount
        settings_['CLOSESPIDER_ERRORCOUNT'] = errorcount
        if settings is not None:
            settings_.update(settings)
        spider_params = self._get_params()
        spider_params['jobdir'] = self.jobdir
        try:
            _run_process(
                func=_run_spider,
                spider=self.__class__,
                spider_kwargs=spider_params,
                settings=settings_
            )
        except KeyboardInterrupt:
            pass
    
    def scrape(self, n=10, settings=None):
        """Scrape given number of items.
        
        Args:
            n (int, optional): Number of items to scrape. Zero corresponds to
                no limit. Defaults to 10.
            settings (dict or None, optional): Scrapy spider settings to use.
                Defaults to None, which correspond to default settings.
                See list of available settings at:
                https://docs.scrapy.org/en/latest/topics/settings.html.
        
        Returns:
            self
        """
        self._run(itemcount=n)
        return self

    def get(self, fmt='df'):
        """Return scraped data as DataFrame or list.
        
        Args:
            fmt (str, optional): Format to return parsed items as. Should be
                in ['df', 'list']. Defaults to 'df'.

        Returns:
            DataFrame, when fmt = 'df'.
            List of scraped items, when fmt = 'list'.
        """
        if fmt not in ['df', 'list']:
            ValueError(f'Format {fmt} should be in ["df", "list"]')
        jsonlines = []
        if self.save_path.exists():
            with open(self.save_path, 'r') as f:
                for line in f:
                    jsonlines.append(json.loads(line))
        if fmt == 'list':
            return jsonlines
        elif fmt == 'df':
            return pd.DataFrame(jsonlines)
    
    def save(self):
        """Save spider in `jobdir` for later use."""
        spider_params = self._get_params()
        spider_class = self.__class__

        save_path = self.jobdir / 'spider.pkl'
        with open(save_path, 'wb') as f:
            pickle.dump((spider_class, spider_params), f)
        return str(self.jobdir)

    @staticmethod
    def load(jobdir):
        """Load spider from `jobdir`."""
        with open(Path(jobdir) / 'spider.pkl', 'rb') as f:
            spider_class, spider_params = pickle.load(f)
        spider_params['jobdir'] = Path(jobdir)
        return spider_class(**spider_params)

    def close(self):
        # TODO: Implement function that deletes the jobdir safely
        #       Maybe with __del__ as well...?
        #       + cleanup the previous implementation
