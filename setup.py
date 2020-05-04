import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='finscraper',
    version='0.0.1b',
    license='MIT',
    description='Web scraping API for Finnish websites',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Jesse Myrberg',
    author_email='jesse.myrberg@gmail.com',
    url='https://github.com/jmyrberg/finscraper',
    keywords=['web', 'scraping', 'finnish'],
    install_requires=[
        'pandas>=1.0.3',
        'scrapy>=2.1.0'
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ]
)