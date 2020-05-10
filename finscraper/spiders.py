"""Module for Spider API - the main interface of finscraper."""


from textwrap import indent

from finscraper.wrappers import _SpiderWrapper
from finscraper.scrapy_spiders.ilarticle import _ILArticleSpider, \
    _ILArticleItem
from finscraper.scrapy_spiders.isarticle import _ISArticleSpider, \
    _ISArticleItem
from finscraper.scrapy_spiders.ylearticle import _YLEArticleSpider, \
    _YLEArticleItem


__wrapper_doc__ = '''
jobdir (str or None, optional): Working directory of the spider.
    Defaults to None, which creates a temp directory to be used.
    Note that this directory will only be deleted through the ``clear`` method!
progress_bar (bool, optional): Whether to enable progress bar or not. This
    parameter is ignored if ``log_level`` is not None. Defaults to True.
log_level (str or None, optional): Logging level to display. Should be in
    ['debug', 'info', 'warn', 'error', 'critical'] or None (disabled).
    Defaults to None.
    
    .. note::
        This parameter can be overridden through Scrapy ``settings``
        (LOG_LEVEL, LOG_ENABLED) within the ``scrape`` -method.
'''


def _get_docstring(spider_cls, item_cls):
    return (spider_cls.__init__.__doc__.strip()
            + indent(__wrapper_doc__, ' ' * 12)
            + indent(item_cls.__doc__, ' ' * 4))


class ISArticle(_SpiderWrapper):
    __doc__ = _get_docstring(_ISArticleSpider, _ISArticleItem)
    def __init__(self, category=None, follow_link_extractor=None,
                 item_link_extractor=None, allow_chromedriver=False,
                 jobdir=None, progress_bar=True, log_level=None):
        super(ISArticle, self).__init__(
            spider_cls=_ISArticleSpider,
            spider_params=dict(
                category=category,
                follow_link_extractor=follow_link_extractor,
                item_link_extractor=item_link_extractor,
                allow_chromedriver=allow_chromedriver
            ),
            jobdir=jobdir,
            progress_bar=progress_bar,
            log_level=log_level)


class ILArticle(_SpiderWrapper):
    __doc__ = _get_docstring(_ILArticleSpider, _ILArticleItem)
    def __init__(self, category=None, follow_link_extractor=None,
                 item_link_extractor=None, jobdir=None, progress_bar=True,
                 log_level=None):
        super(ILArticle, self).__init__(
            spider_cls=_ILArticleSpider,
            spider_params=dict(
                category=category,
                follow_link_extractor=follow_link_extractor,
                item_link_extractor=item_link_extractor
            ),
            jobdir=jobdir,
            progress_bar=progress_bar,
            log_level=log_level)


class YLEArticle(_SpiderWrapper):
    __doc__ = _get_docstring(_YLEArticleSpider, _YLEArticleItem)
    def __init__(self, follow_link_extractor=None, item_link_extractor=None,
                 jobdir=None, progress_bar=True, log_level=None):
        super(YLEArticle, self).__init__(
            spider_cls=_YLEArticleSpider,
            spider_params=dict(
                follow_link_extractor=follow_link_extractor,
                item_link_extractor=item_link_extractor
            ),
            jobdir=jobdir,
            progress_bar=progress_bar,
            log_level=log_level)
