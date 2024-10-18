from rudi_node_write.connectors.io_rudi_media_write import RudiMediaHeadersFactoryBasicAuth, RudiNodeMediaConnector
from rudi_node_write.connectors.rudi_node_auth import RudiNodeAuth
from rudi_node_write.utils.file_utils import is_file, read_json_file, is_dir

USR_AUTH_KEY = "usr"
PWD_AUTH_KEY = "pwd"
NODE_URL = "url"

test_dir = "./dwnld"
if not is_dir(test_dir):
    raise FileNotFoundError(f"A local dir should be created at path '{test_dir}'")

creds_file = "./creds/creds_bas.json"
if not is_file(creds_file):
    raise FileNotFoundError(f"A JSON file with the credentials for accessing the node is required at {creds_file}")
rudi_node_creds = read_json_file(creds_file)


def test_RudiMediaHeadersFactoryBasicAuth():
    auth = RudiNodeAuth.from_json(rudi_node_creds)
    assert isinstance(auth, RudiNodeAuth)
    media_headers_factory = RudiMediaHeadersFactoryBasicAuth(auth)
    rudi_media = RudiNodeMediaConnector(server_url=rudi_node_creds[NODE_URL], headers_factory=media_headers_factory)

    assert len(rudi_media.media_list) > 0
