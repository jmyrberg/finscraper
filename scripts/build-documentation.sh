#!/bin/sh

conda activate finscraper && \
sphinx-apidoc -f -o docs/source finscraper && \
sphinx-build -b html docs/source docs/build && \
open -a /Applications/Safari.app file:///Users/e103089/Documents/Personal/finscraper/docs/build/index.html