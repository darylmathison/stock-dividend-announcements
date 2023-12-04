import datetime
import logging
import time

import dateutil.parser
import requests

from stock_news_gathering import config


def get_stocks(the_day: datetime.datetime, settings: config.Config):
    repeat = True
    size = 0
    date = (the_day + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    uri = settings.uri.format(apikey=settings.apikey, date=date)
    while repeat:
        r = requests.get(uri).json()
        time.sleep(60/5)
        if 'next_url' in r:
            uri = r['next_url'] + '&apiKey=' + settings.apikey
            repeat = True
        else:
            repeat = False
        if 'results' in r:
            size += len(r['results'])
            logging.info(f"size: {size}, ex_dividend_date: {r['results'][-1]['ex_dividend_date']}")
            for asset in r['results']:
                if asset['currency'] == 'USD':
                    yield asset


def handle(event, context):
    logging.getLogger().setLevel(logging.INFO)
    settings = config.Config()
    start = datetime.datetime.now()
    end = start + datetime.timedelta(weeks=1)
    dividends = []
    for asset in get_stocks(start, settings):
        if dateutil.parser.parse(asset['ex_dividend_date']).date() <= end.date():
            dividends.append(asset)
        else:
            break

    return dividends


if __name__ == '__main__':
    print(handle(None, None))
