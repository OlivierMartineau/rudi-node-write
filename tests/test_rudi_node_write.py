from time import time
from rudi_node_write.connectors.io_rudi_manager_write import RudiNodeAuth
from rudi_node_write.rudi_node_writer import RudiNodeWriter
from rudi_node_write.rudi_types.rudi_org import RudiOrganization
from rudi_node_write.utils.file_utils import read_json_file
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.str_utils import is_uuid_v4

begin = time()
NODE_URL = "url"  # The URL of RUDI node
PM_URL = "pm_url"  # The URL of the RUDI node manager. If not set in the credential file, it will be set to NODE_URL+'/prodmanager'
tests = "RudiNodeManagerConnector tests"
creds_file = "./creds/creds.json"
rudi_node_creds = read_json_file(creds_file)
# pm_url = rudi_node_creds[NODE_URL] + "/prodmanager"
pm_url = rudi_node_creds[PM_URL]

USER_AGENT = "RudiNodeWriterTests"

auth = RudiNodeAuth(b64url_auth=rudi_node_creds["pm_b64auth"])


def test_RudiNodeWriter():
    rudi_node_writer = RudiNodeWriter(pm_url=pm_url, auth=auth, headers_user_agent=USER_AGENT)
    assert rudi_node_writer.headers_user_agent == USER_AGENT
    assert rudi_node_writer._pm_url == pm_url
    assert rudi_node_writer.connector.test_connection()


rudi_node_writer = RudiNodeWriter(pm_url=pm_url, auth=auth)


def test_metadata_count():
    assert rudi_node_writer.metadata_count > 0
    assert len(rudi_node_writer.metadata_list) == rudi_node_writer.metadata_count


def test_metadata_list():
    assert is_uuid_v4(rudi_node_writer.metadata_list[0]["global_id"])


def test_organization_list():
    orgs = rudi_node_writer.organization_list
    org1 = orgs[0]
    assert is_uuid_v4(org1["organization_id"])
    RudiOrganization.from_json(org1)


def test_used_organization_list():
    assert is_uuid_v4(rudi_node_writer.used_organization_list[0]["organization_id"])


def test_organization_names():
    assert isinstance(rudi_node_writer.organization_names[0], str)


def test_contact_list():
    assert is_uuid_v4(rudi_node_writer.contact_list[0]["contact_id"])


def test_used_contact_list():
    assert is_uuid_v4(rudi_node_writer.used_contact_list[0]["contact_id"])


def test_contact_names():
    assert isinstance(rudi_node_writer.contact_names[0], str)
