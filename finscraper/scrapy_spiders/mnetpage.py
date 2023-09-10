"""Module for Muuskoiden.net forum spider."""

import time

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from itemloaders.processors import TakeFirst, Identity, Compose
from finscraper.text_utils import strip_join, strip_elements, \
    drop_empty_elements


class _MNetPageSpider(FollowAndParseItemMixin, Spider):
    name = 'mnetpage'
    start_urls = ['https://muusikoiden.net/keskustelu/conferences.php']
    follow_link_extractor = LinkExtractor(
        allow_domains=('muusikoiden.net'),
        allow=(r'keskustelu\/\d+'),
        deny=(r'posts.php?.+'),
        deny_domains=(),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('muusikoiden.net'),
        allow=(r'keskustelu\/posts.php?.+'),
        deny=(),
        deny_domains=(),
        canonicalize=True
    )
    custom_settings = {}

    def __init__(self, *args, **kwargs):
        """Fetch threads from muusikoiden.net discussions.

        Args:
        """
        super(_MNetPageSpider, self).__init__(*args, **kwargs)

    def _parse_message(self, message: Selector, author: str, time_posted: str):
        """Parse message on thread page.

        Args:
            message (Selector): Selector for message
            author (str): Name of the message author
            time (str): Time of the message

        Returns:
            ItemLoader: Item with data about the message
        """
        il = ItemLoader(item=_MNetMessageItem(), selector=message)
        il.add_value('author', author)
        il.add_value('time_posted', time_posted)
        il.add_xpath('quotes', '//i[@class="quote"]//text()')
        il.add_xpath('content', '//font[@class="msg"]/text()[not(self::i)]')

        return il.load_item()

    def _parse_item(self, resp):
        """Parse thread page.

        Args:
            resp (HtmlResponse): Response from fetching the thread

        Returns:
            _MNetPageItem: _description_
        """
        il = ItemLoader(item=_MNetPageItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))
        il.add_xpath('title', '//b[contains(@class, "linkcolor")]//text()')
        il.add_xpath('page_number', '(//b[@class="selected_page"])[1]//text()')

        messages = []
        message_authors = resp.xpath('//a[@class="keskustelu_nick"]//text()')
        message_timestamps = resp.xpath('//font[@class="light"]//text()')

        # parse messages in thread
        for i, message in enumerate(resp.xpath('//font[@class="msg"]')):
            messages.append(
                self._parse_message(
                    message=Selector(text=message.get()),
                    author=message_authors[i].get(),
                    time_posted=message_timestamps[i].get(),
                )
            )

        # add messages into thread item
        il.add_value('messages', messages)

        return il.load_item()


class _MNetMessageItem(Item):
    """
    Returned message fields:
        * author (str): Author of the message.
        * time_posted (str): Publish time of the message.
        * quotes (list of str): List of quotes in the message.
        * content (str): Contents of the message.
    """
    author = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    time_posted = Field(
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
    page_number = Field(
        input_processor=Identity(),
        output_processor=Identity()
    )


class _MNetPageItem(Item):
    __doc__ = """
    Returned page fields:
        * url (str): Url of the thread page.
        * time (int): UNIX timestamp of the scraping.
        * title (str): Title of the thread.
        * page_number (int): Number of the page in the thread.
        * messages (list of str): Messages on the thread page.
    """ + _MNetMessageItem.__doc__
    url = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    time = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    title = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    page_number = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    messages = Field(
        input_processor=Identity(),
        output_processor=Identity()
    )
