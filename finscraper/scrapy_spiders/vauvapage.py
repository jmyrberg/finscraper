"""Module for VauvaPage spider."""


import time


from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity, MapCompose, Compose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.text_utils import strip_join, safe_cast_int, strip_elements, \
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
        allow=(r'keskustelu/[0-9]+/[A-z0-9\-]+'),
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
        il = ItemLoader(item=_VauvaCommentItem(), selector=comment)
        il.add_xpath('author', '//*[contains(@property, "name")]//text()')
        il.add_xpath('date', '//div[contains(@class, "post-date")]//text()')
        il.add_xpath('quotes', '//blockquote//text()')
        il.add_xpath('content', '//p//text()')
        votes = il.nested_xpath('//span[contains(@class, "voting-count")]')
        votes.add_xpath('upvotes', '//li[@class="first"]//text()')
        votes.add_xpath('downvotes', '//li[@class="last"]//text()')
        return il.load_item()

    def _parse_item(self, resp):
        il = ItemLoader(item=_VauvaPageItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))
        il.add_xpath(
            'title',
            '//article//div[contains(@property, "title")]//text()')
        il.add_xpath(
            'page',
            '//article//li[contains(@class, "pager-current")]//text()')
        il.add_value('page', ['1'])
        il.add_xpath(
            'pages',
            '//article//li[contains(@class, "pager-last")]//text()')
        il.add_xpath(
            'pages',
            '//article//li[contains(@class, "pager-current")]//text()')
        il.add_value('pages', ['1'])
        il.add_xpath(
            'published',
            '(//article//div[contains(@class, "post-date")])[1]//text()')
        il.add_xpath(
            'author',
            '(//article//*[contains(@property, "name")])[1]//text()')

        comments = []
        comment_xpath = '//article//article[contains(@class, "comment")]'
        for comment in resp.xpath(comment_xpath):
            comments.append(self._parse_comment(Selector(text=comment.get())))
        il.add_value('comments', comments)
        return il.load_item()


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
