import pytest

from rudi_node_write.rudi_types.rudi_meta_misc import RudiDatasetSize, RudiDataTemporalSpread, RudiMetadataInfo
from rudi_node_write.utils.type_date import Date
from rudi_node_write.utils.typing_utils import is_type


def test_RudiDatasetSize():
    data_size: RudiDatasetSize = RudiDatasetSize.from_json({"number_of_records": 4, "number_of_fields": 5})  # type: ignore
    assert isinstance(data_size, RudiDatasetSize)
    assert data_size.number_of_records == 4
    assert data_size.number_of_fields == 5

    assert RudiDatasetSize.from_json(None) is None
    with pytest.raises(TypeError):
        RudiDatasetSize.from_json(4)


def test_RudiDataTemporalSpread():
    period = RudiDataTemporalSpread.from_json(
        {"start_date": "2023-06-12T15:40:11+02:00", "end_date": "2023-06-13T11:43:16+02:00"}
    )
    assert period is not None
    assert period.start_date == Date("2023-06-12T15:40:11+02:00")
    assert period.end_date == Date("2023-06-13T11:43:16+02:00")
    assert RudiDataTemporalSpread.from_json(None) is None
    with pytest.raises(ValueError):
        RudiDataTemporalSpread.from_json(
            {"start_date": "2023-06-12T15:40:11+02:00", "end_date": "2022-06-13T11:43:16+02:00"}
        )
    with pytest.raises(ValueError, match="Input argument 'start_date' should not be null"):
        RudiDataTemporalSpread(None)  # type: ignore


META_INFO = {  # pragma: no cover
    "api_version": "1.3.2",
    "metadata_dates": {"created": "2023-04-12T09:39:28.666+00:00", "updated": "2023-04-12T09:39:28.696+00:00"},
    "metadata_provider": {
        "organization_id": "44f5ac9d-34d6-44d0-99a9-0496654bde5c",
        "organization_name": "Breitenberg - Legros",
        "organization_address": "425 Hickle Crest, Duluth",
        "collection_tag": "rudi-test",
    },
    "metadata_contacts": [
        {
            "contact_id": "f275bed9-6b62-43f1-b617-a392896a617c",
            "contact_name": "Sherri Dickinson",
            "email": "sherri.dickinson@irisa.fr",
            "collection_tag": "rudi-test",
        }
    ],
}


def test_RudiMetadataInfo():
    meta_info = RudiMetadataInfo.from_json(META_INFO)
    assert meta_info.api_version == "1.3.2"
    assert RudiMetadataInfo.from_json({"api_version": "1.3.2"}).metadata_dates.created > "2023.07"
    assert (
        RudiMetadataInfo.from_json(
            {
                "api_version": "1.3.2",
                "metadata_contacts": {
                    "contact_id": "f275bed9-6b62-43f1-b617-a392896a617c",
                    "contact_name": "Sherri Dickinson",
                    "email": "sherri.dickinson@irisa.fr",
                    "collection_tag": "rudi-test",
                },
            }
        ).metadata_dates.created
        > "2023.07"
    )
    with pytest.raises(TypeError):
        RudiMetadataInfo.from_json(
            {
                "api_version": "1.3.2",
                "metadata_contacts": "Sherri Dickinson",
            }
        )
