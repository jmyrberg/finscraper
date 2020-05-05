# finscraper

![finscraper cover](docs/cover.jpg)

The library provides an easy-to-use API for fetching data from various Finnish websites:

| Website     | URL                      | Type         | Class                          |
| ----------- | ------------------------ | ------------ | ------------------------------ |
| IltaSanomat | https://www.is.fi        | News article | `finscraper.spiders.ISArticle` |
| Iltalehti   | https://www.iltalehti.fi | News article | `finscraper.spiders.ILArticle` |


## Installation

`pip install finscraper`


## Quickstart

Fetch 10 news articles as pandas DataFrame from IltaSanomat:

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

Proper documentation is still a work in progress, but meanwhile you may utilize the *help* -function, e.g. `help(ISArticle)`.

## Contributing

Web scrapers tend to break quite easily. Unfortunately, I can't make a promise to keep this repository up-to-date all by myself, and thus I invite you to make a pull request against the *dev* branch when a spider breaks.

---

Jesse Myrberg (jesse.myrberg@gmail.com)
