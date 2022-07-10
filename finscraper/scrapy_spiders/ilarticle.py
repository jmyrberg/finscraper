"""Module for ILArticle spider."""


import time

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity, MapCompose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.text_utils import strip_join, paragraph_join


class _ILArticleSpider(FollowAndParseItemMixin, Spider):
    name = 'ilarticle'
    start_urls = ['https://www.iltalehti.fi']
    follow_link_extractor = LinkExtractor(
        allow_domains=('iltalehti.fi'),
        allow=(),
        deny=(r'.*/telkku/.*'),
        deny_domains=(),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('iltalehti.fi'),
        allow=(r'.*/a/[0-9A-z\-]+'),
        deny=(r'.*/telkku/.*'),
        deny_domains=(),
        canonicalize=True
    )
    custom_settings = {}

    def __init__(self, *args, **kwargs):
        """Fetch Iltalehti news articles.

        Args:
        """
        super(_ILArticleSpider, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_image_metadata(text):
        sel = Selector(text=text)
        return {
            'src': sel.xpath('//img//@src').get(),
            'alt': sel.xpath('//img//@alt').get(),
            'caption': sel.xpath(
                '//div[contains(@class, "media-caption")]//text()').getall()
        }

    def _parse_item(self, resp):
        il = ItemLoader(item=_ILArticleItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))
        il.add_xpath(
            'title',
            '//article//h1[contains(@class, "article-headline")]//text()')
        il.add_xpath(
            'ingress',
            '//article//div[contains(@class, "article-description")]//text()')

        pgraphs_xpath = '//article//div[contains(@class, "article-body")]//p'
        content = [''.join(Selector(text=pgraph).xpath('//text()').getall())
                   for pgraph in resp.xpath(pgraphs_xpath).getall()]
        il.add_value('content', content)

        il.add_xpath('published', '//time//text()')
        il.add_xpath(
            'author',
            '//article//div[contains(@class, "author-name")]//text()')
        il.add_xpath(
            'images',
            '//article//div[contains(@class, "article-image")]')
        return il.load_item()


class _ILArticleItem(Item):
    """
    Returned fields:
        * url (str): URL of the scraped web page.
        * time (int): UNIX timestamp of the scraping.
        * title (str): Title of the article.
        * ingress (str): Ingress of the article.
        * content (str): Contents of the article.
        * published (str): Publish time of the article.
        * author (str): Author of the article.
        * images (list of dict): Images of the article.
    """
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
    ingress = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    content = Field(
        input_processor=paragraph_join,
        output_processor=TakeFirst()
    )
    published = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    author = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    images = Field(
        input_processor=MapCompose(_ILArticleSpider._get_image_metadata),
        output_processor=Identity()
    )
