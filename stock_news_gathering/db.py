import datetime
import logging
from decimal import Decimal

import boto3
import dateutil.parser
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def str_to_decimal(date: str) -> Decimal:
    time = dateutil.parser.parse(date)
    return Decimal(str(time.timestamp()))


def decimal_date_to_str(date: Decimal) -> str:
    date = datetime.datetime.fromtimestamp(float(date))
    return date.strftime("%Y-%m-%d")


class Announcement:
    def __init__(
        self,
        ticker: str,
        ex_dividend_date: str,
        record_date: str,
        pay_date: str,
        cash_amount: str,
        declared_date: str,
        currency: str,
        frequency: str,
        dividend_type: str,
        *args,
        **kwargs,
    ):
        self.symbol = ticker
        self.ex_dividend_date = ex_dividend_date
        self.record_date = record_date
        self.pay_date = pay_date
        self.cash_amount = cash_amount
        self.declared_date = declared_date
        self.currency = currency
        self.frequency = frequency
        self.dividend_type = dividend_type

    @property
    def ex_dividend_decimal(self):
        return str_to_decimal(self.ex_dividend_date)

    @property
    def record_decimal(self):
        return str_to_decimal(self.record_date)

    @property
    def pay_decimal(self):
        return str_to_decimal(self.pay_date)

    @property
    def declared_decimal(self):
        return str_to_decimal(self.declared_date)

    def to_dynamo_db(self):
        return {
            "symbol": self.symbol,
            "ex_dividend_date": self.ex_dividend_decimal,
            "record_date": self.record_decimal,
            "pay_date": self.pay_decimal,
            "cash_amount": str(self.cash_amount),
            "declared_date": self.declared_decimal,
            "currency": self.currency,
            "frequency": str(self.frequency),
            "dividend_type": self.dividend_type,
        }

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "ex_dividend_date": self.ex_dividend_date,
            "record_date": self.record_date,
            "pay_date": self.pay_date,
            "cash_amount": self.cash_amount,
            "declared_date": self.declared_date,
            "currency": self.currency,
            "frequency": self.frequency,
            "dividend_type": self.dividend_type,
        }

    def __str__(self):
        return f"{self.symbol} {self.ex_dividend_date} {self.record_date} {self.pay_date} {self.cash_amount} {self.declared_date} {self.currency} {self.frequency} {self.dividend_type}"

    def __repr__(self):
        return f"Announcement(symbol={self.symbol} ex_dividend_date={self.ex_dividend_date} record_date={self.record_date} pay_date={self.pay_date} cash_amount={self.cash_amount} declared_date={self.declared_date} currency={self.currency} frequency={self.frequency} dividend_type={self.dividend_type})"

    @staticmethod
    def from_dynamo_db(data):
        if "declared_date" in data:
            declared_date = decimal_date_to_str(data["declared_date"])
        else:
            declared_date = ""

        return Announcement(
            data["symbol"],
            decimal_date_to_str(data["ex_dividend_date"]),
            decimal_date_to_str(data["record_date"]),
            decimal_date_to_str(data["pay_date"]),
            data["cash_amount"],
            declared_date,
            data.get("currency", "USD"),
            data.get("frequency", ""),
            data.get("dividend_type", ""),
        )


class TableWrapper:
    def __init__(self, table):
        self.table = boto3.resource("dynamodb").Table(table)

    def add_announcement(self, announcement: Announcement):
        try:
            data_to_send = announcement.to_dynamo_db()
            logger.info("data to save %s", data_to_send)
            self.table.put_item(Item=data_to_send)
        except ClientError as err:
            logger.error(
                "Couldn't add announcement %s to table %s. Here's why: %s: %s",
                announcement.ex_dividend_date,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_announcements(self, start: datetime.datetime, end: datetime.datetime):
        try:
            start_timestamp = Decimal(str(start.timestamp()))
            end_timestamp = Decimal(str(end.timestamp()))

            # Query the table
            response = self.table.scan(
                FilterExpression=Key("ex_dividend_date").between(
                    start_timestamp, end_timestamp
                )
            )

            # The response will contain the items that match the condition
            items = [Announcement.from_dynamo_db(item) for item in response["Items"]]
            while "LastEvaluatedKey" in response:
                response = self.table.scan(
                    FilterExpression=Key("ex_dividend_date").between(
                        start_timestamp, end_timestamp
                    ),
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(
                    Announcement.from_dynamo_db(item) for item in response["Items"]
                )
            return items
        except ClientError as err:
            logger.error(
                "Couldn't find latest announcements to table %s. Here's why: %s: %s",
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_last_date(self, start: datetime.datetime, end: datetime.datetime):
        try:
            start_timestamp = Decimal(str(start.timestamp()))
            end_timestamp = Decimal(str(end.timestamp()))

            # Query the table
            response = self.table.scan(
                FilterExpression=Key("ex_dividend_date").between(
                    start_timestamp, end_timestamp
                )
            )

            # The response will contain the items that match the condition
            items = response["Items"]
            if items:
                last_partition_key = max(items, key=lambda x: x["ex_dividend_date"])
                return datetime.datetime.fromtimestamp(
                    float(last_partition_key["ex_dividend_date"])
                )
            else:
                return start
        except ClientError as err:
            logger.error(
                "Couldn't find latest announcements to table %s. Here's why: %s: %s",
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
