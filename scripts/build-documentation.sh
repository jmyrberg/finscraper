#!/bin/sh

conda activate finscraper && \
rm -rf docs/build && \
sphinx-apidoc -f -o docs/source finscraper && \
rm -rf docs/source/modules.rst && \
sphinx-build -b html docs/source docs/build
# open -a /Applications/Safari.app file:///Users/e103089/Documents/Personal/finscraper/docs/build/index.html