from time import sleep

import pytest

from rudi_node_write.connectors.io_rudi_jwt_factory import RudiNodeJwtFactory, B64_AUTH_KEY, USR_AUTH_KEY, PWD_AUTH_KEY
from rudi_node_write.utils.err import UnexpectedValueException
from rudi_node_write.utils.file_utils import read_json_file, is_file
from rudi_node_write.utils.jwt import REGEX_JWT
from rudi_node_write.utils.log import log_d


def test_RudiNodeJwtFactory():
    creds_file = "./creds/creds.json"
    if not is_file(creds_file):
        raise FileNotFoundError(f"A JSON file with the credentials for accessing the node is required at {creds_file}")
    rudi_node_creds = read_json_file(creds_file)
    url = rudi_node_creds["url"]
    jwt = None
    for creds in [
        {B64_AUTH_KEY: rudi_node_creds[B64_AUTH_KEY]},
        {
            USR_AUTH_KEY: rudi_node_creds[USR_AUTH_KEY],
            PWD_AUTH_KEY: rudi_node_creds[PWD_AUTH_KEY],
        },
    ]:
        log_d("test_RudiNodeJwtFactory", "creds", creds)
        rudi_jwt_connector = RudiNodeJwtFactory(url, creds)
        jwt = rudi_jwt_connector.get_jwt(1)
        assert REGEX_JWT.match(jwt)
    with pytest.raises(UnexpectedValueException):
        RudiNodeJwtFactory("https://bacasable.fenix.rudi-univ-rennes1.fr", {"auth": "err"})
    sleep(1)
    assert jwt != rudi_jwt_connector.get_jwt()
