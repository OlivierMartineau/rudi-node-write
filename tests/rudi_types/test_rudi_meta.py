from copy import deepcopy

import pytest

from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.utils.list_utils import is_list

RUDI_META = {
    "global_id": "e8b513a1-8d0e-4824-9a7d-1087fc66af9d",
    "resource_title": "Synergistic system-worthy encoding",
    "synopsis": [{"lang": "fr", "text": "Tasty incentivize bricks-and-clicks systems"}],
    "summary": [
        {
            "lang": "fr",
            "text": "I'll index the wireless GB hard drive, that should capacitor the JSON firewall! You can't index the interface without programming the neural RSS application! Aliquid quasi earum. Debitis possimus sit aut voluptatum ut nostrum. At corrupti optio pariatur corrupti autem ut.",
        }
    ],
    "theme": "education",
    "keywords": ["Compte administratif", "Santé"],
    "producer": {
        "organization_id": "fa557d8b-0892-47aa-809b-6da59081e0aa",
        "organization_name": "Gusikowski LLC",
        "organization_address": "4974 Altenwerth Wells, Brownville",
        "collection_tag": "rudi-test",
    },
    "contacts": [
        {
            "contact_id": "f275bed9-6b62-43f1-b617-a392896a617c",
            "contact_name": "Sherri Dickinson",
            "email": "sherri.dickinson@irisa.fr",
            "collection_tag": "rudi-test",
        },
        {
            "contact_id": "6371498a-f9df-46a5-b4e6-9dec377ada2b",
            "contact_name": "Wanda Torphy",
            "email": "wanda.torphy@irisa.fr",
            "collection_tag": "rudi-test",
        },
    ],
    "available_formats": [
        {
            "media_type": "FILE",
            "media_id": "9de29661-a53a-4eea-835c-b0799e181636",
            "media_name": "Synergistic system-worthy encoding.json",
            "connector": {
                "url": "https://shared-rudi.aqmo.org/media/9de29661-a53a-4eea-835c-b0799e181636",
                "interface_contract": "dwnl",
            },
            "file_type": "application/json",
            "file_size": 59016,
            "checksum": {"algo": "MD5", "hash": "4c9ee0f14e835927a1bbafde0eb89fb3"},
            "media_dates": {"created": "2023-03-03T11:15:57.226+00:00", "updated": "2023-03-03T11:15:57.226+00:00"},
            "file_storage_status": "missing",
            "file_status_update": "2023-03-03T11:15:57.232+00:00",
            "collection_tag": "rudi-test",
        }
    ],
    "dataset_dates": {
        "created": "2023-04-12T02:00:38+00:00",
        "updated": "2023-04-12T02:00:38+00:00",
        "published": "2023-04-12T09:39:28.562+00:00",
    },
    "dataset_size": {"number_of_records": 45},
    "storage_status": "pending",
    "access_condition": {
        "licence": {"licence_label": "etalab-1.0", "licence_type": "STANDARD"},
        "confidentiality": {"restricted_access": False, "gdpr_sensitive": False},
    },
    "metadata_info": {
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
    },
    "resource_languages": ["fr"],
    "temporal_spread": {"start_date": "2022-11-07T06:55:11+00:00"},
    "geography": {
        "bounding_box": {
            "south_latitude": -48.112834,
            "north_latitude": 48.112834,
            "west_longitude": -1.677803,
            "east_longitude": 1.677803,
        },
        "geographic_distribution": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-1.677803, -48.112834],
                    [1.677803, -48.112834],
                    [1.677803, 48.112834],
                    [-1.677803, 48.112834],
                    [-1.677803, -48.112834],
                ]
            ],
            "bbox": [-1.677803, -48.112834, 1.677803, 48.112834],
        },
        "projection": "WGS 84 (EPSG:4326)",
    },
    "collection_tag": "rudi-test",
}


def test_RudiMetadata():
    assert RudiMetadata.from_json(RUDI_META).global_id == RUDI_META["global_id"]

    rudi_meta_test_kw = deepcopy(RUDI_META)
    rudi_meta_test_kw["keywords"] = "1,2,3"
    assert RudiMetadata.from_json(rudi_meta_test_kw).keywords == ["1", "2", "3"]

    rudi_meta_test_kw["keywords"] = 1
    with pytest.raises(TypeError):
        RudiMetadata.from_json(rudi_meta_test_kw)

    rudi_meta_test_cont = deepcopy(RUDI_META)
    rudi_meta_test_cont["contacts"] = {
        "contact_id": "f275bed9-6b62-43f1-b617-a392896a617c",
        "contact_name": "Sherri Dickinson",
        "email": "sherri.dickinson@irisa.fr",
    }
    assert is_list(RudiMetadata.from_json(rudi_meta_test_cont).contacts)
    rudi_meta_test_cont["contacts"] = 4
    with pytest.raises(TypeError):
        RudiMetadata.from_json(rudi_meta_test_cont)


def test_RudiMetadata_get_number_of_records():
    assert RudiMetadata.from_json(RUDI_META).get_number_of_records() == 45


def test_RudiMetadata_get_licence():
    assert RudiMetadata.from_json(RUDI_META).get_licence().licence_type in ["STANDARD", "CUSTOM"]
