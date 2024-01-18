from rudi_node_write.connectors.io_rudi_media_write import RudiMediaHeadersFactoryBasicAuth, RudiNodeMediaConnector
from rudi_node_write.utils.file_utils import is_file, read_json_file, is_dir

USR_AUTH_KEY = "usr"
PWD_AUTH_KEY = "pwd"

test_dir = "./dwnld"
if not is_dir(test_dir):
    raise FileNotFoundError(f"A local dir should be created at path '{test_dir}'")

creds_file = "./creds/creds.json"
if not is_file(creds_file):
    raise FileNotFoundError(f"A JSON file with the credentials for accessing the node is required at {creds_file}")
rudi_node_creds = read_json_file(creds_file)


def test_RudiMediaHeadersFactoryBasicAuth():
    media_headers_factory = RudiMediaHeadersFactoryBasicAuth(
        usr=rudi_node_creds[USR_AUTH_KEY], pwd=rudi_node_creds[PWD_AUTH_KEY]
    )
    rudi_media = RudiNodeMediaConnector(server_url=rudi_node_creds["url"], headers_factory=media_headers_factory)

    assert len(rudi_media.media_list) > 0
