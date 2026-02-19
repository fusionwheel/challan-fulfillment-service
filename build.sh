#!/bin/bash
set -e

rm -rf dist build
python setup.py build_ext --build-lib dist

cp main.py fulfillment.py sms_worker.py requirements.txt run.sh dist/
cp .env dist/
mkdir -p dist/.svc/
cp .svc/* dist/.svc/
find dist -type d -exec touch {}/__init__.py \;

cd dist
python -c "from challan_workflow.services import utils; print('Build verified OK')"
cd ..
