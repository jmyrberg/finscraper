************
Installation
************

You can install finscraper and its dependencies from PyPi with:

.. code-block:: python

    pip install finscraper


Some pages require Javascript rendering before anything is shown to the user.
Moreover, some websites may display the desired content only when rendered in
a proper browser and after scrolling the page.

To simulate this behavior, `Selenium <https://selenium-python.readthedocs.io>`_
together with `ChromeDriver <https://chromedriver.chromium.org>`_ is used.
finscraper tries to find and download a suitable driver for your OS automatically,
but in case of issues, you may do this manually.

In case of issues, please check installation details of the core dependencies:

* `Scrapy <https://docs.scrapy.org/en/latest/intro/install.html>`_

* `Selenium <https://selenium-python.readthedocs.io>`_

* `ChromeDriver <https://chromedriver.chromium.org>`_


