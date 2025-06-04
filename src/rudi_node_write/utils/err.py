from math import ceil
from time import time

from rudi_node_write.utils.jwt import get_jwt_exp
from rudi_node_write.utils.str_utils import slash_join


class MissingEnvironmentVariableException(ValueError):
    def __init__(self, var_name: str, var_use: str = ""):
        super().__init__(f"an environment variable should be defined {var_use}: {var_name}")


class IniMissingValueException(ValueError):
    def __init__(self, ini_section: str, ini_subsection: str, err_msg: str):
        super().__init__(f"Missing value in INI config file for parameter {ini_section}.{ini_subsection}: {err_msg}")


class IniUnexpectedValueException(ValueError):
    def __init__(self, ini_section: str, ini_subsection: str, err_msg: str):
        super().__init__(f"Unexpected value in INI config file for parameter {ini_section}.{ini_subsection}: {err_msg}")


class NoNullException(ValueError):
    def __init__(self, err_msg: str):
        super().__init__(err_msg)


class MissingParameterException(ValueError):
    def __init__(self, param_name: str):
        super().__init__(f"no value was provided for parameter '{param_name}'")


class UnexpectedValueException(ValueError):
    def __init__(self, param_name: str, expected_val, received_val):
        super().__init__(
            f"Unexpected value for parameter '{param_name}': expected '{expected_val}', got '{received_val}'"
        )


class LiteralUnexpectedValueException(ValueError):
    def __init__(
        self,
        received_val,
        expected_literal: tuple,
        err_msg: str = "Unexpected value error",
    ):
        super().__init__(f"{err_msg}. Expected {expected_literal}, got '{received_val}'")


class ExpiredTokenException(Exception):
    def __init__(self, jwt: str | None = None):
        if jwt is None:
            super().__init__("a JWT is required")
        else:
            exp = get_jwt_exp(jwt)
            now_epoch_s = ceil(time())
            super().__init__(f"JWT has expired: {exp} < {now_epoch_s}")


class HttpError(Exception):
    def __init__(
        self, err, status=500, req_method: str | None = None, base_url: str | None = None, url: str | None = None
    ):
        here = "HttpError"
        self.status = status
        self.method = req_method
        self.base_url = base_url
        self.url = url
        # print(here, f"http err {self.status}:", err)
        if type(err) is dict and "error" in err and "message" in err:
            self.status = err["status"] if "status" in err else err.get("statusCode")
            err_type = err["error"]
            err_msg = err["message"]
            self.message = f"{err_type}: {err_msg}"
        else:
            self.message = f"{err}"
        if req_method and base_url:
            self.message = f"for request '{req_method} {slash_join(base_url, url)}' -> {err}"
        super().__init__(self.message)

    def __str__(self):
        return f"HTTP ERR {self.status} {self.message}"


class HttpErrorNotFound(HttpError):
    status = 404

    def __init__(self, err, req_method: str | None = None, base_url: str | None = None, url: str | None = None):
        super().__init__({"status": 404, "error": "Not found", "message": err}, req_method, base_url, url)
