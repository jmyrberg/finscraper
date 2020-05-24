"""Module for Scrapy pipelines."""


class DefaultValueNonePipeline:
    """Pipeline that sets default values of all item fields to None."""

    def process_item(self, item, spider):
        for field in item.fields:
            item.setdefault(field, None)
        return item
