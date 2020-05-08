
*******************
Examples
*******************


Basic usage
===========

Fetch 10 articles from Iltalehti with :class:`ILArticle <finscraper.spiders.ILArticle>`
by using :class:`scrape <finscraper.spiders.ILArticle.scrape>` and
:class:`get <finscraper.spiders.ILArticle.get>`:

.. code-block:: python
   
   from finscraper.spiders import ILArticle

   spider = ILArticle()
   spider.scrape(10)
   articles = spider.get()


Use :class:`save <finscraper.spiders.ILArticle.save>` and 
:class:`load <finscraper.spiders.ILArticle.load>` to continue scraping:

.. code-block:: python

    save_dir = spider.save()
    spider = ILArticle.load(save_dir)
    articles = spider.scrape(10).get()  # 20 articles in total


The spider will create a temporary directory that can be removed via
``spider.clear()``.


Advanced usage
==============

Because `Scrapy <https://scrapy.org/>`_ is under the hood, all the 
`settings available <https://docs.scrapy.org/en/latest/topics/settings.html/>`_ for Scrapy 
can be passed into :class:`scrape <finscraper.spiders.ILArticle.scrape>` -method
within the *settings* -argument. For example, to limit the number of concurrent requests per domain:

.. code-block:: python
   
   from finscraper.spiders import ILArticle

   settings = {'CONCURRENT_REQUESTS_PER_DOMAIN': 1}

   spider = ILArticle().scrape(10, settings=settings)
   articles = spider.get()
