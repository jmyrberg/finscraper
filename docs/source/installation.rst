*******************
Installation
*******************

You can install *finscraper* and its dependencies from PyPi with:

.. code-block:: python

    pip install finscraper


.. Note::

    Some pages require Javascript rendering before anything is shown to the user.
    Moreover, some websites may display the desired content only when rendered in
    a proper browser and after scrolling the page.

    To simulate this behavior, `Selenium <https://selenium-python.readthedocs.io/>`_
    together with `ChromeDriver <https://chromedriver.chromium.org/>`_ is being used.
    This library tries to fetch all dependencies and suitable driver automatically,
    but in case of issues, one may download and install the driver manually as well.

    In case of issues, please check possible details from the installation guides
    of the main dependencies:

    * `Scrapy <https://docs.scrapy.org/en/latest/intro/install.html/>`_

    * `Selenium <https://selenium-python.readthedocs.io/>`_

    * `ChromeDriver <https://chromedriver.chromium.org/>`_


