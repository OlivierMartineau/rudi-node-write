import pytest

from rudi_node_write.utils.type_date import Date


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
