"""Module for Scrapy spider mixins."""


from scrapy import Request


class FollowAndParseItemMixin:
    """Parse items and follow links based on defined link extractors.
    
    When using this mixin, the following needs to be defined when inheriting:
        1) `item_link_extractor` attribute: Extract links to parse items from.
        2) `follow_link_extractor` attribute: Extract links to follow and find
            item pages from.
        3) `parse_item` function: Parse item from response.
    """
    item_link_extractor = None
    follow_link_extractor = None
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'finscraper.middlewares.DownloaderMiddlewareWithJs': 543
        }
    }

    def __init__(self, follow_meta=None, items_meta=None):
        self.follow_meta = follow_meta
        self.items_meta = items_meta

    def _parse_item(self, resp):
        raise NotImplementedError('Function `_parse_item` not implemented!')

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse, meta=self.follow_meta)

    def parse(self, resp, to_parse=False):
        """Parse items and follow links based on defined link extractors."""
        if to_parse:
            yield self._parse_item(resp)

        # Parse items and further on extract links from those pages
        item_links = self.item_link_extractor.extract_links(resp)
        for link in item_links:
            yield Request(link.url, callback=self.parse, meta=self.items_meta,
                          cb_kwargs={'to_parse': True})

        # Extract all links from this page
        follow_links = self.follow_link_extractor.extract_links(resp)
        for link in follow_links:
            yield Request(link.url, callback=self.parse, meta=self.follow_meta)
