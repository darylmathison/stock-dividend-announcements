#!/bin/bash

FILENAME="dividend_announcements.zip"

rm -rf package
mkdir package

pip install -r requirements.txt --target ./package

cd package
zip -r ../$FILENAME .

cd ..
zip $FILENAME stock_news_gathering/*.py default.json
