from urllib.parse import quote

from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.type_string import is_string
from rudi_node_write.utils.types import get_type_name


def url_encode_req_params(url_str: str) -> str:
    """
    Use urllib.parse.quote on every value of a key/value pair in request parameters (RFC 3986, see the documentation
    of urllib.parse.quote for further info)
    :param url_str: a URL that needs to be encoded
    :return: the encoded URL
    """
    fun = 'clean_url'
    # log_d(fun, 'url_str', url_str)
    if not is_string(url_str):
        TypeError(f"input URL should be a string, got '{get_type_name(url_str)}'")
    if url_str.find('=') == -1:
        return url_str  # No request parameters to clean
    url_bits = url_str.split('?')
    if len(url_bits) == 0:
        raise ValueError('input is not a valid URL')
    base_url = ''
    relative_url = ''
    if len(url_bits) == 1:
        relative_url = url_bits[0]
    elif len(url_bits) == 2:
        # case where we were given the relative url_str only
        base_url = f'{url_bits[0]}?'
        relative_url = url_bits[1]
    # log_d(fun, 'relative_url', relative_url)
    clean_relative_url = ''
    relative_url_bits = relative_url.split('&')

    for bit in relative_url_bits:
        key_val_pair = bit.split('=')
        # log_d(fun, 'key_val_pair', key_val_pair)
        if len(key_val_pair) == 2:
            clean_relative_url += f'{key_val_pair[0]}={quote(key_val_pair[1])}&'
        else:
            clean_relative_url += f'{bit}&'
    return f'{base_url}{clean_relative_url[:-1]}'


if __name__ == '__main__':  # url_str =
    url = 'https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/loisirs-az-4bis/exports/json?lang=fr' \
          '&timezone=Europe/Paris&use_labels=true&delimiter=;'
    log_d('URL utils', 'clean_url', url_encode_req_params(url))
