# finscraper

This library provides a Python API for downloading data from popular Finnish websites in a structured format.

![TODO: Cover picture](docs/cover.png)

Websites covered include:

* News articles from IltaSanomat (is.fi)


## Installation

`pip install -r requirements.txt`

TODO: Make a pip package?

## Documentation

TODO: Sphinx documentation or similar

## Quickstart

The library provides an easy-to-use API for fetching data from various Finnish websites. For example, fetching news articles from IltaSanomat and saving them into *items.json* can be done as follows:

```python
from finscraper.spiders import ISArticle

spider = ISArticle(category='nhl',
                   FEEDS={'items.json': {'format': 'json'}})
spider.run()
```

Please see example [Jupyter notebooks]() for more detailed reference:

* [Scraping news articles from IltaSanomat](notebooks/scraping-news-articles-from-is.ipynb)

* [Continuing scraping from previous run](notebooks/continuing-scraping-from-previous-run.ipynb)


## Contributing

Web scrapers break when the formatting of websites change - **often**. Unfortunately, I can't make a promise to keep this repository up-to-date all by myself, and therefore I invite you to help when a spider stops working:

1) Update the xpaths of a broken spider within the [finscraper/scrapy_spiders -module](finscraper/scrapy_spiders) to correspond to the latest version of the website to be scraped

2) Create a pull request


---

Jesse Myrberg (jesse.myrberg@gmail.com)