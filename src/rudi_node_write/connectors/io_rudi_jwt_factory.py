from rudi_node_write.connectors.io_connector import Connector
from rudi_node_write.utils.dict_utils import has_key
from rudi_node_write.utils.err import UnexpectedValueException
from rudi_node_write.utils.file_utils import read_json_file
from rudi_node_write.utils.jwt import get_basic_auth, is_jwt_expired
from rudi_node_write.utils.log import log_d, log_e
from rudi_node_write.utils.type_date import Date

B64_AUTH_KEY = "b64auth"
USR_AUTH_KEY = "usr"
PWD_AUTH_KEY = "pwd"

DEFAULT_EXP = 3600


class RudiNodeJwtFactory(Connector):
    def __init__(
        self,
        server_url: str,
        auth: dict,
        default_exp_s: int = DEFAULT_EXP,
        headers_user_agent: str = "RudiNodeJwtFactory",
    ):
        super().__init__(server_url)
        self.sub = "rudi_prod_token"
        if has_key(auth, B64_AUTH_KEY):
            self._b64_auth = f"Basic {auth[B64_AUTH_KEY]}"
        elif has_key(auth, USR_AUTH_KEY) and has_key(auth, PWD_AUTH_KEY):
            self._b64_auth = get_basic_auth(auth[USR_AUTH_KEY], auth[PWD_AUTH_KEY])
        elif has_key(auth, "sub"):
            self.sub = auth["sub"]
            self._b64_auth = ""
        else:
            err_msg = f"{B64_AUTH_KEY}', or both '{USR_AUTH_KEY}' and '{PWD_AUTH_KEY}"
            raise UnexpectedValueException("auth", err_msg, auth)

        self._headers = {
            "User-Agent": headers_user_agent,
            "Content-Type": "application/json",
            "Authorization": self._b64_auth,
        }
        log_d("RudiNodeJwtFactory.init", "self._b64_auth", self._b64_auth)
        self.test_connection()
        self._jwt = None
        self._default_exp_s = default_exp_s

    def test_connection(self):
        test = self.request(relative_url="crypto/jwt", req_method="GET", headers=self._headers)
        if not isinstance(test, dict) or test.get("RUDI") != "JWT":
            log_e("RudiNodeJwtFactory", f"!! Node '{self.host}'", "no connection!")
            raise ConnectionError(f"An error occurred while connecting to RUDI node JWT server {self.base_url}")
        # log_d("RudiNodeJwtFactory", f"Node '{self.host}'", "connection OK")
        return True

    def _renew_jwt(self, delay_s: int) -> str:
        if delay_s is None or not isinstance(delay_s, int) or delay_s < 2:
            delay_s = self._default_exp_s
        jwt_body = {
            "exp": Date.time_epoch_s(delay_s),
            "sub": self.sub,
            "req_mtd": "all",
            "req_url": "all",
        }
        reply = self.request(
            relative_url="crypto/jwt/forge",
            req_method="POST",
            body=jwt_body,
            headers=self._headers,
        )
        if is_jwt_expired(reply):
            raise ValueError(f"The JWT server replied with an expired JWT or an unexpected answer: {reply}")
        return str(reply)

    def get_jwt(self, delay_s: int | None = None) -> str:
        if delay_s is None or not isinstance(delay_s, int) or delay_s < 2:
            delay_s = self._default_exp_s
        if is_jwt_expired(self._jwt):
            self._jwt = self._renew_jwt(delay_s)
        return self._jwt  # type: ignore


if __name__ == "__main__":  # pragma: no cover
    tests = "JwtFactory tests"
    creds_file = "../creds/creds_bas.json"
    rudi_node_creds = read_json_file(creds_file)
    # log_d(tests, "rudi_node_creds", rudi_node_creds)
    rudi_jwt_connector = RudiNodeJwtFactory(rudi_node_creds["url"], rudi_node_creds)
    log_d("RudiNodeJwtFactory", "jwt", rudi_jwt_connector.get_jwt())
