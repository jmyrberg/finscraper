#!/bin/sh

conda activate finscraper && \
rm -rf dist/ &&\
python setup.py sdist && \
twine upload dist/*