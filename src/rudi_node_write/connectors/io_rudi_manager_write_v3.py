from http.client import IncompleteRead
from json import dumps
from os.path import exists, isdir
from re import T
from time import time
from typing import Literal
from urllib.parse import quote

from rudi_node_write.connectors.io_connector import Connector, https_download
from rudi_node_write.connectors.io_rudi_manager_write import CONSOLE_JWT_NAME, RudiNodeManagerConnector
from rudi_node_write.connectors.rudi_node_auth import RudiNodeAuth
from rudi_node_write.rudi_types.rudi_const import (
    MEDIA_TYPE_FILE,
    MIME_TYPES_UTF8_TEXT,
    RUDI_OBJECT_TYPES,
    RudiObjectTypeStr,
)
from rudi_node_write.rudi_types.rudi_contact import RudiContact
from rudi_node_write.rudi_types.rudi_media import RudiMediaFile, RudiMediaService
from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.rudi_types.rudi_org import RudiOrganization
from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.dict_utils import check_is_dict, merge_dict_of_list, pick_in_dict, safe_get_key
from rudi_node_write.utils.err import HttpError, HttpErrorNotFound, UnexpectedValueException
from rudi_node_write.utils.file_utils import check_is_file, read_json_file, write_file
from rudi_node_write.utils.jwt import is_jwt_expired
from rudi_node_write.utils.list_utils import get_first_list_elt_or_none
from rudi_node_write.utils.log import log_d, log_e, log_w
from rudi_node_write.utils.str_utils import absolute_path, check_is_uuid4, is_uuid_v4, slash_join, uuid4_str
from rudi_node_write.utils.type_date import Date
from rudi_node_write.utils.typing_utils import check_is_int, get_type_name
from rudi_node_write.utils.url_utils import ensure_url_startswith


# Defaults for constructor
_DEFAULT_USER_AGENT = "RudiNodeManagerConnectorV3"

# Manager API prefixes
MGR_CATALOG_PREFIX = "catalog"
OLD_MGR_CATALOG_PREFIX = "data"

REQ_LIMIT = 500
_DELAY_REFRESH_S = 60  # seconds
_REFRESH_KEY = "refresh_time"  # seconds

_STATUS_SKIPPED = "skipped"
_STATUS_MISSING = "missing"
_STATUS_DOWNLOADED = "downloaded"


here = "RudiNodeManagerConnectorV3"


def ensure_url_startswith_catalog(url):
    if url.startswith(MGR_CATALOG_PREFIX) or url.startswith(OLD_MGR_CATALOG_PREFIX):
        return url
    return ensure_url_startswith(url, MGR_CATALOG_PREFIX)


class RudiNodeManagerConnectorV3(RudiNodeManagerConnector):
    """
    Every RUDI node has a UI module called "RUDI node manager", or "Manager" for shorts,
    that offers to list, edit or create RUDI metadata, given that you have the required level of access.
    This library takes advantage of the manager backend API to send data and metadata.
    "GenC" stands for "Generation C", as this particular file takes advantage of the 3rd generation of RUDI node interface.
    """

    def __init__(
        self,
        server_url: str,
        auth: RudiNodeAuth | dict,
        name: str | None = None,
        headers_user_agent: str = _DEFAULT_USER_AGENT,
        keep_connection: bool = False,
    ):
        super().__init__(
            server_url=server_url,
            auth=auth,
            name=name,
            headers_user_agent=headers_user_agent,
            keep_connection=keep_connection,
        )
        self._gen = 3

        self._cached_api_version = None
        self._cached_conf = None

        self._cached_manager_jwt = None
        self._cached_manager_headers = None

        self._cached_storage_url = None
        self._cached_storage_jwt = None
        self._cached_storage_connector = None

        self.conf
        # self.test_identified_connection()

    @property
    def conf(self):
        if self._cached_conf is None:
            try:
                conf = self.request(req_method="GET", relative_url="conf")
                if not isinstance(conf, dict):
                    raise TypeError(f"Result should be a Python 'dict'. Got: '{get_type_name(conf)}'")
                # log_d(here, "conf", conf)
                self.catalog_url = conf["catalogPubUrl"]
                self._cached_storage_url = conf["storagePubUrl"]
                self.manager_path = conf["managerPath"]
                self.manager_url = slash_join(f"{self.scheme}://{self.host}", self.manager_path)
                self.back_path = conf["backPath"]

                # Every request to the connector will be relative to <node_url>/<manager_api_prefix>
                self.set_path(self.back_path)
                self.back_url = self.base_url

                self._cached_conf = conf
                self._gen = 3
            except:
                raise NotImplementedError("This node version is not compatible with this object")
        return self._cached_conf

    # ----------[ Basic API calls ]-------------------------------------------------------------------------------------
    def get_api(self, url: str, headers: dict, keep_alive: bool = False):
        """
        Performs an identified GET request through /api path
        :param url: part of the URL that comes after /api
        :param keep_alive: True if the connection should be kept alive (for successive requests). Use
        self.connection.close() in the end of your request series.
        :return: the result of the request, most likely a JSON
        """
        return self.request(
            req_method="GET",
            relative_url=url,
            headers=headers,
            keep_alive=keep_alive,
        )

    def put_api(self, url: str, body: dict | str, headers: dict, keep_alive: bool = False):
        """
        Performs an identified PUT request through /api path
        :param url: part of the URL that comes after /api
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        return self.request(
            req_method="PUT",
            relative_url=url,
            headers=headers,
            body=body,
            keep_alive=keep_alive,
        )

    def post_api(self, url: str, body: dict | str, headers: dict, keep_alive: bool = False):
        """
        Performs an identified PUT request through /api path
        :param url: part of the URL that comes after /api
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        return self.request(
            req_method="POST",
            relative_url=url,
            headers=headers,
            body=body,
            keep_alive=keep_alive,
        )

    def del_api(self, url: str, headers: dict, keep_alive: bool = False):
        """
        Performs an identified PUT request through /api path
        :param url: part of the URL that comes after /api
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        return self.request(
            req_method="DELETE",
            relative_url=url,
            headers=headers,
            keep_alive=keep_alive,
        )

    def test_connection(self):
        test = self.get_api(url="open/test", headers=self._def_headers)
        if test == "test":
            log_d(here, f"Node '{self.host}'", "connection OK")
            # log_d(here, f"Node '{self.host}'", "connection OK")
            return True
        log_e(here, f"!! Address {self.base_url}/open/test:", test, "=> no connection!")
        raise ConnectionError(f"An error occurred while connecting to RUDI node manager on {self.base_url}/open/test")

    def test_identified_connection(self):
        self.test_connection()
        try:
            self.get_api(url="catalog/uuid", headers=self._id_headers)
        except HttpError:
            raise ConnectionError(f"Identifiers seem to be not working for the node: {self.server_url}")
        return True

    @property
    def api_version(self) -> str:
        """
        Gives the API version of the node. I.e. make a get request to the rudi-node external API through the
        manager to know the api version.
        """
        version = self.get_cache("catalog/version")
        if not isinstance(version, str):
            raise TypeError("Could not get RUDI node Catalog's API version")
        return version

    @property
    def tags(self):
        return self.get_api(url="open/tags", headers=self._def_headers)

    @property
    def hash(self):
        return self.get_api(url="open/hash", headers=self._def_headers)

    @property
    def _def_headers(self):
        return {
            "User-Agent": self._headers_user_agent,
            "Content-Type": "text/plain; charset=utf-8",
            "Accept": "application/json",
        }

    # ----------[ JWT ]-------------------------------------------------------------------------------------------------
    @property
    def _manager_jwt(self):
        if is_jwt_expired(self._cached_manager_jwt):
            self.post_api(
                url="front/login",
                body={"username": self._usr, "password": self._pwd},
                headers=self._def_headers,
            )
            if self._cookies is None:
                raise AssertionError("No cookies were found in the server response")
            # log_d(here, "get_user_cookies", self._cookies)

            self._cached_manager_jwt = self._cookies[CONSOLE_JWT_NAME]
            # log_d(here, "get_user_cookies", self._pm_cookie)
        return self._cached_manager_jwt

    @property
    def _id_headers(self):
        if self._cached_manager_headers is None:
            # Headers initialization
            self._cached_manager_headers = self._def_headers | {"Authorization": f"Bearer {self._manager_jwt}"}
        elif is_jwt_expired(self._cached_manager_jwt):
            # Headers are now obsolete, need a refresh
            self._cached_manager_headers["Authorization"] = f"Bearer {self._manager_jwt}"
        return self._cached_manager_headers

    def set_storage_url(self, storage_url: str):
        self._cached_storage_url = storage_url

    @property
    def init_data(self):
        return self.get_cache("front/init-data")

    @property
    def node_urls(self):
        try:
            return self.get_cache("front/node-urls")
        except Exception:
            log_w(here, "The server does not know the URL: front/node-urls")
            return None

    @property
    def _storage_jwt(self) -> str:
        here = "_storage_jwt"
        if is_jwt_expired(self._cached_storage_jwt):
            res = self.get_api(url="storage/jwt", headers=self._id_headers)

            if not isinstance(res, dict):
                raise TypeError(f"An error occurred while getting Storage JWT: got {res}")
            jwt = f'{res.get("token")}'
            # log_d(here, "jwt:", jwt)
            if is_jwt_expired(jwt):
                raise HttpErrorNotFound(f"Could not access a valid JWT, got: {jwt}")
            self._cached_storage_jwt = jwt
        assert self._cached_storage_jwt is not None
        return self._cached_storage_jwt

    @property
    def storage_connector(self):
        if self._cached_storage_connector is None:
            self._cached_storage_connector = RudiNodeStorageConnectorV3(self.storage_url, self._storage_jwt)
        if is_jwt_expired(self._cached_storage_connector.jwt):
            self._cached_storage_connector.jwt = self._storage_jwt
        return self._cached_storage_connector

    # ----------[ Identified API calls ]--------------------------------------------------------------------------------

    def get_catalog(self, url: str, keep_alive: bool = False):
        """
        Performs an identified GET request through /api path
        :param url: part of the URL that comes after /api
        :param keep_alive: True if the connection should be kept alive (for successive requests). Use
        self.connection.close() in the end of your request series.
        :return: the result of the request, most likely a JSON
        """
        return self.request(
            req_method="GET",
            relative_url=ensure_url_startswith_catalog(url),
            headers=self._id_headers,
            keep_alive=keep_alive,
        )

    def put_catalog(self, url: str, body: dict | str | Serializable, keep_alive: bool = False):
        """
        Performs an identified PUT request through /api/data path
        :param url: part of the URL that comes after /api/data
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        # here = f"{self.__class__.__name__}.put_catalog"
        self._force_clean_cache()
        return self.request(
            req_method="PUT",
            relative_url=ensure_url_startswith_catalog(url),
            headers=self._id_headers,
            body=body,
            keep_alive=keep_alive,
        )

    def del_catalog(self, url: str, keep_alive: bool = False):
        """
        Performs an identified PUT request through /api/data path
        :param url: part of the URL that comes after /api/data
        :param payload: the PUT request payload
        :return: the answer, most likely as a JSON
        """
        self._force_clean_cache()
        return self.request(
            req_method="DELETE",
            relative_url=ensure_url_startswith_catalog(url),
            headers=self._id_headers,
            keep_alive=keep_alive,
        )

    def get_api_data(self, url: str, keep_alive: bool = False):
        return self.get_catalog(url=url, keep_alive=keep_alive)

    def put_api_data(self, url: str, body: dict | str | Serializable, keep_alive: bool = False):
        return self.put_catalog(url=url, body=body, keep_alive=keep_alive)

    def del_api_data(self, url: str, keep_alive: bool = False):
        return self.del_catalog(url=url, keep_alive=keep_alive)

    # ----------[ Caching data ]----------------------------------------------------------------------------------------
    def _force_clean_cache(self) -> None:
        self._data_cache = {}

    def _clean_obsolete_cache(self) -> None:
        if self._data_cache is None:
            self._data_cache = {}
        for cached_type in self._data_cache.keys():
            obj_cache = self._data_cache.get(cached_type)
            if obj_cache is not None and ((time() - obj_cache[_REFRESH_KEY]) > _DELAY_REFRESH_S):
                self._data_cache[cached_type] = None
        # TODO: check the date of the last modified object on source node

    def get_cache(self, url: str):
        """
        Access a list of RUDI objects and store them in a temporary cache:
        - 'resources' (= metadata)
        - 'organizations' (= producers)
        - 'contacts'
        - 'media' (= files, although some can be RudiService objects, i.e. URLs)
        Additionally, you can access any URL on the node and cache the result for later use.
        :param obj_type: one of RUDI object types
        :return: the list of objects for this type
        """
        self._clean_obsolete_cache()
        if url is None:
            raise ValueError("Input parameter should not be None")
        obj_cache = self._data_cache.get(url)

        if obj_cache is None or time() - obj_cache.get(_REFRESH_KEY) > _DELAY_REFRESH_S:
            if url in RUDI_OBJECT_TYPES:
                data: list[dict] = self._get_full_obj_list(url)
            else:
                data = self.get_api(url=url, headers=self._id_headers)  # type: ignore

            self._data_cache[url] = {"data": data, _REFRESH_KEY: time()}
        obj_data = self._data_cache[url]["data"]
        # if not isinstance(obj_data, (list, dict)):
        #     raise TypeError(f"Resulting data should be a JSON or a list, got:\n{obj_data}")
        return obj_data

    def get_catalog_cached(self, obj_type: RudiObjectTypeStr | str) -> list[dict] | dict:  # type: ignore
        """
        Access a list of RUDI objects and store them in a temporary cache:
        - 'resources' (= metadata)
        - 'organizations' (= producers)
        - 'contacts'
        - 'media' (= files, although some can be RudiService objects, i.e. URLs)
        :param obj_type: one of RUDI object types
        :return: the list of objects for this type
        """
        here = f"{self.class_name}.get_data"

        if obj_type in RUDI_OBJECT_TYPES:
            if not (self._gen == 1 and obj_type == "media"):
                return self.get_cache(obj_type)
            else:
                log_w(here, "Legacy node, request not available for 'media'")
                return {}
        else:
            return self.get_cache(ensure_url_startswith_catalog(obj_type))

    # ----------[ Requesting data ]-------------------------------------------------------------------------------------

    def _count_obj(self, obj_type: RudiObjectTypeStr | str) -> int:
        if obj_type not in RUDI_OBJECT_TYPES:
            raise ValueError(f"Input parameter expected to be in {RUDI_OBJECT_TYPES}, got '{obj_type}‘")
        obj_nb = int(self.get_catalog_cached(slash_join(obj_type, "count")))  # type: ignore
        return obj_nb

    def _get_full_obj_list(self, url_bit: str, max_count: int = 0) -> list[dict]:
        """
        Utility function to get a full list of RUDI objects, using limit/offset to browse the whole collection.
        :param url_bit: requested URL, with possibly some request parameters separated from the base URL by a
        question mark
        :param max_count: a limit set to the number of results we need
        :return: a list of RUDI objects
        """
        here = f"{self.class_name}._get_full_obj_list({url_bit})"
        split_url = url_bit.split("?")
        path = split_url[0]
        params_str = f"{split_url[1]}&" if len(split_url) > 1 else ""

        obj_nb = self._count_obj(path)

        log_d(here, "obj_nb", obj_nb)
        obj_set = []
        req_offset = 0
        req_max_count = obj_nb if max_count == 0 else min(obj_nb, max_count)

        while req_offset < req_max_count:
            req_limit = REQ_LIMIT if req_offset + REQ_LIMIT < req_max_count else req_max_count - req_offset
            partial_req_url = f"{path}?{params_str}sort_by=-updatedAt&limit={req_limit}&offset={req_offset}"
            obj_subset = self.get_catalog(partial_req_url, keep_alive=True)
            if isinstance(obj_subset, list):
                obj_set += obj_subset
            else:
                if obj_subset is not None:
                    log_e(here, "should be a list", obj_subset)
            req_offset += REQ_LIMIT
        self.close_connection()
        return obj_set

    @property
    def last_metadata_update_date(self) -> Date | None:
        res = self.get_catalog_cached("resources?sort_by=-updatedAt&fields=updatedAt&limit=1")
        if not isinstance(res, list):
            raise TypeError(f"The server should have returned a list, got:\n{res}")
        if len(res) == 0:
            return None
        update_date = res[0].get("updatedAt")
        return Date(update_date)

    @property
    def last_data_update_date(self) -> Date | None:
        res = self.get_catalog_cached("resources?sort_by=-dataset_dates.updated&limit=1&fields=dataset_dates.updated")
        # print("last_data_update_date", res)
        if not isinstance(res, list):
            raise TypeError(f"The server should have returned a list, got:\n{res}")
        if len(res) == 0:
            return None
        update_date = safe_get_key(res[0], "dataset_dates", "updated")
        return Date(update_date)

    # ----------[ Data access as properties ]---------------------------------------------------------------------------

    @property
    def organization_list(self) -> list[dict]:
        """
        :return: the list of the organizations/producers declared on the RUDI producer node
        """
        return self.get_catalog_cached("organizations")  # type: ignore

    @property
    def contact_list(self) -> list[dict]:
        """
        :return: the list of the metadata contacts declared on the RUDI producer node
        """
        return self.get_catalog_cached("contacts")  # type: ignore

    @property
    def media_list(self) -> list[dict]:
        """
        :return: the list of the media declared on the RUDI producer node
        """
        here = f"{self.class_name}.media_list"
        list_medias = None
        if not self._gen == 1:
            try:
                list_medias = self.get_catalog_cached("media")
            except:
                log_w(here, f"Cannot acces /catalog/media on node {self.base_url}")
                self._gen = 1

        if not isinstance(list_medias, list) or len(list_medias) == 0:
            medias = {}
            metadatas = self.metadata_list
            for meta in metadatas:
                for media in meta["available_formats"]:
                    medias[media["media_id"]] = media
            list_medias = list(medias.values())
            self._data_cache["media"] = {"data": list_medias, _REFRESH_KEY: time()}
        return list_medias

    @property
    def organization_names(self) -> list[str]:
        """
        :return: the list of the names of the organizations/producers declared on the RUDI producer node
        """
        return sorted([org["organization_name"] for org in self.organization_list])

    @property
    def contact_names(self) -> list[str]:
        """
        :return: the list of the names of the metadata_contacts declared on the RUDI producer node
        """
        return sorted([contact["contact_name"] for contact in self.contact_list])

    @property
    def media_names(self) -> list[dict]:
        """
        :return: the list of the names of the media declared on the RUDI producer node
        """
        return sorted([media["media_name"] for media in self.media_list])

    @property
    def metadata_count(self) -> int:
        """
        :return: the number of metadata declared on the RUDI producer node
        """
        return self._count_obj("resources")

    @property
    def metadata_list(self) -> list[dict]:
        """
        :return: the full list of metadata declared on this RUDI producer node
        """
        return self.get_catalog_cached("resources")  # type: ignore

    @property
    def used_organization_list(self) -> list[dict]:
        here = "used_organization_list"
        used_orgs = {}
        for meta in self.metadata_list:
            producer_info: dict = safe_get_key(meta, "producer")  # type: ignore
            producer_id: str = check_is_uuid4(safe_get_key(producer_info, "organization_id"))
            used_orgs[producer_id] = producer_info
            publisher_info: dict | None = safe_get_key(meta, "metadata_info", "metadata_provider")  # type: ignore
            if publisher_info is not None:
                publisher_id = safe_get_key(publisher_info, "organization_id")
                used_orgs[publisher_id] = publisher_info
        return sorted(list(used_orgs.values()), key=lambda org: org["organization_name"])

    @property
    def used_contact_list(self) -> list[dict]:
        used_contacts = {}
        for meta in self.metadata_list:
            meta_contacts = safe_get_key(meta, "contacts")
            if not isinstance(meta_contacts, list):
                raise TypeError("Contacts should be a list of dict")
            if isinstance(publisher_contacts := safe_get_key(meta, "metadata_info", "metadata_contacts"), list):
                meta_contacts = meta_contacts + publisher_contacts
            for contact in meta_contacts:
                prod_contact_id = safe_get_key(contact, "contact_id")
                used_contacts[prod_contact_id] = contact
        return sorted(list(used_contacts.values()), key=lambda contact: contact["contact_name"])

    @property
    def used_media_list(self) -> list[dict]:
        used_medias = {}
        for meta in self.metadata_list:
            meta_medias = safe_get_key(meta, "available_formats")
            if not isinstance(meta_medias, list):
                raise Exception("Available formats should be a list of dict")
            for media in meta_medias:
                media_id = safe_get_key(media, "media_id")
                used_medias[media_id] = media
        return sorted(list(used_medias.values()), key=lambda media: media["media_name"])

    # ----------[ Organizations / producers ]---------------------------------------------------------------------------

    def _get_producer_with_condition(self, condition: str) -> RudiOrganization | None:
        """
        :param condition: a key=value pair
        :return: the information associated with the producer on the RUDI node
        """
        orgs = self.get_catalog_cached(f"organizations?{condition}")
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
        if isinstance(organization_info, dict):
            new_org_info |= organization_info
        log_d(here, "new_org", new_org_info)
        if new_org := self.put_catalog("organizations", new_org_info):
            return RudiOrganization.from_json(new_org)  # type: ignore

    def delete_org_with_id(self, organization_id: str) -> RudiOrganization:
        """
        Delete organization using its id.
        :param organization_id: the UUID v4 identifier of the organization
        :return: the deleted organization
        """
        if is_uuid_v4(organization_id) and self.get_producer_with_id(organization_id):
            if deleted_org := self.del_catalog(f"organizations/{organization_id}"):
                if isinstance(deleted_org, dict):
                    return RudiOrganization.from_json(deleted_org)
                raise TypeError(
                    f"Unexpected response type, expected a RudiOrganization compatible 'dict', got {type(deleted_org)}"
                )
        raise HttpErrorNotFound(f"No organization was found with id '{organization_id}'")

    def delete_org_with_name(self, organization_name: str) -> RudiOrganization:
        """
        Delete organization using its name.
        :param organization_name: the name of the organization
        :return: the deleted organization
        """
        if org := self.get_producer_with_name(organization_name):
            if deleted_org := self.del_catalog(f"organizations/{org.organization_id}"):
                if isinstance(deleted_org, dict):
                    return RudiOrganization.from_json(deleted_org)
                else:
                    raise TypeError(f"The RUDI node should have returned a dict, got : {deleted_org}")
        raise HttpErrorNotFound(f"No organization was found with name '{organization_name}'")

    # ----------[ Contacts ]--------------------------------------------------------------------------------------------

    def _get_contact_with_condition(self, condition: str) -> RudiContact | None:
        """
        :param condition: a key=value pair
        :return: the information associated with the contact on the RUDI node, or None if none were found
        """
        contacts = self.get_catalog_cached(f"contacts?{condition}")
        return RudiContact.from_json(contact) if (contact := get_first_list_elt_or_none(contacts)) is not None else None  # type: ignore

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
        if contact_info is not None:
            new_contact |= contact_info
        return RudiContact.from_json(self.put_catalog("contacts", new_contact))  # type: ignore

    # ----------[ Enums ]-----------------------------------------------------------------------------------------------
    @property
    def enums(self) -> dict:
        """
        :return: the list of the themes declared on the RUDI producer node
        """
        return self.get_catalog_cached("enum")  # type: ignore

    @property
    def themes(self) -> list[str]:
        """
        :return: the list of the themes declared on the RUDI producer node
        """
        return self.get_catalog_cached("enum/themes/fr")  # type: ignore

    @property
    def keywords(self) -> list[str]:
        """
        :return: the list of the keywords declared on the RUDI producer node
        """
        return self.enums["keywords"]

    def _get_used_enums(self, enum_type: Literal["theme", "keywords"]) -> list[str]:
        """
        Utility function to get the list of the enums used in the metadata declared on the RUDI producer node
        :param enum_type: 'theme' | 'keywords'
        :return: the list of the enums used in the metadata declared on the RUDI producer node
        """
        enum_count_list = self.get_catalog_cached(f"resources?count_by={enum_type}")
        if len(enum_count_list) == 0:
            return []
        return [enum_count[enum_type] for enum_count in enum_count_list]

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

    def _get_first_metadata_with_condition(self, condition: str) -> RudiMetadata | None:
        """
        :param condition: a key=value pair
        :return: the first metadata that verifies the condition, or None if it wasn't found
        """
        metadata_list = self.get_catalog_cached(f"resources?{condition}")
        if (metadata := get_first_list_elt_or_none(metadata_list)) is not None and isinstance(metadata, dict):
            return RudiMetadata.from_json(metadata)
        else:
            return None

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
        meta_list = self.get_catalog_cached(f"resources?{filter_str}&limit={REQ_LIMIT}")
        if not isinstance(meta_list, list):
            raise TypeError(f"The server should have returned a list, got:\n{meta_list}")
        return meta_list
        # if len(meta_list) < REQ_LIMIT:
        #     return meta_list
        # else:
        #     return self._get_full_obj_list(f"resources?{filter_str}")

    def select_metadata_with_available_media(self) -> list[dict]:
        meta_list = self.get_catalog_cached("resources?available_formats.file_storage_status=available")
        if not isinstance(meta_list, list):
            raise TypeError(f"The server should have returned a list, got:\n{meta_list}")
        return meta_list

    def put_metadata(self, metadata: dict | RudiMetadata):
        if isinstance(metadata, dict):
            rudi_meta: RudiMetadata = RudiMetadata.from_json(metadata)
        elif isinstance(metadata, RudiMetadata):
            rudi_meta: RudiMetadata = metadata
        else:
            raise ValueError('Input should be of type "RudiMetadata" or a dict with the RUDI metadata structure.')
        return self.put_catalog("resources", rudi_meta)

    def create_or_update_meta(self, metadata: dict | RudiMetadata):
        return self.put_metadata(metadata)

    def _search_metadata_with_obj_name(self, obj_prop, obj_name: str) -> list[dict]:
        meta_list = self.get_catalog_cached(f"resources?{obj_prop}={quote(obj_name)}&limit={REQ_LIMIT}")
        if not isinstance(meta_list, list):
            raise TypeError("The server should have returned a list, an error occurred on the server side.")
        if len(meta_list) < REQ_LIMIT:
            return meta_list
        else:
            meta_count_list = self.get_catalog_cached(f"resources?{obj_prop}={quote(obj_name)}&count_by={obj_prop}")
            if not isinstance(meta_count_list, list):
                raise TypeError(f"The server should have returned a list, got:\n{meta_count_list}")

            meta_nb = check_is_int(meta_count_list[0].get("count"))
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
        return self.get_catalog_cached(f"media/{media_uuid}")  # type: ignore

    def search_available_media_with_name(self, media_name: str) -> list[dict]:
        """
        Get the information for every media that has the name given as input.
        Check this link for more details about the structure of the media information:
        https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI/1.3.0#/Media
        :param media_name: the name of the media.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return self.get_catalog_cached(f"media?media_name={media_name}&file_storage_status=available")  # type: ignore

    def get_media_file_with_info(self, media_name: str, file_size: int, checksum: str) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media_name: the name of the media.
        :param file_size: the size of the RudiMediaFile.
        :param checksum: the checksum of the RudiMediaFile.
        :return: media info whose `media_name` attribute matches the `media_name` input parameter.
        """
        return get_first_list_elt_or_none(  # type: ignore
            self.get_catalog_cached(
                f"media?media_type=FILE&file_storage_status=available"
                f"&media_name={media_name}&file_size={file_size}&checksum.hash={checksum}&"
            )
        )

    def get_media_file_with_rudi_obj(self, media: RudiMediaFile) -> dict:
        """
        Finds a RudiMediaService with input information
        :param media: a RudiMediaFile object
        :return: media info whose name, size and checksum attributes matches the media input parameters.
        """
        return get_first_list_elt_or_none(  # type: ignore
            self.get_catalog_cached(
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
        return get_first_list_elt_or_none(  # type: ignore
            self.get_catalog_cached(f"media?media_type=SERVICE&media_name={media_name}&connector.url={url}")
        )

    def get_media_service_with_rudi_obj(self, media: RudiMediaService) -> dict:
        """
        Finds a RudiMediaService with input information (except the id: we're looking for a similar object already
        existing)
        :param media: a RudiMediaService object
        :return: media info whose `media_name` and 'source_url' attributes match the `media_name` and 'source_url'
        input parameters.
        """
        return get_first_list_elt_or_none(  # type: ignore
            self.get_catalog_cached(
                f"media?media_type=SERVICE&media_name={media.media_name}&connector.url={media.connector.url}"
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
        here = "RudiNodeManagerConnector.download_file_from_media_info"

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
            media: dict = self.get_media_with_uuid(media_uuid)  # type: ignore
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
            dwnld_info = self.download_file_from_media_info(check_is_dict(media.to_json()), local_download_dir)
            files_dwnld_info = merge_dict_of_list(files_dwnld_info, dwnld_info)
        return files_dwnld_info

    # ----------[ Communication with Storage module ]---------------------------------------------------------------------
    def post_local_file(
        self,
        file_local_path: str,
        media_id: str = uuid4_str(),
        rudi_media: RudiMediaFile | None = None,
    ) -> RudiMediaFile:
        """
        :param file_local_path: the path of a local file we wish to send to a RUDI node Storage server
        :param media_id: the UUIDv4 that identifies the media on the RUDI node
        :return:
        """
        here = f"{self.class_name}.post_local_file"

        if rudi_media is None:
            rudi_media = RudiMediaFile.from_local_file(file_local_path, media_id)
        else:
            check_media_info = RudiMediaFile.from_local_file(file_local_path, media_id)
            rudi_media.file_size = check_media_info.file_size
            rudi_media.checksum = check_media_info.checksum

        media_id = rudi_media.media_id

        # Posting the file as a binary directly to RUDI node Storage module
        try:
            res = self.storage_connector.post_local_file(
                file_local_path=check_is_file(file_local_path),
                media_id=rudi_media.media_id,
                rudi_media=rudi_media,
            )
        except IncompleteRead as e:
            log_e(here, "Upload to RUDI Storage failed (IncompleteRead)", e)
            log_e(here, "e.partial", e.partial)
            raise e
        except Exception as e:
            log_e(here, "Upload to RUDI Storage failed", e)
            raise e
        if res is None or not isinstance(res, dict) or res.get("media_info") is None:
            raise Exception("Upload to RUDI Storage failed!")
        media_info, zone_name, commit_uuid = (
            res["media_info"],
            res["zone_name"],
            res["commit_uuid"],
        )
        assert isinstance(media_info, RudiMediaFile)
        # log_d(here, "media_info", str(media_info))
        # log_d(here, "zone_name", zone_name)
        # log_d(here, "commit_uuid", commit_uuid)

        # Posting the file metadata as a RudiMediaFile object to the RUDI Catalog module through the PM data API
        if not self._gen == 1:
            try:
                api_media_info = self.put_catalog("media", media_info)
            except HttpError:
                self._gen = 1
                log_w(
                    here,
                    "The Manager module for this node cannot commit RudiMediaFile on the Catalog, please handle this by updating the file storage status in the metadata",
                )
                return media_info
        else:
            return media_info

        # Committing the file that has been uploaded
        res_commit = self.commit_media(media_id=media_id, zone_name=zone_name, commit_uuid=commit_uuid)
        log_d(here, "res_commit", res_commit)

        # Returning the updated RudiMedia information
        if isinstance(api_media_info, dict):
            updated_media_info = RudiMediaFile.from_json(api_media_info)
        else:
            log_w(here, f"unexpected result, should have a 'RudiMediaFile' compatible dict, got {api_media_info}")
            return media_info

        # Returning the updated RudiMedia information
        return updated_media_info

    # TODO: PM API for commit only file / only API / both?

    def commit_media(self, media_id: str, commit_uuid: str, zone_name: str, metadata_id: str | None = None):
        ack = self.post_api(
            url="media/commit",
            body={"media_id": media_id, "commit_uuid": commit_uuid, "zone_name": zone_name, "global_id": metadata_id},
            headers=self._id_headers,
        )
        return ack


class RudiNodeStorageConnectorV3(Connector):
    def __init__(self, server_url: str, jwt: str):
        super().__init__(server_url)
        self.jwt = jwt
        self._initial_headers = {
            "User-Agent": self.class_name,
            "Content-Type": "text/plain; charset=utf-8",
            "Accept": "application/json",
        }
        # self.test_connection()

    @property
    def auth_headers(self) -> dict:
        return self._initial_headers | {"Authorization": f"Bearer {self.jwt}"}

    def get_storage(self, relative_url: str, headers: dict = {}):
        return self.request(req_method="GET", relative_url=relative_url, headers=self.auth_headers | headers)

    def post_storage(self, relative_url: str, payload, headers: dict = {}):
        return self.request(
            req_method="POST", relative_url=relative_url, headers=self.auth_headers | headers, body=payload
        )

    def put_storage(self, relative_url: str, payload, headers: dict = {}):
        return self.request(
            req_method="PUT", relative_url=relative_url, headers=self.auth_headers | headers, body=payload
        )

    def test_connection(self) -> bool:  # type: ignore
        test = bool(self.get_storage(relative_url="hash"))
        log_d(
            "RudiNodeStorage",
            f"Node '{self.host}'",
            f"connection {'OK' if test else 'KO'}",
        )
        return test

    def get_media_headers_for_file(self, file_info: RudiMediaFile):
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
        if file_info.checksum.algo != "MD5":
            raise ValueError("Please provide a MD5 hash for this file")

        file_metadata = {
            "media_id": file_info.media_id,
            "media_type": MEDIA_TYPE_FILE,
            "media_name": quote(file_info.media_name),
            "file_size": file_info.file_size,
            "file_type": file_info.file_type,
            "md5": file_info.checksum.hash_str,
        }
        if file_info.file_type.endswith("+crypt"):
            return self.auth_headers | {
                "Content-Type": f"{file_info.file_type}",
                "Content-Length": file_info.file_size,
                "file_metadata": dumps(file_metadata),
            }

        if file_info.file_type.startswith("text"):
            charset = file_info.file_encoding if file_info.file_encoding else "utf-8"
            file_metadata["charset"] = charset
            return self.auth_headers | {
                "Content-Type": f"{file_info.file_type}; charset={charset}",
                "Content-Length": file_info.file_size,
                "file_metadata": dumps(file_metadata),
            }

        if file_info.file_type in MIME_TYPES_UTF8_TEXT:
            file_metadata["charset"] = "utf-8"

        return self.auth_headers | {
            "Content-Type": f"{file_info.file_type}; charset=utf-8",
            "Content-Length": file_info.file_size,
            "file_metadata": dumps(file_metadata),
        }

    @property
    def media_list(self) -> list:
        here = f"{self.class_name}.media_list"
        media_list = self.get_storage(relative_url="list", headers=self.auth_headers)
        if not isinstance(media_list, dict):
            raise TypeError(f"The server should have returned a dict, got:\n{media_list}")
        media_info = media_list.get("zone1")
        if media_info is None:
            media_info = media_list.get("zone_A")
            log_d(here, "media_info", media_info)

        return [] if media_info is None else media_info.get("list")

    def post_local_file(
        self,
        file_local_path: str,
        media_id: str | None = None,
        rudi_media: RudiMediaFile | None = None,
    ):
        """
        :param file_local_path: the path of a local file we wish to send to a RUDI node Media server
        :param media_id: the UUIDv4 that identifies the media on the RUDI node
        :param rudi_media: an optional RudiMediaFile object (in the case of an update)
        :return:
        """
        # :param media_name: the original name of the file
        # :param file_size: the size of the file in bytes
        # :param file_type: the MIME type of the file
        # :param charset: the encoding of the file
        here = f"{self.class_name}.post_local_file"

        if rudi_media is None:
            rudi_media = RudiMediaFile.from_local_file(file_local_path, media_id)
        else:
            check_media_info = RudiMediaFile.from_local_file(file_local_path, media_id)
            rudi_media.file_size = check_media_info.file_size
            rudi_media.checksum = check_media_info.checksum

        if rudi_media.file_size > FileTooBigException.MAX_SIZE:
            raise FileTooBigException(rudi_media.file_size)
        media_id = rudi_media.media_id

        log_d(here, "sending as binary for file", rudi_media)
        headers = self.get_media_headers_for_file(rudi_media) | {"Content-Type": "octet/stream"}
        # log_d(here, "headers", headers)
        with open(file_local_path, "rb") as bin_content:
            try:
                res = self.post_storage("post", bin_content, headers)
            except IncompleteRead as e:
                log_e(here, "Upload to RUDI Storage failed (IncompleteRead)", e)
                log_e(here, "e.partial", e.partial)
                log_e(here, "e.args", e.args)
                raise e
            except Exception as e:
                log_e(here, "ERR", e)
                raise e
        if not isinstance(res, list):
            raise TypeError(f"The server should have returned a list, got:\n{res}")
        if {"status": "OK"} in res:
            log_d(here, "upload status", "success", res)
            commit_ready = res[-2]
            log_d(here, "commit_ready", commit_ready)
            # Updating the connector.url information for the media
            rudi_media.set_url(slash_join(self.base_url, "download", rudi_media.media_id))
            # Updating the file storage status information for the media
            rudi_media.set_status("available")
            return {
                "media_info": rudi_media,
                "zone_name": commit_ready["zone_name"],
                "commit_uuid": commit_ready["commit_uuid"],
            }
        if len(res) > 0 and res[0].get("status") == "error":
            log_w(here, "ERR upload failed", res[0].get("msg"))
            raise Exception("File upload to RUDI Media falied:" + res[0])

        return res


class FileTooBigException(Exception):
    """Max file size for upload"""

    MAX_SIZE = 524288000  # (== 500 MB)

    def __init__(self, file_size):
        super().__init__(
            f"This file is too big to be uploaded to a RUDI node ("
            f"file size = {int(file_size / 1048576)} MB > max size = {int(self.MAX_SIZE / 1048576)} MB)"
        )


if __name__ == "__main__":  # pragma: no cover
    begin = time()
    tests = "RudiNodeManagerConnectorV3 tests"
    creds_file = "../creds/creds_pytest.json"
    rudi_node_creds = read_json_file(creds_file)
    manager_url = slash_join(rudi_node_creds["url"], "manager")
    log_d(tests, "node_url", manager_url)
    auth = RudiNodeAuth.from_json(rudi_node_creds)

    manager = RudiNodeManagerConnectorV3(server_url=manager_url, auth=auth)
    log_d(tests, "catalog_url", manager.catalog_url)
    log_d(tests, "storage_url", manager.storage_url)
    log_d(tests, "manager_url", manager.manager_url)
    log_d(tests, "manager_back_url", manager.base_url)
    log_d(tests, "test 1", manager.request(relative_url="open/test"))
    log_d(tests, "test 2", manager.get_api(url="open/test", headers=manager._def_headers))
    log_d(tests, "test 3", manager.test_connection())

    log_d(tests, "nb orgs", manager._count_obj("organizations"))
    log_d(tests, "list orgs", manager._get_full_obj_list("organizations"))

    test_dir = "../dwnld"
    log_d(tests, "producers", len(manager.organization_list))
    log_d(tests, "producer names", manager.organization_names)
    log_d(tests, "contacts", len(manager.contact_list))
    log_d(tests, "contact names", manager.contact_names)
    log_d(tests, "media", len(manager.media_list))
    log_d(tests, "media", (manager.media_names))

    log_d(tests, "enum", len(manager.enums))
    log_d(tests, "themes FR", len(manager.themes))
    log_d(tests, "used_themes", len(manager.used_themes))
    log_d(tests, "keywords", len(manager.keywords))
    log_d(tests, "used_keywords", len(manager.used_keywords))
    storage_url = manager.storage_url
    log_d(tests, "rudi_media_url", storage_url)

    # "Hack" when no SSL connection is available
    storage = RudiNodeStorageConnectorV3(server_url=storage_url, jwt=manager._storage_jwt)
    storage.scheme = "http"
    storage.should_log_response = True
    manager._cached_storage_connector = storage
    log_d(tests, "rudi_media.media_list", len(storage.media_list))

    dwnld_dir = "../tests/_test_files/"
    if not exists(dwnld_dir):
        raise Exception(f"This folder should be created: '{dwnld_dir}'")
    media_uuid = [
        "eeeeeeee-3233-4541-855e-55de7086b40e",
        "eeeeeeee-3233-4541-855e-55de7086b40f",
    ]
    text_file = "unicode_chars.txt"
    yaml_file = "RUDI producer internal API - 1.3.0.yml"
    for i, f in enumerate([text_file, yaml_file]):
        try:
            upload_res = manager.post_local_file(slash_join(dwnld_dir, f), media_uuid[i])
            log_d(tests, f"File '{f}' now available at", upload_res)
            stored_media_list = [
                stored_media for stored_media in storage.media_list if stored_media.get("uuid") == media_uuid[i]
            ]
            log_d(
                tests,
                "stored_media",
                stored_media_list[0] if len(stored_media_list) > 0 else None,
            )
        except HttpError as e:
            log_w(tests, e)

    log_d(tests, "last_metadata_update_date", manager.last_metadata_update_date)
    log_d(tests, "last_data_update_date", manager.last_data_update_date)
    log_d(tests, "exec. time", time() - begin)
