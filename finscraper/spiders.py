"""Module for spiders."""


from textwrap import indent

from finscraper.wrappers import _SpiderWrapper
from finscraper.scrapy_spiders.ilarticle import _ILArticleSpider, \
    _ILArticleItem
from finscraper.scrapy_spiders.isarticle import _ISArticleSpider, \
    _ISArticleItem


__jobdir_doc__ = '''
jobdir (None or str, optional): Working directory of the spider.
    Defaults to None, which creates a temp directory to be used.
    Note that this directory will only be deleted through the
    `clear` method!
'''


def _get_docstring(spider_cls, item_cls):
    return ( spider_cls.__init__.__doc__.strip()
            + indent(__jobdir_doc__, ' ' * 12)
            + indent(item_cls.__doc__, ' ' * 4))


class ISArticle(_SpiderWrapper):
    __doc__ = _get_docstring(_ISArticleSpider, _ISArticleItem)
    def __init__(self, category=None, follow_link_extractor=None,
                 item_link_extractor=None, allow_chromedriver=False,
                 jobdir=None):
        super(ISArticle, self).__init__(
            spider_cls=_ISArticleSpider,
            spider_params=dict(
                category=category,
                follow_link_extractor=follow_link_extractor,
                item_link_extractor=item_link_extractor,
                allow_chromedriver=allow_chromedriver
            ),
            jobdir=jobdir)


class ILArticle(_SpiderWrapper):
    __doc__ = _get_docstring(_ILArticleSpider, _ILArticleItem)
    def __init__(self, category=None, follow_link_extractor=None,
                 item_link_extractor=None, jobdir=None):
        super(ILArticle, self).__init__(
            spider_cls=_ILArticleSpider,
            spider_params=dict(
                category=category,
                follow_link_extractor=follow_link_extractor,
                item_link_extractor=item_link_extractor
            ),
            jobdir=jobdir)
