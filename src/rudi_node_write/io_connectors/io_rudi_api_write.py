from os.path import isdir, abspath
from time import time
from urllib.parse import quote

from rudi_node_write.io_connectors.io_connector import Connector, https_download
from rudi_node_write.io_connectors.io_rudi_jwt_factory import RudiNodeJwtFactory
from rudi_node_write.rudi_types.rudi_const import MEDIA_TYPE_FILE
from rudi_node_write.utils.err import ExpiredTokenException, UnexpectedValueException, NoNullException, HttpError
from rudi_node_write.utils.file import read_file, write_file
from rudi_node_write.utils.jwt import is_jwt_expired
from rudi_node_write.utils.log import log_d, log_e, log_w
from rudi_node_write.utils.type_dict import safe_get_key, pick_in_dict, merge_dict_of_list
from rudi_node_write.utils.type_string import slash_join, is_string
from rudi_node_write.utils.types import is_list, get_type_name, get_first_list_elt_or_none

REQ_LIMIT = 500
_DELAY_REFRESH_S = 60  # seconds

_STATUS_SKIPPED = 'skipped'
_STATUS_MISSING = 'missing'
_STATUS_DOWNLOADED = 'downloaded'


class RudiNodeApiConnector(Connector):

    def __init__(self, server_url: str, jwt: str = None, jwt_factory: RudiNodeJwtFactory = None,
                 headers_user_agent: str = 'RudiNodeApiConnector'):
        """
        Creates a connector to the internal API of the API/proxy module of a RUDI producer node.
        As this API requires an identification, a valid RudiNode JWT must be provided,
        or a connector to the node JWT factory.
        These parameters can be set later but one of them is required to perform the operations.
        :param server_url: the URL of the RUDI Node
        :param jwt: (optional) a valid JWT for this RUDI node
        :param jwt_factory: (optional) a connector to JWT factory on this RUDI node
        :param headers_user_agent: (optional) identifies the user launching the request (or at least the module)
        in the request headers, for logging purpose.
        """
        super().__init__(server_url)
        self._initial_headers = {'User-Agent': headers_user_agent, 'Content-type': 'text/plain',
                                 'Accept': 'application/json'}
        self._stored_jwt = jwt
        self._jwt_factory = jwt_factory
        self.test_connection()

        self._data = None

    def test_connection(self):
        test = self.request('api/admin/hash')
        if test is None:
            log_e('RudiNodeApiConnector', f"!! Node '{self.host}'", 'no connection!')
            raise ConnectionError(f"An error occurred while connecting to RUDI node JWT server {self.base_url}")
        else:
            log_d('RudiNodeApiConnector', f"Node '{self.host}'", 'connection OK')

    def set_jwt_factory(self, jwt_factory: RudiNodeJwtFactory):
        if jwt_factory is None:
            raise UnexpectedValueException('jwt_factory', 'a RudiNodeJwtFactory object', 'None')
        self._jwt_factory = jwt_factory

    def set_jwt(self, jwt: str):
        if is_jwt_expired(jwt):
            raise ExpiredTokenException(jwt)
        self._stored_jwt = jwt

    @property
    def _jwt(self):
        if self._jwt_factory is not None:
            return self._jwt_factory.get_jwt()
        if self._stored_jwt is None:
            raise NoNullException('a JWT is required, or a connector to a Rudi node JWT factory')
        if is_jwt_expired(self._stored_jwt):
            raise ExpiredTokenException(self._stored_jwt)
        return self._stored_jwt

    @property
    def _headers(self):
        return self._initial_headers | {'Authorization': f'Bearer {self._jwt}'}

    def _get_admin_api(self, url: str, keep_alive=False):
        """
        Performs an identified GET request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param keep_alive: True if the connection should be kep alive (for successive requests). Use
        self.connection.close() in the end of your request series.
        :return: a JSON
        """
        return self.request(relative_url=slash_join('api/admin', url), req_method='GET', headers=self._headers,
                            keep_alive=keep_alive)

    def _put_admin_api(self, url: str, payload: dict):
        """
        Performs an identified PUT request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param jwt: a valid JWT base 64 URL string
        :return: a JSON
        """
        return self.request(relative_url=slash_join('api/admin', url), req_method='PUT', headers=self._headers)

    def _get_full_obj_list(self, url_bit: str, max_count: int = 0) -> list[dict]:
        """
        Utility function to get a full list of RUDI objects, using limit/offset to browse the whole collection.
        :param url_bit: requested URL, with possibly some request parameters separated from the base URL by a
        question mark
        :param max_count: a limit set to the number of results we need
        :return: a list of RUDI objects
        """
        split_url = url_bit.split('?')
        base_url = split_url[0]
        params_str = f'{split_url[1]}&' if len(split_url) > 1 else ''

        obj_nb = self._get_admin_api(f'{base_url}/count')
        obj_set = []
        req_offset = 0
        req_max_count = obj_nb if max_count == 0 else min(obj_nb, max_count)

        while req_offset < req_max_count:
            req_limit = REQ_LIMIT if req_offset + REQ_LIMIT < req_max_count else req_max_count - req_offset
            partial_req_url = f'{base_url}?{params_str}sort_by=-updatedAt&limit={req_limit}&offset={req_offset}'
            obj_set += self._get_admin_api(partial_req_url, keep_alive=True)
            req_offset += REQ_LIMIT
        self.close_connection()
        return obj_set

    def _get_info(self, obj_type):
        if self._data is None:
            self._data = {}
        obj_data = self._data.get(obj_type)
        if obj_data is None or time() - obj_data.get('refresh_time') > _DELAY_REFRESH_S:
            self._data[obj_type] = {'data': self._get_admin_api(obj_type),
                                    'refresh_time': time()}  # TODO: full obj list vs. self.get_admin_api => get obj info ?
        return self._data[obj_type]['data']

    @property
    def producers(self) -> list[dict]:
        """
        :return: the list of the organizations/producers declared on the RUDI producer node
        """
        return self._get_info('organizations')

    @property
    def contacts(self) -> list[dict]:
        """
        :return: the list of the metadata_contacts declared on the RUDI producer node
        """
        return self._get_info('contacts')

    @property
    def producer_names(self) -> list[str]:
        """
        :return: the list of the names of the organizations/producers declared on the RUDI producer node
        """
        return sorted([org['organization_name'] for org in self.producers])

    def find_producer_with_name(self, org_name):
        """
        :param org_name: a producer name
        :return: the information associated with the producer on the RUDI node
        """
        return get_first_list_elt_or_none(self._get_admin_api(f'organizations?organization_name={org_name}'))

    @property
    def contact_names(self) -> list[str]:
        """
        :return: the list of the names of the metadata_contacts declared on the RUDI producer node
        """
        return sorted([contact['contact_name'] for contact in self.contacts])

    @property
    def themes(self) -> list[str]:
        """
        :return: the list of the themes declared on the RUDI producer node
        """
        return self._get_info('enum/themes')

    @property
    def keywords(self):
        """
        :return: the list of the keywords declared on the RUDI producer node
        """
        return self._get_info('enum/keywords')

    def _get_used_enums(self, enum_type) -> list[str] | None:
        """
        Utility function to get the list of the enums used in the metadata declared on the RUDI producer node
        :param enum_type: 'theme' | 'keywords'
        :return: the list of the enums used in the metadata declared on the RUDI producer node
        """
        enum_count_list = self._get_info(f'resources?count_by={enum_type}')
        if len(enum_count_list) == 0:
            return None
        return [enum[enum_type] for enum in enum_count_list]

    @property
    def used_themes(self) -> list[str]:
        """
        :return: the list of themes used in the metadata on the RUDI producer node
        """
        return self._get_used_enums('theme')

    @property
    def used_keywords(self) -> list[str]:
        """
        :return: the list of keywords used in the metadata on the RUDI producer node
        """
        return self._get_used_enums('keywords')

    @property
    def metadata_count(self) -> int:
        """
        :return: the number of metadata declared on the RUDI producer node
        """
        return self._get_info('resources/count')

    @property
    def metadata_list(self):
        """
        :return: the full list of metadata declared on this RUDI producer node
        """
        return self._get_full_obj_list('resources')

    def find_metadata_with_uuid(self, metadata_uuid: str) -> dict | None:
        """
        :param metadata_uuid: a UUID v4
        :return: the metadata identified with the input UUID v4, or None if it wasn't found
        """
        return get_first_list_elt_or_none(self._get_admin_api(f'resources?global_id={metadata_uuid}'))

    def find_metadata_with_source_id(self, source_id: str) -> dict | None:
        """
        :param source_id: the ID used on the source server to identify a metadata
        :return: the metadata identified with the input source ID, or None if it wasn't found
        """
        return get_first_list_elt_or_none(self._get_admin_api(f'resources?local_id={source_id}'))

    def find_metadata_with_title(self, title: str) -> dict | None:
        """
        :param title: the title of a metadata
        :return: the metadata identified with the input title, or None if it wasn't found
        """
        return get_first_list_elt_or_none(self._get_admin_api(f'resources?resource_title={title}'))

    def get_metadata_with_filter(self, rudi_fields_filter: dict):
        filter_str = ''
        for i, (key, val) in enumerate(rudi_fields_filter.items()):
            # TODO: special cases of producer / contact / available_formats
            filter_str += f'&{quote(key)}={quote(val)}'
        meta_list = self._get_admin_api(f'resources?{filter_str[1:]}&limit={REQ_LIMIT}')
        if len(meta_list) < REQ_LIMIT:
            return meta_list
        else:
            return self._get_full_obj_list(f'resources?{filter_str[1:]}')

    def get_metadata_with_available_media(self):
        return self._get_full_obj_list('resources?available_formats.file_storage_status=available')

    def _get_metadata_with_obj_name(self, obj_prop, obj_name: str) -> list[dict]:
        meta_list = self._get_admin_api(f'resources?{obj_prop}={quote(obj_name)}&limit={REQ_LIMIT}')
        if len(meta_list) < REQ_LIMIT:
            return meta_list
        else:
            meta_count_list = self._get_admin_api(f'resources?{obj_prop}={quote(obj_name)}&count_by={obj_prop}')
            meta_nb = meta_count_list[0]['count']
            return self._get_full_obj_list(f'resources?{obj_prop}={quote(obj_name)}', meta_nb)

    def get_metadata_with_producer(self, producer_name: str) -> list[dict]:
        return self._get_metadata_with_obj_name('producer.organization_name', producer_name)

    def get_metadata_with_contact(self, contact_name: str) -> list[dict]:
        return self._get_metadata_with_obj_name('metadata_contacts.contact_name', contact_name)

    def get_metadata_with_theme(self, theme: str) -> list[dict]:
        return self._get_full_obj_list(f'resources?theme={quote(theme)}')

    def get_metadata_with_keywords(self, keywords: list[str]) -> list[dict]:
        if is_string(keywords):
            keywords_str = keywords
        elif is_list(keywords):
            keywords_str = ','.join(keywords)
        else:
            raise UnexpectedValueException('keywords', 'a list of string', get_type_name(keywords))
        return self._get_full_obj_list(f'resources?keywords={keywords_str}')

    def get_metadata_ids(self):
        return self._get_full_obj_list('resources?fields=global_id,resource_title')

    def get_list_media_for_metadata(self, metadata_uuid):
        meta = self.find_metadata_with_uuid(metadata_uuid)
        media_list = meta['available_formats']
        media_list_final = []
        for media in media_list:
            media_list_final.append(
                {'url': media['connector']['url'], 'type': media['media_type'], 'meta_contact': media['media_id'],
                 'id': media['media_id']})
        return media_list_final

    def find_metadata_with_media_name(self, media_name: str) -> dict | None:
        """
        :param media_name: meta_contact of the media
        :return: metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self._get_admin_api(f'resources?available_formats.media_name={media_name}')

    def find_metadata_with_media_uuid(self, media_uuid: str) -> dict | None:
        """
        :param media_uuid: UUIDv4 of the media
        :return: metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self._get_admin_api(f'resources?available_formats.media_id={media_uuid}')

    def find_media_with_uuid(self, media_uuid: str) -> dict | None:
        """
        Get the media information from a media ID.
        Check this link for more details about the structure of the media information:
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Media
        :param media_uuid: UUID v4 of the media
        :return: media whose `media_id` attribute matches the `media_uuid` input parameter
        """
        return self._get_admin_api(f'media/{media_uuid}')

    def get_media_with_name(self, media_name: str) -> list[dict]:
        """
        Get the information for every media that has the name given as input.
        Check this link for more details about the structure of the media information:
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Media
        :param media_name: the name of the media
        :return: media info whose `media_name` attribute matches the `media_name` input parameter
        """
        return self._get_admin_api(f'media?media_name={media_name}')

    @staticmethod
    def _download_file_from_media_info(media: dict, local_download_dir: str) -> dict:
        """
        Download a file from its media metadata
        :param media: the file metadata (as found in the RUDI metadata `available_formats` attribute
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        # fun = '_download_media_from_info'

        media_type = media.get('media_type')

        # Most likely for media_type == 'SERVICE'
        if media_type != MEDIA_TYPE_FILE:
            return {_STATUS_SKIPPED: [pick_in_dict(media, ['media_name', 'media_id', 'media_url', 'media_type'])]}

        # If the file is not available on storage, we won't try to download it.
        if media.get('file_storage_status') != 'available':
            return {_STATUS_MISSING: [
                pick_in_dict(media, ['media_name', 'media_id', 'media_url', 'file_type', 'file_storage_status'])]}

        # The metadata says the file is available, let's download it
        if not isdir(local_download_dir):
            raise FileNotFoundError(f"The following folder does not exist: '{local_download_dir}'")

        media_name = media.get('media_name')
        media_url = safe_get_key(media, 'connector', 'url')

        destination_path = abspath(slash_join(local_download_dir, media_name))
        try:
            content = https_download(media_url)
            write_file(destination_path, content, 'b')
            log_d('media_download', 'content saved to file', destination_path)

            file_info = {'media_name': media_name, 'media_id': media.get('media_id'), 'media_url': media_url,
                         'file_type': media.get('file_type'), 'created': safe_get_key(media, 'media_dates', 'created'),
                         'updated': safe_get_key(media, 'media_dates', 'updated'), 'file_path': destination_path}
            return {_STATUS_DOWNLOADED: [file_info]}
        except HttpError as e:
            log_e(f"downloading file '{media_name}' (media ID: {media.get('media_id')}) failed:\n{e}")
            return {_STATUS_MISSING: [
                {'media_name': media_name, 'media_id': media.get('media_id'), 'media_url': media_url}]}

    def download_file_with_media_uuid(self, media_uuid: str, local_download_dir: str) -> dict | None:
        """
        Download a file identified with the input UUID
        :param media_uuid: a UUIDv4 that identifies the media on the RUDI node
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        # fun = 'download_media_with_uuid'
        try:
            media = self.find_media_with_uuid(media_uuid)
        except HttpError as e:
            log_e(f"downloading file with ID '{media_uuid}' failed:\n{e}")
            return {_STATUS_MISSING: [{'media_id': media_uuid}]}
        return self._download_file_from_media_info(media, local_download_dir)

    def download_file_with_name(self, media_name: str, local_download_dir: str) -> dict:
        """
        Find a file from its name and download it if it is available
        :param media_name: the name of the file we want to download
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        here = self.class_name + '.download_file_with_name'
        try:
            media_list = self.get_media_with_name(media_name)
        except HttpError as e:
            log_e(here, f"downloading file with name '{media_name}' failed:\n{e}")
            return {_STATUS_MISSING: [{'media_name': media_name}]}
        if len(media_list) == 0:
            log_w(here, f"No file was found with name: '{media_name}'")
            return {_STATUS_MISSING: [{'media_name': media_name}]}
        if len(media_list) > 1:
            log_w(here, f"Warning! Several files were found with name '{media_name}': downloading the first one")
            media1 = media_list.pop(0)
            media1_status = self._download_file_from_media_info(media1, local_download_dir)
            # log_d(here, 'media1_status', media1_status)
            return merge_dict_of_list(media1_status, {_STATUS_SKIPPED: media_list})
        return self._download_file_from_media_info(media_list[0], local_download_dir)

    def download_files_for_metadata(self, metadata_id, local_download_dir) -> dict | None:
        """
        Download all the available files for a metadata
        :param metadata_id: the UUIDv4 of the metadata
        :param local_download_dir: the path to a local folder
        :return: an object that lists the files that were downloaded, skipped or found missing
        """
        if not isdir(local_download_dir):
            raise FileNotFoundError(f"The following folder does not exist: '{local_download_dir}'")
        meta = self.find_metadata_with_uuid(metadata_id)
        media_list = meta.get('available_formats')
        if not media_list:
            return None
        files_dwnld_info = {_STATUS_DOWNLOADED: [], _STATUS_MISSING: [], _STATUS_SKIPPED: []}
        for media in media_list:
            dwnld_info = self._download_file_from_media_info(media, local_download_dir)
            files_dwnld_info = merge_dict_of_list(files_dwnld_info, dwnld_info)
        return files_dwnld_info


if __name__ == '__main__':
    # ----------- INIT -----------
    fun = 'RudiNodeApiConnector tests'
    begin = time()
    creds_file = '../../../creds/creds.json'
    rudi_node_creds = read_file(creds_file)

    node_jwt_factory = RudiNodeJwtFactory('https://bacasable.fenix.rudi-univ-rennes1.fr', rudi_node_creds)
    rudi_node = RudiNodeApiConnector(server_url='https://bacasable.fenix.rudi-univ-rennes1.fr',
                                     jwt_factory=node_jwt_factory)

    # ----------- TESTS -----------
    test_dir = '../../../dwnld'
    # log_d(fun, 'metadata_nb', rudi_node.metadata_count)
    # metadata_list = rudi_node.metadata_list
    # meta1 = metadata_list[0]
    # meta1_id = meta1['global_id']
    # log_d('RudiNodeApiConnector tests', 'meta1 id', meta1_id)
    # meta = rudi_node.find_metadata_with_uuid(meta1_id)
    # log_d('RudiNodeApiConnector tests', 'meta name', f"'{meta['resource_title']}'")
    log_d(fun, 'producers', len(rudi_node.producers))
    log_d(fun, 'producer names', rudi_node.producer_names)
    log_d(fun, 'metadata_contacts', len(rudi_node.contacts))
    log_d(fun, 'contact names', rudi_node.contact_names)
    # #
    # filter_dict = {'producer.organization_name': 'RUDI'}
    # log_d(fun, 'get_metadata_with_filter', len(rudi_node.get_metadata_with_filter(filter_dict)))
    # log_d(fun, 'get_metadata_with_filter',
    #       len(rudi_node.get_metadata_with_filter({'producer.organization_name': 'Gusikowski LLC'})))
    # log_d(fun, 'get_metadata_with_producer Gusikowski LLC', len(rudi_node.get_metadata_with_producer('Gusikowski LLC')))
    # log_d(fun, 'get_metadata_with_producer RUDI', len(rudi_node.get_metadata_with_producer('RUDI')))
    # log_d(fun, 'get_metadata_with_contact Bacasable', len(rudi_node.get_metadata_with_contact('Bacasable')))
    # log_d(fun, 'get_metadata_with_contact Wanda Torphy', len(rudi_node.get_metadata_with_contact('Wanda Torphy')))
    #
    log_d(fun, 'themes', len(rudi_node.themes))
    log_d(fun, 'used_themes', len(rudi_node.used_themes))
    log_d(fun, 'keywords', len(rudi_node.keywords))
    log_d(fun, 'used_keywords', len(rudi_node.used_keywords))

    log_d(fun, {'a': [1, 2], 'b': ['a', 'b']} | {'a': [0, 2], 'b': ['aa', 'bb']})
    #
    # log_d(fun, 'find_metadata_with_media_uuid',
    #       rudi_node.find_metadata_with_media_uuid('6027b6ec-d950-4e97-b200-b8c244e3a28d'))

    # ----------- TESTS: DWNLD -----------
    log_d(fun, 'download_files_for_metadata',
          rudi_node.download_files_for_metadata('7480479d-92e0-4e1d-9987-44b1eccdde1a', test_dir))

    log_d(fun, "download_file_with_media_uuid '782bab2d-7ee8-4633-9c0a-173649b4d879'",
          rudi_node.download_file_with_media_uuid('782bab2d-7ee8-4633-9c0a-173649b4d879', test_dir))

    log_d(fun, f"download_file_with_name '782bab2d-7ee8-4633-9c0a-173649b4d879'",
          rudi_node.download_file_with_name('782bab2d-7ee8-4633-9c0a-173649b4d879', test_dir))

    log_d(fun, "download_file_with_name 'toucan.jpg'",
          '\n' + str(rudi_node.download_file_with_name('toucan.jpg', test_dir)))

    log_d(fun, 'exec. time', time() - begin)
