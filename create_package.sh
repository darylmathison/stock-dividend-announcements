#!/bin/bash

FILENAME="dividend_announcements.zip"
S3_BUCKET="function-bucket-drm"

rm -rf package
mkdir package

pip install -r requirements.txt --target ./package

cd package
zip -r ../$FILENAME .

cd ..
zip $FILENAME stock_news_gathering/*.py default.json

aws s3 cp $FILENAME s3://$S3_BUCKET/$FILENAME
aws lambda update-function-code --function-name app-load-dividend-announcements --s3-bucket $S3_BUCKET --s3-key $FILENAME > /dev/null
aws lambda update-function-code --function-name app-dividends --s3-bucket $S3_BUCKET --s3-key $FILENAME > /dev/null
aws s3 rm s3://$S3_BUCKET/$FILENAME
rm $FILENAME
