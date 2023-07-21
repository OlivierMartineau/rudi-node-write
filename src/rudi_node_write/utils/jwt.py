from base64 import urlsafe_b64decode, urlsafe_b64encode
from json import loads
from math import ceil
from re import compile
from time import time

from rudi_node_write.utils.log import log_e
from rudi_node_write.utils.typing_utils import is_def

REGEX_JWT = compile(r"^([\w-]+\.){2}[\w-]+$")


def pad_b64_str(jwt_base64url: str):
    jwt_str_length = len(jwt_base64url)
    div, mod = divmod(jwt_str_length, 4)
    return jwt_base64url if mod == 0 else jwt_base64url.ljust(jwt_str_length + 4 - mod, "=")


def get_jwt_basic_auth(usr: str, pwd: str):
    token = urlsafe_b64encode(bytes(f"{usr}:{pwd}", "utf-8")).decode("ascii").replace("=", "")
    return f"Basic {pad_b64_str(token)}"


def get_jwt_exp(jwt: str) -> int:
    jwt_head_b64, jwt_body_b64, jwt_sign_b64 = jwt.split(".")
    jwt_body_b64_pad = pad_b64_str(jwt_body_b64)
    jwt_str = urlsafe_b64decode(jwt_body_b64_pad).decode("utf-8")
    jwt_json = loads(jwt_str)
    return int(jwt_json["exp"])


def is_jwt_expired(jwt: str) -> bool:
    if not is_def(jwt):
        return True
    try:
        exp = get_jwt_exp(jwt)
        now_epoch_s = ceil(time())
        return exp < now_epoch_s
    except ValueError as e:
        log_e("is_jwt_expired", f"this is not a JWT: '{jwt}'", e)
        return True
