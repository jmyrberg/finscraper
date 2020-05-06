"""Module for wrapping Scrapy spiders."""


import json
import logging
import pickle
import shutil
import sys
import tempfile
import uuid

from logging.handlers import QueueListener
from multiprocessing import Process, Queue
from pathlib import Path

import pandas as pd

from scrapy import Request
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.exceptions import CloseSpider
from scrapy.settings import Settings
from scrapy.spiders import Spider
from scrapy.utils.log import configure_logging

from twisted.internet import reactor

from finscraper.utils import QueueHandler


def _run_func_as_process(func, *args, **kwargs):
    settings = kwargs['settings'] if 'settings' in kwargs else {}
    
    # Setup logging
    q_log = None
    ql = None
    if settings.get('LOG_ENABLED', False):
        # (queuehandler --> listener --> root logger --> streamhandler)
        handler = logging.StreamHandler()
        q_log = Queue(-1)
        ql = QueueListener(q_log, handler)
        ql.start()
        logger = logging.getLogger()
        logger.setLevel(settings.get('LOG_LEVEL', logging.INFO))
        handler.setFormatter(logging.Formatter(settings.get('LOG_FORMAT')))
        logger.addHandler(handler)
    
    q = Queue()
    p = Process(target=func, args=(q, q_log, *args), kwargs=kwargs)
    p.start()
    result = q.get()
    p.join()

    if ql:
        ql.stop()

    if isinstance(result, BaseException):
        raise result


def _run_spider_func(q, q_log, spider_cls, spider_params, settings):
    try:
        configure_logging(settings, install_root_handler=True)
        if q_log is not None:
            # Setup logging (worker --> queuehandler --> root logger)
            qh = QueueHandler(q_log)
            logger = logging.getLogger()
            logger.setLevel(settings.get('LOG_LEVEL', logging.INFO))
            qh.setLevel(settings.get('LOG_LEVEL', logging.INFO))
            qh.setFormatter(logging.Formatter(settings.get('LOG_FORMAT')))
            logger.addHandler(qh)

        # Start crawling
        runner = CrawlerRunner(settings)
        deferred = runner.crawl(spider_cls, **spider_params)
        deferred.addBoth(lambda _: reactor.stop())
        reactor.run()
        q.put(None)
    except Exception as e:
        q.put(e)


class _SpiderWrapper:
    _log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARN,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    def __init__(self, spider_cls, spider_params, jobdir=None,
                 log_level=None):
        self.spider_cls = spider_cls
        self.spider_params = spider_params

        if jobdir is None:
            self._jobdir = Path(tempfile.gettempdir()) / str(uuid.uuid4())
        elif type(jobdir) == str:
            self._jobdir = Path(jobdir)
        else:
            raise ValueError(f'Jobdir {jobdir} is not of type str or None')
        self._jobdir.mkdir(parents=True, exist_ok=True)

        self.log_level = log_level
        
        self._items_save_path = self._jobdir / 'items.jl'
        self._spider_save_path = self._jobdir / 'spider.pkl'
        
        # Note: Parameters cannot be changed outside by setting them
        for param in self.spider_params:
            setattr(self, param, self.spider_params[param])

    @property
    def jobdir(self):
        return str(self._jobdir)

    @property
    def log_level(self):
        return self._log_level

    @log_level.setter
    def log_level(self, log_level):
        if log_level is None:
            self._log_level = log_level
        elif (type(log_level) == str 
              and log_level.strip().lower() in self._log_levels):
            self._log_level = self._log_levels[log_level.strip().lower()]
        else:
            raise ValueError(
                    f'Log level should be in {self._log_levels.keys()}')

    @property
    def items_save_path(self):
        return str(self._items_save_path)

    @property
    def spider_save_path(self):
        return str(self._spider_save_path)

    def _run_spider(self, itemcount=10, timeout=120, pagecount=0, errorcount=0,
                    settings=None):
        _settings = Settings()
        _settings.setmodule('finscraper.settings', priority='project')
        _settings['JOBDIR'] = self.jobdir
        _settings['FEEDS'] = {self.items_save_path: {'format': 'jsonlines'}}
        _settings['CLOSESPIDER_ITEMCOUNT'] = itemcount
        _settings['CLOSESPIDER_TIMEOUT'] = timeout
        _settings['CLOSESPIDER_PAGECOUNT'] = pagecount
        _settings['CLOSESPIDER_ERRORCOUNT'] = errorcount
        if self.log_level is None:
            _settings['LOG_ENABLED'] = False
        else:
            _settings['LOG_LEVEL'] = self._log_level
            _settings['LOG_ENABLED'] = True
        if settings is not None:
            _settings.update(settings)
        try:
            _run_func_as_process(
                func=_run_spider_func,
                spider_cls=self.spider_cls,
                spider_params=self.spider_params,
                settings=_settings
            )
        except KeyboardInterrupt:
            pass
    
    def scrape(self, n=10, timeout=120, settings=None):
        """Scrape given number of items.
        
        Args:
            n (int, optional): Number of items to attempt to scrape. Zero
                corresponds to no limit. Defaults to 10.
            timeout (int, optional): Timeout in seconds to wait before stopping
                the spider. Zero corresponds to no limit. Defaults to 120.
            settings (dict or None, optional): Scrapy spider settings to use.
                Defaults to None, which correspond to default settings.
                See list of available settings at:
                https://docs.scrapy.org/en/latest/topics/settings.html.
        
        Returns:
            self
        """
        self._run_spider(itemcount=n, timeout=timeout, settings=settings)
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
