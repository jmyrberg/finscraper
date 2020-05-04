"""Module for spiders."""


from finscraper.wrappers import SpiderWrapper
from finscraper.scrapy_spiders.isarticle import ISArticleSpider


class ISArticle(SpiderWrapper):
    __doc__ = ISArticleSpider.__init__.__doc__
    def __init__(self, jobdir=None, **spider_params):
        super(ISArticle, self).__init__(ISArticleSpider, spider_params, jobdir)