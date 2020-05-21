"""Module for Scrapy spider mixins."""


from scrapy import Request
from scrapy.exceptions import CloseSpider


class FollowAndParseItemMixin:
    """Parse items and follow links based on defined link extractors.
    
    The following needs to be defined when inheriting:
        1) ``item_link_extractor`` -attribute: LinkExtractor that defines \
            the links to parse items from.
        2) ``follow_link_extractor`` -attribute: LinkExtractor that defines \
            the links to follow and find item pages from.
        3) ``parse_item`` -function: Parses the item from response.

    Args:
        follow_meta (dict or None, optional): Dictionary to pass within \
            link follow requests. Defaults to None.
        follow_items (dict or None, optional): Dictionary to pass within \
            item link requests. Defaults to None.

    Raises:
        AttributeError, if required attributes not defined when inheriting.
    """
    itemcount = 0
    def __init__(self, follow_meta=None, items_meta=None):
        self.follow_meta = follow_meta
        self.items_meta = items_meta

        for attr in ['follow_link_extractor', 'item_link_extractor']:
            if not hasattr(self, attr):
                raise AttributeError(f'Attribute `{attr}` must be defined')

    def _parse_item(self, resp):
        raise NotImplementedError('Function `_parse_item` not implemented!')

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse, meta=self.follow_meta)

    def parse(self, resp, to_parse=False):
        """Parse items and follow links based on defined link extractors."""
        if (self.itemcount and 
            self.itemcount == self.settings.get('CLOSESPIDER_ITEMCOUNT', 0)):
                raise CloseSpider

        if to_parse:
            yield self._parse_item(resp)
            self.itemcount += 1

        # Parse items and further on extract links from those pages
        item_links = self.item_link_extractor.extract_links(resp)
        for link in item_links:
            yield Request(link.url, callback=self.parse, meta=self.items_meta,
                          priority=20, cb_kwargs={'to_parse': True})

        # Extract all links from this page
        follow_links = self.follow_link_extractor.extract_links(resp)
        for link in follow_links:
            yield Request(link.url, callback=self.parse, meta=self.follow_meta,
                          priority=10)
