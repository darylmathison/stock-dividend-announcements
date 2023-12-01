import json

import requests
import time
import datetime
import logging
from stock_news_gathering import config
import dateutil.parser


def get_stocks(the_day: datetime.datetime, settings: config.Config):
    repeat = True
    date = the_day.strftime("%Y-%m-%d")
    uri = settings.uri.format(apikey=settings.apikey, date=date)
    while repeat:
        r = requests.get(uri).json()
        time.sleep(0.25)
        if 'next_url' in r:
            uri = r['next_url'] + '&apiKey=' + settings.apikey
        else:
            repeat = False
        if 'results' in r:
            for asset in r['results']:
                if asset['currency'] == 'USD':
                    yield asset


def handle(event, context):
    logging.getLogger().setLevel(logging.INFO)
    settings = config.Config()
    start = datetime.datetime.now()
    end = start + datetime.timedelta(days=30)
    dividends = [asset for asset in get_stocks(start, settings) if
                 dateutil.parser.parse(asset['ex_dividend_date']) <= end]
    return json.dumps(dividends)


if __name__ == '__main__':
    print(handle(None, None))
