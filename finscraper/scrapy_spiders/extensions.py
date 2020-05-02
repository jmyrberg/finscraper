"""Module for scrapy extensions."""


from scrapy import Request
from scrapy.spiders import Spider


class ExtendedSpider(Spider):

    def __init__(self, *args, **kwargs):
        super(ExtendedSpider, self).__init__(*args, **kwargs)

    def parse(self, resp, to_parse=False):
        """Parse items and follow links based on defined link extractors."""
        if to_parse:
            yield self.parse_item(resp)

        # Parse items and further on extract links from those pages
        item_links = self.item_link_extractor.extract_links(resp)
        for link in item_links:            yield Request(link.url, callback=self.parse,
                          cb_kwargs={'to_parse': True})

        # Extract all links from this page
        follow_links = self.follow_link_extractor.extract_links(resp)
        for link in follow_links:
            yield Request(link.url, callback=self.parse)