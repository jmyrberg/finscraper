"""Module for DemiPage spider."""


import time

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.loader import ItemLoader
from scrapy.linkextractors import LinkExtractor
from scrapy.loader.processors import TakeFirst, Identity, MapCompose, Compose
from scrapy.http import HtmlResponse

from selenium.webdriver.support.wait import WebDriverWait

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.text_utils import strip_join, safe_cast_int, strip_elements, \
    drop_empty_elements, paragraph_join


class _DemiPageSpider(FollowAndParseItemMixin, Spider):
    name = 'demipage'
    start_urls = ['https://demi.fi/keskustelut']
    follow_link_extractor = LinkExtractor(
        allow_domains=('demi.fi'),
        allow=(r'.*\/keskustelu[t]*\/.*'),
        deny=(r'\?'),
        deny_domains=(),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('demi.fi'),
        allow=(rf'.*/keskustelu/[A-z0-9\-]+'),
        deny=(r'\?'),
        deny_domains=(),
        restrict_xpaths=['//div[contains(@class, "threadItem")]'],
        canonicalize=True
    )
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'finscraper.middlewares.SeleniumCallbackMiddleware': 800
        }
    }

    def __init__(self, *args, **kwargs):
        """Fetch comments from demi.fi.

        Args:
        """
        kwargs['items_selenium_callback'] = self._wait_item_page
        super(_DemiPageSpider, self).__init__(*args, **kwargs)

    @staticmethod
    def _wait_item_page(request, spider, driver):
        # Wait until number of comments corresponds to numbering
        driver.get(request.url)
        reply_xpath = '//div[contains(@class, "__reply__")]'
        numbering_xpath = (
            f'{reply_xpath}//div[contains(@class, "replyNumbering")]')
        numbering = driver.find_element_by_xpath(numbering_xpath)
        try:
            n_comments = int(numbering.text.split('/')[-1])
        except Exception:
            n_comments = 0
        (WebDriverWait(driver, 2, 0.1).until(
         lambda d: len(d.find_elements_by_xpath(reply_xpath)) >= n_comments))
        return HtmlResponse(
            driver.current_url,
            body=driver.page_source.encode('utf-8'),
            encoding='utf-8',
            request=request
        )

    def _parse_comment(self, comment):
        il = ItemLoader(item=_DemiCommentItem(), selector=comment)
        il.add_xpath(
            'author',
            '//span[contains(@class, "discussionItemAuthor")]//text()')
        il.add_xpath('date', '//span[contains(@class, "__time__")]//text()')
        il.add_xpath('quotes', '//blockquote//text()')
        il.add_xpath('content', '//p//text()')
        il.add_xpath(
            'numbering', '//div[contains(@class, "replyNumbering")]//text()')
        il.add_xpath('likes', '//span[contains(@class, "LikeCount")]//text()')
        return il.load_item()

    def _parse_item(self, resp):
        il = ItemLoader(item=_DemiPageItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))
        first_reply = il.nested_xpath(
            '//div[contains(@class, "firstReplyContainer")]')
        first_reply.add_xpath(
            'title', '//div[contains(@class, "__title__")]//text()')
        first_reply.add_xpath(
            'published', '//span[contains(@class, "__time__")]//text()')
        il.add_xpath(
            'author',
            '//span[contains(@class, "discussionItemAuthor")]//text()')

        comments = []
        comment_xpath = '//div[contains(@class, "__reply__")]'
        for comment in resp.xpath(comment_xpath):
            comments.append(self._parse_comment(Selector(text=comment.get())))
        il.add_value('comments', comments)
        return il.load_item()


class _DemiCommentItem(Item):
    """
    Returned comment fields:
        * author (str): Author of the comment.
        * date (str): Publish time of the comment.
        * quotes (list of str): List of quotes in the comment.
        * content (str): Contents of the comment.
        * numbering (str): Numbering of the comment.
        * likes (int): Like count of the comment.
    """
    author = Field(
        input_processor=Identity(),
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
    numbering = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    likes = Field(
        input_processor=MapCompose(TakeFirst(), safe_cast_int),
        output_processor=TakeFirst()
    )


class _DemiPageItem(Item):
    __doc__ = """
    Returned page fields:
        * url (str): URL of the scraped web page.
        * time (int): UNIX timestamp of the scraping.
        * title (str): Title of the thread.
        * comments (str): Comments of the thread page.
        * published (str): Publish time of the article.
        * author (str): Author of the article.
    """ + _DemiCommentItem.__doc__
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
    comments = Field(
        input_processor=Identity(),
        output_processor=Identity()
    )
    published = Field(
        input_processor=strip_elements,
        output_processor=TakeFirst()
    )
    author = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
