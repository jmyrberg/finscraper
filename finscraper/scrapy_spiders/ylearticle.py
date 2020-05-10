"""Module for YLEArticle spider."""


import time

from functools import partial

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.exceptions import DropItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Identity, MapCompose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.utils import strip_join


class _YLEArticleSpider(FollowAndParseItemMixin, Spider):
    name = 'ylearticle'
    custom_settings = {}

    def __init__(self, follow_link_extractor=None,
                 item_link_extractor=None, *args, **kwargs):
        """Fetch YLE news articles.
        
        Args:
            follow_link_extractor (LinkExtractor or None, optional):
                Link extractor to use for finding new article pages. Defaults
                to None, which uses the default follow link extractor.
            item_link_extractor (LinkExtractor or None, optional): 
                Link extractor for fetching article pages to scrape. Defaults
                to None, which uses the default item link extractor.
        """
        super(_YLEArticleSpider, self).__init__(*args, **kwargs)
        self.follow_link_extractor = follow_link_extractor
        self.item_link_extractor = item_link_extractor

        article_suffix = r'[0-9]+\-[0-9]+'

        self.start_urls = ['https://www.yle.fi/uutiset']
        self.allow_follow = (r'.*/(uutiset|urheilu)/.*')
        self.allow_items = (rf'(uutiset|urheilu)/{article_suffix}')

        self.allow_domains = ('yle.fi')
        self.deny_domains = ()
        self.deny_follow = ()
        self.deny_items = (rf'(uutiset|urheilu)/18-')

        if self.follow_link_extractor is None:
            self.follow_link_extractor = LinkExtractor(
                allow_domains=self.allow_domains,
                allow=self.allow_follow,
                deny=self.deny_follow,
                deny_domains=self.deny_domains,
                canonicalize=True
            )
        if self.item_link_extractor is None:
            self.item_link_extractor = LinkExtractor(
                allow_domains=self.allow_domains,
                allow=self.allow_items,
                deny=self.deny_items,
                deny_domains=self.deny_domains,
                canonicalize=True
            )

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
        l = ItemLoader(item=_YLEArticleItem(), response=resp)
        l.add_value('url', resp.url)
        l.add_value('time', int(time.time()))
        # Oldskool
        l.add_xpath('title',
            '//article'
            '//div[contains(@class, "article__header")]'
            '//h1[contains(@class, "article__heading")]//text()')
        l.add_xpath('ingress',
            '//article'
            '//div[contains(@class, "article__header")]'
            '//p[contains(@class, "article__paragraph")]//text()')
        l.add_xpath('content',
            '//article'+
            '//div[contains(@class, "article__content")]'+
            '//p[contains(@class, "article__paragraph")]//text()')
        l.add_xpath('published',
            '//article'+
            '//div[contains(@class, "article__header")]'+
            '//span[contains(@class, "article__date")]//text()')
        l.add_xpath('author',
            '//article'+
            '//span[contains(@class, "author__name")]//text()')
        l.add_xpath('images',
            '//article'+
            '//figure[contains(@class, "article__figure")]')

        # "Modern"
        l.add_xpath('title',
            '//article'+
            '//h1[contains(@class, "article__feature__heading")]//text()')
        l.add_xpath('content',
            '//article'+
            '//p[contains(@class, "article__feature__paragraph")]//text()')
        return l.load_item()


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
        input_processor=strip_join,
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
