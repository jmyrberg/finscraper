#!/bin/sh

conda activate finscraper && \
python setup.py sdist && \
twine upload dist/*