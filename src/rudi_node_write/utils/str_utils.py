from os.path import abspath, join
from re import compile
from typing import Callable
from uuid import UUID, uuid4

from rudi_node_write.utils.typing_utils import get_type_name


def is_string(s):
    return isinstance(s, str)


def check_is_string(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError(f"input object should be a string, got '{get_type_name(s)}'")
    return s


def check_is_string_or_none(s: str | None) -> str | None:
    if s is None:
        return None
    return check_is_string(s)


REGEX_EMAIL = compile(
    r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
)

REGEX_UUID = compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def is_email(email_str: str):
    return isinstance(email_str, str) and bool(REGEX_EMAIL.match(email_str))


def check_is_email(email_str: str) -> str:
    if email_str is None:
        raise ValueError("a valid email should be provided")
    if not is_email(email_str):
        raise ValueError(f"this is not a valid email: '{email_str}'")
    return email_str


def uuid4_str() -> str:
    return str(uuid4())


def is_uuid_v4(uuid) -> bool:
    if uuid is None or not isinstance(uuid, (str, UUID)):
        return False
    try:
        uuid_v4 = UUID(str(uuid))
        return True if uuid_v4.version == 4 else False
    except ValueError:
        return False


def check_is_uuid4(uuid) -> str:
    if uuid is None:
        raise ValueError("Input parameter should not be null")
    if not isinstance(uuid, (str, UUID)):
        raise ValueError(f"Input parameter is not a valid UUID v4: '{uuid}'")
    try:
        uuid_v4 = UUID(str(uuid))
        if uuid_v4.version == 4:
            return str(uuid_v4)
    except ValueError:
        pass
    raise ValueError(f"Input parameter is not a valid UUID v4: '{uuid}'")


def absolute_path(*args) -> str:
    return abspath(join(*args))


def slash_join(*args) -> str:
    """
    Joins a set of strings with a slash (/) between them (useful for merging URLs or paths fragments)
    """
    non_null_args = []
    for frag in args:
        if frag is None or frag == "":
            pass
        elif not isinstance(frag, str):
            raise AttributeError("input parameters must be strings")
        else:
            non_null_args.append(frag.strip("/"))
    joined_str = "/".join(non_null_args)
    return joined_str


def ensure_startswith(s: str, test_str: str, start_str: str | None = None, transform: Callable | None = None):
    if s.startswith(test_str):
        return s
    if transform is None:
        return test_str + s if start_str is None else start_str + s
    return transform(s)
