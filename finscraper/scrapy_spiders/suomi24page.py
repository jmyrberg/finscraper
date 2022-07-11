"""Module for Suomi24Page spider."""


import time


from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity, MapCompose, Compose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.text_utils import strip_join, safe_cast_int, strip_elements, \
    drop_empty_elements, paragraph_join


class _Suomi24PageSpider(FollowAndParseItemMixin, Spider):
    name = 'suomi24page'
    start_urls = ['https://keskustelu.suomi24.fi']
    follow_link_extractor = LinkExtractor(
        allow_domains=('keskustelu.suomi24.fi'),
        allow=(),
        deny=(r'\?'),
        deny_domains=(),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('keskustelu.suomi24.fi'),
        allow=(r'/t/[0-9]+/[A-z0-9\-]+'),
        deny=(r'\?'),
        deny_domains=(),
        canonicalize=True
    )
    custom_settings = {}

    def __init__(self, *args, **kwargs):
        """Fetch comments from suomi24.fi.

        Args:
        """
        super(_Suomi24PageSpider, self).__init__(*args, **kwargs)

    def _parse_comment_response(self, response):
        il = ItemLoader(item=_Suomi24CommentResponseItem(), selector=response)
        il.add_xpath(
            'author',
            '//*[contains(@class, "Username")]//text()')
        il.add_xpath(
            'date',
            '//*[contains(@class, "Timestamp")]//text()')
        il.add_xpath('quotes', '//blockquote//text()', strip_join)
        il.add_xpath(
            'content',
            '//p[contains(@class, "ListItem__Text")]//text()')
        return il.load_item()

    def _parse_comment(self, comment):
        il = ItemLoader(item=_Suomi24CommentItem(), selector=comment)
        il.add_xpath(
            'author',
            '(//*[contains(@class, "Username")])[1]//text()')
        il.add_xpath(
            'date',
            '(//*[contains(@class, "Timestamp")])[1]//text()')
        il.add_xpath(
            'quotes',
            '(//article)[1]//blockquote//text()')
        il.add_xpath(
            'content',
            '(//article)[1]//p[contains(@class, "ListItem__Text")]//text()')

        responses = []
        responses_xpath = '//li[contains(@class, "CommentResponsesItem")]'
        for response in comment.xpath(responses_xpath):
            responses.append(
                self._parse_comment_response(Selector(text=response.get())))
        il.add_value('responses', responses)
        return il.load_item()

    def _parse_item(self, resp):
        il = ItemLoader(item=_Suomi24PageItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))
        il.add_xpath('title', '//*[contains(@*, "thread-title")]//text()')
        il.add_xpath(
            'published',
            '(//*[contains(@class, "Timestamp")])[1]//text()')
        il.add_xpath(
            'author',
            '(//*[contains(@class, "Username")])[1]//text()')
        il.add_xpath(
            'content',
            '(//*[contains(@*, "thread-body-text")])[1]//text()')
        il.add_xpath(
            'n_comments',
            '(//*[contains(@*, "stats-comments")])[1]//text()')
        il.add_xpath(
            'views',
            '(//*[contains(@*, "stats-views")])[1]//text()')

        comments = []
        comment_xpath = '//li[contains(@class, "CommentItem")]'
        for comment in resp.xpath(comment_xpath):
            comments.append(self._parse_comment(Selector(text=comment.get())))
        il.add_value('comments', comments)
        return il.load_item()


class _Suomi24CommentResponseItem(Item):
    """
    Returned comment response fields:
        * author (str): Author of the comment response.
        * date (str): Publish time of the comment response.
        * quotes (list of str): List of quotes in the comment response.
        * content (str): Contents of the comment response.
    """
    author = Field(
        input_processor=strip_elements,
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
        input_processor=paragraph_join,
        output_processor=TakeFirst()
    )


class _Suomi24CommentItem(Item):
    """
    Returned comment fields:
        * author (str): Author of the comment.
        * date (str): Publish time of the comment.
        * quotes (list of str): List of quotes in the comment.
        * responses (list of dict): Response comments to this comment.
        * content (str): Contents of the comment.
    """
    author = Field(
        input_processor=strip_elements,
        output_processor=TakeFirst()
    )
    date = Field(
        input_processor=strip_join,
        output_processor=Compose(strip_elements, TakeFirst())
    )
    quotes = Field(
        input_processor=Identity(),
        output_processor=Identity()
    )
    responses = Field(
        input_processor=Identity(),
        output_processor=Identity()
    )
    content = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )


class _Suomi24PageItem(Item):
    __doc__ = """
    Returned page fields:
        * url (str): URL of the scraped web page.
        * time (int): UNIX timestamp of the scraping.
        * title (str): Title of the thread.
        * content (str): Content of the first message.
        * comments (str): Comments of the thread page.
        * published (str): Publish time of the thread.
        * author (str): Author of the thread.
        * n_comments (int): Number of comments in the thread.
        * views (str): Number of views.
    """ + _Suomi24CommentItem.__doc__ + _Suomi24CommentResponseItem.__doc__
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
    content = Field(
        input_processor=paragraph_join,
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
    n_comments = Field(
        input_processor=MapCompose(safe_cast_int),
        output_processor=TakeFirst()
    )
    views = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
