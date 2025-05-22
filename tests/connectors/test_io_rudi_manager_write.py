from rudi_node_write.connectors.io_rudi_manager_write import RudiNodeManagerConnector
from rudi_node_write.connectors.rudi_node_auth import RudiNodeAuth
from rudi_node_write.utils.file_utils import check_is_dir, check_is_file, read_json_file
from rudi_node_write.utils.str_utils import slash_join
from rudi_node_write.utils.type_date import Date

test_dir = check_is_dir("./dwnld")
rudi_node_creds = read_json_file("./creds/creds_pytest.json")

auth = RudiNodeAuth.from_json(rudi_node_creds)
url = rudi_node_creds["url"]
pm_url = url if url.endswith("manager") else slash_join(url, "manager")
assert isinstance(auth, RudiNodeAuth)

pm = RudiNodeManagerConnector(server_url=pm_url, auth=auth)

if pm.storage_url == "":
    media_url = slash_join(f"{pm.scheme}://{pm.host}", "media")
    pm.set_storage_url(media_url)


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
    assert pm.storage_url is not None
    assert isinstance(pm.storage_url, str)


def test_last_metadata_update_date():
    # assert pm.last_data_update_date is not None
    assert pm.last_data_update_date is None or isinstance(pm.last_data_update_date, Date)
