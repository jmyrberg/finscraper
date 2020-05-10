# finscraper

[![Build Status](https://travis-ci.com/jmyrberg/finscraper.svg?branch=master)](https://travis-ci.com/jmyrberg/finscraper) [![Documentation Status](https://readthedocs.org/projects/finscraper/badge/?version=latest)](https://finscraper.readthedocs.io/en/latest/?badge=latest)

![finscraper cover](https://github.com/jmyrberg/finscraper/blob/master/docs/cover.jpg?raw=true)

The library provides an easy-to-use API for fetching data from various Finnish websites:

| Website     | URL                        | Type         | Spider API class                |
| ----------- | -------------------------- | ------------ | ------------------------------- |
| IltaSanomat | https://www.is.fi          | News article | `finscraper.spiders.ISArticle`  |
| Iltalehti   | https://www.iltalehti.fi   | News article | `finscraper.spiders.ILArticle`  |
| YLE         | https://www.yle.fi/uutiset | News article | `finscraper.spiders.YLEArticle` |

Documentation is available at [https://finscraper.readthedocs.io](https://finscraper.readthedocs.io).


## Installation

`pip install finscraper`


## Quickstart

Fetch 10 news articles as a pandas DataFrame from [IltaSanomat](https://is.fi):

```python
from finscraper.spiders import ISArticle

spider = ISArticle().scrape(10)

articles = spider.get()
```

## Contributing

When websites change, spiders tend to break. I can't make a promise to keep this
repository up-to-date all by myself - pull requests are more than welcome!


---

Jesse Myrberg (jesse.myrberg@gmail.com)
