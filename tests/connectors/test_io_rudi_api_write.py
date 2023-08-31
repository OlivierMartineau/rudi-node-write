import uuid
from time import sleep

import pytest

from rudi_node_write.connectors.io_rudi_api_write import RudiNodeApiConnector
from rudi_node_write.connectors.io_rudi_jwt_factory import RudiNodeJwtFactory
from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.utils.dict_utils import is_dict
from rudi_node_write.utils.err import ExpiredTokenException, NoNullException
from rudi_node_write.utils.file_utils import is_file, read_json_file, is_dir
from rudi_node_write.utils.str_utils import is_uuid_v4

test_dir = "./dwnld"
if not is_dir(test_dir):
    raise FileNotFoundError(f"A local dir should be created at path '{test_dir}'")

creds_file = "./creds/creds.json"
if not is_file(creds_file):
    raise FileNotFoundError(f"A JSON file with the credentials for accessing the node is required at {creds_file}")
rudi_node_creds = read_json_file(creds_file)
url = rudi_node_creds["url"]


def test_RudiNodeApiConnector():
    rudi_api = RudiNodeApiConnector(url)
    with pytest.raises(NoNullException):
        metadata_count = rudi_api.metadata_count

    rudi_jwt_factory = RudiNodeJwtFactory(url, rudi_node_creds)

    jwt = rudi_jwt_factory.get_jwt(2)
    sleep(2)
    with pytest.raises(ExpiredTokenException):
        rudi_api.set_jwt(jwt)
    rudi_api.set_jwt(rudi_jwt_factory.get_jwt(2))
    sleep(2)
    with pytest.raises(ExpiredTokenException):
        metadata_count = rudi_api.metadata_count

    rudi_api.set_jwt(rudi_jwt_factory.get_jwt())
    metadata_count = rudi_api.metadata_count

    rudi_api.set_jwt_factory(rudi_jwt_factory)

    meta_1 = rudi_api.metadata_list[0]
    meta_id_1 = meta_1["global_id"]
    assert is_uuid_v4(meta_1["global_id"])
    assert is_uuid_v4(rudi_api.get_metadata_with_uuid(meta_id_1)["global_id"])
    rudi_meta = RudiMetadata.from_json(meta_1)
    rudi_meta.local_id = uuid.uuid4()
    rudi_api.create_meta_with_rudi_obj(rudi_meta)

    assert len(rudi_api.producers) > 0
    prod_1 = rudi_api.producers[0]
    assert rudi_api.get_producer_with_id(prod_1["organization_id"])
    producer_name_1 = rudi_api.producer_names[0]
    assert rudi_api.get_producer_with_name(producer_name_1)
    assert rudi_api.get_or_create_org_with_info(producer_name_1, prod_1)
    assert rudi_api.get_or_create_org_with_info(producer_name_1, prod_1)

    new_org = rudi_api.get_or_create_org_with_info("test_org", {"address": "test address"})
    assert is_uuid_v4(new_org_id := new_org.organization_id)
    del_org = rudi_api.delete_org_with_id(new_org_id)
    assert del_org.organization_id == new_org_id

    assert len(contacts := rudi_api.contacts) > 0
    contact_name_1 = rudi_api.contact_names[0]
    assert rudi_api.get_contact_with_name(contact_name_1)
    assert rudi_api.get_contact_with_email(contacts[0]["email"])

    assert len(themes := rudi_api.themes) > 0
    assert len(used_themes := rudi_api.used_themes) > 0
    assert len(keywords := rudi_api.keywords) > 0
    assert len(used_keywords := rudi_api.used_keywords) > 0
    assert (metadata_count := rudi_api.metadata_count) > 0

    assert is_dict(rudi_api.download_files_for_metadata(metadata_id=meta_id_1, local_download_dir=test_dir))
    rudi_api.download_file_with_name("toucan.jpg", local_download_dir=test_dir)
