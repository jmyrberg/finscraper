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

    def __init__(self, category=None, follow_link_extractor=None, 
                 item_link_extractor=None, allow_chromedriver=False,  # TODO: Allow set through property
                 *args, **kwargs):
        """Fetch IltaSanomat news articles.
        
        Args:
            category (str, list or None, optional): Category to fetch articles
                from, meaning pages under https://is.fi/<category>/*. Defaults
                to None, which fetches articles everywhere.
            follow_link_extractor (LinkExtractor or None, optional):
                Link extractor to use for finding new article pages. Defaults
                to None, which uses the default follow link extractor.
            item_link_extractor (LinkExtractor or None, optional): 
                Link extractor for fetching article pages to scrape. Defaults
                to None, which uses the default item link extractor.
            allow_chromedriver (bool, optional): Whether to allow the usage
                of chrome headless browser or not. This is used when category
                is not None, for ensuring that more than a few links can be
                followed for a certain category.

                .. Note::
                    
                    Your OS might ask for permission to use the chromedriver,
                    which may require admin rights.
        """
        if category is None or not allow_chromedriver:  # No follow js
            follow_meta = None
        else:  # Categroy defined --> follow links with js
            follow_meta = {'run_js': True, 
                           'run_js_wait_sec': 1,
                           'scroll_to_bottom': True,
                           'scroll_to_bottom_wait_sec': 0.1}
        super(_ISArticleSpider, self).__init__(
            *args, follow_meta=follow_meta, **kwargs)
        self.category = category
        self.follow_link_extractor = follow_link_extractor
        self.item_link_extractor = item_link_extractor

        article_suffix = r'art\-[0-9]+\.html'
        if category is None:
            self.start_urls = ['https://www.is.fi']
            self.allow_follow = ()
            self.allow_items = (rf'.*/{article_suffix}')
        else:
            if type(category) == str:
                category = [category]
            self.start_urls = []
            self.allow_follow = []
            self.allow_items = []
            for cat in category:
                self.start_urls.append(f'https://www.is.fi/{cat}')
                self.start_urls.append(f'https://www.is.fi/haku/?query={cat}')
                self.allow_follow.append(rf'.*{cat}.*')
                self.allow_items.append(rf'.*/{cat}/{article_suffix}')

        self.allow_domains = ('is.fi')
        self.deny_domains = ('ravit.is.fi')
        self.deny = (r'.*/tag/.*', r'.*/haku/.*', r'.*/reseptit/.*',
                     r'.*/mainos/.*', r'.*/yritys/.*')

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
