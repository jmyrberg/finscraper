"""Module for wrapping Scrapy spiders."""


import json
import logging
import multiprocessing as mp
import pickle
import platform
import shutil
import sys
import tempfile
import uuid
import weakref

from logging.handlers import QueueListener
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


# https://turtlemonvh.github.io/python-multiprocessing-and-corefoundation-libraries.html
if platform.system() == 'Darwin':
    mp = mp.get_context('spawn')


def _run_as_process(func, spider_cls, spider_params, settings):
    # Setup logging / progress bar
    # (queuehandler --> listener --> root logger --> streamhandler)
    progress_bar_enabled = settings['PROGRESS_BAR_ENABLED']
    log_enabled = settings['LOG_ENABLED']
    log_stdout = settings['LOG_STDOUT']
    q_log = None
    ql = None
    if log_enabled or progress_bar_enabled:
        handler = logging.StreamHandler()
        if progress_bar_enabled:
            handler.terminator = ''
            handler.setFormatter(logging.Formatter('%(message)s'))
        else:
            handler.setFormatter(logging.Formatter(settings.get('LOG_FORMAT')))

        q_log = mp.Queue(-1)
        ql = QueueListener(q_log, handler)
        ql.start()

        logger = logging.getLogger()
        logger.setLevel(settings.get('LOG_LEVEL'))
        logger.addHandler(handler)
    
    # Start function as a separate process
    q = mp.Queue()
    p = mp.Process(target=func,
                   args=(q, q_log, spider_cls, spider_params, settings))
    p.start()
    result = q.get()
    p.join()

    if ql:
        ql.stop()

    if isinstance(result, BaseException):
        raise result


def _run_spider_func(q, q_log, spider_cls, spider_params, settings):
    try:
        configure_logging(settings, install_root_handler=False)
        if q_log is not None:
            # Setup logging (worker --> queuehandler --> root logger)
            if not settings['LOG_ENABLED']:  # Disables STDOUT :o
                logging.getLogger('scrapy').propagate = False
            qh = QueueHandler(q_log)
            logger = logging.getLogger()
            logger.setLevel(settings.get('LOG_LEVEL'))
            qh.setLevel(settings.get('LOG_LEVEL'))
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
    """Provide common methods and attributes for all spiders."""
    _log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARN,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    def __init__(self, spider_cls, spider_params, jobdir=None,
                 progress_bar=True, log_level=None):
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
        self.progress_bar = progress_bar and self.log_level is None
        
        self._items_save_path = self._jobdir / 'items.jl'
        self._spider_save_path = self._jobdir / 'spider.pkl'

        self._finalizer = weakref.finalize(
            self, shutil.rmtree, self._jobdir, ignore_errors=True)
        
        # Note: Parameters cannot be changed outside by setting them
        for param in self.spider_params:
            setattr(self, param, self.spider_params[param])

    @property
    def jobdir(self):
        """Working directory of the spider.
        
        Can be changed after initialization of a spider.
        """
        return str(self._jobdir)

    @property
    def log_level(self):
        """Logging level of the spider.
        
        This attribute can be changed after initialization of a spider.
        """
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
    def progress_bar(self):
        """Whether progress bar is enabled or not.
        
        Can be changed after initialization of a spider.
        """
        return self._progress_bar

    @progress_bar.setter
    def progress_bar(self, progress_bar):
        if type(progress_bar) == bool:
            self._progress_bar = progress_bar
        else:
            raise ValueError(f'Progress bar "{progress_bar}" not boolean')

    @property
    def items_save_path(self):
        """Save of path of the scraped items.
        
        Cannot be changed after initialization of a spider.
        """
        return str(self._items_save_path)

    @property
    def spider_save_path(self):
        """Save path of the spider.
        
        Cannot be changed after initialization of a spider.
        """
        return str(self._spider_save_path)

    def _run_spider(self, itemcount=10, timeout=60, pagecount=0, errorcount=0,
                    settings=None):
        _settings = Settings()
        _settings.setmodule('finscraper.settings', priority='project')
        
        _settings['JOBDIR'] = self.jobdir
        _settings['FEEDS'] = {self.items_save_path: {'format': 'jsonlines'}}
        
        _settings['CLOSESPIDER_ITEMCOUNT'] = itemcount
        _settings['CLOSESPIDER_TIMEOUT'] = timeout
        _settings['CLOSESPIDER_PAGECOUNT'] = pagecount
        _settings['CLOSESPIDER_ERRORCOUNT'] = errorcount
        
        _settings['LOG_STDOUT'] = True
        _settings['LOG_LEVEL'] = self.log_level or logging.NOTSET
        _settings['LOG_ENABLED'] = self.log_level is not None
        # Logging dominates progress bar
        _settings['PROGRESS_BAR_ENABLED'] = self.progress_bar
        
        # Will always be prioritized --> conflicts are possible
        if settings is not None:
            _settings.update(settings)
        
        try:
            _run_as_process(
                func=_run_spider_func,
                spider_cls=self.spider_cls,
                spider_params=self.spider_params,
                settings=_settings
            )
        except KeyboardInterrupt:
            pass
    
    def scrape(self, n=10, timeout=60, settings=None):
        """Scrape given number of items.
        
        Args:
            n (int, optional): Number of items to attempt to scrape. Zero
                corresponds to no limit. Defaults to 10.
            timeout (int, optional): Timeout in seconds to wait before stopping
                the spider. Zero corresponds to no limit. Defaults to 60.
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
            If ``fmt = 'df'``, DataFrame of scraped items.
            If ``fmt = 'list'``, list of dict of scraped items.

        Raises:
            ValueError: If ``fmt`` not in allowed values.
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
        """Save spider in ``jobdir`` for later use.
        
        Returns:
            str: Path to job directory.
        """
        save_tuple = (self.spider_cls, self.spider_params, self.jobdir)
        with open(self.spider_save_path, 'wb') as f:
            pickle.dump(save_tuple, f)
        self._finalizer.detach()
        return self.jobdir

    @classmethod
    def load(cls, jobdir):
        """Load existing spider from ``jobdir``.
        
        Args:
            jobdir (str): Path to job directory.
        
        Returns:
            Spider loaded from job directory.
        """
        expected_path = Path(jobdir) / 'spider.pkl'
        with open(expected_path, 'rb') as f:
            (spider_cls, spider_params, jobdir) = pickle.load(f)
        return cls(jobdir=jobdir, **spider_params)

    def clear(self):
        """Clear contents of ``jobdir``."""
        if self._jobdir.exists():
            shutil.rmtree(self._jobdir)
        self._jobdir.mkdir(parents=True, exist_ok=True)
