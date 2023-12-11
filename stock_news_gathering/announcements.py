import datetime
import logging
import time

import dateutil.parser
import requests

from stock_news_gathering import config
from stock_news_gathering.db import Announcement, TableWrapper


def get_stocks(the_day: datetime.datetime, settings: config.Config):
    repeat = True
    size = 0
    date = (the_day + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    uri = settings.uri.format(apikey=settings.apikey, date=date)
    while repeat:
        try:
            r = requests.get(uri)
            r.raise_for_status()
            r = r.json()
            if size > 0:
                time.sleep(60 / 5)
            if "next_url" in r:
                uri = r["next_url"] + "&apiKey=" + settings.apikey
                repeat = True
            else:
                repeat = False
            if "results" in r:
                size += len(r["results"])
                logging.info(
                    f"size: {size}, ex_dividend_date: {r['results'][-1]['ex_dividend_date']}"
                )
                for asset in r["results"]:
                    if asset["currency"] == "USD":
                        yield asset
        except requests.exceptions.HTTPError as err:
            logging.info(err)
            time.sleep(30)
            repeat = True
        except Exception as e:
            logging.error(e)
            repeat = False


def save_announcements(event, context):
    settings = config.Config()
    table = TableWrapper(settings.table)
    start = datetime.datetime.now()
    end = start + datetime.timedelta(weeks=2)

    last_date = table.get_last_date(start, end)
    if last_date.date() < (end + datetime.timedelta(days=1)).date():
        logging.info("last date stored is %s", last_date)

        for asset in get_stocks(last_date, settings):
            if dateutil.parser.parse(asset["ex_dividend_date"]).date() <= end.date():
                table.add_announcement(Announcement(**asset))
            else:
                return "OK"
    else:
        logging.info("date exists")
        return "OK"


def get_announcements(event, context):
    settings = config.Config()
    table = TableWrapper(settings.table)
    start = datetime.datetime.now()
    end = start + datetime.timedelta(weeks=2)

    announcements = table.get_announcements(start, end)
    if announcements:
        return [announcements.to_dict() for announcements in announcements]


if __name__ == "__main__":
    print(get_announcements(None, None))
