"""Module for spiders."""


from finscraper.wrappers import SpiderWrapper
from finscraper.scrapy_spiders.isarticle import ISArticleSpider


__jobdir_doc__ = '''
            jobdir (None or str, optional): Working directory of the spider.
                Defaults to None, which creates a temp directory to be used.
                Note that this directory will only be deleted through the
                `clear` method!
'''

class ISArticle(SpiderWrapper):
    __doc__ = ISArticleSpider.__init__.__doc__.strip() + __jobdir_doc__
    def __init__(self, category=None, follow_link_extractor=None,
                 item_link_extractor=None, jobdir=None):
        super(ISArticle, self).__init__(
            spider_cls=ISArticleSpider,
            spider_params=dict(
                category=category,
                follow_link_extractor=follow_link_extractor,
                item_link_extractor=item_link_extractor
            ),
            jobdir=jobdir)