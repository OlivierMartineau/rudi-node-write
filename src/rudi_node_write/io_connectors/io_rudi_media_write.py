from abc import ABC
from json import dumps
from time import time
from urllib.parse import quote

from rudi_node_write.io_connectors.io_connector import Connector
from rudi_node_write.rudi_types.rudi_const import MEDIA_TYPE_FILE
from rudi_node_write.utils.file import get_file_info, ensure_is_file, read_file
from rudi_node_write.utils.jwt import get_jwt_basic_auth
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.type_string import slash_join


class RudiMediaHeadersFactory(ABC):
    """
    Abstract class to deal with identification in headers of requests sent to RUDI Media server
    When uploading a media to the RUDI Media server, this class will help formatting the headers with the file metadata
    """

    def __init__(self, headers_user_agent: str = 'RudiMediaHeadersFactory'):
        self._initial_headers = {
            'User-Agent': headers_user_agent,
            'Content-type': 'text/plain',
            'Accept': 'application/json'}

    def get_headers(self, additional_headers: dict = None):
        return self._initial_headers if additional_headers is None else self._initial_headers | additional_headers

    def get_headers_for_file(self, file_local_path: str, media_id: str):
        """
        Metadata for RUDI "MediaFiles" {"media_type": "FILE"}
        source: https://gitlab.aqmo.org/rudidev/rudi-media

        "media_id": (mandatory) An uuid-v4 unique identifier
        "media_type": (optional) should specify "FILE", as defined in the standard specification
        "media_name": (optional) the name of the media. This name can be used to give a name for the file when downloaded
        "file_size": (optional) the file size. This value, when correctly used, will improve the transfer speed.
        "file_type": (optional), the mime-type as registered by the IANA authority
        "charset":   (optional), the data encoding format as registered by the IANA authority
        "access_date": (optional), a date after the access is invalid (in the future)
        """
        ensure_is_file(file_local_path)
        file_info = get_file_info(file_local_path)
        file_metadata = {
            'media_id': media_id,
            'media_type': MEDIA_TYPE_FILE,
            'media_name': quote(file_info.get('name')),
            'file_size': file_info.get('size'),
            'file_type': quote(file_info.get('mime_type'))
        }
        charset = file_info.get('charset')
        if charset:
            file_metadata['charset'] = charset

        return self.get_headers({'file_metadata': dumps(file_metadata)})


class RudiMediaHeadersFactoryBasicAuth(RudiMediaHeadersFactory):
    """
    Class used to deal with identification in headers of requests sent to RUDI Media server with credentials for a
    direct authentication as {"Basic": "Authorization <base64url encoded usr:pwd>"}
    """

    def __init__(self, usr: str, pwd: str, headers_user_agent: str = 'RudiMediaHeadersFactoryBasicAuth'):
        super().__init__(headers_user_agent)
        self._initial_headers |= {'Authorization': get_jwt_basic_auth(usr, pwd)}


class RudiNodeMediaConnector(Connector):
    def __init__(self, server_url: str, headers_factory: RudiMediaHeadersFactory):
        super().__init__(server_url)
        self._headers_factory = headers_factory
        self.test_connection()

    def _get_headers(self, additional_headers: dict = None) -> dict:
        return self._headers_factory.get_headers(additional_headers)

    def _get_headers_for_file(self, file_local_path: str, media_id: str) -> dict:
        return self._headers_factory.get_headers_for_file(file_local_path=file_local_path, media_id=media_id)

    def _get_api_media(self, relative_url: str):
        return self.request(relative_url=slash_join('media', relative_url), headers=self._get_headers(),
                            req_method='GET')

    def _put_api_media(self, relative_url: str, payload: dict):
        return self.request(relative_url=slash_join('media', relative_url), headers=self._get_headers(),
                            req_method='PUT', body=payload)

    def test_connection(self) -> bool:
        test = bool(self._get_api_media(relative_url='revision'))
        log_d('RudiNodeMediaConnector', f"Node '{self.host}'", f"connection {'OK' if test else 'KO'}")
        return test

    @property
    def media_list(self) -> list:
        media_info = self._get_api_media('list').get('zone1')  # What if there are other zones?
        return [] if media_info is None else media_info.get('list')

    def post_local_media_file(self, file_local_path: str, media_id: str):
        """
        :param file_local_path: the path of a local file we wish to send to a RUDI node Media server
        :param media_id: the UUIDv4 that identifies the media on the RUDI node
        :return:
        """
        # :param media_name: the original name of the file
        # :param file_size: the size of the file in bytes
        # :param file_type: the MIME type of the file
        # :param charset: the encoding of the file
        headers = self._get_headers_for_file(file_local_path, media_id)

        # 1. créer un objet headers avec la Media headers factory
        # 2. ajouter les infos du fichier au header : au niveau du headers on urlib.parse.quote les champs nécessaires
        # 3.
        return


if __name__ == '__main__':
    # ----------- INIT -----------
    fun = 'RudiNodeApiConnector tests'
    begin = time()

    creds_file = '../../../creds/creds.json'
    rudi_node_creds = read_file(creds_file)
    headers = RudiMediaHeadersFactoryBasicAuth(usr=rudi_node_creds.get('usr'), pwd=rudi_node_creds.get('pwd'))
    rudi_media = RudiNodeMediaConnector(server_url='https://bacasable.fenix.rudi-univ-rennes1.fr',
                                        headers_factory=headers)
    log_d(fun, 'media list', rudi_media.media_list)
    log_d(fun, 'exec. time', time() - begin)
