from base64 import urlsafe_b64decode, urlsafe_b64encode

from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.jwt import is_base64_url, pad_b64_str


class RudiNodeAuth(Serializable):
    """
    Authorization object that makes it possible to connect to the RUDI node UI backend API
    with the credentials of a user account with editor role.
    """

    def __init__(self, b64url_auth: str | None = None, usr: str | None = None, pwd: str | None = None):
        """
        This object can be initialized in two ways:
        - either a `b64url_auth` URL-safe Base64 encoded `usr:pwd` string
        - or with a couple of `usr` and `pwd` strings
        """
        if b64url_auth is not None:
            self._b64_auth = pad_b64_str(b64url_auth)
            if not is_base64_url(self._b64_auth):
                raise ValueError("The input `b64url_auth` should be a urlsafe-base64 string.")
            try:
                self.usr, self.pwd = urlsafe_b64decode(b64url_auth).decode("utf-8").split(":")
            except:
                raise ValueError(
                    "The input `b64url_auth` should be a urlsafe-base64 string that encodes a `usr:pwd` string couple"
                )
        elif usr is not None and pwd is not None:
            self.usr = usr
            self.pwd = pwd
            self._b64_auth = urlsafe_b64encode(bytes(f"{usr}:{pwd}", "utf-8")).decode("ascii").replace("=", "")
        else:
            raise ValueError(
                "Either a urlsafe-base64 string `b64url_auth` parameter or a couple of usr/pwd strings are to be provided"
            )

    def to_json(self, keep_nones: bool = False) -> dict | list | str:
        return "***"

    def to_json_str(self, keep_nones: bool = False, ensure_ascii: bool = False, sort_keys: bool = False) -> str:
        return "***"

    def __str__(self) -> str:
        return "***"

    @staticmethod
    def from_json(o: dict | str):
        if isinstance(o, str):
            if is_base64_url(o):
                return RudiNodeAuth(b64url_auth=o)
            str_list = o.split(":")
            if len(str_list) == 2:
                usr, pwd = str_list
                return RudiNodeAuth(usr=usr, pwd=pwd)
            raise ValueError("The input is a string that cannot be recognized as identifiers")
        if isinstance(o, dict):
            for key in ("b64auth", "b64_auth", "b64url_auth", "b64_url_auth"):
                if (b64_auth := o.get(key)) is not None:
                    return RudiNodeAuth(b64url_auth=b64_auth)
            usr = o.get("usr")
            pwd = o.get("pwd")
            if usr is not None and pwd is not None:
                return RudiNodeAuth(usr=usr, pwd=pwd)
        raise ValueError("The input cannot be recognized as identifiers")

    @property
    def basic_auth(self) -> str:
        return f"Basic {pad_b64_str(self._b64_auth)}"
