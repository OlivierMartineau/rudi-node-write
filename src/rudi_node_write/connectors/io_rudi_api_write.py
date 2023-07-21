from os.path import isdir, abspath
from time import time
from urllib.parse import quote

from rudi_node_write.connectors.io_connector import Connector, https_download, CONTENT_TYPE_KEY
from rudi_node_write.connectors.io_rudi_jwt_factory import RudiNodeJwtFactory
from rudi_node_write.rudi_types.rudi_const import MEDIA_TYPE_FILE, RudiObjectType
from rudi_node_write.rudi_types.rudi_contact import RudiContact
from rudi_node_write.rudi_types.rudi_media import RudiMediaService, RudiMediaFile
from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.rudi_types.rudi_org import RudiOrganization
from rudi_node_write.utils.dict_utils import (
    safe_get_key,
    pick_in_dict,
    merge_dict_of_list,
)
from rudi_node_write.utils.err import (
    ExpiredTokenException,
    UnexpectedValueException,
    NoNullException,
    HttpError,
)
from rudi_node_write.utils.file_utils import read_json_file, write_file
from rudi_node_write.utils.jwt import is_jwt_expired
from rudi_node_write.utils.list_utils import get_first_list_elt_or_none
from rudi_node_write.utils.log import log_d, log_e, log_w
from rudi_node_write.utils.str_utils import slash_join, uuid4_str
from rudi_node_write.utils.typing_utils import get_type_name, check_type

REQ_LIMIT = 500
_DELAY_REFRESH_S = 60  # seconds
_REFRESH_KEY = "refresh_time"  # seconds

_STATUS_SKIPPED = "skipped"
_STATUS_MISSING = "missing"
_STATUS_DOWNLOADED = "downloaded"


class RudiNodeApiConnector(Connector):
    def __init__(
        self,
        server_url: str,
        jwt: str = None,
        jwt_factory: RudiNodeJwtFactory = None,
        headers_user_agent: str = "RudiNodeApiConnector",
    ):
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
        self._initial_headers = {
            "User-Agent": headers_user_agent,
            CONTENT_TYPE_KEY: "text/plain",
            "Accept": "application/json",
        }
        self._stored_jwt = jwt
        self._jwt_factory = jwt_factory
        self.test_connection()

        self._data = None

    def test_connection(self):
        test = self.request("api/admin/hash")
        if test is None:  # pragma: no cover
            log_e("RudiNodeApiConnector", f"!! Node '{self.host}'", "no connection!")
            raise ConnectionError(f"An error occurred while connecting to RUDI node JWT server {self.base_url}")
        else:
            log_d("RudiNodeApiConnector", f"Node '{self.host}'", "connection OK")

    def set_jwt_factory(self, jwt_factory: RudiNodeJwtFactory):
        self._jwt_factory: RudiNodeJwtFactory = check_type(jwt_factory, RudiNodeJwtFactory)
        self._jwt_factory.test_connection()

    def set_jwt(self, jwt: str):
        if is_jwt_expired(jwt):
            raise ExpiredTokenException(jwt)
        self._stored_jwt = jwt

    @property
    def _jwt(self):
        if self._jwt_factory is not None:
            return self._jwt_factory.get_jwt()
        if self._stored_jwt is None:
            raise NoNullException("a JWT is required, or a connector to a Rudi node JWT factory")
        if is_jwt_expired(self._stored_jwt):
            raise ExpiredTokenException(self._stored_jwt)
        return self._stored_jwt

    @property
    def _headers(self):
        return self._initial_headers | {"Authorization": f"Bearer {self._jwt}"}

    def _get_admin_api(self, url: str, keep_alive=False) -> str | int | list | dict:
        """
        Performs an identified GET request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param keep_alive: True if the connection should be kep alive (for successive requests). Use
        self.connection.close() in the end of your request series.
        :return: the result of the request, most likely a JSON
        """
        return self.request(
            req_method="GET",
            relative_url=slash_join("api/admin", url),
            headers=self._headers,
            keep_alive=keep_alive,
        )

    def _put_admin_api(self, url: str, payload: dict | str, headers: dict = None):
        """
        Performs an identified PUT request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        return self.request(
            req_method="PUT",
            relative_url=slash_join("api/admin", url),
            headers=headers if headers else self._headers,
            body=payload,
        )

    def _get_full_obj_list(self, url_bit: str, max_count: int = 0) -> list[dict]:
        """
        Utility function to get a full list of RUDI objects, using limit/offset to browse the whole collection.
        :param url_bit: requested URL, with possibly some request parameters separated from the base URL by a
        question mark
        :param max_count: a limit set to the number of results we need
        :return: a list of RUDI objects
        """
        here = "_get_full_obj_list"
        split_url = url_bit.split("?")
        base_url = split_url[0]
        params_str = f"{split_url[1]}&" if len(split_url) > 1 else ""

        obj_nb = self._get_admin_api(f"{base_url}/count")
        log_d(here, "obj_nb", obj_nb)
        obj_set = []
        req_offset = 0
        req_max_count = obj_nb if max_count == 0 else min(obj_nb, max_count)

        while req_offset < req_max_count:
            req_limit = REQ_LIMIT if req_offset + REQ_LIMIT < req_max_count else req_max_count - req_offset
            partial_req_url = f"{base_url}?{params_str}sort_by=-updatedAt&limit={req_limit}&offset={req_offset}"
            obj_set += self._get_admin_api(partial_req_url, keep_alive=True)
            req_offset += REQ_LIMIT
        self.close_connection()
        return obj_set

    def _clean_cache(self) -> None:
        if self._data is None:
            self._data = {}
        for cached_type in self._data.keys():
            if time() - (safe_get_key(self._data, cached_type, _REFRESH_KEY)) > _DELAY_REFRESH_S:
                self._data[cached_type] = None

    def _get_cached_info(self, obj_type: RudiObjectType | str) -> list[dict] | int | str | list | dict:
        """
        Access a list of RUDI objects (resources/metadata, contacts, producers/organizations, media) and get them in
        a temporary cache.
        :param obj_type: one of RUDI object types
        :return: the list of objects for this type
        """
        self._clean_cache()
        obj_data = self._data.get(obj_type)
        if obj_data is None or time() - obj_data.get(_REFRESH_KEY) > _DELAY_REFRESH_S:
            if obj_type in RudiObjectType:
                self._data[obj_type] = {
                    "data": self._get_full_obj_list(obj_type),
                    _REFRESH_KEY: time(),
                }
            else:
                self._data[obj_type] = {
                    "data": self._get_admin_api(obj_type),
                    _REFRESH_KEY: time(),
                }
        return self._data[obj_type]["data"]

    @property
    def producers(self) -> list[dict]:
        """
        :return: the list of the organizations/producers declared on the RUDI producer node
        """
        return self._get_cached_info("organizations")

    @property
    def contacts(self) -> list[dict]:
        """
        :return: the list of the metadata_contacts declared on the RUDI producer node
        """
        return self._get_cached_info("contacts")

    @property
    def producer_names(self) -> list[str]:
        """
        :return: the list of the names of the organizations/producers declared on the RUDI producer node
        """
        return sorted([org["organization_name"] for org in self.producers])

    def get_producer_with_name(self, org_name: str):
        """
        :param org_name: a producer name
        :return: the information associated with the producer on the RUDI node
        """
        return get_first_list_elt_or_none(self._get_admin_api(f"organizations?organization_name={org_name}"))

    def get_producer_with_id(self, org_id: str):
        """
        :param org_id: a producer UUID v4
        :return: the information associated with the producer on the RUDI node
        """
        return self._get_admin_api(f"organizations/{org_id}")

    def get_or_create_org_with_info(self, org_name: str, organization_info: dict = None):
        """
        :param org_name: a producer name
        :param organization_info: additional organization info (address, GPS coordinates, etc.) that will be set if the
        producer organization doesn't already exist on the RUDI node
        :return: the information associated with the producer on the RUDI node
        """
        fun = "get_or_create_org_with_info"
        if org := self.get_producer_with_name(org_name):
            log_d(fun, "found org", org)
            return org
        new_org = {"organization_name": org_name, "organization_id": uuid4_str()}
        if organization_info:
            new_org |= organization_info
        log_d(fun, "new_org", new_org)
        return self._put_admin_api("organizations", new_org)

    def get_or_create_org_with_rudi_obj(self, org: RudiOrganization) -> RudiOrganization:
        """
        :param org: minimal or complete organization info (organization_name, address, GPS coordinates,
        etc.) that will be set if the producer organization doesn't already exist on the RUDI node. The
        organization_id
        :return: the information associated with the producer on the RUDI node
        """
        fun = "get_or_create_org_with_rudi_obj"
        if (found_org := self.get_producer_with_name(org.organization_name)) or (
            found_org := self.get_producer_with_id(org.organization_id)
        ):
            log_d(fun, "found org", found_org)
            return RudiOrganization.from_json(found_org)
        return RudiOrganization.from_json(self._put_admin_api("organizations", org.to_json_str()))

    # ----------[ Contacts ]--------------------------------------------------------------------------------------------
    @property
    def contact_names(self) -> list[str]:
        """
        :return: the list of the names of the metadata_contacts declared on the RUDI producer node
        """
        return sorted([contact["contact_name"] for contact in self.contacts])

    def get_contact_with_name(self, contact_name: str):
        """
        :param contact_name: a contact name
        :return: the information associated with the contact on the RUDI node
        """
        return get_first_list_elt_or_none(self._get_admin_api(f"contacts?contact_name={contact_name}"))

    def get_contact_with_email(self, email: str):
        """
        :param email: a contact email
        :return: the information associated with the contact on the RUDI node
        """
        return get_first_list_elt_or_none(self._get_admin_api(f"contacts?email={email}"))

    def get_contact_with_name_or_email(self, contact_name: str, email: str):
        """
        :param contact_name: a contact name
        :param email: a contact email
        :return: the information associated with the contact on the RUDI node
        """
        if contact_name and (contact := self.get_contact_with_name(contact_name)):
            return contact
        if email:
            return self.get_contact_with_email(email)
        return None

    def get_or_create_contact_with_info(self, contact_name: str, contact_email: str, contact_info: dict = None):
        """
        Finds a contact from input name or email, or creates it.
        :param contact_name: the name of the contact
        :param contact_email: the email of the contact
        :param contact_info: additional contact info (cf.
        https://app.swaggerhub.com/apis/OlivierMartineau/RUDI-PRODUCER/1.3.0#/Contact)
        :return: the information associated with the producer on the RUDI node
        """
        fun = "get_or_create_contact_with_info"
        # log_d(fun, 'contact_name', contact_name)
        # log_d(fun, 'contact_email', contact_email)
        if contact := self.get_contact_with_name_or_email(contact_name, contact_email):
            return contact
        new_contact = {
            "contact_name": contact_name,
            "contact_id": uuid4_str(),
            "email": contact_email,
        }
        if contact_info:
            new_contact |= contact_info
        return self._put_admin_api("contacts", new_contact)

    def get_or_create_contact_with_rudi_obj(self, contact: RudiContact) -> RudiContact:
        """
        Finds a contact from input name or email, or creates it.
        :param contact: minimal or complete contact info (contact_name, email, etc.) that will be set if the contact
        doesn't already exist on the RUDI node.
        https://app.swaggerhub.com/apis/OlivierMartineau/RUDI-PRODUCER/1.3.0#/Contact
        :return: the information associated with the contact on the RUDI node
        """
        if (found_contact := self.get_contact_with_email(contact.email)) or (
            found_contact := self.get_contact_with_name(contact.contact_name)
        ):
            return RudiContact.from_json(found_contact)
        return RudiContact.from_json(self._put_admin_api("contacts", contact.to_json_str()))

    # ----------[ Enums ]-----------------------------------------------------------------------------------------------
    @property
    def themes(self) -> list[str]:
        """
        :return: the list of the themes declared on the RUDI producer node
        """
        return self._get_cached_info("enum/themes")

    @property
    def keywords(self):
        """
        :return: the list of the keywords declared on the RUDI producer node
        """
        return self._get_cached_info("enum/keywords")

    def _get_used_enums(self, enum_type) -> list[str] | None:
        """
        Utility function to get the list of the enums used in the metadata declared on the RUDI producer node
        :param enum_type: 'theme' | 'keywords'
        :return: the list of the enums used in the metadata declared on the RUDI producer node
        """
        enum_count_list = self._get_cached_info(f"resources?count_by={enum_type}")
        if len(enum_count_list) == 0:
            return None
        return [enum[enum_type] for enum in enum_count_list]

    @property
    def used_themes(self) -> list[str]:
        """
        :return: the list of themes used in the metadata on the RUDI producer node
        """
        return self._get_used_enums("theme")

    @property
    def used_keywords(self) -> list[str]:
        """
        :return: the list of keywords used in the metadata on the RUDI producer node
        """
        return self._get_used_enums("keywords")

    # ----------[ Metadata ]--------------------------------------------------------------------------------------------

    @property
    def metadata_count(self) -> int:
        """
        :return: the number of metadata declared on the RUDI producer node
        """
        return self._get_cached_info("resources/count")

    @property
    def metadata_list(self):
        """
        :return: the full list of metadata declared on this RUDI producer node
        """
        return self._get_full_obj_list("resources")

    def get_metadata_with_uuid(self, metadata_uuid: str) -> dict | None:
        """
        :param metadata_uuid: a UUID v4
        :return: the metadata identified with the input UUID v4, or None if it wasn't found
        """
        return get_first_list_elt_or_none(self._get_admin_api(f"resources?global_id={metadata_uuid}"))

    def get_metadata_with_source_id(self, source_id: str) -> dict | None:
        """
        :param source_id: the ID used on the source server to identify a metadata
        :return: the metadata identified with the input source ID, or None if it wasn't found
        """
        return get_first_list_elt_or_none(self._get_admin_api(f"resources?local_id={source_id}"))

    def get_metadata_with_title(self, title: str) -> dict | None:
        """
        :param title: the title of a metadata
        :return: the metadata identified with the input title, or None if it wasn't found
        """
        return get_first_list_elt_or_none(self._get_admin_api(f"resources?resource_title={title}"))

    def search_metadata_with_filter(self, rudi_fields_filter: dict) -> list[dict]:
        filter_str = ""
        for i, (key, val) in enumerate(rudi_fields_filter.items()):
            # TODO: special cases of producer / contact / available_formats
            filter_str += f"&{quote(key)}={quote(val)}"
        meta_list = self._get_admin_api(f"resources?{filter_str[1:]}&limit={REQ_LIMIT}")
        if len(meta_list) < REQ_LIMIT:
            return meta_list
        else:
            return self._get_full_obj_list(f"resources?{filter_str[1:]}")

    def search_metadata_with_available_media(self) -> list[dict]:
        return self._get_full_obj_list("resources?available_formats.file_storage_status=available")

    def get_or_create_meta_with_info(self, meta_title: str, meta_info: dict = None):
        """
        :param meta_title: the metadata resource title
        :param meta_info: additional metadata info
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Metadata
        :return: the metadata that can be found on the RUDI node
        """
        here = " get_or_create_meta_with_info"
        if found_meta := self.get_metadata_with_title(meta_title):
            log_d(here, "found org", found_meta)
            return found_meta
        new_meta = {"resource_title": meta_title, "global_id": uuid4_str()}
        if meta_info:
            new_meta |= meta_info
        log_d(here, "new_org", new_meta)
        return self._put_admin_api("resources", new_meta)

    def get_meta_with_rudi_obj(self, meta: RudiMetadata) -> RudiMetadata | None:
        """
        :param
        :return: the information associated with the producer on the RUDI node
        """
        here = " get_meta_with_rudi_obj"
        found_meta = self.get_metadata_with_source_id(meta.local_id)
        if (
            found_meta
            or (found_meta := self.get_metadata_with_title(meta.resource_title))
            or (found_meta := self.get_metadata_with_uuid(meta.global_id))
        ):
            return RudiMetadata.from_json(found_meta)
        return None

    def create_meta_with_rudi_obj(self, meta: RudiMetadata) -> dict:
        """
        :param
        :return: the information associated with the producer on the RUDI node
        """
        meta_str = meta.to_json_str(ensure_ascii=True)
        log_d("create_meta_with_rudi_obj", "meta_str", meta_str)
        return self._put_admin_api(
            url="resources",
            headers=self._headers | {CONTENT_TYPE_KEY: "application/json"},
            payload=meta_str,
        )

    def _search_metadata_with_obj_name(self, obj_prop, obj_name: str) -> list[dict]:
        meta_list = self._get_admin_api(f"resources?{obj_prop}={quote(obj_name)}&limit={REQ_LIMIT}")
        if len(meta_list) < REQ_LIMIT:
            return meta_list
        else:
            meta_count_list = self._get_admin_api(f"resources?{obj_prop}={quote(obj_name)}&count_by={obj_prop}")
            meta_nb = meta_count_list[0].get("count")
            return self._get_full_obj_list(f"resources?{obj_prop}={quote(obj_name)}", meta_nb)

    def search_metadata_with_producer(self, producer_name: str) -> list[dict]:
        return self._search_metadata_with_obj_name("producer.organization_name", producer_name)

    def search_metadata_with_contact(self, contact_name: str) -> list[dict]:
        return self._search_metadata_with_obj_name("metadata_contacts.contact_name", contact_name)

    def search_metadata_with_theme(self, theme: str) -> list[dict]:
        return self._get_full_obj_list(f"resources?theme={quote(theme)}")

    def search_metadata_with_keywords(self, keywords: str | list[str]) -> list[dict]:
        if isinstance(keywords, str):
            keywords_str = keywords
        elif isinstance(keywords, list):
            keywords_str = ",".join(keywords)
        else:
            raise UnexpectedValueException("keywords", "a list of string", get_type_name(keywords))
        return self._get_full_obj_list(f"resources?keywords={keywords_str}")

    def get_list_media_for_metadata(self, metadata_uuid):
        meta = self.get_metadata_with_uuid(metadata_uuid)
        media_list = meta["available_formats"]
        media_list_final = []
        for media in media_list:
            media_list_final.append(
                {
                    "url": media["connector"]["relative_url"],
                    "type": media["media_type"],
                    "meta_contact": media["media_id"],
                    "id": media["media_id"],
                }
            )
        return media_list_final

    def search_metadata_with_media_name(self, media_name: str) -> dict | None:
        """
        :param media_name: meta_contact of the media
        :return: metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self._get_admin_api(f"resources?available_formats.media_name={media_name}")

    def search_metadata_with_media_uuid(self, media_uuid: str) -> dict | None:
        """
        :param media_uuid: UUIDv4 of the media
        :return: metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self._get_admin_api(f"resources?available_formats.media_id={media_uuid}")

    # ----------[ Media ]-----------------------------------------------------------------------------------------------

    def get_media_with_uuid(self, media_uuid: str) -> dict | None:
        """
        Get the media information from a media ID.
        Check this link for more details about the structure of the media information:
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Media
        :param media_uuid: UUID v4 of the media.
        :return: media whose `media_id` attribute matches the `media_uuid` input parameter.
        """
        return self._get_admin_api(f"media/{media_uuid}")

    def search_available_media_with_name(self, media_name: str) -> list[dict]:
        """
        Get the information for every media that has the name given as input.
        Check this link for more details about the structure of the media information:
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Media
        :param media_name: the name of the media.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return self._get_admin_api(f"media?media_name={media_name}&file_storage_status=available")

    def get_media_file_with_info(self, media_name: str, file_size: int, checksum: str) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media_name: the name of the media.
        :param file_size: the size of the RudiMediaFile.
        :param checksum: the checksum of the RudiMediaFile.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return get_first_list_elt_or_none(
            self._get_admin_api(
                f"media?media_type=FILE&file_storage_status=available"
                f"&media_name={media_name}&file_size={file_size}&checksum.hash={checksum}&"
            )
        )

    def get_media_file_with_rudi_obj(self, media: RudiMediaFile) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media: a RudiMediaSFile object
        :return: media info whose name, size and checksum attributes matches the media input parameters.
        """
        return get_first_list_elt_or_none(
            self._get_admin_api(
                f"media?media_type=FILE&file_storage_status=available"
                f"&media_name={media.media_name}&file_size={media.file_size}&checksum.hash={media.checksum}&"
            )
        )

    def get_media_service_with_info(self, media_name: str, url: str) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media_name: the name of the media.
        :param url: the url of the RudiMediaService.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return get_first_list_elt_or_none(
            self._get_admin_api(f"media?media_type=SERVICE&media_name={media_name}&connector.url={url}")
        )

    def get_media_service_with_rudi_obj(self, media: RudiMediaService) -> dict:
        """
        Finds a RudiMediaService with input information (except the id: we're looking for a similar object already
        existing)
        :param media: a RudiMediaService object
        :return: media info whose `media_name` and 'source_url' attributes match the `media_name` and 'source_url'
        input parameters.
        """
        return get_first_list_elt_or_none(
            self._get_admin_api(
                f"media?media_type=SERVICE&media_name={media.media_name}&connector.url={media.source_url}"
            )
        )

    @staticmethod
    def download_file_from_media_info(media: dict, local_download_dir: str) -> dict:
        """
        Download a file from its media metadata
        :param media: the file metadata (as found in the RUDI metadata `available_formats` attribute
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        here = "download_file_from_media_info"

        media_type = media.get("media_type")

        # Most likely for media_type == 'SERVICE'
        if media_type != MEDIA_TYPE_FILE:
            return {_STATUS_SKIPPED: [pick_in_dict(media, ["media_name", "media_id", "media_url", "media_type"])]}

        # If the file is not available on storage, we won't try to download it.
        if media.get("file_storage_status") != "available":
            return {
                _STATUS_MISSING: [
                    pick_in_dict(
                        media,
                        [
                            "media_name",
                            "media_id",
                            "media_url",
                            "file_type",
                            "file_storage_status",
                        ],
                    )
                ]
            }

        # The metadata says the file is available, let's download it
        if not isdir(local_download_dir):
            raise FileNotFoundError(f"The following folder does not exist: '{local_download_dir}'")

        media_name = media.get("media_name")
        media_url = safe_get_key(media, "connector", "url")

        destination_path = abspath(slash_join(local_download_dir, media_name))
        try:
            content = https_download(media_url)
            if not content:
                log_e(here, "empty data for", media_url)

            write_file(destination_path, content, "b")
            log_d("media_download", "content saved to file", destination_path)

            file_info = {
                "media_name": media_name,
                "media_id": media.get("media_id"),
                "media_url": media_url,
                "file_type": media.get("file_type"),
                "created": safe_get_key(media, "media_dates", "created"),
                "updated": safe_get_key(media, "media_dates", "updated"),
                "file_path": destination_path,
            }
            return {_STATUS_DOWNLOADED: [file_info]}
        except HttpError as e:
            log_e(f"downloading file '{media_name}' (media ID: {media.get('media_id')}) failed:\n{e}")
            return {
                _STATUS_MISSING: [
                    {
                        "media_name": media_name,
                        "media_id": media.get("media_id"),
                        "media_url": media_url,
                    }
                ]
            }

    def download_file_with_media_uuid(self, media_uuid: str, local_download_dir: str) -> dict | None:
        """
        Download a file identified with the input UUID
        :param media_uuid: a UUIDv4 that identifies the media on the RUDI node
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        # here = 'download_media_with_uuid'
        try:
            media = self.get_media_with_uuid(media_uuid)
        except HttpError as e:
            log_e(f"downloading file with ID '{media_uuid}' failed:\n{e}")
            return {_STATUS_MISSING: [{"media_id": media_uuid}]}
        return self.download_file_from_media_info(media, local_download_dir)

    def download_file_with_name(self, media_name: str, local_download_dir: str) -> dict:
        """
        Find a file from its name and download it if it is available
        :param media_name: the name of the file we want to download
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        here = self.class_name + ".download_file_with_name"
        try:
            media_list = self.search_available_media_with_name(media_name)
        except HttpError as e:
            log_e(here, f"downloading file with name '{media_name}' failed:\n{e}")
            return {_STATUS_MISSING: [{"media_name": media_name}]}
        if len(media_list) == 0:
            log_w(here, f"No file was found with name: '{media_name}'")
            return {_STATUS_MISSING: [{"media_name": media_name}]}
        if len(media_list) > 1:
            log_w(
                here,
                f"Warning! Several files were found with name '{media_name}': downloading the first one",
            )
            media1 = media_list.pop(0)
            media1_status = self.download_file_from_media_info(media1, local_download_dir)
            # log_d(here, 'media1_status', media1_status)
            return merge_dict_of_list(media1_status, {_STATUS_SKIPPED: media_list})
        return self.download_file_from_media_info(media_list[0], local_download_dir)

    def download_files_for_metadata(self, metadata_id, local_download_dir) -> dict | None:
        """
        Download all the available files for a metadata
        :param metadata_id: the UUIDv4 of the metadata
        :param local_download_dir: the path to a local folder
        :return: an object that lists the files that were downloaded, skipped or found missing
        """
        if not isdir(local_download_dir):
            raise FileNotFoundError(f"The following folder does not exist: '{local_download_dir}'")
        meta = self.get_metadata_with_uuid(metadata_id)
        media_list = meta.get("available_formats")
        if not media_list:
            return None
        files_dwnld_info = {
            _STATUS_DOWNLOADED: [],
            _STATUS_MISSING: [],
            _STATUS_SKIPPED: [],
        }
        for media in media_list:
            dwnld_info = self.download_file_from_media_info(media, local_download_dir)
            files_dwnld_info = merge_dict_of_list(files_dwnld_info, dwnld_info)
        return files_dwnld_info


if __name__ == "__main__":  # pragma: no cover
    # ----------- INIT -----------
    tests = "RudiNodeApiConnector tests"
    begin = time()
    creds_file = "../../../creds/creds.json"
    rudi_node_creds = read_json_file(creds_file)

    node_jwt_factory = RudiNodeJwtFactory("https://bacasable.fenix.rudi-univ-rennes1.fr", rudi_node_creds)
    rudi_node = RudiNodeApiConnector(
        server_url="https://bacasable.fenix.rudi-univ-rennes1.fr",
        jwt_factory=node_jwt_factory,
    )

    # ----------- TESTS -----------
    test_dir = "../../../dwnld"
    # log_d(here, 'metadata_nb', rudi_node.metadata_count)
    # metadata_list = rudi_node.metadata_list
    # meta1 = metadata_list[0]
    # meta1_id = meta1['global_id']
    # log_d('RudiNodeApiConnector tests', 'meta1 id', meta1_id)
    # meta = rudi_node. get_metadata_with_uuid(meta1_id)
    # log_d('RudiNodeApiConnector tests', 'meta name', f"'{meta['resource_title']}'")
    log_d(tests, "producers", len(rudi_node.producers))
    log_d(tests, "producer names", rudi_node.producer_names)
    log_d(tests, "metadata_contacts", len(rudi_node.contacts))
    log_d(tests, "contact names", rudi_node.contact_names)
    # #
    # filter_dict = {'producer.organization_name': 'RUDI'}
    # log_d(here, 'get_metadata_with_filter', len(rudi_node.get_metadata_with_filter(filter_dict)))
    # log_d(here, 'get_metadata_with_filter',
    #       len(rudi_node.get_metadata_with_filter({'producer.organization_name': 'Gusikowski LLC'})))
    # log_d(here, 'get_metadata_with_producer Gusikowski LLC', len(rudi_node.get_metadata_with_producer('Gusikowski LLC')))
    # log_d(here, 'get_metadata_with_producer RUDI', len(rudi_node.get_metadata_with_producer('RUDI')))
    # log_d(here, 'get_metadata_with_contact Bacasable', len(rudi_node.get_metadata_with_contact('Bacasable')))
    # log_d(here, 'get_metadata_with_contact Wanda Torphy', len(rudi_node.get_metadata_with_contact('Wanda Torphy')))
    #
    log_d(tests, "themes", len(rudi_node.themes))
    log_d(tests, "used_themes", len(rudi_node.used_themes))
    log_d(tests, "keywords", len(rudi_node.keywords))
    log_d(tests, "used_keywords", len(rudi_node.used_keywords))

    # log_d(tests, {"a": [1, 2], "b": ["a", "b"]} | {"a": [0, 2], "b": ["aa", "bb"]})
    #
    # log_d(here, ' get_metadata_with_media_uuid',
    #       rudi_node. get_metadata_with_media_uuid('6027b6ec-d950-4e97-b200-b8c244e3a28d'))

    # ----------- TESTS: DWNLD -----------
    log_d(
        tests,
        "download_files_for_metadata",
        rudi_node.download_files_for_metadata("7480479d-92e0-4e1d-9987-44b1eccdde1a", test_dir),
    )

    log_d(
        tests,
        "download_file_with_media_uuid '782bab2d-7ee8-4633-9c0a-173649b4d879'",
        rudi_node.download_file_with_media_uuid("782bab2d-7ee8-4633-9c0a-173649b4d879", test_dir),
    )

    log_d(
        tests,
        f"download_file_with_name '782bab2d-7ee8-4633-9c0a-173649b4d879'",
        rudi_node.download_file_with_name("782bab2d-7ee8-4633-9c0a-173649b4d879", test_dir),
    )

    log_d(
        tests,
        "download_file_with_name 'toucan.jpg'",
        "\n" + str(rudi_node.download_file_with_name("toucan.jpg", test_dir)),
    )

    log_d(tests, "exec. time", time() - begin)
