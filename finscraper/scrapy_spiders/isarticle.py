"""Module for ISArticle spider."""


import time

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Identity, MapCompose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.utils import strip_join


class _ISArticleSpider(FollowAndParseItemMixin, Spider):
    name = 'isarticle'
    start_urls = ['https://www.is.fi']
    follow_link_extractor = LinkExtractor(
        allow_domains=('is.fi'),
        allow=(),
        deny=(r'.*/tag/.*', r'.*/haku/.*', r'.*/reseptit/.*', r'.*/mainos/.*',
              r'.*/yritys/.*'),
        deny_domains=('ravit.is.fi'),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('is.fi'),
        allow=(rf'.*/art\-[0-9]+\.html'),
        deny=(r'.*/tag/.*', r'.*/haku/.*', r'.*/reseptit/.*', r'.*/mainos/.*',
              r'.*/yritys/.*'),
        deny_domains=('ravit.is.fi'),
        canonicalize=True
    )
    def __init__(self, *args, **kwargs):
        """Fetch IltaSanomat news articles.
        
        Args:
        """
        super(_ISArticleSpider, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_image_metadata(text):
        sel = Selector(text=text)
        return {
            'src': sel.xpath('//img//@src').get(),
            'alt': sel.xpath('//img//@alt').get(),
            'caption': strip_join(sel.xpath('//p//text()').getall())
        }
    
    def _parse_item(self, resp):
        l = ItemLoader(item=_ISArticleItem(), response=resp)
        l.add_value('url', resp.url)
        l.add_value('time', int(time.time()))
        l.add_xpath('title', '//article//h1//text()')
        l.add_xpath('ingress',
            '//section//article//p[contains(@class, "ingress")]//text()')
        l.add_xpath('content',
            '//article//p[contains(@class, "body")]//text()')
        l.add_xpath('published',
            '//article//div[contains(@class, "timestamp")]//text()')
        l.add_xpath('author',
            '//article//div[contains(@itemprop, "author")]//text()')
        l.add_xpath('images',
            '//section//article//div[contains(@class, "clearing-container")]')
        return l.load_item()


class _ISArticleItem(Item):
    """
    Returns:
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
        input_processor=strip_join,
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
        input_processor=MapCompose(_ISArticleSpider._get_image_metadata),
        output_processor=Identity()
    )
