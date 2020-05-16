*******
Spiders
*******


Classes
--------------

The main interface of finscraper is the :class:`Spider API <finscraper.spiders>`,
which aims to make web scraping as easy as possible. Each class represents specific
content that can be scraped with it, and no more.

.. note::
    If you need more flexibility in terms of the content to be scraped, you might want to 
    implement your spiders with the lower level library `Scrapy <https://docs.scrapy.org>`_.


Parameters
-----------------

Some spiders may have their own parameters which typically describe the content to be
crawled. All spiders also have common parameters, such as ``jobdir``, ``log_level`` and ``progress_bar``.
These are mainly for controlling the verbosity and working directories of the spiders.


Scraping
--------

The :class:`scrape <finscraper.wrappers._SpiderWrapper.scrape>` -method starts making
HTTP requests and parsing desired items. In most cases, the spider keeps track of already
visited pages to avoid fetching the same content more than once.

The workflow of a typical spider in pseudocode would look something like:

.. code-block:: none

    1. Start from a certain URL

    2. While there are links to follow
        a) Find new links to follow
        b) Find links with desired content and parse them
        c) Stop, if a condition is met (e.g. number of scraped items)

.. Warning::
    
    Some websites try to prevent bots from crawling them, which could lead to
    a **ban of your IP address**. By default, finscraper obeys website-specific
    crawling rules (`robots.txt <https://en.wikipedia.org/wiki/Robots_exclusion_standard>`_)
    to avoid this.


Results
-------

Scraped items and the state of the spider are saved into your hard disk as
defined by ``jobdir``. By default, this is your temporary directory.

The items are saved in *jsonline* -format into a single file at ``spider.items_save_path``,
and when calling the :class:`get <finscraper.spiders.ILArticle.get>` -method, the data
is read from the disk and returned as a `pandas.DataFrame <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_.


Save & load
--------------------

You may :class:`save <finscraper.spiders.ILArticle.save>` and :class:`load <finscraper.spiders.ILArticle.load>`
spiders to continue scraping later on. Moreover, you may use :class:`clear <finscraper.spiders.ILArticle.clear>` 
-method to reset the state and scraped items of an existing spider.
