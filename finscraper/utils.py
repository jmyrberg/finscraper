"""Module for utility functions and classes."""


import io
import logging
import pickle

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class TqdmLogger(io.StringIO):
    """File-like object that redirects buffer to stdout."""

    def __init__(self, logger):
        self.logger = logger
        self.buf = ''

    def write(self, buf):
        self.buf = buf

    def flush(self):
        if self.buf.strip() != '':
            self.logger.log(logging.WARNING, self.buf)


class QueueHandler(logging.Handler):
    """Sends events to a queue, allowing multiprocessing.

    This handler checks for picklability before saving items into queue.
    Modified from: https://gist.github.com/vsajip/591589
    """

    def __init__(self, queue):
        logging.Handler.__init__(self)
        self.queue = queue

    def _get_picklable_attrs(self, record):
        # TODO: More performant way to do the same
        attrdict = {}
        for attr in vars(record):
            value = getattr(record, attr)
            try:
                pickle.dumps(value)
                attrdict[attr] = value
            except AttributeError:
                pass
            except Exception:
                pass

        if type(record.args) == tuple:
            attrdict['args'] = record.args
        else:
            args = {}
            for attr, value in record.args.items():
                try:
                    pickle.dumps(value)
                    args[attr] = value
                except AttributeError:
                    args[attr] = str(value)
                except Exception:
                    pass
            attrdict['args'] = args
        new_record = logging.makeLogRecord(attrdict)
        return new_record

    def enqueue(self, record):
        self.queue.put_nowait(record)

    def prepare(self, record):
        record = self._get_picklable_attrs(record)
        self.format(record)
        record.msg = record.message
        record.args = None
        record.exc_info = None
        return record

    def emit(self, record):
        try:
            self.enqueue(self.prepare(record))
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def get_chromedriver(options=None, settings=None):
    """Get chromedriver automatically.

    Args:
        options (selenium.webdriver.chrome.options.Options, optional):
            Options to start chromedriver with. If None, will use default
            settings. Defaults to None.
        settings (scrapy.settings.Settings, optional): Scrapy settings to
            take into consideration when starting chromedriver. If None,
            will not be taken into consideration. Defaults to None.

    Returns:
        Selenium webdriver for Chrome (selenium.webdriver.Chrome).
    """
    settings = settings or {}
    if options is None:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option(
            'prefs', {'intl.accept_languages': 'fi,fi_FI'})
        if not settings.get('DISABLE_HEADLESS', False):
            options.add_argument("--headless")
        if settings.get('PROGRESS_BAR_ENABLED', True):
            options.add_argument('--disable-logging')

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    if settings.get('MINIMIZE_WINDOW', False):
        try:
            driver.minimize_window()
        except WebDriverException:
            pass

    return driver
