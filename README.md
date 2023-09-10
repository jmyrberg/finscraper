# finscraper

[![Spiders](https://github.com/jmyrberg/finscraper/actions/workflows/spiders.yml/badge.svg)](https://github.com/jmyrberg/finscraper/actions/workflows/spiders.yml)
[![Documentation](https://readthedocs.org/projects/finscraper/badge/?version=latest)](https://finscraper.readthedocs.io/en/latest/?badge=latest)

![finscraper cover](https://github.com/jmyrberg/finscraper/blob/master/docs/cover.jpg?raw=true)

The library provides an easy-to-use API for fetching data from various Finnish websites:

| Website                                                        | Type              | Spider API class   |
|----------------------------------------------------------------|-------------------|--------------------|
| [Ilta-Sanomat](https://www.is.fi)                              | News article      | `ISArticle`        |
| [Iltalehti](https://www.il.fi)                                 | News article      | `ILArticle`        |
| [YLE Uutiset](https://www.yle.fi/uutiset)                      | News article      | `YLEArticle`       |
| [Suomi24](https://keskustelu.suomi24.fi)                       | Discussion thread | `Suomi24Page`      |
| [Muusikoiden.net](https://www.muusikoiden.net)                 | Discussion thread | `MNetPage`         |
| [Vauva](https://www.vauva.fi)                                  | Discussion thread | `VauvaPage`        |
| [Oikotie Asunnot](https://asunnot.oikotie.fi/myytavat-asunnot) | Apartment ad      | `OikotieApartment` |
| [Tori](https://www.tori.fi)                                    | Item deal         | `ToriDeal`         |

Documentation is available at [https://finscraper.readthedocs.io](https://finscraper.readthedocs.io) and [simple online demo here](https://jmyrberg.com/demo-projects/finscraper).


## Installation

`pip install finscraper`


## Quickstart

Fetch 10 news articles as a pandas DataFrame from [Ilta-Sanomat](https://is.fi):

```python
from finscraper.spiders import ISArticle

spider = ISArticle().scrape(10)

articles = spider.get()
```

The API is similar for all the spiders:

![Finscraper in action](https://github.com/jmyrberg/finscraper/blob/master/docs/finscraper.gif)


## Contributing

Please see [CONTRIBUTING.md](https://github.com/jmyrberg/finscraper/blob/master/CONTRIBUTING.md) for more information.


---

Jesse Myrberg (jesse.myrberg@gmail.com)
