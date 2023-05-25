from http.client import HTTPSConnection, HTTPConnection
from json import dumps, loads, JSONDecodeError
from typing import Literal, get_args
from urllib.parse import urlsplit

from rudi_node_write.rudi_types.rudi_const import check_is_accepted
from rudi_node_write.utils.err import HttpError
from rudi_node_write.utils.log import log_d_if, log_e, log_d
from rudi_node_write.utils.type_string import slash_join
from rudi_node_write.utils.url import url_encode_req_params

HttpRequestMethod = Literal['GET', 'PUT', 'DEL', 'POST']
HTTP_REQUEST_METHODS = get_args(HttpRequestMethod)


def https_download(resource_url: str, should_show_debug_line: bool = False):
    fun = 'https_download'
    (scheme, netloc, path, query, fragment) = urlsplit(resource_url)
    if scheme != 'https':
        raise NotImplementedError(f'only HTTPS protocol is supported, cannot treat this url: {resource_url}')
    connection = HTTPSConnection(netloc)
    connection.request(method='GET', url=resource_url)
    response = connection.getresponse()
    if response.status != 200:
        log_e(fun, f'ERR {response.status}', resource_url)
        return None
    else:
        log_d_if(should_show_debug_line, fun, f'OK {response.status}', resource_url)
        res_data = response.read()
        connection.close()
        return res_data


class Connector:
    _default_connector = None

    def __init__(self, server_url: str):
        (scheme, netloc, path, query, fragment) = urlsplit(server_url)
        if scheme != 'http' and scheme != 'https':
            raise NotImplementedError('only http and https are supported')
        self.scheme = scheme
        self.host = netloc
        self.path = path
        self.base_url = slash_join(f"{self.scheme}://{self.host}", self.path)
        self.connection = None

        # log_d('Connector', 'base_url', self.base_url)

    @property
    def class_name(self):
        return self.__class__.__name__

    def full_url(self, relative_url: str = '/'):
        return slash_join(self.base_url, url_encode_req_params(relative_url))

    def full_path(self, relative_url: str = '/'):
        return slash_join('/', self.path, url_encode_req_params(relative_url))

    def test_connection(self):
        return self.request()

    def close_connection(self):
        try:
            self.connection.close()
        except Exception as e:
            log_e(self.__class__.__name__, 'close_connection ERROR', e)

    def request(self, relative_url: str = '/', req_method: HttpRequestMethod = 'GET', body: dict | str = None,
                headers: dict = None, keep_alive: bool = False, should_log_response: bool = False) -> (str, dict):
        """
        Send a http(s) request
        :param relative_url: a relative URL that will be joined to the connector's base URL to form the request URL
        :param req_method: the HTTP request method
        :param body: in the case of a POST/PUT request, the body of the request
        :param headers: the HTTP request headers
        :param keep_alive: True if you need to send several successive requests (defaults to False). Use
        self.close_connection() afterwards, then.
        :param should_log_response: True if some log lines should be displayed (defaults to False).
        :return: the data returned from the request
        """
        if self.scheme == 'https':
            self.connection = HTTPSConnection(self.host)
        else:
            self.connection = HTTPConnection(self.host)
        check_is_accepted(req_method, HTTP_REQUEST_METHODS, 'incorrect type for request method')

        if not headers:
            headers = {'Content-Type': 'text/plain', 'Accept': 'application/json'}
        if body and type(body) == dict:
            headers['Content-type'] = 'application/json'
            body = dumps(body)
        fun = f'{self.class_name}.request'
        # log_d(fun, 'relative_url', relative_url)
        path_url = self.full_path(relative_url)
        log_d(fun, 'to', path_url)
        try:
            self.connection.request(req_method, path_url, body, headers)
        except ConnectionRefusedError as e:
            log_e(fun, 'Error on request', req_method, self.full_url(relative_url))
            log_e(fun, 'ERR', e)
            raise e
        return self.parse_response(relative_url=relative_url, req_method=req_method,
                                   keep_alive=keep_alive, should_log_response=should_log_response)

    def parse_response(self, relative_url, req_method, keep_alive: bool = False,
                       should_log_response: bool = True):

        """ Basic parsing of the result
        """
        fun = f'{self.class_name}.parse_response'
        response = self.connection.getresponse()
        if response.status not in [200, 500, 501] and not (530 <= response.status < 540) and not (
                400 <= response.status < 500):
            return None

        rdata = response.read()
        try:
            response_data = loads(rdata)
            log_d_if(should_log_response, fun, 'Response is a JSON', response_data)
        except (TypeError, JSONDecodeError) as e:
            response_data = repr(rdata)
            log_d_if(should_log_response, fun, 'Response is not a JSON', response_data)
        if not keep_alive:
            self.close_connection()

        if type(response_data) is str:
            log_d_if(should_log_response, fun, 'Response is a string', response_data)
            if response.status == 200:
                return rdata.decode('utf8')
        if response.status == 200:
            return response_data
        if response.status >= 400:
            log_e(fun, 'Connection error', response_data)
            log_e(fun, 'Request in error', req_method, self.full_url(relative_url))
            raise HttpError(response_data, req_method, self.base_url, relative_url)


if __name__ == '__main__':
    if 'GET' in HttpRequestMethod:
        log_d('Testing Literal', 'GET in HttpRequestMethod', 'OK')
    else:
        log_d('Testing Literal', 'GET in HttpRequestMethod', 'KO')

    connector = Connector('https://data-rudi.aqmo.org/api/v1')
    data = connector.request(relative_url='resources?limit=1')
    print(data)

    url = 'https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/b086c7b2-bd6d-401f-86f5-f1f207023bae'
    log_d('https_utils', url, https_download(url))
