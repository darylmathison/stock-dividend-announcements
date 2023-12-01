import datetime
import uuid

from botocore.exceptions import ClientError
import dateutil
import logging
from decimal import Decimal
import collections
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

Announcement = collections.namedtuple("Announcement", ("ex_dividend_date", "ticker", "pay_date", "cash_amount"))


class TableWrapper:
    def __init__(self, table):
        self.table = table

    def add_announcement(self, announcement: Announcement):
        try:
            data_to_send = self._convert_data(announcement)
            logger.info("data to save %s", data_to_send)
            self.table.put_item(Item=data_to_send)
        except ClientError as err:
            logger.error(
                "Couldn't add announcement %s to table %s. Here's why: %s: %s",
                announcement.ex_dividend_date, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def how_many_left(self):
        try:
            today = datetime.datetime.now()
            today_timestamp = Decimal(str(today.timestamp()))

            # Query the table
            response = self.table.batch_get_item(
                RequestItems={
                    'dividend_announcements': {
                        'Keys': [
                            {
                                'ex_dividend_date': today_timestamp
                            }
                        ]
                    }
                }
            )

            # The response will contain the items that match the condition
            items = response['Items']
            return len(items)
        except ClientError as err:
            logger.error(
                "Couldn't find latest announcements to table %s. Here's why: %s: %s",
                self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def _convert_data(self, announcement: Announcement):

        converted_date = dateutil.parser.parse(announcement.ex_dividend_datee)
        converted_date = str(converted_date.timestamp())
        return {
            "id": uuid.uuid4(),
            "ex_dividend_date": Decimal(converted_date),
            "ticker": announcement.ticker,
            "pay_date": announcement.pay_date,
            "cash_amount": Decimal(announcement.cash_amount)
        }
