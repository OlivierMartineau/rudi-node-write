from rudi_node_write.connectors.io_rudi_manager_write_v3 import RudiNodeManagerConnectorV3
from rudi_node_write.connectors.rudi_node_auth import RudiNodeAuth
from rudi_node_write.rudi_types.rudi_org import RudiOrganization
from rudi_node_write.utils.file_utils import check_is_dir, read_json_file
from rudi_node_write.utils.str_utils import slash_join
from rudi_node_write.utils.type_date import Date

test_dir = check_is_dir("./dwnld")
rudi_node_creds = read_json_file("./creds/creds_2.5.2.json")

auth = RudiNodeAuth.from_json(rudi_node_creds)
url = rudi_node_creds["url"]
pm_url = url if url.endswith("manager") else slash_join(url, "manager")
assert isinstance(auth, RudiNodeAuth)

manager = RudiNodeManagerConnectorV3(server_url=pm_url, auth=auth)


def test_connection():
    assert manager.test_connection()
    assert manager.test_identified_connection()


def test_organization_list():
    assert len(manager.organization_list) > 0


def test_organization_names():
    assert isinstance(manager.organization_names, list)
    assert len(manager.organization_names)
    assert isinstance(manager.organization_names[0], str)


def test_used_organization_list():
    assert isinstance(manager.used_organization_list, list)
    assert len(manager.used_organization_list)
    assert isinstance(RudiOrganization.from_json(manager.used_organization_list[0]), RudiOrganization)


def test_contact_names():
    assert len(manager.contact_names)
    assert isinstance(manager.contact_names[0], str)


def test_media_names():
    assert len(manager.media_names)
    assert isinstance(manager.media_names[0], str)


def test_metadata_count():
    assert manager.metadata_count > 0


def test_metadata_list():
    assert len(manager.metadata_list) > 0


def test_keywords():
    assert len(manager.keywords) > 0


def test_used_keywords():
    assert len(manager.used_keywords) > 0


def test_used_themes():
    assert len(manager.used_themes) > 0


def test_tags():
    assert isinstance(manager.tags, dict)
    assert manager.tags["hash"] is not None


def test_hash():
    assert manager.hash is not None
    assert isinstance(manager.hash, str)


def test_media_url():
    assert manager.storage_url is not None
    assert isinstance(manager.storage_url, str)


def test_last_metadata_update_date():
    # assert pm.last_data_update_date is not None
    assert manager.last_data_update_date is None or isinstance(manager.last_data_update_date, Date)
