"""Module for Scrapy middlewares."""


from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse

from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from finscraper.request import SeleniumCallbackRequest
from finscraper.utils import get_chromedriver


class SeleniumCallbackMiddleware:
    """Middleware that processes request with given callback.

    Headless mode can be disabled via ``DISABLE_HEADLESS`` Scrapy setting.
    In non-headless mode, window can be minimized via ``MINIMIZE_WINDOW``
    Scrapy setting.
    """

    def __init__(self, settings):
        self.settings = settings

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
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option(
            'prefs', {'intl.accept_languages': 'fi,fi_FI'})
        if not self.settings.get('DISABLE_HEADLESS', False):
            options.add_argument("--headless")
        if self.settings.get('PROGRESS_BAR_ENABLED', True):
            options.add_argument('--disable-logging')
        try:
            self.driver = get_chromedriver(options)
            if self.settings.get('MINIMIZE_WINDOW', False):
                try:
                    self.driver.minimize_window()
                except WebDriverException:
                    pass
        except Exception:
            raise NotConfigured('Could not get chromedriver')

    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.close()

    def process_request(self, request, spider):
        if not isinstance(request, SeleniumCallbackRequest):
            return None

        selenium_callback = request.meta.get('selenium_callback')
        if selenium_callback is None:
            self.driver.get(request.url)
            return HtmlResponse(
                self.driver.current_url,
                body=self.driver.page_source.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
        else:
            return selenium_callback(request, spider, self.driver)
