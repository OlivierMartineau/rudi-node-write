from rudi_node_write.utils.date_utils import (
    time_epoch_s,
    time_epoch_ms,
    is_iso_full_date,
    now,
    REGEX_RANDOM_DATE,
    now_iso,
    REGEX_ISO_FULL_DATE,
    parse_date,
    is_date,
)


def test_now_epoch_s():
    now_s = time_epoch_s()
    # print(now_s)
    assert 2683040158 > now_s > 1683040158
    assert 2683040158 > time_epoch_s(10) > 1683040158


def test_now_epoch_ms():
    now_ms = time_epoch_ms()
    # print(now_ms)
    assert 21683040158094 > now_ms > 1683040158094
    assert 21683040158094 > time_epoch_ms(10) > 1683040158094


def test_now():
    date_now = now()
    assert date_now.startswith("20")
    assert REGEX_RANDOM_DATE.match(date_now)


def test_now_iso():
    date_now = now_iso()
    assert REGEX_ISO_FULL_DATE.match(date_now)


def test_parse_date():
    date_now = now_iso()
    assert parse_date(date_now)


def test_is_date():
    assert is_date(now_iso())
    assert is_date(now())
    assert is_date("2023")
    assert is_date("2023-07-13")
    assert is_date("2023/07/13")
    assert is_date("2023/07/13 10:50")
    assert is_date("2023/07/13 10:50:06")


def test_is_iso_full_date():
    assert is_iso_full_date("2019-05-02T11:30:57+00:00")
    assert is_iso_full_date("2019-05-02T11:30:57-10:00")
    assert is_iso_full_date("2019-05-02T11:30:57Z")
