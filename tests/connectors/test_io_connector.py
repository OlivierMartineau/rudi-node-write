import pytest

from rudi_node_write.connectors.io_connector import Connector, https_download
from rudi_node_write.utils.err import HttpError


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
    connector = Connector("https://bacasable.fenix.rudi-univ-rennes1.fr/api/version")
    assert connector.test_connection() == "1.3.2"

    rudi_connector = Connector("https://bacasable.fenix.rudi-univ-rennes1.fr/api/v1")
    resources = rudi_connector.request("resources")
    assert resources["total"] > 0


def test_Connector_download():
    rudi_connector = Connector("https://bacasable.fenix.rudi-univ-rennes1.fr")
    assert rudi_connector.download("media/download/b086c7b2-bd6d-401f-86f5-f1f207023bae")

    rudi_connector.download("fake.com")
    rudi_connector.download("api/v1/resources/a")

    with pytest.raises(HttpError):
        rudi_connector.request("api/v1/resources/a")


def test_https_download():
    url = "https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/b086c7b2-bd6d-401f-86f5-f1f207023bae"
    assert https_download(url)

    with pytest.raises(NotImplementedError):
        https_download("ftp://fake.com")

    assert https_download("https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/b" "-f1f207023ba") is None


def test_Connector_redirect():
    rudi_connector = Connector("https://rm.rudi.irisa.fr")
    rudi_connector.request("resources?limit=1")
