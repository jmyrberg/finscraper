"""Module for VauvaPage spider."""


import time

from functools import partial

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.exceptions import DropItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Identity, MapCompose, Compose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.utils import strip_join, safe_cast_int, strip_elements, \
    drop_empty_elements


class _VauvaPageSpider(FollowAndParseItemMixin, Spider):
    name = 'vauvapage'
    start_urls = ['https://vauva.fi']
    follow_link_extractor = LinkExtractor(
        allow_domains=('vauva.fi'),
        allow=(r'.*\/keskustelu\/.*'),
        deny=('quote', 'changed', 'user', r'(\&|\?)(rate)\='),
        deny_domains=(),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('vauva.fi'),
        allow=(rf'keskustelu/[0-9]+/[A-z0-9\-]+'),
        deny=('quote', 'changed', 'user', r'(\&|\?)(rate)\='),
        deny_domains=(),
        canonicalize=True
    )
    custom_settings = {}

    def __init__(self, *args, **kwargs):
        """Fetch comments from vauva.fi.
        
        Args:
        """
        super(_VauvaPageSpider, self).__init__(*args, **kwargs)

    def _parse_comment(self, comment):
        l = ItemLoader(item=_VauvaCommentItem(), selector=comment)
        l.add_xpath('author', '//*[contains(@property, "name")]//text()')
        l.add_xpath('date', '//div[contains(@class, "post-date")]//text()')
        l.add_xpath('quotes', '//blockquote//text()', strip_join)
        l.add_xpath('content', '//p//text()')
        votes = l.nested_xpath('//span[contains(@class, "voting-count")]')
        votes.add_xpath('upvotes', '//li[@class="first"]//text()')
        votes.add_xpath('downvotes', '//li[@class="last"]//text()')
        return l.load_item()
    
    def _parse_item(self, resp):
        l = ItemLoader(item=_VauvaPageItem(), response=resp)
        l.add_value('url', resp.url)
        l.add_value('time', int(time.time()))
        l.add_xpath('title',
            '//article//div[contains(@property, "title")]//text()')
        l.add_xpath('page',
            '//article//li[contains(@class, "pager-current")]//text()')
        l.add_value('page', ['1'])
        l.add_xpath('pages',
            '//article//li[contains(@class, "pager-last")]//text()')
        l.add_xpath('pages',
            '//article//li[contains(@class, "pager-current")]//text()')
        l.add_value('pages', ['1'])
        l.add_xpath('published',
            '(//article//div[contains(@class, "post-date")])[1]//text()')
        l.add_xpath('author',
            '(//article//*[contains(@property, "name")])[1]//text()')
        
        comments = []
        comment_xpath = '//article//article[contains(@class, "comment")]'
        for comment in resp.xpath(comment_xpath):
            comments.append(self._parse_comment(Selector(text=comment.get())))
        l.add_value('comments', comments)
        loaded_item = l.load_item()
        return loaded_item


class _VauvaCommentItem(Item):
    """
    Returned comment fields:
        * author (str): Author of the comment.
        * date (str): Publish time of the comment.
        * quotes (list of str): List of quotes in the comment.
        * content (str): Contents of the comment.
        * upvotes (int): Upvotes of the comment.
        * downvotes (int): Downvotes of the comment.
    """
    author = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    date = Field(
        input_processor=strip_join,
        output_processor=Compose(strip_elements, TakeFirst())
    )
    quotes = Field(
        input_processor=drop_empty_elements,
        output_processor=Identity()
    )
    content = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    upvotes = Field(
        input_processor=MapCompose(TakeFirst(), safe_cast_int),
        output_processor=TakeFirst()
    )
    downvotes = Field(
        input_processor=MapCompose(TakeFirst(), safe_cast_int),
        output_processor=TakeFirst()
    )


class _VauvaPageItem(Item):
    __doc__ = """
    Returned page fields:
        * url (str): URL of the scraped web page.
        * time (int): UNIX timestamp of the scraping.
        * title (str): Title of the thread.
        * page (int): Page number of the thread.
        * pages (int): Pages in the thread.
        * comments (str): Comments of the thread page.
        * published (str): Publish time of the article.
        * author (str): Author of the article.
    """ + _VauvaCommentItem.__doc__
    url = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    time = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    title = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    page = Field(
        input_processor=MapCompose(safe_cast_int),
        output_processor=TakeFirst()
    )
    pages = Field(
        input_processor=MapCompose(safe_cast_int),
        output_processor=TakeFirst()
    )
    comments = Field(
        input_processor=Identity(),
        output_processor=Identity()
    )
    published = Field(
        input_processor=strip_join,
        output_processor=Compose(strip_elements, TakeFirst())
    )
    author = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
