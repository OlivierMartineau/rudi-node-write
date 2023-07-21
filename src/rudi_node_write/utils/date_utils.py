from datetime import datetime
from re import compile
from typing import Literal

REGEX_ISO_FULL_DATE = compile(
    r"^([+-]?[1-9]\d{3})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12]\d)T(2[0-3]|[01]\d):([0-5]\d):([0-5]\d)(?:\.(\d{3}))?("
    r"?:Z|[+-](?:1[0-2]|0\d):[03]0)$"
)

REGEX_RANDOM_DATE = compile(
    r"^([1-9]\d{3})(?:[-./ ]?(1[0-2]|0[1-9])(?:[-./ ]?(3[01]|0[1-9]|[12]\d)(?:[-T ](2[0-3]|[01]\d)[.:hH](["
    r"0-5]\d)(?:[.:mM](?:([0-5]\d)[sS]?(?:\.(\d{3})(\d{3})?)?(?:Z|([+-])(1[0-2]|0\d)(?::([03]0))?)?)?)?)?)?)?$"
)

TimeSpec = Literal["seconds", "milliseconds", "microseconds"]


def time_epoch_s(delay_s: int = 0):
    return int(datetime.timestamp(datetime.now())) + delay_s


def time_epoch_ms(delay_ms: int = 0):
    return int(1000 * datetime.timestamp(datetime.now())) + delay_ms


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_iso(timespec: TimeSpec = "seconds") -> str:
    return datetime.now().astimezone().isoformat(timespec=timespec)


def is_iso_full_date(date_str: str):
    return bool(REGEX_ISO_FULL_DATE.match(date_str))


def parse_date(date_str: str):
    return REGEX_RANDOM_DATE.match(date_str)


def is_date(date_str: str):
    return bool(REGEX_RANDOM_DATE.match(date_str))
