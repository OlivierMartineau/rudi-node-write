import pytest

from rudi_node_write.utils.type_date import REGEX_ISO_FULL_DATE, REGEX_RANDOM_DATE, Date


def test_Date_init():
    for date_str in [
        "2020",
        "2020-01",
        "202001",
        "2020-01-01",
        "2020-01-01 00:00",
        "2020-01-01 00:00:00",
        "2020-01-01T00:00:00",
        "2020-01-01T00:00:00Z",
        "2020-01-01T00:00:00.000",
        "2020-01-01T00:00:00.000Z",
        "20200101",
    ]:
        date = Date(date_str)
        assert date
        assert date == "2020"

    for date_ok in [
        "2023-01-01 20:23:34.041456+02:00",
        "2023-01-01T20:23:34.041456+02:00",
        "2023-01-01T20:23:34.041456Z",
        "2023-01-01T20:23:34.041Z",
        "2023-01-01T20:23:34Z",
        "2023-01-01 20:23",
        "2023-01-01T20:23",
        "2023-01-01",
        "2023-01",
        "2023",
        2023,
        None,
    ]:
        assert Date(date_ok)

    for date_ko in [
        "2023-01-01T20:23Z",
        "2023-01-01T20Z",
    ]:
        with pytest.raises(ValueError):
            Date(date_ko)


def test_Date_class_name():
    assert Date(2023).class_name == "Date"


def test_Date_iso():
    assert Date(2023).iso == "2023-01-01T00:00:00+00:00"


def test_Date_to_json_str():
    assert Date(2023).to_json_str() == "2023-01-01T00:00:00+00:00"


def test_Date_to_json():
    assert Date(2023).to_json() == "2023-01-01T00:00:00+00:00"


def test_Date_from_json():
    assert Date.from_json("2023-01-01T00:00:00+00:00") == "2023-01-01T00:00:00+00:00"


def test_Date_from_str():
    assert Date.from_str("2023-01-01 20:23:34.041456+02:00") == Date("2023-01-01 19:23:34.041456+01:00")
    assert Date.from_str("2023-01-01 20:23:34.041456+02:00") == "2023-01-01 19:23:34.041456+01:00"
    assert Date.from_str("2023-01-01 20:23:34.041456+02:00") == "2023-01-01 18:23:34.041456"
    assert Date.from_str(default_date="2023-01-01T18:23:34.041456Z") == "2023-01-01 18:23:34.041456"
    assert Date.from_str() is None

    with pytest.raises(ValueError):
        Date.from_str(is_none_accepted=False)


def test_Date_str():
    assert str(Date(2023)) == "2023-01-01T00:00:00+00:00"
    assert Date(2023) == "2023-01-01T00:00:00"
    assert Date(2023) != "2023-01-01T00:00:00.001"
    assert Date(2023) != ["2023-01-01T00:00:00.001"]
    assert Date(2023) > Date(2022)
    assert Date(2023) > "2022"
    assert Date(2023) > 2022
    assert 2023 > Date(2022)

    with pytest.raises(ValueError):
        Date(2023) > [2022]


def test_now_epoch_s():
    now_s = Date.time_epoch_s()
    # print(now_s)
    assert 2683040158 > now_s > 1683040158
    assert 2683040158 > Date.time_epoch_s(10) > 1683040158


def test_now_epoch_ms():
    now_ms = Date.time_epoch_ms()
    # print(now_ms)
    assert 21683040158094 > now_ms > 1683040158094
    assert 21683040158094 > Date.time_epoch_ms(10) > 1683040158094


def test_now_str():
    date_now = Date.now_str()
    assert date_now.startswith("20")
    assert REGEX_RANDOM_DATE.match(date_now)


def test_now():
    date_now = f"{Date.now()}"
    assert date_now.startswith("20")
    assert REGEX_RANDOM_DATE.match(date_now)


def test_now_iso():
    date_now = f"{Date.now_iso()}"
    assert REGEX_ISO_FULL_DATE.match(date_now)


def test_parse_date():
    date_now = Date.now_iso_str()
    assert Date.parse_date_str(date_now)


def test_is_date():
    assert Date.is_date_str(Date.now_iso_str())
    assert Date.is_date_str(Date.now_str())
    assert Date.is_date_str("2023")
    assert Date.is_date_str("2023-07-13")
    assert Date.is_date_str("2023/07/13")
    assert Date.is_date_str("2023/07/13 10:50")
    assert Date.is_date_str("2023/07/13 10:50:06")


def test_is_iso_full_date():
    assert Date.is_iso_full_date_str("2019-05-02T11:30:57+00:00")
    assert Date.is_iso_full_date_str("2019-05-02T11:30:57-10:00")
    assert Date.is_iso_full_date_str("2019-05-02T11:30:57Z")
    assert not Date.is_iso_full_date_str("201-05-02T11:30:57Z")
