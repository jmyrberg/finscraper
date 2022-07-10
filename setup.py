import setuptools


with open('README.md', 'r') as f:
    long_description = f.read()

with open('VERSION', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name='finscraper',
    version=version,
    license='MIT',
    description='Web scraping API for Finnish websites',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Jesse Myrberg',
    author_email='jesse.myrberg@gmail.com',
    url='https://github.com/jmyrberg/finscraper',
    keywords=['web', 'scraping', 'finnish', 'nlp'],
    install_requires=[
        'attrs>=21.4.0',
        'pandas>=1.4.0',
        'selenium>=4.3.0',
        'scrapy>=2.6.1',
        'tqdm>=4.64.0',
        'webdriver-manager>=2.4.0'
    ],
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Framework :: Scrapy',
        'Natural Language :: Finnish',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License'
    ]
)
