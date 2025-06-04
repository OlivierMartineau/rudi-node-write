from os.path import exists
from ssl import SSLCertVerificationError
from time import time

from rudi_node_write.connectors.io_connector import HttpError
from rudi_node_write.connectors.io_rudi_manager_write import RudiNodeManagerConnector, RudiNodeStorageConnector
from rudi_node_write.connectors.rudi_node_auth import RudiNodeAuth
from rudi_node_write.utils.file_utils import read_json_file
from rudi_node_write.utils.log import log_d, log_w
from rudi_node_write.utils.str_utils import slash_join
from rudi_node_write.utils.url_utils import ensure_url_startswith


# Defaults for constructor
_DEFAULT_USER_AGENT = "RudiNodeManagerConnectorV2"

here = "RudiNodeManagerConnector"


def ensure_url_startswith_api(url):
    return ensure_url_startswith(url, "api")


def ensure_url_startswith_api_data(url):
    if url.startswith("data"):
        return ensure_url_startswith_api(url)
    return ensure_url_startswith(url, "api/data")


class RudiNodeManagerConnectorV2(RudiNodeManagerConnector):
    """
    Every RUDI node has a UI module called "RUDI node manager", or "producer node manager" (shortened as "prod-manager")
    that offers to list, edit or create RUDI metadata, given that you have the required level of access.
    This library takes advantage of the prodmanager backend API to send data and metadata.
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
        self._gen = 2

        # self.test_identified_connection()


if __name__ == "__main__":  # pragma: no cover
    begin = time()
    tests = "RudiNodeManagerConnector tests"
    creds_file = "../creds/creds_stage.json"
    rudi_node_creds = read_json_file(creds_file)
    pm_url = rudi_node_creds["pm_url"]
    log_d(tests, "node_url", pm_url)
    auth = RudiNodeAuth.from_json(rudi_node_creds)

    pm_connector = RudiNodeManagerConnector(server_url=pm_url, auth=auth)
    pm_connector.test_connection()
    log_d(tests, "nb orgs", pm_connector.count_obj("organizations"))
    log_d(tests, "list orgs", pm_connector._get_full_obj_list("organizations"))

    test_dir = "../dwnld"
    log_d(tests, "producers", len(pm_connector.organization_list))
    log_d(tests, "producer names", pm_connector.organization_names)
    log_d(tests, "contacts", len(pm_connector.contact_list))
    log_d(tests, "contact names", pm_connector.contact_names)
    # log_d(tests, "media", len(pm_connector.media_list))
    # log_d(tests, "media", (pm_connector.media_names))

    log_d(tests, "enum", len(pm_connector.enums))
    log_d(tests, "themes FR", len(pm_connector.themes))
    log_d(tests, "used_themes", len(pm_connector.used_themes))
    log_d(tests, "keywords", len(pm_connector.keywords))
    log_d(tests, "used_keywords", len(pm_connector.used_keywords))

    try:
        rudi_media_url = pm_connector.storage_url
        log_d(tests, "rudi_media_url", rudi_media_url)
        rudi_media = RudiNodeStorageConnector(server_url=rudi_media_url, jwt=pm_connector._storage_jwt)
    except SSLCertVerificationError:
        pm_connector._cached_storage_url = pm_connector.storage_url.replace("https", "http")
        rudi_media_url = pm_connector.storage_url
        log_d(tests, "rudi_media_url", rudi_media_url)
        rudi_media = RudiNodeStorageConnector(server_url=rudi_media_url, jwt=pm_connector._storage_jwt)
    log_d(tests, "rudi_media.media_list", len(rudi_media.media_list))

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
            upload_res = pm_connector.post_local_file(slash_join(dwnld_dir, f), media_uuid[i])
            log_d(tests, f"File '{f}' now available at", upload_res)
            stored_media_list = [
                stored_media for stored_media in rudi_media.media_list if stored_media.get("uuid") == media_uuid[i]
            ]
            log_d(
                tests,
                "stored_media",
                stored_media_list[0] if len(stored_media_list) > 0 else None,
            )
        except HttpError as e:
            log_w(tests, e)

    log_d(tests, "last_metadata_update_date", pm_connector.last_metadata_update_date)
    log_d(tests, "last_data_update_date", pm_connector.last_data_update_date)
    log_d(tests, "exec. time", time() - begin)
