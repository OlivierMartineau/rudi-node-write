from http.client import HTTPSConnection, HTTPConnection
from json import dumps, loads, JSONDecodeError
from typing import Literal, get_args, BinaryIO, TextIO
from urllib.parse import urlsplit

from rudi_node_write.rudi_types.rudi_const import check_is_literal
from rudi_node_write.utils.dict_utils import is_dict
from rudi_node_write.utils.err import HttpError
from rudi_node_write.utils.log import log_d_if, log_e, log_d
from rudi_node_write.utils.str_utils import slash_join
from rudi_node_write.utils.url_utils import url_encode_req_params

HttpRequestMethod = Literal["GET", "PUT", "DEL", "POST"]
HTTP_REQUEST_METHODS = get_args(HttpRequestMethod)

CONTENT_TYPE_KEY = "Content-Type"

DEFAULT_HEADERS = {CONTENT_TYPE_KEY: "text/plain; ", "Accept": "application/json"}

STATUS = "status"
REDIRECTION = "redirection"


def https_download(resource_url: str, headers=None, should_show_debug_line: bool = False):
    if headers is None:
        headers = DEFAULT_HEADERS
    here = "https_download"
    (scheme, netloc, path, query, fragment) = urlsplit(resource_url)
    if scheme != "https":
        raise NotImplementedError(f"only HTTPS protocol is supported, cannot treat this url: {resource_url}")
    connection = HTTPSConnection(netloc)

    connection.request(method="GET", url=resource_url, headers=headers)
    response = connection.getresponse()
    if response.status != 200:
        log_e(here, f"ERR {response.status}", resource_url)
        return None
    else:
        log_d_if(should_show_debug_line, here, f"OK {response.status}", resource_url)
        res_data = response.read()
        connection.close()
        return res_data


class Connector:
    _default_connector = None

    def __init__(self, server_url: str):
        self.scheme = None
        self.host = None
        self.path = None
        self.base_url = None
        self.connection = None

        self._set_url(server_url)

    def _set_url(self, server_url: str):
        fun = f"super.{self.class_name}._set_url"
        (scheme, netloc, path, query, fragment) = urlsplit(server_url)
        if scheme != "http" and scheme != "https":
            raise NotImplementedError(f"only http and https are supported, got '{scheme}'")
        # self.scheme = scheme
        self.scheme = "https"
        self.host = netloc
        self.path = path
        self.base_url = slash_join(f"{self.scheme}://{self.host}", self.path)
        log_d(fun, "base_url", self.base_url)

    @property
    def class_name(self):
        return self.__class__.__name__

    def full_url(self, relative_url: str = "/"):
        return slash_join(self.base_url, url_encode_req_params(relative_url))

    def full_path(self, relative_url: str = "/"):
        return slash_join("/", self.path, url_encode_req_params(relative_url))

    def test_connection(self):
        return self.request()

    def close_connection(self):
        try:
            self.connection.close()
        except Exception as e:  # pragma: no cover
            log_e(self.class_name, "close_connection ERROR", e)

    def download(
        self, relative_url: str, headers: dict = None, keep_alive: bool = False, should_log_response: bool = False
    ):
        """
        Download a file on the connector server
        :param relative_url: a relative URL that will be joined to the connector's base URL to form the request URL
        :param headers: the HTTP request headers
        :param keep_alive: True if you need to send several successive requests (defaults to False). Use
        self.close_connection() afterwards, then.
        :param should_log_response: True if some log lines should be displayed (defaults to False).
        :return: a status
        """
        here = f"{self.class_name}.download"
        if headers is None:
            headers = DEFAULT_HEADERS

        path_url = self.full_path(relative_url)

        self.connection = HTTPSConnection(self.host)
        self.connection.request(method="GET", url=path_url, headers=headers)
        response = self.connection.getresponse()
        if response.status != 200:
            log_e(here, f"ERR {response.status}", path_url)
            return None
        else:
            log_d_if(should_log_response, here, f"OK {response.status}", path_url)
            res_data = response.read()
            if not keep_alive:
                self.connection.close()
            if not res_data:
                log_e(here, "empty data?")
            return res_data

    def request(
        self,
        relative_url: str = "/",
        req_method: HttpRequestMethod = "GET",
        body: dict | str | BinaryIO | TextIO = None,
        headers=None,
        keep_alive: bool = False,
        should_log_response: bool = False,
    ) -> (str, dict):
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
        fun = f"{self.class_name}.request"

        check_is_literal(req_method, HTTP_REQUEST_METHODS, "incorrect type for request method")

        if headers is None:
            headers = DEFAULT_HEADERS
        if is_dict(body):
            headers[CONTENT_TYPE_KEY] = "application/json"
            body = dumps(body)

        path_url = self.full_path(relative_url)

        if self.scheme == "http":  # pragma: no cover
            self.connection = HTTPConnection(self.host)
        else:
            self.connection = HTTPSConnection(self.host)
        log_d(fun, req_method, self.full_url(relative_url))

        try:
            # log_d(fun, "request details", "method=", req_method, "url=", path_url, "body=", body, "headers=", headers)
            self.connection.request(method=req_method, url=path_url, body=body, headers=headers)
        except ConnectionRefusedError as e:
            log_e(fun, "Error on request", req_method, self.full_url(relative_url))
            log_e(fun, "ERR", e)
            raise e
        return self.parse_response(
            relative_url=relative_url,
            req_method=req_method,
            keep_alive=keep_alive,
            should_log_response=should_log_response,
        )

    def parse_response(
        self,
        relative_url: str,
        req_method: HttpRequestMethod,
        keep_alive: bool = False,
        should_log_response: bool = True,
    ):
        """Basic parsing of the result"""
        fun = f"{self.class_name}.parse_response"
        response = self.connection.getresponse()
        # log_d(fun, "Response", response.getcode(), response.getheaders(), response.info())
        if response.status in [301, 302]:
            return {STATUS: response.status, REDIRECTION: response.getheader("location")}
        if (
            response.status not in [200, 500, 501]
            and not (530 <= response.status < 540)
            and not (400 <= response.status < 500)
        ):
            return None

        rdata = response.read()
        # log_d(fun, "rdata", rdata)
        try:
            response_data = loads(rdata)
            log_d_if(should_log_response, fun, "Response is a JSON", response_data)
        except (TypeError, JSONDecodeError):
            response_data = repr(rdata)
            log_d_if(should_log_response, fun, "Response is not a JSON", response_data)
        if not keep_alive:
            self.close_connection()

        if type(response_data) is str:
            log_d_if(should_log_response, fun, "Response is a string", response_data)
            if response.status == 200:
                return rdata.decode("utf8")
        if response.status == 200:
            return response_data
        if response.status >= 400:
            log_e(fun, "Connection error", response_data)
            log_e(fun, "Request in error", req_method, self.full_url(relative_url))
            raise HttpError(response_data, req_method, self.base_url, relative_url)


if __name__ == "__main__":  # pragma: no cover
    tests = "Connector tests"
    connector = Connector("https://bacasable.fenix.rudi-univ-rennes1.fr/api/version")
    log_d(tests, "testing connection, got version", connector.test_connection())
    # data = connector.request(relative_url="resources?limit=1")
    # print(data)

    connector = Connector("https://bacasable.fenix.rudi-univ-rennes1.fr/api/v1")
    res = connector.request("resources")

    log_d(tests, "number of resources declared", res["total"])

    url = "https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/b086c7b2-bd6d-401f-86f5-f1f207023bae"
    log_d("https_utils", url, https_download(url))
