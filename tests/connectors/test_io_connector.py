import pytest

from rudi_node_write.conf.meta_defaults import RUDI_API_VERSION
from rudi_node_write.connectors.io_connector import Connector, https_download
from rudi_node_write.utils.err import HttpError
from rudi_node_write.utils.file_utils import check_is_file
from rudi_node_write.utils.str_utils import is_uuid_v4

creds_file = check_is_file("./creds/creds.json")

node_url = "https://exatow.fenix.rudi-univ-rennes1.fr"
file_url = "https://exatow.fenix.rudi-univ-rennes1.fr/media/download/6d7e6dc4-0aba-4edb-8df2-4eebfec50285"


def test_Connector():
    connector = Connector("https://data-rudi.aqmo.org/api/v1")
    assert connector.class_name == "Connector"
    assert connector.scheme == "https"
    assert connector.host == "data-rudi.aqmo.org"
    assert connector.path == "/api/v1"
    assert connector.base_url == "https://data-rudi.aqmo.org/api/v1"
    assert connector.full_url("resources") == "https://data-rudi.aqmo.org/api/v1/resources"
    assert connector.full_path("resources") == "/api/v1/resources"

    with pytest.raises(NotImplementedError, match="only http and https are supported"):
        Connector("ftp://data-rudi.aqmo.org/api/v1")


def test_Connector_connection():
    connector = Connector(f"{node_url}/api/version")
    assert connector.test_connection() == RUDI_API_VERSION

    rudi_connector = Connector(f"{node_url}/api/v1")
    meta_total = rudi_connector.request("resources")
    assert meta_total is not None
    assert isinstance(meta_total, dict)
    assert int(meta_total["total"]) > 0


def test_Connector_download():
    rudi_connector = Connector(node_url)
    metadata_list = rudi_connector.request(
        "/api/v1/resources?available_formats.file_storage_status=available&fields=available_formats"
    )
    assert isinstance(metadata_list, dict)
    assert isinstance(metadata_list["items"], list)
    metadata1 = metadata_list["items"][0]
    assert isinstance(metadata1, dict)
    media1 = metadata1["available_formats"][0]
    assert is_uuid_v4(media_1_id := media1["media_id"])
    assert media1["connector"]["url"] == f"{node_url}/media/download/{media_1_id}"
    assert rudi_connector.download(f"media/download/{media_1_id}")

    assert rudi_connector.download("fake.org") is None
    rudi_connector.download("api/v1/resources/a")

    with pytest.raises(HttpError):
        rudi_connector.request("api/v1/resources/a")


def test_https_download():
    assert https_download(file_url)

    with pytest.raises(NotImplementedError):
        https_download("ftp://fake.org")

    assert https_download(f"{node_url}/media/download/b" "-f1f207023ba") is None


def test_Connector_redirect():
    rudi_connector = Connector("https://rm.rudi.irisa.fr")
    rudi_connector.request("resources?limit=1")
