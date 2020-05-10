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
        'pandas>=1.0.3',
        'selenium>=3.141.0',
        'scrapy>=2.1.0',
        'tqdm>=4.46.0',
        'webdriver-manager>=2.4.0',
        'attrs>=19.2.0'
    ],
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ]
)
