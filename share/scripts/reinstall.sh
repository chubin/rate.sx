#!/usr/bin/env bash

set -e

rm -rf ve/
virtualenv ve
ve/bin/pip3 install -r requirements.txt

cp share/fixes/diagram.py ve/lib/python3.10/site-packages/diagram.py
cp share/fixes/terminaltables.py ve/lib/python3.10/site-packages/terminaltables.py
cp share/fixes/colorclass.py ve/lib/python3.10/site-packages/colorclass.py
