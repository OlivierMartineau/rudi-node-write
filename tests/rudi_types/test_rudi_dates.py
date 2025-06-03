from rudi_node_write.rudi_types.rudi_dates import RudiDates


def test_RudiDates_init():
    rudi_dates = RudiDates()
    assert rudi_dates
    assert rudi_dates.created
    assert rudi_dates.updated == rudi_dates.created
    assert rudi_dates.validated is None
    assert rudi_dates.published is None
    assert rudi_dates.expires is None
    assert rudi_dates.deleted is None

    date_before = "2023-02-10T14:32:06+02:00"
    date_after = "2023-02-10T15:32:06+02:00"
    rudi_dates = RudiDates(created=date_after, updated=date_before)
    assert rudi_dates.created < rudi_dates.updated


def test_RudiDates_from_json():
    date_before = "2023-02-10T14:32:06+02:00"
    date_after = "2023-07-18T11:00:02+02:00"
    dates_json = {"created": date_before, "updated": date_after}
    rudi_dates = RudiDates.from_json(dates_json)
    assert rudi_dates
    assert rudi_dates.created == date_before
    assert rudi_dates.updated == date_after

    assert RudiDates.from_json(None)
