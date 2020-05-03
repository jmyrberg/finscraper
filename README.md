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


## Development

Web scrapers break when the formatting of websites change, which may happen quite often **often**! Unfortunately, I can't promise being able to keep this repository always up-to-date, but you're always welcome to make a pull request, when a spider stops working. Thus, I encourage you to have a look at the spiders at [finscraper/scrapy_spiders -module](finscraper/scrapy_spiders) and modify the xpaths to correspond to the latest version of the website to be scraped.

At minimum, I hope that this repository will provide you some basic information on how you can build a spider on your own. 


---

Jesse Myrberg (jesse.myrberg@gmail.com)