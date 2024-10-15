import pytest

from rudi_node_write.connectors.io_rudi_api_write import RudiNodeApiConnector
from rudi_node_write.connectors.io_rudi_jwt_factory import RudiNodeJwtFactory
from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.utils.dict_utils import is_dict
from rudi_node_write.utils.err import ExpiredTokenException
from rudi_node_write.utils.file_utils import check_is_dir, check_is_file, read_json_file
from rudi_node_write.utils.jwt import is_jwt_expired
from rudi_node_write.utils.str_utils import is_uuid_v4

test_dir = check_is_dir("./dwnld")
creds_file = check_is_file("./creds/test_creds_catalog.json")

rudi_node_creds = read_json_file(creds_file)
url = rudi_node_creds["url"]
auth_url = rudi_node_creds["auth_url"] if "auth_url" in rudi_node_creds else url


def test_RudiNodeApiConnector():
    rudi_jwt_factory = RudiNodeJwtFactory(auth_url, auth=rudi_node_creds)
    rudi_api = RudiNodeApiConnector(url, jwt_factory=rudi_jwt_factory)
    rudi_api.set_jwt_factory(rudi_jwt_factory)

    with pytest.raises(ExpiredTokenException):
        rudi_api.set_jwt(None)  # type: ignore


rudi_jwt_factory = RudiNodeJwtFactory(auth_url, auth=rudi_node_creds, default_exp_s=360)
rudi_api = RudiNodeApiConnector(url, jwt_factory=rudi_jwt_factory)


def test_RudiNodeApiConnector_metadata_count():
    metadata_count = rudi_api.metadata_count
    assert metadata_count > 0


def test_RudiNodeApiConnector_metadata_list():
    meta_1 = rudi_api.metadata_list[0]
    rudi_meta = RudiMetadata.from_json(meta_1)
    assert is_uuid_v4(rudi_meta.global_id)
    meta_id_1 = meta_1["global_id"]
    assert is_uuid_v4(meta_1["global_id"])
    meta_obj = rudi_api.get_metadata_with_uuid(meta_id_1)
    assert meta_obj is not None
    assert is_uuid_v4(meta_obj.global_id)


def test_RudiNodeApiConnector_producers():
    assert isinstance(rudi_api.organization_list, list)
    assert len(rudi_api.organization_list) > 0
    prod_1 = rudi_api.organization_list[0]
    prod_1_id = prod_1["organization_id"]
    assert is_uuid_v4(prod_1_id)
    assert (org := rudi_api.get_producer_with_id(prod_1_id))
    assert is_uuid_v4(org.organization_id)
    producer_name_1 = rudi_api.producer_names[0]
    assert rudi_api.get_producer_with_name(producer_name_1)
    assert rudi_api.get_or_create_org_with_info(producer_name_1, prod_1)
    assert rudi_api.get_or_create_org_with_info(producer_name_1, prod_1)


def test_RudiNodeApiConnector_get_or_create_org_with_info():
    new_org = rudi_api.get_or_create_org_with_info("test_org", {"address": "test address"})
    assert new_org is not None
    assert is_uuid_v4(new_org_id := new_org.organization_id)
    del_org = rudi_api.delete_org_with_id(new_org_id)
    assert del_org.organization_id == new_org_id


def test_RudiNodeApiConnector_contacts():
    assert len(contacts := rudi_api.contact_list) > 0
    contact_name_1 = rudi_api.contact_names[0]
    assert rudi_api.get_contact_with_name(contact_name_1)
    assert rudi_api.get_contact_with_email(contacts[0]["email"])


def test_RudiNodeApiConnector_thesauri():
    assert len(themes := rudi_api.themes) > 0
    assert len(used_themes := rudi_api.used_themes) > 0
    assert len(keywords := rudi_api.keywords) > 0
    assert len(used_keywords := rudi_api.used_keywords) > 0


def test_RudiNodeApiConnector_download_files_for_metadata():
    meta_id_1 = rudi_api.metadata_list[0]["global_id"]
    assert is_dict(rudi_api.download_files_for_metadata(metadata_id=meta_id_1, local_download_dir=test_dir))


def test_RudiNodeApiConnector_download_file_with_name():
    rudi_api.download_file_with_name("toucan.jpg", local_download_dir=test_dir)
