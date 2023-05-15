from datetime import datetime, timezone, timedelta
from re import compile
from typing import Literal

REGEX_ISO_FULL_DATE = compile(
    r'^([+-]?[1-9]\d{3})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12]\d)T(2[0-3]|[01]\d):([0-5]\d):([0-5]\d)(?:\.(\d{3}))?('
    r'?:Z|[+-](?:1[0-2]|0\d):[03]0)$')

REGEX_RANDOM_DATE = compile(
    r'^([1-9]\d{3})(?:[-./ ](1[0-2]|0[1-9])(?:[-./ ](3[01]|0[1-9]|[12]\d)[-T ](2[0-3]|[01]\d)[.:hH]([0-5]\d)[.:mM](['
    r'0-5]\d)[sS]?(?:\.(\d{3})(\d{3})?)?(?:Z|(?:([+-])(1[0-2]|0\d)(?::([03]0))?))?)?)?$')

TimeSpec = Literal['seconds', 'milliseconds', 'microseconds']


def is_iso_full_date(date_str: str):
    return bool(REGEX_ISO_FULL_DATE.match(date_str))


def is_date(date_str: str):
    return REGEX_RANDOM_DATE.match(date_str)


def to_int(val: str | None, default_val: int = 0):
    return int(val if val else default_val)


def ensure_date_str(date_str: str, default_date: str = None, is_none_accepted: bool = True):
    if not date_str:
        if default_date:
            return default_date
        elif is_none_accepted:
            return None
        else:
            raise ValueError('empty value not accepted')
    reg_date = is_date(date_str)
    if not reg_date:
        raise ValueError(f"this is not a valid date: '{date_str}'")
    (year, month, day, hour, minute, second, ms, us, tz_sign, tz_hour, tz_minute) = reg_date.groups()
    tz_info = timezone(-1 if tz_sign == '-' else 1 * timedelta(hours=to_int(tz_hour), minutes=to_int(tz_minute)))
    timespec = 'microseconds' if us else 'milliseconds' if ms else 'seconds'
    date_obj = datetime(to_int(year), to_int(month, 1), to_int(day, 1), to_int(hour), to_int(minute), to_int(second),
                        to_int(ms) * 1000 + to_int(us), tzinfo=tz_info)
    return date_obj.isoformat(timespec=timespec)


def time_epoch_s(delay_s: int = 0):
    return int(datetime.timestamp(datetime.now())) + delay_s


def time_epoch_ms(delay_ms: int = 0):
    return int(1000 * datetime.timestamp(datetime.now())) + delay_ms


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def nowISO(timespec: TimeSpec = 'seconds') -> str:
    return datetime.now().astimezone().isoformat(timespec=timespec)


if __name__ == '__main__':
    print('nowISO', nowISO())
    # print('ensure_is_date', ensure_is_date('2023-01-01T20:23:34'))
    date = '2023-01-01 20:23:34.041456+02:00'
    print('str_to_date:', f"'{date}'", '->', f"'{ensure_date_str(date)}'")
