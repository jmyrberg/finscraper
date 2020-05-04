from distutils.core import setup


setup(
    name='finscraper',
    packages=['finscraper'],
    version='0.1.0-alpha',
    license='MIT',
    description='Web scraping API for Finnish websites',
    author='Jesse Myrberg',
    author_email='jesse.myrberg@gmail.com',
    url='https://github.com/jmyrberg/finscraper',
    download_url='https://github.com/user/jmyrberg/archive/v0.1.0-alpha.tar.gz',
    keywords=['web', 'scraping', 'finnish'],
    install_requires=[
        'pandas>=1.0.3',
        'scrapy>=2.1.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
)