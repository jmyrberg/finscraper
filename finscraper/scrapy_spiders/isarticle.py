"""Module for ISArticle spider."""


import time

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Identity, MapCompose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.utils import strip_join


class ISArticleSpider(FollowAndParseItemMixin, Spider):
    name = 'isarticle'
    custom_settings = {}

    def __init__(
            self,
            category=None,
            allow_domains=('is.fi'),
            deny_domains=('ravit.is.fi'),
            deny=('.*/tag/.*', '.*/haku/.*', '.*/reseptit/.*'),
            *args,
            **kwargs):
        """Fetch IltaSanomat news articles.
        
        Args:
            category (str, list or None): Category to fetch articles from,    
                meaning pages under 'is.fi/<category>/'. Defaults to None,
                which fetches articles everywhere.
        """
        super(ISArticleSpider, self).__init__(*args, **kwargs)
        self.category = category
        self.allow_domains = allow_domains
        self.deny_domains = deny_domains
        self.deny = deny

        if category is None:
            self.start_urls = ['https://www.is.fi']
            self.allow_follow = ()
            self.allow_items = (r'.*/art\-[0-9]+\.html')
        else:
            if type(category) == str:
                category = [category]
            self.start_urls = []
            self.allow_follow = []
            self.allow_items = []
            for cat in category:
                self.start_urls.append(f'https://www.is.fi/{cat}')
                self.allow_follow.append(rf'.*/{cat}/.*')
                self.allow_items.append(rf'.*/{cat}/art\-[0-9]+\.html')

        self.follow_link_extractor = LinkExtractor(
            allow_domains=self.allow_domains,
            allow=self.allow_follow,
            deny=self.deny,
            deny_domains=self.deny_domains,
            canonicalize=True
        )
        self.item_link_extractor = LinkExtractor(
            allow_domains=self.allow_domains,
            allow=self.allow_items,
            deny=self.deny,
            deny_domains=self.deny_domains,
            canonicalize=True
        )

    @staticmethod
    def _get_image_metadata(text):
        sel = Selector(text=text)
        return {
            'src': sel.xpath('//img//@src').get(),
            'alt': sel.xpath('//img//@alt').get(),
            'caption': strip_join(sel.xpath('//p//text()').getall())
        }
    
    def _parse_item(self, resp):
        l = ItemLoader(item=ISArticleItem(), response=resp)
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


class ISArticleItem(Item):
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
        input_processor=MapCompose(ISArticleSpider._get_image_metadata),
        output_processor=Identity()
    )
