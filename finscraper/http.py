"""Module for custom Scrapy HTTP components."""


from scrapy import Request


class SeleniumCallbackRequest(Request):
    """Process request with given callback using Selenium.

    Args:
        selenium_callback (func or None): Function that will be called with the
            chrome webdriver. The function should take in parameters 
            (request, spider, driver) and return request, response or None.
            If None, driver will be used for fetching the page, and return is
            response. Defaults to None.
    """

    def __init__(self, *args, selenium_callback=None, **kwargs):
        #if not callable(selenium_callback):
        #    raise ValueError('`callback` must be a function!')
        meta = kwargs.pop('meta', {})
        if 'selenium_callback' not in meta:
            meta['selenium_callback'] = selenium_callback
        new_kwargs = dict(**kwargs, meta=meta)
        super(SeleniumCallbackRequest, self).__init__(*args, **new_kwargs)
