import pytest
from rudi_node_write.connectors.io_rudi_manager_write import RudiNodeAuth, RudiNodeManagerConnector
from rudi_node_write.utils.file_utils import check_is_dir, check_is_file, read_json_file
from rudi_node_write.utils.type_date import Date

test_dir = check_is_dir("./dwnld")
creds_file = check_is_file("./creds/creds.json")

rudi_node_creds = read_json_file(creds_file)
NODE_URL = "url"  # The URL of RUDI node
PM_URL = "pm_url"  # The URL of the RUDI node manager. If not set in the credential file, it will be set to NODE_URL+'/prodmanager'
url = rudi_node_creds[NODE_URL]
pm_url = rudi_node_creds[PM_URL] if rudi_node_creds[PM_URL] else (rudi_node_creds[NODE_URL] + "/prodmanager")

auth = RudiNodeAuth(b64url_auth=rudi_node_creds["pm_b64auth"])
pm = RudiNodeManagerConnector(server_url=pm_url, auth=auth)


def test_connection():
    assert pm.test_connection()


def test_organization_list():
    assert len(pm.organization_list) > 0


def test_organization_names():
    assert len(pm.organization_names)
    assert isinstance(pm.organization_names[0], str)


def test_contact_names():
    assert len(pm.contact_names)
    assert isinstance(pm.contact_names[0], str)


def test_media_names():
    assert len(pm.media_names)
    assert isinstance(pm.media_names[0], str)


def test_metadata_count():
    assert pm.metadata_count > 0


def test_metadata_list():
    assert len(pm.metadata_list) > 0


def test_keywords():
    assert len(pm.keywords) > 0


def test_used_keywords():
    assert len(pm.used_keywords) > 0


def test_used_themes():
    assert len(pm.used_themes) > 0


def test_tags():
    assert isinstance(pm.tags, dict)
    assert pm.tags["hash"] is not None


def test_hash():
    assert pm.hash is not None
    assert isinstance(pm.hash, str)


def test_media_url():
    assert pm.media_url is not None
    assert isinstance(pm.media_url, str)


def test_last_metadata_update_date():
    # assert pm.last_data_update_date is not None
    assert pm.last_data_update_date is None or isinstance(pm.last_data_update_date, Date)
