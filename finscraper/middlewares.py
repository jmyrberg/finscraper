"""Module for Scrapy middleware."""

import logging
logger = logging.getLogger(__name__)

import time

from scrapy import signals
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager


class DownloaderMiddlewareWithJs(object):
    # https://stackoverflow.com/questions/31174330/passing-selenium-response-url-to-scrapy 

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
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
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=options)

    def spider_closed(self, spider):
        self.driver.close()

    def process_request(self, request, spider):
        return_response = False
        run_js = request.meta.get('run_js')
        run_js_wait_sec = request.meta.get('run_js_wait_sec', 0)
        scroll_to_bottom = request.meta.get('scroll_to_bottom')
        scroll_to_bottom_wait_sec = request.meta.get(
            'scroll_to_bottom_wait_sec', 0)
        
        request.meta['driver'] = self.driver
        if run_js or scroll_to_bottom:
            logger.debug('Loading site with javascript')
            self.driver.get(request.url)  # TODO: Implement conditional wait
            time.sleep(run_js_wait_sec)
            if scroll_to_bottom:
                logger.debug('Scrolling to bottom')
                self.driver.execute_script(
                    'window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(scroll_to_bottom_wait_sec)
            return HtmlResponse(request.url, encoding='utf-8', request=request,
                                body=self.driver.page_source.encode('utf-8'))
        else:
            return None
