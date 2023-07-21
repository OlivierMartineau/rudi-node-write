from datetime import datetime, timezone, timedelta
from time import time

from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.date_utils import parse_date
from rudi_node_write.utils.str_utils import is_string


class Date(Serializable):
    def __init__(self, date_str: str | int):
        if not is_string(date_str):
            date_str = str(date_str)
        reg_date = parse_date(date_str)
        if not reg_date:
            raise ValueError(f"this is not a valid date: '{date_str}'")
        (
            year,
            month,
            day,
            hour,
            minute,
            second,
            ms,
            us,
            tz_sign,
            tz_hour,
            tz_minute,
        ) = reg_date.groups()

        self.year = self._to_int(year)
        self.month = self._to_int(month, 1)
        self.day = self._to_int(day, 1)
        self.hour = self._to_int(hour)
        self.minute = self._to_int(minute)
        self.second = self._to_int(second)
        self.ms = self._to_int(ms) if ms else None
        self.us = self._to_int(us) if us else None
        self.microseconds = self._to_int(ms) * 1000 + self._to_int(us)
        self.tz_info = timezone(
            -1 if tz_sign == "-" else 1 * timedelta(hours=self._to_int(tz_hour), minutes=self._to_int(tz_minute))
        )
        self.timespec = "microseconds" if self.us else "milliseconds" if self.ms else "seconds"

        self._py_date = None
        self._iso_date = None

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def datetime(self) -> datetime:
        if self._py_date is None:
            self._py_date = datetime(
                year=self.year,
                month=self.month,
                day=self.day,
                hour=self.hour,
                minute=self.minute,
                second=self.second,
                microsecond=self.microseconds,
                tzinfo=self.tz_info,
            )
        return self._py_date

    @property
    def iso(self) -> str:
        if self._iso_date is None:
            self._iso_date = self.datetime.isoformat(timespec=self.timespec)
        return self._iso_date

    def __str__(self) -> str:
        return self.iso

    def __eq__(self, other):
        if not isinstance(other, (Date, str, int)):
            return False
        other_date = Date(other) if is_string(other) else other
        return self.datetime == other_date.datetime

    def __gt__(self, other):
        if isinstance(other, Date):
            other_date = other
        elif isinstance(other, (int, str)):
            other_date = Date(other)
        else:
            raise ValueError(f"Cannot compare a date and a '{other.__class__.__name__}' (got '{other}')")
        return self.datetime > other_date.datetime

    def __lt__(self, other):
        return not self > other

    def to_json_str(self, **kwargs) -> str:
        return self.iso

    def to_json(self, keep_nones: bool = False) -> str:
        return self.iso

    @staticmethod
    def _to_int(val: str | None, default_val: int = 0):
        return int(val if val else default_val)

    @staticmethod
    def from_str(date_str: str = None, default_date: str = None, is_none_accepted: bool = True):
        if date_str is None:
            if default_date:
                return Date(default_date)
            elif is_none_accepted:
                return None
            else:
                raise ValueError("empty value not accepted")
        return Date(date_str)

    @staticmethod
    def from_json(date_str: str):
        return Date.from_str(date_str)


if __name__ == "__main__":  # pragma: no cover
    tests = "date_tests"
    begin = time()

    date = "2023-01-01 20:23:34.041456+02:00"
    print(tests, "str_to_date:", f"'{date}'", "->", f"'{Date(date)}'")
    print(tests, "==", date == Date(date))
    date_list = [
        "2020",
        "2020-01",
        "202001",
        "2020-01-01",
        "2020-01-01 00:00",
        "2020-01-01 00:00:00",
        "2020-01-01T00:00:00",
        "2020-01-01T00:00:00Z",
        "2020-01-01T00:00:00+00:00",
        "2020-01-01T00:00:00.000Z",
        "2020-01-01T00:00:00.000+00:00",
        "20200101",
    ]
    for str_date in date_list:
        print(tests, f"Date('{str_date}')", Date(str_date))
    for str_date in date_list:
        print(tests, f"2020 == Date('{str_date}') ->", "2020" == Date(str_date))
    print(tests, "exec. time:", time() - begin)
