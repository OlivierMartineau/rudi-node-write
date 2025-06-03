from http.client import HTTPSConnection, HTTPConnection
from json import dumps, loads, JSONDecodeError
from typing import Literal, get_args, BinaryIO, TextIO
from urllib.parse import urlsplit

from rudi_node_write.rudi_types.rudi_const import check_is_literal
from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.dict_utils import safe_get_key
from rudi_node_write.utils.err import HttpError
from rudi_node_write.utils.log import log_d_if, log_e, log_d
from rudi_node_write.utils.str_utils import slash_join
from rudi_node_write.utils.url_utils import get_response_cookies, url_encode_req_params

HttpRequestMethod = Literal["GET", "PUT", "DELETE", "POST"]
HTTP_REQUEST_METHODS = get_args(HttpRequestMethod)

DEFAULT_HEADERS = {"Content-Type": "text/plain; ", "Accept": "application/json"}

STATUS = "status"
REDIRECTION = "redirection"


def https_download(resource_url: str, headers=None, should_show_debug_line: bool = False):
    if headers is None:
        headers = DEFAULT_HEADERS
    here = "https_download"
    (scheme, netloc, path, query, fragment) = urlsplit(resource_url)
    if scheme not in ("https", "http"):
        raise NotImplementedError(f"only HTTPS protocol is supported, cannot treat this url: {resource_url}")
    connection = (HTTPSConnection if scheme == "https" else HTTPConnection)(netloc)

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

    def __init__(self, server_url: str, keep_connection: bool = False):
        self.scheme = None
        self.host = None
        self.path = None
        self.base_url = None
        self.connection = None
        self.keep_connection = keep_connection

        self._set_url(server_url)
        self._cookies = None

        self.should_log_request: bool = True
        self.should_log_response: bool = False

    def _set_url(self, server_url: str):
        here = f"super.{self.class_name}._set_url"
        (scheme, netloc, path, query, fragment) = urlsplit(server_url)
        if scheme not in ("https", "http"):
            raise NotImplementedError(f"only http and https are supported, got '{scheme}'")
        self.scheme = scheme
        self.host = netloc
        self.path = path
        self.base_url = slash_join(f"{self.scheme}://{self.host}", self.path)
        # log_d(here, "base_url", self.base_url)

    @property
    def class_name(self):
        return self.__class__.__name__

    def full_url(self, relative_url: str = "/"):
        return slash_join(self.base_url, url_encode_req_params(relative_url))

    def set_path(self, new_path: str):
        self.path = new_path
        self.base_url = slash_join(f"{self.scheme}://{self.host}", self.path)

    def full_path(self, relative_url: str = "/"):
        return slash_join("/", self.path, url_encode_req_params(relative_url))

    def test_connection(self) -> bool | str | dict:
        return self.request()  # type: ignore

    def close_connection(self):
        if self.connection is None:
            raise ConnectionAbortedError("The connection should be alive still")
        try:
            self.connection.close()
        except Exception as e:  # pragma: no cover
            log_e(self.class_name, "close_connection ERROR", e)

    def download(
        self,
        relative_url: str,
        headers: dict | None = None,
        keep_alive: bool = False,
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
        if self.host is None:
            raise AttributeError("The host was not defined")
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
            log_d_if(self.should_log_response, here, f"OK {response.status}", path_url)
            res_data = response.read()
            if not keep_alive and not self.keep_connection:
                self.connection.close()
            if not res_data:
                log_e(here, "empty data?")
            return res_data

    def request(
        self,
        relative_url: str = "/",
        req_method: HttpRequestMethod = "GET",
        body: dict | str | list | Serializable | BinaryIO | TextIO | None = None,
        headers=None,
        keep_alive: bool = False,
    ) -> dict | str | list | None:
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
        here = f"{self.class_name}.request"

        check_is_literal(req_method, HTTP_REQUEST_METHODS, "incorrect type for request method")

        if headers is None:
            headers = DEFAULT_HEADERS
        if req_method == "POST" or req_method == "PUT":
            if isinstance(body, dict):
                headers["Content-Type"] = "application/json"
                body_str = dumps(body)
            elif isinstance(body, Serializable):
                headers["Content-Type"] = "application/json"
                body_str = body.to_json_str(ensure_ascii=True)
            elif isinstance(body, list):
                body_str = str(list)
            else:
                body_str = body
        else:
            # log_w(here, f"Body is ignored since http method used is {req_method}")
            body_str = None

        path_url = self.full_path(relative_url)
        if self.host is None:
            raise ConnectionError("The connector host should be defined")
        self.connection = HTTPConnection(self.host) if self.scheme == "http" else HTTPSConnection(self.host)

        # log_d_if(self.should_log_request, here, req_method, self.full_url(relative_url))
        log_d_if(self.should_log_request, here, req_method, self.full_url(relative_url))

        try:
            self.connection.request(method=req_method, url=path_url, body=body_str, headers=headers)  # type: ignore
        except ConnectionRefusedError as e:
            log_e(here, "Error on request", req_method, self.full_url(relative_url))
            log_e(here, "ERR", e)
            raise e
        res = self.parse_response(
            relative_url=relative_url,
            req_method=req_method,
            keep_alive=keep_alive,
        )
        return res
        # if not isinstance(res, dict):
        #     return res
        # redirect_url = res.get("redirection")
        # if redirect_url is None:
        #     return res

        # try:
        #     self.request(method=req_method, url=redirect_url, body=body_str, headers=headers)  # type: ignore
        # except ConnectionRefusedError as e:
        #     log_e(here, "Error on redirected request", req_method, self.full_url(relative_url))
        #     log_e(here, "ERR", e)
        #     raise e
        # return self.parse_response(
        #     relative_url=relative_url,
        #     req_method=req_method,
        #     keep_alive=keep_alive,
        # )

    def parse_response(
        self,
        relative_url: str,
        req_method: HttpRequestMethod,
        keep_alive: bool = False,
    ):
        """Basic parsing of the result"""
        here = f"{self.class_name}.parse_response"
        if self.connection is None:
            raise ConnectionError("The connector HTTPSConnection should be defined")
        response = self.connection.getresponse()
        self._cookies = get_response_cookies(response)

        if response.status in [301, 302, 307, 308]:
            return {"status": response.status, "from": relative_url, "redirection": response.getheader("location")}

        # if (
        #     response.status not in [200, 500, 501]
        #     and not (530 <= response.status < 540)
        #     and not (400 <= response.status < 500)
        # ):
        #     return None

        rdata = response.read()
        # log_d(here, "rdata", rdata)
        try:
            response_data = loads(rdata)
            log_d_if(self.should_log_response, here, "Response is a JSON", response_data)
        except (TypeError, JSONDecodeError):
            response_data = repr(rdata)
            log_d_if(self.should_log_response, here, "Response is not a JSON", response_data)
        if not keep_alive and not self.keep_connection:
            self.close_connection()

        if isinstance(response_data, str):
            log_d_if(self.should_log_response, here, "Response is a string", response_data)
            if response.status < 400:
                return rdata.decode("utf8")
        if response.status < 400:
            return response_data

        log_e(here, "Connection error", response_data)
        log_e(here, "Request in error", req_method, self.full_url(relative_url))
        # log_e(here, "Headers", response.headers)
        raise HttpError(response_data, response.status, req_method, self.base_url, relative_url)


if __name__ == "__main__":  # pragma: no cover
    tests = "Connector tests"
    node_url = "https://bacasable.fenix.rudi-univ-rennes1.fr"
    connector = Connector(f"{node_url}/catalog/version")
    log_d(tests, "testing connection, got version", connector.test_connection())

    connector = Connector(f"{node_url}/catalog/v1")
    metadata_list = connector.request("resources")
    if isinstance(metadata_list, dict) and metadata_list["total"] is not None:
        log_d(tests, "number of resources declared", f"{metadata_list['total']}")
    else:
        log_e(
            tests,
            f"An error occurred, result should be a dict with 'total' and 'items' properties, got {metadata_list}",
        )

    url = "resources?available_formats.file_storage_status=available&fields=available_formats"
    meta_list: list = connector.request(url)["items"]  # type: ignore
    # print(tests, "media_list", meta_list)
    available_files = []
    for meta in meta_list:
        for media in meta["available_formats"]:
            # log_d(tests, "media", media)
            file_storage_status = safe_get_key(media, "file_storage_status")
            if file_storage_status == "available":
                available_files.append(media)

    if len(available_files) == 0:
        print("no media available, quiting")
    else:
        media_1 = available_files[0]
        url = media_1["connector"]["url"]
        log_d("https_utils", url, https_download(url))
