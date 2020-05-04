# finscraper

The library provides an easy-to-use API for fetching data from various Finnish websites, including:

| Website     | URL               | Type         | Class                          |
| ----------- | ----------------- | ------------ | ------------------------------ |
| IltaSanomat | https://www.is.fi | News article | `finscraper.spiders.ISArticle` |


## Installation

`pip install finscraper`


## Quickstart

Fetch 10 news articles as a pandas DataFrame from IltaSanomat:

```python
from finscraper.spiders import ISArticle

spider = ISArticle(category='ulkomaat').scrape(10)

articles = spider.get()
```

Save and load spider

```python
spider_dir = spider.save()

loaded_spider = ISArticle.load(spider_dir)

# Scrape 10 more articles and get all 20 articles scraped so far
articles = loaded_spider.scrape(10).get()
```

## Documentation

More thorough documentation is to be made, but meanwhile you may utilize the *help* -function to figure out the parameters, such as:

```python
help(ISArticle)
```

## Contributing

Web scrapers tend to break quite easily. Unfortunately, I can't make a promise to keep this repository up-to-date all by myself, and thus I invite you to make a pull request against the *dev* branch when a spider breaks.

---

Jesse Myrberg (jesse.myrberg@gmail.com)
