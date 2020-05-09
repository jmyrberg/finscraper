"""Module for Scrapy middlewares."""


import logging

import time

from scrapy import signals
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Monkey patch, see https://github.com/pypa/pipenv/issues/2609
import webdriver_manager.utils
def console(text, bold=False):
    pass
webdriver_manager.utils.console = console

from webdriver_manager.chrome import ChromeDriverManager


class DownloaderMiddlewareWithJs:
    """Middleware that runs JavaScript.
        
    Usage via ``scrapy.Request.meta``:
        * run_js (bool): Whether to run JavaScript or not.
        * run_js_wait_sec (int): How many seconds to wait when rendering the \
        page.
        * scroll_to_bottom (bool): Whether to scroll page to bottom or not.
        * scroll_to_bottom_wait_sec (int): How many seconds to wait after \
        scrolling to bottom.

    If meta is not used, the request is just passed through.
    """
    def __init__(self, settings):
        self.log_enabled = settings.get('LOG_ENABLED', False)
        self.log_level = settings.get('LOG_LEVEL', logging.NOTSET)
        self.progress_bar_enabled = settings.get('PROGRESS_BAR_ENABLED', False)

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        crawler.signals.connect(middleware.spider_opened,
                                signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed,
                                signals.spider_closed)
        
        return middleware

    def spider_opened(self, spider):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        #options.add_argument("--no-sandbox") # linux only
        if self.progress_bar_enabled:
            options.add_argument('--disable-logging')
            for name in ['selenium.webdriver.remote.remote_connection',
                         'requests', 'urllib3']:
                logging.getLogger(name).propagate = False

        self.driver = webdriver.Chrome(ChromeDriverManager().install(),
                                       options=options)

    def spider_closed(self, spider):
        self.driver.close()

    def process_request(self, request, spider):
        run_js = request.meta.get('run_js')
        run_js_wait_sec = request.meta.get('run_js_wait_sec', 0)
        scroll_to_bottom = request.meta.get('scroll_to_bottom')
        scroll_to_bottom_wait_sec = request.meta.get(
            'scroll_to_bottom_wait_sec', 0)
        
        request.meta['driver'] = self.driver
        if run_js or scroll_to_bottom:
            self.driver.get(request.url)  # TODO: Implement conditional wait
            time.sleep(run_js_wait_sec)
            if scroll_to_bottom:
                self.driver.execute_script(
                    'window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(scroll_to_bottom_wait_sec)
            return HtmlResponse(request.url, encoding='utf-8', request=request,
                                body=self.driver.page_source.encode('utf-8'))
        else:
            return None
