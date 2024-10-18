from json import dumps
from os.path import abspath, isdir
from time import time

from rudi_node_write.connectors.io_connector import https_download
from rudi_node_write.connectors.io_rudi_manager_write import RudiNodeManagerConnector
from rudi_node_write.connectors.rudi_node_auth import RudiNodeAuth
from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.utils.dict_utils import (
    check_get_key,
    filter_dict_list,
    find_in_dict_list,
    pick_in_dict,
    safe_get_key,
)
from rudi_node_write.utils.file_utils import read_json_file
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.str_utils import check_is_string, check_is_uuid4, slash_join, uuid4_str
from rudi_node_write.utils.type_date import Date

_USER_AGENT_DEFAULT = "RudiNodeWriter"

_STATUS_SKIPPED = "skipped"
_STATUS_MISSING = "missing"
_STATUS_DOWNLOADED = "downloaded"


class RudiNodeWriter:
    _default_getter = None

    def __init__(
        self,
        pm_url: str,
        auth: RudiNodeAuth,
        headers_user_agent: str = _USER_AGENT_DEFAULT,
        keep_connection: bool = False,
    ):
        """
        The main object of this library.
        :param pm_url: the URL of the RUDI node
        :param auth: an authentication object
        :param headers_user_agent: a mean to authentificate the requester in the request headers
        """
        here = "RudiNodeWriter.__init__"
        self._pm_url = pm_url
        self._auth = auth
        self._headers_user_agent = headers_user_agent
        self.keep_connection = keep_connection

        self._init_pm_connector()
        # self.connector.test_identified_connection()

    def _init_pm_connector(self) -> None:
        self._pm_connector = RudiNodeManagerConnector(
            server_url=self._pm_url,
            auth=self._auth,
            headers_user_agent=self._headers_user_agent,
            keep_connection=self.keep_connection,
        )

    def close_connection(self):
        self._pm_connector.close_connection()

    @property
    def headers_user_agent(self) -> str:
        return self._headers_user_agent

    @property
    def is_legacy(self) -> str:
        return self._pm_connector._is_legacy

    @property
    def connector(self) -> RudiNodeManagerConnector:
        """
        :return: the RudiNodeConnector object used for requesting the RUDI node
        """
        if self._pm_connector is None:
            self._init_pm_connector()
        return self._pm_connector

    @property
    def pm_url(self) -> str:
        """
        :return: the URL of the RUDI Producer node
        """
        return self._pm_url

    @property
    def media_url(self) -> list[dict]:
        """
        :return: the list of the organizations that appear in the metadata
        (both data producer and metadata publisher)
        """
        return self.connector.media_url

    @property
    def init_data(self) -> list[dict]:
        """
        :return: the list of the organizations that appear in the metadata
        (both data producer and metadata publisher)
        """
        return self.connector.init_data

    # ----------[ Data access as properties ]---------------------------------------------------------------------------

    @property
    def organization_list(self) -> list[dict]:
        """
        :return: the list of the organizations that appear in the metadata
        (both data producer and metadata publisher)
        """
        return self.connector.organization_list

    @property
    def contact_list(self) -> list[dict]:
        """
        :return: the list of the contacts declared in the RUDI node metadata
        """
        return self.connector.contact_list

    @property
    def media_list(self) -> list[dict]:
        """
        :return: the list of the metadata_contacts declared on the RUDI producer node
        """
        return self.connector.media_list

    @property
    def metadata_list(self) -> list[dict]:
        """
        :return: the full list of the metadata stored on the RUDI Producer node
        """
        return self.connector.metadata_list

    @property
    def used_organization_list(self) -> list[dict]:
        return self.connector.used_organization_list

    @property
    def used_contact_list(self) -> list[dict]:
        return self.connector.used_contact_list

    @property
    def used_media_list(self) -> list[dict]:
        return self.connector.used_media_list

    @property
    def organization_names(self) -> list[str]:
        """
        :return: the list of the names of the organizations that appear in the metadata
        (both data producer and metadata publisher)
        """
        return self.connector.organization_names

    @property
    def contact_names(self) -> list[str]:
        """
        :return: the list of the names of the contacts declared in the RUDI node metadata
        """
        return self.connector.contact_names

    @property
    def metadata_count(self) -> int:
        """
        :return: the number of metadata stored on the RUDI Producer node
        """
        return self.connector.metadata_count

    @property
    def last_metadata_update_date(self) -> Date | None:
        return self.connector.last_metadata_update_date

    @property
    def last_data_update_date(self) -> Date | None:
        return self.connector.last_data_update_date

    @property
    def enums(self) -> dict:
        """
        :return: the list of the themes declared on the RUDI producer node
        """
        return self.connector.enums

    @property
    def themes(self) -> list[str]:
        """
        :return: the list of the themes declared on the RUDI producer node
        """
        return self.connector.themes

    @property
    def keywords(self):
        """
        :return: the list of the keywords declared on the RUDI producer node
        """
        return self.connector.keywords

    @property
    def used_themes(self) -> list[str]:
        """
        :return: the list of themes used in the metadata on the RUDI producer node
        """
        return self.connector.used_themes

    @property
    def used_keywords(self) -> list[str]:
        """
        :return: the list of keywords used in the metadata on the RUDI producer node
        """
        return self.connector.used_keywords

    # ----------[ Find a metadata ]-------------------------------------------------------------------------------------
    # Logic here is:
    # - get_metadata => get one (possibly the first) metadata that fulfill the condition
    # - find metadata => get one metadata that fulfill the condition or None
    # - get_all_metadata => get the list of all the metadata that fullfil the condition

    def find_in_metadata_list(self, matching_filter: dict) -> dict | None:
        """
        :param matching_filter: JSON-like object whose attributes are all matched in the resulting
        metadata list
        :return: the first metadata that matches the filter
        """
        return find_in_dict_list(self.metadata_list, matching_filter)

    def find_metadata_with_uuid(self, metadata_id: str) -> dict | None:
        """
        :param metadata_id: a UUIDv4 string
        :return: list of the metadata whose `global_id` attribute matches the `metadata_id` input parameter
        """
        return self.find_in_metadata_list({"global_id": check_is_uuid4(metadata_id)})

    def find_metadata_with_source_id(self, source_id: str) -> dict | None:
        """
        :param source_id: a string that was used in the producer's data source to identify the dataset
        :return: list of the metadata whose `local_id` attribute matches the `media_name` input parameter
        """
        return self.find_in_metadata_list({"local_id": source_id})

    def find_metadata_with_title(self, title: str) -> dict | None:
        """
        :param title: title of the metadata
        :return: list of the metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self.find_in_metadata_list({"resource_title": check_is_string(title)})

    def find_metadata_with_media(self, media_info: dict) -> dict | None:
        """
        :param title: title of the metadata
        :return: list of the metadata whose `resource_title` attribute matches the `title` input parameter
        """
        return self.find_in_metadata_list({"available_formats": [media_info]})

    # ----------[ Filter the list of metadata ]-------------------------------------------------------------------------

    def filter_metadata_list(self, matching_filter: dict) -> list[dict]:
        """
        :param matching_filter: JSON-like object whose attributes are all matched in the resulting
        metadata list
        :return: list of the metadata that match the filter
        """
        return filter_dict_list(self.metadata_list, matching_filter)

    def select_metadata_with_producer(self, producer_name: str) -> list[dict]:
        """
        :param org_name: the name of the organization declared in the metadata
        :return: list of the metadata whose `producer.organization_name` attribute matches the `producer_name` input
        parameter
        """
        return self.filter_metadata_list({"producer": {"organization_name": producer_name}})

    def select_metadata_with_producer_id(self, producer_id: str) -> list[dict]:
        """
        :param producer_id: the UUIDv4 of the organization declared as producer in the metadata
        :return: list of the metadata whose `producer.organization_id` attribute matches the `producer_id` input
        parameter
        """
        return self.filter_metadata_list({"producer": {"organization_id": check_is_uuid4(producer_id)}})

    def select_metadata_with_contact(self, contact_name: str) -> list[dict]:
        """
        :param contact_name: the meta_contact of the contact declared in the metadata
        :return: list of the metadata whose `contacts` attribute contains a contact object whose `contact_name`
        attribute matches the `contact_name` input parameter
        """
        return self.filter_metadata_list({"contacts": [{"contact_name": contact_name}]})

    def select_metadata_with_theme(self, theme: str) -> list[dict]:
        """
        :param theme: a string used to filter the metadata by theme
        :return: list of the metadata whose `theme` attribute matches the `theme` input parameter
        """
        return self.filter_metadata_list({"theme": theme})

    def select_metadata_with_keywords(self, keywords: str | list) -> list[dict]:
        """
        :param keywords: a string or a list of strings used to filter the metadata by keywords
        :return: list of the metadata whose `keywords` attribute contains every `keywords` input parameter
        """
        return self.filter_metadata_list({"keywords": keywords})

    def select_metadata_with_available_media(self) -> list[dict]:
        """
        :return: list of the metadata whose `available_formats` attribute contains at least one media for which the
        `file_storage_status` attribute is set to `available`
        """
        return self.filter_metadata_list({"available_formats": [{"file_storage_status": "available"}]})

    def select_metadata_with_media_name(self, media_name: str) -> list[dict]:
        """
        :param media_name: name of the media
        :return: list of the metadata whose `available_formats` attribute contains at least one media for which the
        `media_name` attribute matches the `media_name` input parameter
        """
        return self.filter_metadata_list({"available_formats": [{"media_name": check_is_string(media_name)}]})

    def select_metadata_with_media_uuid(self, media_uuid: str) -> list[dict]:
        """
        :param media_uuid: UUIDv4 of the media
        :return: list of the metadata whose `available_formats` attribute contains at least one media for which the
        `media_id` attribute matches the `media_uuid` input parameter
        """
        return self.filter_metadata_list({"available_formats": [{"media_id": check_is_uuid4(media_uuid)}]})

    @staticmethod
    def _download_media_from_info(media: dict, local_download_dir: str) -> dict:
        """
        Download a file from its media metadata
        :param media: the file metadata (as found in the RUDI metadata `available_formats` attribute
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        media_type = safe_get_key(media, "media_type")

        # Most likely for media_type == 'SERVICE'
        if media_type != "FILE":
            return {
                "status": _STATUS_SKIPPED,
                "media": pick_in_dict(media, ["media_name", "media_id", "media_url", "media_type"]),
            }

        # If the file is not available on storage, we won't try to download it.
        if safe_get_key(media, "file_storage_status") != "available":
            return {
                "status": _STATUS_MISSING,
                "media": pick_in_dict(
                    media,
                    [
                        "media_name",
                        "media_id",
                        "media_url",
                        "file_type",
                        "file_storage_status",
                    ],
                ),
            }

        # The metadata says the file is available, let's download it
        if not isdir(local_download_dir):
            raise FileNotFoundError(f"The following folder does not exist: '{local_download_dir}'")

        media_name = check_get_key(media, "media_name")
        media_url = check_get_key(media, "connector", "url")

        destination_path = abspath(slash_join(local_download_dir, media_name))
        content = https_download(media_url)
        if content is None:
            raise Exception(f"Could not download from {media_url}")
        open(destination_path, "wb").write(content)
        log_d("media_download", "content saved to file", destination_path)

        file_info = {
            "media_name": media_name,
            "media_id": safe_get_key(media, "media_id"),
            "media_url": media_url,
            "file_type": safe_get_key(media, "file_type"),
            "created": safe_get_key(media, "media_dates", "created"),
            "updated": safe_get_key(media, "media_dates", "updated"),
            "file_path": destination_path,
        }
        return {"status": _STATUS_DOWNLOADED, "media": file_info}

    def download_file_with_uuid(self, media_uuid: str, local_download_dir: str) -> dict | None:
        """
        Download a file identified with the input UUID
        :param media_uuid: a UUIDv4 that identifies the media on the RUDI node
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        meta_list = self.select_metadata_with_media_uuid(media_uuid=media_uuid)
        if len(meta_list) == 0:
            return None
        media_list: list = safe_get_key(meta_list[0], "available_formats")  # type: ignore
        media: dict = find_in_dict_list(media_list, {"media_id": media_uuid})  # type: ignore
        return self._download_media_from_info(media, local_download_dir)

    def download_file_with_name(self, media_name: str, local_download_dir: str) -> dict | None:
        """
        Find a file from its name and download it if it is available
        :param media_name: the name of the file we want to download
        :param local_download_dir: the path to a local folder
        :return: an object that states if the file was downloaded, skipped or found missing
        """
        meta_list = self.select_metadata_with_media_name(media_name)
        if len(meta_list) == 0:
            return None
        media_list: list = safe_get_key(meta_list[0], "available_formats")  # type: ignore
        media: dict = find_in_dict_list(media_list, {"media_name": media_name})  # type: ignore
        return self._download_media_from_info(media, local_download_dir)

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
        media_list = safe_get_key(meta, "available_formats")
        if not media_list:
            return None
        files_dwnld_info: dict = {
            _STATUS_DOWNLOADED: [],
            _STATUS_MISSING: [],
            _STATUS_SKIPPED: [],
        }
        for media in media_list:
            dwnld_info = self._download_media_from_info(media, local_download_dir)
            status = dwnld_info["status"]
            files_dwnld_info[status].append(dwnld_info["media"])
        return files_dwnld_info

    def save_metadata_list_to_file(self, local_download_dir: str, file_name: str = "rudi_node_metadata.json") -> None:
        """
        Dumps the metadata list to a local file
        :param local_download_dir: the path to a local folder
        :param file_name: the name of the file in which the JSON representation of the list of metadata will be saved
        """
        file_path = abspath(slash_join(local_download_dir, file_name))
        json_str = dumps(obj=self.metadata_list, ensure_ascii=False, indent=2).encode("utf-8")
        open(file_path, "wb").write(json_str)

    def put_metadata(self, metadata: dict | RudiMetadata):
        """
        Create or update a metadata on the RUDI node API
        """
        return self.connector.put_metadata(metadata=metadata)

    def post_local_file_and_media_info(self, file_local_path: str, media_id: str = uuid4_str()):
        """
        Upload a local file on the RUDI node
        Creates automatically the "media" part of the metadata
        :return:
        """
        return self.connector.post_local_file(file_local_path=file_local_path, media_id=media_id)


if __name__ == "__main__":  # pragma: no cover
    begin = time()
    NODE_URL = "url"  # The URL of RUDI node
    PM_URL = "pm_url"  # The URL of the RUDI node manager. If not set in the credential file, it will be set to NODE_URL+'/prodmanager'
    tests = "RudiNodeWriter tests"
    creds_file = "../creds/creds_bas.json"
    rudi_node_creds = read_json_file(creds_file)
    if rudi_node_creds.get(PM_URL) is not None:
        pm_url = rudi_node_creds[PM_URL]
    else:
        pm_url = rudi_node_creds[NODE_URL] + "/prodmanager"

    if (b64url_auth := rudi_node_creds["b64auth"]) is not None:
        auth = RudiNodeAuth(b64url_auth=b64url_auth)
    else:
        auth = RudiNodeAuth(usr=rudi_node_creds["pm_usr"], pwd=rudi_node_creds["pm_pwd"])

    rudi_node_writer = RudiNodeWriter(pm_url=pm_url, auth=auth)
    log_d(tests, "used_organization_list", rudi_node_writer.used_organization_list)
    log_d(tests, "metadata_count", rudi_node_writer.metadata_count)
    log_d(tests, "meta_1_id", rudi_node_writer.metadata_list[0]["global_id"])
    log_d(tests, "org_1_id", rudi_node_writer.organization_list[0]["organization_id"])
    log_d(tests, "contact_1_id", rudi_node_writer.contact_list[0]["contact_id"])
    # log_d(tests, "metadata_with_available_media", rudi_node_writer.select_metadata_with_available_media())
