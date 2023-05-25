from rudi_node_write.io_connectors.io_connector import Connector
from rudi_node_write.utils.date import time_epoch_s
from rudi_node_write.utils.err import UnexpectedValueException
from rudi_node_write.utils.file import read_file
from rudi_node_write.utils.jwt import get_jwt_basic_auth, is_jwt_expired
from rudi_node_write.utils.log import log_d, log_e
from rudi_node_write.utils.type_dict import has_key

B64_AUTH_KEY = 'b64auth'
USR_AUTH_KEY = 'usr'
PWD_AUTH_KEY = 'pwd'


class RudiNodeJwtFactory(Connector):
    def __init__(self, server_url: str, auth: dict, default_exp_s: int = 3600,
                 headers_user_agent: str = 'RudiNodeJwtFactory'):
        super().__init__(server_url)
        if has_key(auth, B64_AUTH_KEY):
            self._b64_auth = f'Basic {auth[B64_AUTH_KEY]}'
        elif has_key(auth, USR_AUTH_KEY) and has_key(auth, PWD_AUTH_KEY):
            self._b64_auth = get_jwt_basic_auth(auth[USR_AUTH_KEY], auth[PWD_AUTH_KEY])
        else:
            err_msg = f"{B64_AUTH_KEY}', or both '{USR_AUTH_KEY}' and '{PWD_AUTH_KEY}"
            raise UnexpectedValueException('auth', err_msg, auth)

        self._headers = {'User-Agent': headers_user_agent, 'Content-type': 'text/plain', 'Accept': 'application/json',
                         'Authorization': self._b64_auth}

        self.test_connection()
        self._jwt = None
        self._default_exp_s = default_exp_s

    def test_connection(self):
        test = self.request(relative_url='crypto/jwt', req_method='GET', headers=self._headers)
        if test['RUDI'] != 'JWT':
            log_e('RudiNodeJwtFactory', f"!! Node '{self.host}'", 'no connection!')
            raise ConnectionError(f"An error occurred while connecting to RUDI node JWT server {self.base_url}")
        log_d('RudiNodeJwtFactory', f"Node '{self.host}'", 'connection OK')
        return True

    def _renew_jwt(self, delay_s: int):
        if delay_s is None:
            delay_s = self._default_exp_s
        jwt_body = {'exp': time_epoch_s(self._default_exp_s if delay_s is None else delay_s),
                    'sub': 'rudi_prod_token',
                    'req_mtd': 'all',
                    'req_url': 'all'}
        return self.request(relative_url='crypto/jwt/forge', req_method='POST', body=jwt_body, headers=self._headers)

    def get_jwt(self, delay_s: int = 3600):
        if is_jwt_expired(self._jwt):
            self._jwt = self._renew_jwt(delay_s)
        return self._jwt


if __name__ == '__main__':
    creds_file = '../../../creds/creds.json'
    rudi_node_creds = read_file(creds_file)

    rudi_jwt_connector = RudiNodeJwtFactory('https://bacasable.fenix.rudi-univ-rennes1.fr', rudi_node_creds)
    log_d('RudiNodeJwtFactory', 'jwt', rudi_jwt_connector.get_jwt())
