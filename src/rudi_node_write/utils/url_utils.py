from http.client import HTTPResponse
from urllib.parse import quote

from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.str_utils import slash_join
from rudi_node_write.utils.typing_utils import get_type_name


def ensure_http(url: str, scheme="https://"):
    return url if url.startswith("http") else slash_join(scheme, "/", url)


def ensure_url_startswith(url: str, str_start: str):
    return url if url.startswith(str_start) else slash_join(str_start, url)


def get_response_cookies(http_response: HTTPResponse):
    cookie_list = http_response.headers.get_all("set-cookie")
    # log_d("get_response_cookies", "cookie_list", cookie_list)
    if cookie_list is None or len(cookie_list) == 0:
        return None
    cookies = {}
    for cookie_str in cookie_list:
        cookie_info = cookie_str.split(";")
        [name, val] = cookie_info[0].split("=")
        cookies[name] = val
    return cookies


def url_encode_req_params(url_str: str) -> str:
    """
    Use urllib.parse.quote on every value of a key/value pair in request parameters (RFC 3986, see the documentation
    of urllib.parse.quote for further info)
    :param url_str: a URL that needs to be encoded
    :return: the encoded URL
    """
    # log_d(here, 'url_str', url_str)
    if not isinstance(url_str, str):
        raise TypeError(f"input URL should be a string, got '{get_type_name(url_str)}'")
    if url_str.find("=") == -1 & url_str.find("&") == -1:
        return url_str  # No request parameters to clean
    url_bits = url_str.split("?")
    base_url = ""
    relative_url = ""
    # log_d(here, "len(url_bits)", len(url_bits))
    if len(url_bits) == 1:
        relative_url = url_bits[0]
    elif len(url_bits) == 2:
        # case where we were given the relative url_str only
        base_url = f"{url_bits[0]}?"
        relative_url = url_bits[1]
    # log_d(here, 'relative_url', relative_url)
    clean_relative_url = ""
    relative_url_bits = relative_url.split("&")

    for bit in relative_url_bits:
        key_val_pair = bit.split("=")
        # log_d(here, 'key_val_pair', key_val_pair)
        if len(key_val_pair) == 2:
            clean_relative_url += f"{key_val_pair[0]}={quote(key_val_pair[1])}&"
        else:
            clean_relative_url += f"{bit}&"
    return f"{base_url}{clean_relative_url[:-1]}"


if __name__ == "__main__":  # pragma: no cover
    tests = "URL utils"
    url = (
        "https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/loisirs-az-4bis/exports/json?lang=fr"
        "&timezone=Europe/Paris&use_labels=true&delimiter=;"
    )
    log_d(tests, "url", url_encode_req_params(url))
    log_d(tests, url := "https://url.com/?lang", url_encode_req_params(url))
    log_d(tests, url := "https://url.com/", url_encode_req_params(url))
    log_d(tests, url := "https://url.com", url_encode_req_params(url))
    log_d(tests, url := "https://url.com?req", url_encode_req_params(url))
    log_d(tests, url := "https://url.com?=", url_encode_req_params(url))
    log_d(tests, url := "https://url.com/p1=val&p2", url_encode_req_params(url))
    log_d(tests, url := "=", url_encode_req_params(url))
    log_d(tests, url := "https://url.com/?req=é'()à!è", url_encode_req_params(url))
