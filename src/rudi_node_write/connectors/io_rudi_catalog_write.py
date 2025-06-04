from os.path import isdir
from time import time
from urllib.parse import quote


from rudi_node_write.connectors.io_connector import Connector, https_download
from rudi_node_write.connectors.io_rudi_jwt_factory import RudiNodeJwtFactory
from rudi_node_write.rudi_types.rudi_const import MEDIA_TYPE_FILE, RUDI_OBJECT_TYPES, RudiObjectTypeStr
from rudi_node_write.rudi_types.rudi_contact import RudiContact
from rudi_node_write.rudi_types.rudi_media import RudiMediaService, RudiMediaFile
from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.rudi_types.rudi_org import RudiOrganization
from rudi_node_write.rudi_types.serializable import Serializable
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
    HttpErrorNotFound,
)
from rudi_node_write.utils.file_utils import read_json_file, write_file
from rudi_node_write.utils.jwt import is_jwt_expired
from rudi_node_write.utils.list_utils import get_first_list_elt_or_none
from rudi_node_write.utils.log import log_d, log_e, log_w
from rudi_node_write.utils.str_utils import absolute_path, slash_join, uuid4_str, is_uuid_v4
from rudi_node_write.utils.typing_utils import get_type_name
from rudi_node_write.utils.url_utils import ensure_url_startswith


REQ_LIMIT = 500
_DELAY_REFRESH_S = 60  # seconds
_REFRESH_KEY = "refresh_time"  # seconds

_STATUS_SKIPPED = "skipped"
_STATUS_MISSING = "missing"
_STATUS_DOWNLOADED = "downloaded"

here = "RudiNodeCatalogConnector"


def ensure_url_startswith_api_admin(url):
    return ensure_url_startswith(url, "api/admin")


class RudiNodeCatalogConnector(Connector):
    def __init__(
        self,
        server_url: str,
        jwt_factory: RudiNodeJwtFactory | None = None,
        jwt: str | None = None,
        headers_user_agent: str = "RudiNodeCatalogConnector",
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
            "Content-Type": "text/plain",
            "Accept": "application/json",
        }
        if jwt_factory is not None:
            self.set_jwt_factory(jwt_factory)
        elif jwt is not None:
            self.set_jwt(jwt)
        else:
            raise AttributeError("Either a RudiNodeJwtFactory object or a valid JWT is required")
        self.test_connection()
        self._data_cache = {}

    def test_connection(self):
        test = self.request("api/admin/hash")
        if test is None:  # pragma: no cover
            log_e(here, f"!! Node '{self.host}'", "no connection!")
            raise ConnectionError(f"An error occurred while connecting to RUDI node JWT server {self.base_url}")

        # log_d(here, f"Node '{self.host}'", "connection OK")
        return test

    def set_jwt_factory(self, jwt_factory: RudiNodeJwtFactory) -> None:
        if not isinstance(jwt_factory, RudiNodeJwtFactory):
            raise TypeError("Input parameter should be of type 'RudiNodeJwtFactory'")
        self._jwt_factory = jwt_factory
        self._jwt_factory.test_connection()

    def set_jwt(self, jwt: str) -> None:
        if is_jwt_expired(jwt):
            raise ExpiredTokenException(jwt)
        self._stored_jwt = jwt

    @property
    def _jwt(self) -> str:
        if isinstance(self._jwt_factory, RudiNodeJwtFactory):
            return self._jwt_factory.get_jwt()
        if self._stored_jwt is None:
            raise NoNullException("a JWT is required, or a connector to a Rudi node JWT factory")
        if is_jwt_expired(self._stored_jwt):
            raise ExpiredTokenException(self._stored_jwt)
        return self._stored_jwt

    @property
    def _headers(self):
        return self._initial_headers | {"Authorization": f"Bearer {self._jwt}"}

    def get_admin_api(self, url: str, keep_alive: bool = False) -> str | int | list | dict:
        """
        Performs an identified GET request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param keep_alive: True if the connection should be kept alive (for successive requests). Use
        self.connection.close() in the end of your request series.
        :return: the result of the request, most likely a JSON
        """
        return self.request(
            req_method="GET",
            relative_url=ensure_url_startswith_api_admin(url),
            headers=self._headers,
            keep_alive=keep_alive,
        )  # type: ignore

    def put_admin_api(
        self, url: str, payload: dict | str | Serializable, headers: dict | None = None, keep_alive: bool = False
    ):
        """
        Performs an identified PUT request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        return self.request(
            req_method="PUT",
            relative_url=ensure_url_startswith_api_admin(url),
            headers=headers if headers else self._headers,
            body=payload,
            keep_alive=keep_alive,
        )

    def post_admin_api(
        self, url: str, payload: dict | str | Serializable, headers: dict | None = None, keep_alive: bool = False
    ):
        """
        Performs an identified PUT request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        return self.request(
            req_method="POST",
            relative_url=ensure_url_startswith_api_admin(url),
            headers=headers if headers else self._headers,
            body=payload,
            keep_alive=keep_alive,
        )

    def del_admin_api(self, url: str, headers: dict | None = None, keep_alive: bool = False):
        """
        Performs an identified PUT request through /api/admin path
        :param url: part of the URL that comes after /api/admin
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        return self.request(
            req_method="DELETE",
            relative_url=ensure_url_startswith_api_admin(url),
            headers=headers if headers else self._headers,
            keep_alive=keep_alive,
        )

    def _get_full_obj_list(self, url_bit: str, max_count: int = 0) -> list[dict]:
        """
        Utility function to get a full list of RUDI objects, using limit/offset to browse the whole collection.
        :param url_bit: requested URL, with possibly some request parameters separated from the base URL by a
        question mark
        :param max_count: a limit set to the number of results we need
        :return: a list of RUDI objects
        """
        here = f"{self.class_name}._get_full_obj_list"
        split_url = url_bit.split("?")
        base_url = split_url[0]
        params_str = f"{split_url[1]}&" if len(split_url) > 1 else ""

        obj_nb = int(self.get_admin_api(slash_join(base_url, "count")))

        log_d(here, "obj_nb", obj_nb)
        obj_set = []
        req_offset = 0
        req_max_count = obj_nb if max_count == 0 else min(obj_nb, max_count)

        while req_offset < req_max_count:
            req_limit = REQ_LIMIT if req_offset + REQ_LIMIT < req_max_count else req_max_count - req_offset
            partial_req_url = f"{base_url}?{params_str}sort_by=-updatedAt&limit={req_limit}&offset={req_offset}"
            obj_set += self.get_admin_api(partial_req_url, keep_alive=True)  # type: ignore
            req_offset += REQ_LIMIT
        self.close_connection()
        return obj_set

    def _clean_cache(self) -> None:
        if self._data_cache is None:
            self._data_cache = {}
        for cached_type in self._data_cache.keys():
            if time() - (self._data_cache[cached_type][_REFRESH_KEY]) > _DELAY_REFRESH_S:
                self._data_cache[cached_type] = None
        # TODO: check the date of the last modified object on source node

    def _get_cached_info(self, obj_type: RudiObjectTypeStr | str) -> list[dict] | list:
        """
        Access a list of RUDI objects (resources/metadata, contacts, producers/organizations, media) and get them in
        a temporary cache.
        :param obj_type: one of RUDI object types
        :return: the list of objects for this type
        """
        self._clean_cache()
        obj_data = self._data_cache.get(obj_type)
        if obj_data is None or time() - obj_data.get(_REFRESH_KEY) > _DELAY_REFRESH_S:
            if obj_type in RUDI_OBJECT_TYPES:
                self._data_cache[obj_type] = {
                    "data": self._get_full_obj_list(obj_type),
                    _REFRESH_KEY: time(),
                }
            else:
                self._data_cache[obj_type] = {
                    "data": self.get_admin_api(obj_type),
                    _REFRESH_KEY: time(),
                }
        return self._data_cache[obj_type]["data"]

    @property
    def organization_list(self) -> list[dict]:
        """
        :return: the list of the organizations/producers declared on the RUDI producer node
        """
        return self._get_cached_info("organizations")

    @property
    def producer_names(self) -> list[str]:
        """
        :return: the list of the names of the organizations/producers declared on the RUDI producer node
        """
        return sorted([org["organization_name"] for org in self.organization_list])

    def _get_producer_with_condition(self, condition: str) -> RudiOrganization | None:
        """
        :param condition: a key=value pair
        :return: the information associated with the producer on the RUDI node
        """
        orgs = self.get_admin_api(f"organizations?{condition}")
        return RudiOrganization.from_json(org) if (org := get_first_list_elt_or_none(orgs)) is not None else None

    def get_producer_with_name(self, org_name: str) -> RudiOrganization | None:
        """
        :param org_name: a producer name
        :return: the information associated with the producer on the RUDI node
        """
        return self._get_producer_with_condition(f"organization_name={org_name}")

    def get_producer_with_id(self, org_id: str) -> RudiOrganization | None:
        """
        :param org_id: a producer UUID v4
        :return: the information associated with the producer on the RUDI node
        """
        return self._get_producer_with_condition(f"organization_id={org_id}")

    def get_or_create_org_with_info(
        self, org_name: str, organization_info: dict | None = None
    ) -> RudiOrganization | None:
        """
        :param org_name: a producer name
        :param organization_info: additional organization info (address, GPS coordinates, etc.) that will be set if the
        producer organization doesn't already exist on the RUDI node
        :return: the information associated with the producer on the RUDI node
        """
        here = f"{self.class_name}.get_or_create_org_with_info"
        if org := self.get_producer_with_name(org_name):
            log_d(here, "found org", org)
            return org
        new_org_info = {"organization_name": org_name, "organization_id": uuid4_str()}
        if organization_info:
            new_org_info |= organization_info
        log_d(here, "new_org", new_org_info)
        if new_org := self.put_admin_api("organizations", new_org_info):
            return RudiOrganization.from_json(new_org)

    def delete_org_with_id(self, organization_id: str) -> RudiOrganization:
        """
        Delete organization using its id.
        :param organization_id: the UUID v4 identifier of the organization
        :return: the deleted organization
        """
        if is_uuid_v4(organization_id) and self.get_producer_with_id(organization_id):
            if deleted_org := self.del_admin_api(f"organizations/{organization_id}"):
                return RudiOrganization.from_json(deleted_org)
        raise HttpErrorNotFound(f"No organization was found with id '{organization_id}'")

    def delete_org_with_name(self, organization_name: str) -> RudiOrganization:
        """
        Delete organization using its name.
        :param organization_name: the name of the organization
        :return: the deleted organization
        """
        if org := self.get_producer_with_name(organization_name):
            if deleted_org := self.del_admin_api(f"organizations/{org.organization_id}"):
                return RudiOrganization.from_json(deleted_org)
        raise HttpErrorNotFound(f"No organization was found with name '{organization_name}'")

    # ----------[ Contacts ]--------------------------------------------------------------------------------------------
    @property
    def contact_list(self) -> list[dict]:
        """
        :return: the list of the metadata_contacts declared on the RUDI producer node
        """
        return self._get_cached_info("contacts")

    @property
    def contact_names(self) -> list[str]:
        """
        :return: the list of the names of the metadata_contacts declared on the RUDI producer node
        """
        return sorted([contact["contact_name"] for contact in self.contact_list])

    def _get_contact_with_condition(self, condition: str) -> RudiContact | None:
        """
        :param condition: a key=value pair
        :return: the information associated with the contact on the RUDI node, or None if none were found
        """
        contacts = self.get_admin_api(f"contacts?{condition}")
        return RudiContact.from_json(contact) if (contact := get_first_list_elt_or_none(contacts)) is not None else None

    def get_contact_with_name(self, contact_name: str) -> RudiContact | None:
        """
        :param contact_name: a contact name
        :return: the information associated with the contact on the RUDI node
        """
        return self._get_contact_with_condition(f"contact_name={contact_name}")

    def get_contact_with_email(self, email: str) -> RudiContact | None:
        """
        :param email: a contact email
        :return: the information associated with the contact on the RUDI node
        """
        return self._get_contact_with_condition(f"email={email}")

    def get_contact_with_name_or_email(self, contact_name: str, email: str) -> RudiContact | None:
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

    def get_or_create_contact_with_info(
        self, contact_name: str, contact_email: str, contact_info: dict | None = None
    ) -> RudiContact:
        """
        Finds a contact from input name or email, or creates it.
        :param contact_name: the name of the contact
        :param contact_email: the email of the contact
        :param contact_info: additional contact info (cf.
        https://app.swaggerhub.com/apis/OlivierMartineau/RUDI-PRODUCER/1.3.0#/Contact)
        :return: the information associated with the producer on the RUDI node
        """
        if (contact := self.get_contact_with_name_or_email(contact_name, contact_email)) is not None:
            return contact
        new_contact = {"contact_name": contact_name, "contact_id": uuid4_str(), "email": contact_email}
        if contact_info:
            new_contact |= contact_info
        return RudiContact.from_json(self.put_admin_api("contacts", new_contact))

    # ----------[ Enums ]-----------------------------------------------------------------------------------------------
    @property
    def themes(self) -> list[str]:
        """
        :return: the list of the themes declared on the RUDI producer node
        """
        return self._get_cached_info("enum/themes")  # type: ignore

    @property
    def keywords(self) -> list[str]:
        """
        :return: the list of the keywords declared on the RUDI producer node
        """
        return self._get_cached_info("enum/keywords")  # type: ignore

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
        return self._get_used_enums("theme")  # type: ignore

    @property
    def used_keywords(self) -> list[str]:
        """
        :return: the list of keywords used in the metadata on the RUDI producer node
        """
        return self._get_used_enums("keywords")  # type: ignore

    # ----------[ Metadata ]--------------------------------------------------------------------------------------------

    @property
    def metadata_count(self) -> int:
        """
        :return: the number of metadata declared on the RUDI producer node
        """
        return self._get_cached_info("resources/count")  # type: ignore

    @property
    def metadata_list(self):
        """
        :return: the full list of metadata declared on this RUDI producer node
        """
        return self._get_full_obj_list("resources")

    def _get_first_metadata_with_condition(self, condition: str) -> RudiMetadata | None:
        """
        :param condition: a key=value pair
        :return: the first metadata that verifies the condition, or None if it wasn't found
        """
        metadata_list = self.get_admin_api(f"resources?{condition}")
        return (
            RudiMetadata.from_json(metadata)
            if (metadata := get_first_list_elt_or_none(metadata_list)) is not None
            else None
        )

    def get_metadata_with_uuid(self, metadata_uuid: str) -> RudiMetadata | None:
        """
        :param metadata_uuid: a UUID v4
        :return: the metadata identified with the input UUID v4, or None if it wasn't found
        """
        return self._get_first_metadata_with_condition(f"global_id={metadata_uuid}")

    def get_metadata_with_source_id(self, source_id: str) -> RudiMetadata | None:
        """
        :param source_id: the ID used on the source server to identify a metadata
        :return: the metadata identified with the input source ID, or None if it wasn't found
        """
        return self._get_first_metadata_with_condition(f"local_id={source_id}")

    def get_metadata_with_title(self, title: str) -> RudiMetadata | None:
        """
        :param title: the title of a metadata
        :return: the metadata identified with the input title, or None if it wasn't found
        """
        return self._get_first_metadata_with_condition(f"resource_title={title}")

    def search_metadata_with_filter(self, rudi_fields_filter: dict) -> list[dict]:
        filter_str = ""
        for i, (key, val) in enumerate(rudi_fields_filter.items()):
            # TODO: special cases of producer / contact / available_formats
            filter_str += f"&{quote(key)}={quote(val)}"
        meta_list = self.get_admin_api(f"resources?{filter_str[1:]}&limit={REQ_LIMIT}")
        if isinstance(meta_list, list):
            if len(meta_list) < REQ_LIMIT:
                return meta_list
            else:
                return self._get_full_obj_list(f"resources?{filter_str[1:]}")
        else:
            raise ValueError("Expected the request to return a list")

    def search_metadata_with_available_media(self) -> list[dict]:
        return self._get_full_obj_list("resources?available_formats.file_storage_status=available")

    def _search_metadata_with_obj_name(self, obj_prop: str, obj_name: str) -> list[dict]:
        meta_list = self.get_admin_api(f"resources?{obj_prop}={quote(obj_name)}&limit={REQ_LIMIT}")
        if not isinstance(meta_list, list):
            raise Exception(f"Expected result was a list, got {get_type_name( meta_list)}: {meta_list}")
        if len(meta_list) < REQ_LIMIT:
            return meta_list
        else:
            meta_count_list = self.get_admin_api(f"resources?{obj_prop}={quote(obj_name)}&count_by={obj_prop}")
        if not isinstance(meta_count_list, list):
            raise Exception(f"Expected result was a list, got {get_type_name( meta_count_list)}: {meta_count_list}")
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
        if meta is None:
            return []
        media_list = meta.available_formats
        media_list_final = []
        for media in media_list:
            media_list_final.append(
                {
                    "id": media.media_id,
                    "type": media.media_type,
                    "name": media.media_name,
                    "url": media.connector.url,
                }
            )
        return media_list_final

    def search_metadata_with_media_name(self, media_name: str) -> list[dict] | None:
        """
        :param media_name: name of the media
        :return: metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self._get_full_obj_list(f"resources?available_formats.media_name={media_name}")

    def search_metadata_with_media_uuid(self, media_uuid: str) -> list[dict] | None:
        """
        :param media_uuid: UUIDv4 of the media
        :return: metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self._get_full_obj_list(f"resources?available_formats.media_id={media_uuid}")

    # ----------[ Media ]-----------------------------------------------------------------------------------------------

    def get_media_with_uuid(self, media_uuid: str) -> dict | None:
        """
        Get the media information from a media ID.
        Check this link for more details about the structure of the media information:
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Media
        :param media_uuid: UUID v4 of the media.
        :return: media whose `media_id` attribute matches the `media_uuid` input parameter.
        """
        return self.get_admin_api(f"media/{media_uuid}")  # type: ignore

    def search_available_media_with_name(self, media_name: str) -> list[dict]:
        """
        Get the information for every media that has the name given as input.
        Check this link for more details about the structure of the media information:
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Media
        :param media_name: the name of the media.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return self.get_admin_api(f"media?media_name={media_name}&file_storage_status=available")  # type: ignore

    def get_media_file_with_info(self, media_name: str, file_size: int, checksum: str) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media_name: the name of the media.
        :param file_size: the size of the RudiMediaFile.
        :param checksum: the checksum of the RudiMediaFile.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return get_first_list_elt_or_none(
            self.get_admin_api(
                f"media?media_type=FILE&file_storage_status=available"
                f"&media_name={media_name}&file_size={file_size}&checksum.hash={checksum}&"
            )
        )  # type: ignore

    def get_media_file_with_rudi_obj(self, media: RudiMediaFile) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media: a RudiMediaFile object
        :return: media info whose name, size and checksum attributes matches the media input parameters.
        """
        return get_first_list_elt_or_none(
            self.get_admin_api(
                f"media?media_type=FILE&file_storage_status=available"
                f"&media_name={media.media_name}&file_size={media.file_size}&checksum.hash={media.checksum}&"
            )
        )  # type: ignore

    def get_media_service_with_info(self, media_name: str, url: str) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media_name: the name of the media.
        :param url: the url of the RudiMediaService.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return get_first_list_elt_or_none(
            self.get_admin_api(f"media?media_type=SERVICE&media_name={media_name}&connector.url={url}")
        )  # type: ignore

    def get_media_service_with_rudi_obj(self, media: RudiMediaService) -> dict:
        """
        Finds a RudiMediaService with input information (except the id: we're looking for a similar object already
        existing)
        :param media: a RudiMediaService object
        :return: media info whose `media_name` and 'source_url' attributes match the `media_name` and 'source_url'
        input parameters.
        """
        return get_first_list_elt_or_none(
            self.get_admin_api(
                f"media?media_type=SERVICE&media_name={media.media_name}&connector.url={media.source_url}"
            )
        )  # type: ignore

    @staticmethod
    def download_file_from_media_info(media: dict, local_download_dir: str) -> dict:
        """
        Download a file from its media metadata
        :param media: the file metadata (as found in the RUDI metadata `available_formats` attribute
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        here = "RudiNodeCatalogConnector.download_file_from_media_info"

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
        assert isinstance(media_name, str)
        media_url = safe_get_key(media, "connector", "url")
        if not media_url:
            raise FileNotFoundError(f"No URL was provided for the media {media_name}")

        destination_path = absolute_path(local_download_dir, media_name)
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
        here = f"{self.class_name}..download_file_with_name"
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
        if meta is None:
            return None
        media_list = meta.available_formats
        if not media_list:
            return None
        files_dwnld_info = {
            _STATUS_DOWNLOADED: [],
            _STATUS_MISSING: [],
            _STATUS_SKIPPED: [],
        }
        for media in media_list:
            dwnld_info = self.download_file_from_media_info(media.to_json(), local_download_dir)
            files_dwnld_info = merge_dict_of_list(files_dwnld_info, dwnld_info)
        return files_dwnld_info


if __name__ == "__main__":  # pragma: no cover
    # ----------- INIT -----------
    tests = "RudiNodeCatalogConnector tests"
    begin = time()
    creds_file = "../creds/creds_bas.json"
    rudi_node_creds = read_json_file(creds_file)
    url = rudi_node_creds["url"]

    jwt_factory = RudiNodeJwtFactory(url, rudi_node_creds)
    catalog = RudiNodeCatalogConnector(server_url=url, jwt_factory=jwt_factory)

    # ----------- TESTS -----------
    test_dir = "../dwnld"
    log_d(tests, "producers", len(catalog.organization_list))
    log_d(tests, "producer names", catalog.producer_names)
    log_d(tests, "metadata_contacts", len(catalog.contact_list))
    log_d(tests, "contact names", catalog.contact_names)

    log_d(tests, "themes", len(catalog.themes))
    log_d(tests, "used_themes", len(catalog.used_themes))
    log_d(tests, "keywords", len(catalog.keywords))
    log_d(tests, "used_keywords", len(catalog.used_keywords))

    #
    # log_d(here, ' get_metadata_with_media_uuid',
    #       rudi_node. get_metadata_with_media_uuid('6027b6ec-d950-4e97-b200-b8c244e3a28d'))

    # ----------- TESTS: DWNLD -----------
    log_d(
        tests,
        "download_files_for_metadata",
        catalog.download_files_for_metadata("65d99589-7a7a-46a3-afe8-c5a47b964310", test_dir),
    )

    log_d(
        tests,
        "download_file_with_media_uuid '782bab2d-7ee8-4633-9c0a-173649b4d879'",
        catalog.download_file_with_media_uuid("fef11852-0756-4cbe-bdfb-3722a1751de9", test_dir),
    )

    log_d(
        tests,
        "download_file_with_name '782bab2d-7ee8-4633-9c0a-173649b4d879'",
        catalog.download_file_with_name("782bab2d-7ee8-4633-9c0a-173649b4d879", test_dir),
    )

    log_d(
        tests,
        "download_file_with_name 'toucan.jpg'",
        "\n" + str(catalog.download_file_with_name("toucan.jpg", test_dir)),
    )

    log_d(tests, "exec. time", time() - begin)
