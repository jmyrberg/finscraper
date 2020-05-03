"""Module for wrapping Scrapy spiders."""


import json
import pickle
import shutil
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


def _run_func_as_process(func, *args, **kwargs):
    q = Queue()
    p = Process(target=func, args=(q, *args),
                kwargs=kwargs)
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result


def _run_spider_func(q, spider_cls, spider_params, settings):
    try:
        configure_logging()
        runner = CrawlerRunner(settings)
        deferred = runner.crawl(spider_cls, **spider_params)
        deferred.addBoth(lambda _: reactor.stop())
        reactor.run()
        q.put(None)
    except Exception as e:
        Queue.put(e)


class SpiderWrapper:

    def __init__(self, spider_cls, spider_params, jobdir=None):
        self.spider_cls = spider_cls
        self.spider_params = spider_params

        if jobdir is None:
            self._jobdir = Path(tempfile.gettempdir()) / str(uuid.uuid4())
        else:
            self._jobdir = Path(jobdir)
        self._jobdir.mkdir(parents=True, exist_ok=True)
        
        self._items_save_path = self._jobdir / 'items.jl'
        self._spider_save_path = self._jobdir / 'spider.pkl'
        
        # Note: Parameters cannot be changed outside by setting them
        for param in self.spider_params:
            setattr(self, param, self.spider_params[param])

    @property
    def jobdir(self):
        return str(self._jobdir)

    @property
    def items_save_path(self):
        return str(self._items_save_path)

    @property
    def spider_save_path(self):
        return str(self._spider_save_path)

    def _run_spider(self, itemcount=10, timeout=0, pagecount=0, errorcount=0,
                    settings=None):
        settings_ = Settings()
        settings_.setmodule('finscraper.settings', priority='project')
        settings_['JOBDIR'] = self.jobdir
        settings_['FEEDS'] = {self.items_save_path: {'format': 'jsonlines'}}
        settings_['CLOSESPIDER_ITEMCOUNT'] = itemcount
        settings_['CLOSESPIDER_TIMEOUT'] = timeout
        settings_['CLOSESPIDER_PAGECOUNT'] = pagecount
        settings_['CLOSESPIDER_ERRORCOUNT'] = errorcount
        if settings is not None:
            settings_.update(settings)
        try:
            _run_func_as_process(
                func=_run_spider_func,
                spider_cls=self.spider_cls,
                spider_params=self.spider_params,
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
        self._run_spider(itemcount=n, settings=settings)
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
        if self._items_save_path.exists():
            with open(self.items_save_path, 'r') as f:
                for line in f:
                    jsonlines.append(json.loads(line))
        if fmt == 'list':
            return jsonlines
        elif fmt == 'df':
            return pd.DataFrame(jsonlines)
    
    def save(self):
        """Save spider in `jobdir` for later use.
        
        Returns:
            Path to job directory as a string.
        """
        save_tuple = (self.spider_cls, self.spider_params, self.jobdir)
        with open(self.spider_save_path, 'wb') as f:
            pickle.dump(save_tuple, f)
        return self.jobdir

    @classmethod
    def load(cls, jobdir):
        """Load spider from `jobdir`."""
        expected_path = Path(jobdir) / 'spider.pkl'
        with open(expected_path, 'rb') as f:
            (spider_cls, spider_params, jobdir) = pickle.load(f)
        return cls(jobdir=jobdir, **spider_params)

    def clear(self):
        """Clear contents of `jobdir`."""
        if self._jobdir.exists():
            shutil.rmtree(self._jobdir)
        self._jobdir.mkdir(parents=True, exist_ok=True)
