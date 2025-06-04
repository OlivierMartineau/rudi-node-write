import pytest

from rudi_node_write.utils.url_utils import url_encode_req_params, ensure_http


def test_url_encode_req_params() -> str:
    url = "https://url.com/?lang=fr&timezone=Europe/Paris&use_labels=true&delimiter=;"
    assert url_encode_req_params(url) == "https://url.com/?lang=fr&timezone=Europe/Paris&use_labels=true&delimiter=%3B"
    assert url_encode_req_params("https://url.com/?lang") == "https://url.com/?lang"
    assert url_encode_req_params("https://url.com/") == "https://url.com/"
    assert url_encode_req_params("https://url.com") == "https://url.com"
    assert url_encode_req_params("https://url.com/rel") == "https://url.com/rel"
    assert url_encode_req_params("https://url.com/rel?") == "https://url.com/rel?"
    assert url_encode_req_params("https://url.com/rel?=") == "https://url.com/rel?="
    assert url_encode_req_params("https://url.com/p1=val&p2") == "https://url.com/p1=val&p2"
    with pytest.raises(TypeError):
        url_encode_req_params(0)
    with pytest.raises(TypeError):
        url_encode_req_params(None)


def test_ensure_http() -> str:
    assert ensure_http("https://test.org").startswith("http")
    assert ensure_http("http://test.org").startswith("http")
    assert ensure_http("test.org").startswith("https://")
