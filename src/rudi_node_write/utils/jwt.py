from base64 import urlsafe_b64decode, urlsafe_b64encode
from json import loads
from math import ceil
from re import Pattern, compile
from time import time

from rudi_node_write.utils.log import log_e
from rudi_node_write.utils.typing_utils import is_def

REGEX_JWT: Pattern = compile(r"^([\w-]+\.){2}[\w-]+$")


def is_base64_url(sb):
    """
    Check if an input is urlsafe-base64 encoded
    :param sb: a string or a bytes
    source: https://stackoverflow.com/a/45928164
    """
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(sb, "ascii")
        elif isinstance(sb, bytes):
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")
        return urlsafe_b64encode(urlsafe_b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False


def pad_b64_str(jwt_base64url: str):
    jwt_str_length = len(jwt_base64url)
    _, mod = divmod(jwt_str_length, 4)
    return jwt_base64url if mod == 0 else jwt_base64url.ljust(jwt_str_length + 4 - mod, "=")


def get_basic_auth(usr: str, pwd: str):
    auth_str = urlsafe_b64encode(bytes(f"{usr}:{pwd}", "utf-8")).decode("ascii").replace("=", "")
    return f"Basic {pad_b64_str(auth_str)}"


def get_jwt_exp(jwt: str) -> int:
    _, jwt_body_b64, _ = jwt.split(".")
    jwt_body_b64_pad = pad_b64_str(jwt_body_b64)
    jwt_str = urlsafe_b64decode(jwt_body_b64_pad).decode("utf-8")
    jwt_json = loads(jwt_str)
    return int(jwt_json["exp"])


def is_jwt_valid(jwt) -> bool:
    """
    Warning: this does not check the signature of the JWT, only the format of it, and the expiration date!
    """
    return not is_jwt_expired(jwt)


def is_jwt_expired(jwt) -> bool:
    """
    Check the format of the JWT, and if the expiration date is before now.
    """
    if jwt is None or not isinstance(jwt, str) or len(jwt) == 0:
        return True
    try:
        exp = get_jwt_exp(jwt)
        now_epoch_s = ceil(time())
        return exp < now_epoch_s
    except ValueError as e:
        log_e("is_jwt_expired", f"this is not a JWT: '{jwt}'", e)
        return True


if __name__ == "__main__":  # pragma: no cover
    for arg in ["testing", "YrmFjpOshYMxl0tth73NhYmtl4GFzew"]:
        print("* is_base64_url", f"'{arg}'? ->", is_base64_url(arg))
        arg = pad_b64_str(arg)
        print("* is_base64_url", f"'{arg}'? ->", is_base64_url(arg))
