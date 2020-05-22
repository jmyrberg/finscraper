************
Installation
************

You can install finscraper and its dependencies from PyPi with:

.. code-block:: python

    pip install finscraper

To enjoy all the spiders of the library, install
`Google Chrome <https://www.google.com/chrome/>`_, which is used for
rendering Javascript on some websites.

.. note::
    Under the hood, finscraper uses `Scrapy <https://docs.scrapy.org/en/latest>`_ 
    for web scraping, and `Selenium <https://selenium-python.readthedocs.io>`_
    together with `Chrome <https://www.google.com/chrome/>`_ and
    `ChromeDriver <https://chromedriver.chromium.org>`_ for Javascript rendering.
    finscraper tries to find and download a suitable driver for your operating system
    automatically, but in case of issues, you may do this manually as well. 

    In case of issues, please check the installation details of the core dependencies:

    * `Scrapy <https://docs.scrapy.org/en/latest/intro/install.html>`_

    * `Selenium <https://selenium-python.readthedocs.io>`_

    * `ChromeDriver <https://chromedriver.chromium.org>`_


