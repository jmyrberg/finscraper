"""Module for YLEArticle spider."""


import time

from functools import partial

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity, MapCompose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.text_utils import strip_join, paragraph_join


class _YLEArticleSpider(FollowAndParseItemMixin, Spider):
    name = 'ylearticle'
    start_urls = ['https://www.yle.fi/uutiset']
    follow_link_extractor = LinkExtractor(
        allow_domains=('yle.fi'),
        allow=(r'.*/(uutiset|urheilu|a)/.*'),
        deny=(),
        deny_domains=(),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('yle.fi'),
        allow=(r'(uutiset|urheilu|a)/[0-9]+\-[0-9]+'),
        deny=(r'(uutiset|urheilu|a)/18-'),
        deny_domains=(),
        canonicalize=True
    )
    custom_settings = {}

    def __init__(self, *args, **kwargs):
        """Fetch YLE news articles.

        Args:
        """
        super(_YLEArticleSpider, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_image_metadata(text):
        sel = Selector(text=text)
        return {
            'src': sel.xpath('//img//@src').get(),
            'alt': sel.xpath('//img//@alt').get(),
            'caption': sel.xpath(
                '//figcaption//text()').getall()
        }

    def _parse_item(self, resp):
        il = ItemLoader(item=_YLEArticleItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))

        # Tradition style
        il.add_xpath(
            'title',
            '//article'
            '//header[contains(@class, "article__header")]'
            '//h1[contains(@class, "article__heading")]//text()')
        il.add_xpath(
            'ingress',
            '//article'
            '//header[contains(@class, "article__header")]'
            '//p[contains(@class, "article__paragraph")]//text()')

        pgraphs_xpath = (
            '//article//section[contains(@class, "article__content")]'
            '//p[contains(@class, "article__paragraph")]'
        )
        content = [''.join(Selector(text=pgraph).xpath('//text()').getall())
                   for pgraph in resp.xpath(pgraphs_xpath).getall()]
        il.add_value('content', content)

        # Header div based on position: 1=domain, 2=author, 3=published
        il.add_xpath(
            'published',
            '//article'
            '//header[contains(@class, "article__header")]'
            '//div[contains(@class, "article__date")]//text()')
        il.add_xpath(
            'author',
            '//article'
            '//header[contains(@class, "article__header")]'
            '//div[contains(@class, "aw-")][2]'
            '//span[contains(@class, "aw-")]'
            '//text()')
        il.add_xpath(
            'images',
            '//article//figure[contains(@class, "article__figure")]')

        # "Modern" style news
        il.add_xpath(
            'title',
            '//article'
            '//h1[contains(@class, "article__feature__heading")]//text()')
        il.add_xpath(
            'content',
            '//article'
            '//p[contains(@class, "article__feature__paragraph")]//text()')
        return il.load_item()


class _YLEArticleItem(Item):
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
        input_processor=partial(strip_join, join_with=', '),
        output_processor=TakeFirst()
    )
    author = Field(
        input_processor=partial(strip_join, join_with=', '),
        output_processor=TakeFirst()
    )
    images = Field(
        input_processor=MapCompose(_YLEArticleSpider._get_image_metadata),
        output_processor=Identity()
    )
