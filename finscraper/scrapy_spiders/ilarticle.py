"""Module for ILArticle spider."""


import time

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Identity, MapCompose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.utils import strip_join


class _ILArticleSpider(FollowAndParseItemMixin, Spider):
    name = 'ilarticle'
    custom_settings = {}

    def __init__(self, category=None, follow_link_extractor=None,
                 item_link_extractor=None, *args, **kwargs):
        """Fetch Iltalehti news articles.
        
        Args:
            category (str, list or None, optional): Category to fetch articles
                from, meaning pages under https://iltalehti.fi/category/*.
                Defaults to None, which fetches articles everywhere.
            follow_link_extractor (LinkExtractor or None, optional):
                Link extractor to use for finding new article pages. Defaults
                to None, which uses the default follow link extractor.
            item_link_extractor (LinkExtractor or None, optional): 
                Link extractor for fetching article pages to scrape. Defaults
                to None, which uses the default item link extractor.
        """
        super(_ILArticleSpider, self).__init__(*args, **kwargs)
        self.category = category
        self.follow_link_extractor = follow_link_extractor
        self.item_link_extractor = item_link_extractor

        article_suffix = r'a/[0-9A-z\-]+'
        if category is None:
            self.start_urls = ['https://www.iltalehti.fi']
            self.allow_follow = ()
            self.allow_items = (rf'.*/{article_suffix}')
        else:
            if type(category) == str:
                category = [category]
            self.start_urls = []
            self.allow_follow = []
            self.allow_items = []
            for cat in category:
                self.start_urls.append(f'https://www.iltalehti.fi/{cat}')
                self.allow_follow.append(rf'.*{cat}.*')
                self.allow_items.append(rf'.*/{cat}/{article_suffix}')

        self.allow_domains = ('iltalehti.fi')
        self.deny_domains = ()
        self.deny = (r'.*/telkku/.*')

        if self.follow_link_extractor is None:
            self.follow_link_extractor = LinkExtractor(
                allow_domains=self.allow_domains,
                allow=self.allow_follow,
                deny=self.deny,
                deny_domains=self.deny_domains,
                canonicalize=True
            )
        if self.item_link_extractor is None:
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
            'caption': sel.xpath(
                '//div[contains(@class, "media-caption")]//text()').getall()
        }
    
    def _parse_item(self, resp):
        l = ItemLoader(item=_ILArticleItem(), response=resp)
        l.add_value('url', resp.url)
        l.add_value('time', int(time.time()))
        l.add_xpath('title',
            '//article//h1[contains(@class, "article-headline")]//text()')
        l.add_xpath('ingress',
            '//article//div[contains(@class, "article-description")]//text()')
        l.add_xpath('content',
            '//article//div[contains(@class, "article-body")]//text()')
        l.add_xpath('published',
            '//time//text()')
        l.add_xpath('author',
            '//article//div[contains(@class, "author-name")]//text()')
        l.add_xpath('images',
            '//article//div[contains(@class, "article-image")]')
        return l.load_item()


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
        input_processor=MapCompose(_ILArticleSpider._get_image_metadata),
        output_processor=Identity()
    )
