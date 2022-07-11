#!/bin/sh

ENV_NAME=finscraper
PYTHON_VERSION=3.10

conda create -y -n $ENV_NAME python=$PYTHON_VERSION &&
conda activate $ENV_NAME &&
conda install pip flake8 jupyter -y &&
pip install -r requirements.txt -r requirements-dev.txt &&
echo "Installation successful"
