from abc import ABC
from json import dumps
from time import time
from typing import BinaryIO, TextIO
from urllib.parse import quote

from rudi_node_write.connectors.io_connector import Connector
from rudi_node_write.connectors.io_rudi_manager_write import RudiNodeManagerConnector
from rudi_node_write.connectors.rudi_node_auth import RudiNodeAuth
from rudi_node_write.rudi_types.rudi_const import MEDIA_TYPE_FILE, MIME_TYPES_UTF8_TEXT
from rudi_node_write.utils.file_utils import read_json_file, FileDetails
from rudi_node_write.utils.jwt import get_basic_auth
from rudi_node_write.utils.log import log_d, log_w
from rudi_node_write.utils.str_utils import slash_join, uuid4_str
from rudi_node_write.utils.url_utils import ensure_url_startswith

MAX_SIZE = 524288000  # (== 500 MB)


def ensure_url_startswith_media(url):
    return ensure_url_startswith(url, "media")


class FileTooBigException(Exception):
    def __init__(self, file_size):
        super().__init__(
            f"This file is too big to be uploaded to a RUDI node ("
            f"file size = {int(file_size / 1048576)} MB > max size = {int(MAX_SIZE / 1048576)} MB)"
        )


class RudiMediaHeadersFactory(ABC):
    """
    Abstract class to deal with identification in headers of requests sent to RUDI Media server
    When uploading a media to the RUDI Media server, this class will help formatting the headers with the file metadata
    """

    def __init__(self, headers_user_agent: str = "RudiMediaHeadersFactory"):
        self._initial_headers = {
            "User-Agent": headers_user_agent,
            "Content-Type": "text/plain; charset=utf-8",
            "Accept": "application/json",
        }

    def get_headers(self, additional_headers: dict | None = None):
        return self._initial_headers if additional_headers is None else self._initial_headers | additional_headers

    def get_headers_for_file(self, file_info: FileDetails, media_id: str):
        """
        Metadata for RUDI "MediaFiles" {"media_type": "FILE"}
        source: https://gitlab.aqmo.org/rudidev/rudi-media

        "media_id": (mandatory) An uuid-v4 unique identifier
        "media_type": (optional) should specify "FILE", as defined in the standard specification
        "media_name": (optional) the name of the media. This name can be used to give a name for the file when
        downloaded
        "file_size": (optional) the file size. This value, when correctly used, will improve the transfer speed.
        "file_type": (optional), the MIME type as registered by the IANA authority
        "charset":   (optional), the data encoding format as registered by the IANA authority
        "access_date": (optional), a date after the access is invalid (in the future)
        """

        file_metadata = {
            "media_id": media_id,
            "media_type": MEDIA_TYPE_FILE,
            "media_name": quote(file_info.name),
            "file_size": file_info.size,
            "file_type": file_info.mime,
        }
        if file_info.mime.endswith("+crypt"):
            return self.get_headers(
                {
                    "Content-Type": f"{file_info.mime}",
                    "file_metadata": dumps(file_metadata),
                }
            )

        if file_info.mime.startswith("text"):
            charset = file_info.charset if file_info.charset else "utf-8"
            file_metadata["charset"] = charset
            return self.get_headers(
                {
                    "Content-Type": f"{file_info.mime}; charset={charset}",
                    "file_metadata": dumps(file_metadata),
                }
            )
        if file_info.mime in MIME_TYPES_UTF8_TEXT:
            file_metadata["charset"] = "utf-8"

        return self.get_headers(
            {
                "Content-Type": f"{file_info.mime}; charset=utf-8",
                "file_metadata": dumps(file_metadata),
            }
        )


class RudiMediaHeadersFactoryBasicAuth(RudiMediaHeadersFactory):
    """
    Class used to deal with identification in headers of requests sent to RUDI Media server with credentials for a
    direct authentication as {"Basic": "Authorization <base64url encoded usr:pwd>"}
    """

    def __init__(
        self,
        auth: RudiNodeAuth,
        headers_user_agent: str = "RudiMediaHeadersFactoryBasicAuth",
    ):
        super().__init__(headers_user_agent)
        self._initial_headers |= {"Authorization": auth.basic_auth}


class RudiNodeStorageConnector(Connector):
    def __init__(self, server_url: str, headers_factory: RudiMediaHeadersFactory | None = None):
        super().__init__(server_url)
        self._headers_factory = headers_factory
        self.test_connection()

    def _get_headers(self, additional_headers: dict | None = None) -> dict:
        if self._headers_factory:
            return self._headers_factory.get_headers(additional_headers)
        else:
            raise Exception("If no headers is defined, you have to provide this connector a RudiMediaHeadersFactory")

    def _get_headers_for_file(self, file_info: FileDetails, media_id: str) -> dict:
        if self._headers_factory:
            return self._headers_factory.get_headers_for_file(file_info=file_info, media_id=media_id)
        else:
            raise Exception("If no headers is defined, you have to provide this connector a RudiMediaHeadersFactory")

    def _get_api_media(
        self,
        relative_url: str,
        headers: dict | None = None,
    ):
        return self.request(
            relative_url=ensure_url_startswith_media(relative_url),
            headers=headers if headers is not None else self._get_headers(),
            req_method="GET",
        )

    def _post_api_media(
        self,
        relative_url: str,
        payload: str | dict | BinaryIO | TextIO,
        headers: dict | None = None,
    ):
        return self.request(
            relative_url=ensure_url_startswith_media(relative_url),
            headers=headers if headers is not None else self._get_headers(),
            body=payload,
            req_method="POST",
        )

    def _put_api_media(self, relative_url: str, payload: str | dict | BinaryIO, headers: dict | None = None):
        return self.request(
            relative_url=ensure_url_startswith_media(relative_url),
            headers=headers if headers is not None else self._get_headers(),
            body=payload,
            req_method="PUT",
        )

    def test_connection(self) -> bool:
        test = bool(self._get_api_media(relative_url="hash"))
        log_d(
            "RudiNodeStorage",
            f"Node '{self.host}'",
            f"connection {'OK' if test else 'KO'}",
        )
        return test

    @property
    def media_list(self) -> list:
        media_info = self._get_api_media("list").get("zone1")  # What if there are other zones? # type: ignore
        return [] if media_info is None else media_info.get("list")

    def post_local_media_file(self, file_local_path: str, media_id: str = uuid4_str()):
        """
        :param file_local_path: the path of a local file we wish to send to a RUDI node Media server
        :param media_id: the UUIDv4 that identifies the media on the RUDI node
        :return:
        """
        # :param media_name: the original name of the file
        # :param file_size: the size of the file in bytes
        # :param file_type: the MIME type of the file
        # :param charset: the encoding of the file
        here = f"{self.class_name}.post_local_media_file"

        file_info = FileDetails(file_local_path)
        if file_info.size > MAX_SIZE:
            raise FileTooBigException(file_info.size)

        log_d(here, f"sending as binary the file: {file_info}")
        headers = self._get_headers_for_file(file_info, media_id)
        with open(file_local_path, "rb") as bin_content:
            res = self._post_api_media("post", bin_content, headers)
        if isinstance(res, list):
            if {"status": "OK"} in res:
                log_d(here, "upload status", "success")
                return slash_join(self.base_url, "media/download", media_id)
            if len(res) > 0 and res[0].get("status") == "error":
                log_w(here, "ERR upload failed", res[0].get("msg"))
                return res[0]
        else:
            raise Exception(f"The format of the message received by the RUDI Media modeule is incorrect: {res}")


if __name__ == "__main__":  # pragma: no cover
    # ----------- INIT -----------
    tests = "RudiNodeCatalogConnector tests"
    begin = time()

    creds_file = "../creds/creds_bas.json"
    rudi_node_creds = read_json_file(creds_file)
    auth = RudiNodeAuth(usr=rudi_node_creds["usr"], pwd=rudi_node_creds["pwd"])
    media_headers_factory = RudiMediaHeadersFactoryBasicAuth(auth=auth)
    rudi_media = RudiNodeStorageConnector(server_url=rudi_node_creds["url"], headers_factory=media_headers_factory)
    log_d(tests, "media list", rudi_media.media_list)

    dwnld_dir = "../../../tests/_test_files/"
    media_uuid = [
        "eeeeeeee-3233-4541-855e-55de7086b40b",
        "eeeeeeee-3233-4541-855e-55de7086b40c",
    ]
    text_file = "unicode_chars.txt"
    yaml_file = "RUDI producer internal API - 1.3.0.yml"
    for i, f in enumerate([text_file, yaml_file]):
        upload_res = rudi_media.post_local_media_file(dwnld_dir + f, media_uuid[i])
        log_d(tests, f"File '{f}' now available at", upload_res)
        log_d(
            tests,
            "stored_media",
            [stored_media for stored_media in rudi_media.media_list if stored_media.get("uuid") == media_uuid[i]][0],
        )

    log_d(tests, "exec. time", time() - begin)
