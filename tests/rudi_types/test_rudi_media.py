from copy import deepcopy
from json import dumps

import pytest
from deepdiff import DeepDiff

from rudi_node_write.rudi_types.rudi_media import (
    RudiMedia,
    RudiMediaFile,
    RudiMediaService,
    RudiMediaConnectorParameter,
    RudiMediaConnectorParameterList,
    RudiMediaConnector,
    RudiChecksum,
)
from rudi_node_write.utils.dict_utils import safe_get_key
from rudi_node_write.utils.err import LiteralUnexpectedValueException
from rudi_node_write.utils.str_utils import is_string

RUDI_FILE = {
    "media_type": "FILE",
    "media_id": "2611547a-42f1-4d7c-b736-2fef5cca30fe",
    "media_name": "unicorn.png",
    "media_caption": "test MediaFile",
    "file_type": "image/png",
    "file_size": 414931,
    "checksum": {"algo": "SHA-256", "hash": "f72d0035896447b55ff27998d6fd8773a68b2770027336c09da2bc6fd67e2dcf"},
    "connector": {
        "url": "https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/2611547a-42f1-4d7c-b736-2fef5cca30fe",
        "interface_contract": "dwnl",
        "connector_parameters": [
            {
                "key": "random key f",
                "value": "random val f",
                "type": "STRING",
                "usage": "test f",
                "accepted_values": ["random val f"],
            }
        ],
    },
    "media_dates": {"created": "2022-01-21T10:40:28.781+00:00", "updated": "2022-01-21T10:40:28.781+00:00"},
    "file_storage_status": "available",
    "file_status_update": "2023-04-14T13:57:15.859+00:00",
}
RUDI_SERVICE = {
    "media_type": "SERVICE",
    "media_id": "e611547a-42f1-4d7c-b736-2fef5cca30fe",
    "media_name": "exports disponibles",
    "media_dates": {"created": "2023-07-18T17:06:42+02:00", "updated": "2023-07-18T17:06:42+02:00"},
    "connector": {
        "url": "https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/qualite-de-service-selon-operateurs-et-axe-de-transport-2g-3g-4g/exports",
        "interface_contract": "external",
        "connector_parameters": [
            {
                "key": "random key s",
                "value": "random val s",
                "type": "STRING",
                "usage": "test s",
                "accepted_values": ["random val s"],
            }
        ],
    },
    "media_caption": "not really, testing MediaService",
    "api_documentation_url": "https://app.swaggerhub.com/apis/OlivierMartineau/RUDI-PRODUCER",
}


def test_RudiMedia_from_json():
    rudi_file = RudiMedia.from_json(RUDI_FILE)
    assert isinstance(rudi_file, RudiMedia)
    assert isinstance(rudi_file, RudiMediaFile)
    assert not DeepDiff(RUDI_FILE, rudi_file.to_json(), ignore_order=True)

    rudi_file_no_interface_contract = deepcopy(RUDI_FILE)
    del rudi_file_no_interface_contract["connector"]["interface_contract"]
    assert RudiMedia.from_json(rudi_file_no_interface_contract).connector.interface_contract == "dwnl"

    rudi_service = RudiMedia.from_json(RUDI_SERVICE)
    assert isinstance(rudi_service, RudiMedia)
    assert isinstance(rudi_service, RudiMediaService)
    assert not DeepDiff(RUDI_SERVICE, rudi_service.to_json(), ignore_order=True)

    rudi_service_no_interface_contract = deepcopy(RUDI_SERVICE)
    del rudi_service_no_interface_contract["connector"]["interface_contract"]
    assert RudiMedia.from_json(rudi_service_no_interface_contract).connector.interface_contract == "external"

    with pytest.raises(NotImplementedError):
        RudiMedia.from_json({"media_type": "Not"})
    with pytest.raises(ValueError):
        RudiMediaService.from_json(RUDI_FILE)
    with pytest.raises(ValueError):
        RudiMediaFile.from_json(RUDI_SERVICE)


def test_RudiMedia_source_url():
    rudi_service = RudiMedia.from_json(RUDI_SERVICE)
    assert rudi_service.source_url == rudi_service.connector.url


def test_RudiMediaFile_to_json():
    rudi_file = RudiMediaFile.from_json(RUDI_FILE)
    rudi_file_json = rudi_file.to_json()
    assert is_string(safe_get_key(rudi_file_json, "connector", "url"))
    assert not DeepDiff(RUDI_FILE, rudi_file_json)


def test_RudiMediaFile_to_json_str():
    rudi_file = RudiMediaFile.from_json(RUDI_FILE)
    assert rudi_file.to_json_str(sort_keys=True) == dumps(RUDI_FILE, sort_keys=True)


def test_RudiMediaService_to_json():
    rudi_service = RudiMediaService.from_json(RUDI_SERVICE)
    rudi_service_json = rudi_service.to_json()
    assert is_string(safe_get_key(rudi_service_json, "connector", "url"))
    assert not DeepDiff(RUDI_SERVICE, rudi_service_json)


def test_RudiMediaService_to_json_str():
    rudi_service = RudiMediaService.from_json(RUDI_SERVICE)
    assert rudi_service.to_json_str(sort_keys=True) == dumps(RUDI_SERVICE, sort_keys=True)


def test_RudiChecksum_from_json():
    valid_checksum_dict = {
        "algo": "SHA-256",
        "hash": "f72d0035896447b55ff27998d6fd8773a68b2770027336c09da2bc6fd67e2dcf",
    }
    rudi_checksum = RudiChecksum.from_json(valid_checksum_dict)
    assert rudi_checksum.algo == "SHA-256"
    assert rudi_checksum.to_json_str() == dumps(valid_checksum_dict)


OK_CP = [
    {
        "key": "random key",
        "value": "random val",
        "type": "str",
        "usage": "test",
        "accepted_values": ["random val"],
    },
    {
        "key": "random key",
        "value": "random val",
        "usage": "test",
        "accepted_values": ["random val"],
    },
    {
        "key": "random key",
        "value": {"e": 1},
        "usage": "test",
        "accepted_values": [{"e": 1}],
    },
]


def test_RudiMediaConnectorParameter_from_json():
    for cp_dict in OK_CP:
        assert RudiMediaConnectorParameter.from_json(cp_dict).value_type == "STRING"
    for not_cp_dict in [
        {
            "key": "random key",
            "value": "type does not match value's",
            "type": "int",
            "usage": "test",
            "accepted_values": ["type does not match value's"],
        },
        {
            "key": "random key",
            "value": "random val",
            "type": "str",
            "usage": "test",
            "accepted_values": ["value is not an accepted value"],
        },
    ]:
        with pytest.raises(ValueError):
            RudiMediaConnectorParameter.from_json(not_cp_dict)
    no_type_cp = RudiMediaConnectorParameter.from_json(
        {
            "key": "random key",
            "value": {"e": 1},
            "usage": "test",
            "accepted_values": [{"e": 1}],
        }
    )
    assert no_type_cp.value_type == "STRING"
    assert no_type_cp.value == "{'e': 1}"
    assert no_type_cp.accepted_values == ["{'e': 1}"]
    for val_type in ["int", "str", "dict"]:
        not_cp_dict = {
            "key": "random key",
            "value": {"e": "value is a dict and will be stringified"},
            "type": val_type,
            "usage": "test",
            "accepted_values": [{"e": "value is a dict and will be stringified"}],
        }
        with pytest.raises(LiteralUnexpectedValueException):
            RudiMediaConnectorParameter.from_json(not_cp_dict)

    cp_list = RudiMediaConnectorParameter.from_json(OK_CP)
    assert len(cp_list) == 3

    with pytest.raises(TypeError):
        RudiMediaConnectorParameter.from_json(4)


def test_RudiMediaConnectorParameterList():
    assert len(RudiMediaConnectorParameterList(RudiMediaConnectorParameter.from_json(OK_CP[0]))) == 1
    assert len(RudiMediaConnectorParameterList(RudiMediaConnectorParameter.from_json(OK_CP))) == 3
    with pytest.raises(TypeError):
        RudiMediaConnectorParameterList(4)


def test_RudiMediaConnectorParameterList_to_json():
    co_params = RudiMediaConnectorParameterList.from_json(OK_CP)
    assert co_params.to_json()[0]["type"] == "STRING"


def test_RudiMediaConnectorParameterList_from_json():
    assert len(RudiMediaConnectorParameterList.from_json(OK_CP[0])) == 1
    assert len(RudiMediaConnectorParameterList.from_json(OK_CP)) == 3
    with pytest.raises(TypeError):
        RudiMediaConnectorParameterList.from_json(4)


def test_RudiMediaConnector_from_json():
    assert (
        len(
            RudiMediaConnector.from_json(
                {
                    "url": "https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/2611547a-42f1-4d7c-b736-2fef5cca30fe",
                    "interface_contract": "dwnl",
                    "connector_parameters": [
                        {
                            "key": "random key 1",
                            "value": "random val 1",
                            "type": "STRING",
                            "usage": "test 1",
                            "accepted_values": ["random val 1", "random val 2"],
                        },
                        {
                            "key": "random key 2",
                            "value": "random val 2",
                            "type": "STRING",
                            "usage": "test 2",
                            "accepted_values": ["random val 1", "random val 2"],
                        },
                    ],
                }
            ).connector_parameters
        )
        == 2
    )


assert (
    len(
        RudiMediaConnector.from_json(
            {
                "url": "https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/2611547a-42f1-4d7c-b736-2fef5cca30fe",
                "interface_contract": "dwnl",
                "connector_parameters": {
                    "key": "random key 1",
                    "value": "random val 1",
                    "type": "STRING",
                    "usage": "test 1",
                    "accepted_values": ["random val 1", "random val 2"],
                },
            }
        ).connector_parameters
    )
    == 1
)


def test_RudiMediaConnector():
    url = "https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/2611547a-42f1-4d7c-b736-2fef5cca30fe"
    connect_params = [
        RudiMediaConnectorParameter.from_json(
            {
                "key": "random key 1",
                "value": "random val 1",
                "usage": "test 1",
                "accepted_values": ["random val 1", "random val 2"],
            }
        )
    ]
    connector_parameters = RudiMediaConnector(url, connector_parameters=connect_params).connector_parameters
    assert connector_parameters is not None
    assert isinstance(connector_parameters, list)
    assert connector_parameters[0].value_type == "STRING"
    with pytest.raises(TypeError):
        RudiMediaConnector(url, connector_parameters=4)  # type: ignore
