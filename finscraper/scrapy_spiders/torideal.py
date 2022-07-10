"""Module for ToriDeal spider."""


import time

from scrapy import Item, Field, Selector
from scrapy.crawler import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity, MapCompose, Compose

from finscraper.scrapy_spiders.mixins import FollowAndParseItemMixin
from finscraper.text_utils import strip_join, drop_empty_elements, \
    paragraph_join


class _ToriDealSpider(FollowAndParseItemMixin, Spider):
    name = 'torideal'
    start_urls = ['https://tori.fi']
    follow_link_extractor = LinkExtractor(
        allow_domains=('tori.fi'),
        allow=(),
        deny=('.*tili.*'),
        deny_domains=('tuki.tori.fi', 'blog.tori.fi', 'tori-kaupat.tori.fi',
                      'careers.tori.fi', 'media.tori.fi'),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('tori.fi'),
        allow=(r'/[A-z0-9\_]+.htm.*'),
        deny=('.*tili.*'),
        deny_domains=('tuki.tori.fi', 'blog.tori.fi', 'tori-kaupat.tori.fi',
                      'careers.tori.fi', 'media.tori.fi', 'asunnot.tori.fi'),
        canonicalize=True
    )
    custom_settings = {
        'ROBOTSTXT_OBEY': False
    }

    def __init__(self, *args, **kwargs):
        """Fetch deals from tori.fi.

        Args:
        """
        super(_ToriDealSpider, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_image_metadata(text):
        sel = Selector(text=text)
        return {
            'src': sel.xpath('//@src').get(),
            'alt': sel.xpath('//@alt').get(),
            'title': sel.xpath('//@title').get()
        }

    def _parse_item(self, resp):
        il = ItemLoader(item=_ToriDealItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))
        il.add_xpath(
            'seller',
            '//div[contains(@id, "seller_info")]//text()')
        il.add_xpath(
            'name',
            '//div[@class="topic"]//*[contains(@itemprop, "name")]//text()')
        il.add_xpath(
            'description',
            '//*[contains(@itemprop, "description")]//text()')
        il.add_xpath(
            'price',
            '//*[contains(@itemprop, "price")]//text()')
        il.add_xpath(
            'type',
            '//td[contains(text(), "Ilmoitustyyppi")]'
            '/following-sibling::td[1]//text()')
        il.add_xpath(
            'published',
            '//td[contains(text(), "Ilmoitus jätetty")]'
            '/following-sibling::td[1]//text()')
        il.add_xpath('images', '//div[@class="media_container"]//img')
        return il.load_item()


class _ToriDealItem(Item):
    __doc__ = """
    Returned fields:
        * url (str): URL of the scraped web page.
        * time (int): UNIX timestamp of the scraping.
        * seller (str): Seller of the item.
        * name (str): Name of the item.
        * description (list of str): Description of the item.
        * price (str): Price of the item.
        * type (str): Type of the deal.
        * published (str): Publish time of the deal.
        * images (list of dict): Images of the item.
    """
    url = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    time = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    seller = Field(
        input_processor=Compose(drop_empty_elements, paragraph_join),
        output_processor=TakeFirst()
    )
    name = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    description = Field(
        input_processor=Compose(drop_empty_elements, paragraph_join),
        output_processor=TakeFirst()
    )
    price = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    type = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    published = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    images = Field(
        input_processor=MapCompose(_ToriDealSpider._get_image_metadata),
        output_processor=Identity()
    )
