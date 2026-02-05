#!/bin/bash
set -e

rm -rf dist build
python setup.py build_ext --build-lib dist

cp main.py fulfillment.py requirements.txt dist/
find dist -type d -exec touch {}/__init__.py \;

cd dist
python -c "from workflow.services import utils; print('Build verified OK')"
cd ..

rm -rf dist build