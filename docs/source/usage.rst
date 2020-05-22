*****
Usage
*****

Fetch 10 articles from Iltalehti with :class:`ILArticle <finscraper.spiders.ILArticle>`
with the help of :class:`scrape <finscraper.spiders.ILArticle.scrape>` and
:class:`get <finscraper.spiders.ILArticle.get>` -methods:

.. code-block:: python
   
   from finscraper.spiders import ILArticle

   spider = ILArticle()
   spider.scrape(10)
   articles = spider.get()


Use :class:`save <finscraper.spiders.ILArticle.save>` and 
:class:`load <finscraper.spiders.ILArticle.load>` to continue scraping later on:

.. code-block:: python

    save_dir = spider.save()
    spider = ILArticle.load(save_dir)
    articles = spider.scrape(10).get()  # 20 articles in total

Items are fetched into ``spider.jobdir`` -directory which **is destroyed
together with the** ``spider`` **-object unless** :class:`spider.save() <finscraper.spiders.ILArticle.save>`
**have been called**.

Because `Scrapy <https://scrapy.org/>`_ is used under the hood, any of
`its settings <https://docs.scrapy.org/en/latest/topics/settings.html#built-in-settings-reference>`_ 
can be passed into :class:`scrape <finscraper.spiders.ILArticle.scrape>` -method. 
For example, to limit the number of concurrent requests per domain:

.. code-block:: python
   
   from finscraper.spiders import ILArticle

   settings = {'CONCURRENT_REQUESTS_PER_DOMAIN': 1}

   spider = ILArticle().scrape(10, settings=settings)
   articles = spider.get()
