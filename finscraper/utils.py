"""Module for utility functions and classes."""


import io
import logging
import pickle
import re

# Monkey patch, see https://github.com/pypa/pipenv/issues/2609
import webdriver_manager.utils
def console(text, bold=False):
    pass
webdriver_manager.utils.console = console

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from tqdm.auto import tqdm


class TqdmLogger(io.StringIO):
    """File-like object that redirects buffer to stdout."""
    def __init__(self, logger):
        self.logger = logger
        self.buf = ''

    def write(self, buf):
        self.buf = buf

    def flush(self):
        if self.buf.strip() != '':
            self.logger.log(logging.DEBUG, self.buf)


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
            except:
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
                    pass
                except:
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
        except:
            self.handleError(record)


def get_chromedriver(options=None):
    if not options:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    return driver


def strip_join(text_list, join_with=' '):
    joined_text = join_with.join(text.strip() for text in text_list
                                 if text is not None)
    return joined_text


def strip_elements(text_list):
    return [text.strip() for text in text_list if text is not None]


def drop_empty_elements(text_list):
    return [text for text in text_list
            if text.strip() != '' and text is not None]

def safe_cast_int(text):
    try:
        return int(text)
    except:
        return None
