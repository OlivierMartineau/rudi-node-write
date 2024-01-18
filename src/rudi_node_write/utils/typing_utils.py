from re import compile
from typing import Type


def get_type_name(obj) -> str:
    return type(obj).__name__


def is_type_name(obj, type_name: str) -> bool:
    return get_type_name(obj) == type_name


def is_type(o, target_class: Type | tuple) -> bool:
    return isinstance(o, target_class)


def are_same_type(obj, other) -> bool:
    return isinstance(other, obj.__class__) and isinstance(obj, other.__class__)


def does_inherit_from(obj, mother_class) -> bool:
    return issubclass(type(obj), mother_class)


def is_bool(b: bool) -> bool:
    return isinstance(b, bool)


def check_is_bool(b: bool, accept_none: bool = False) -> bool | None:
    if b is None and accept_none:
        return None
    if not isinstance(b, bool):
        raise TypeError(f"input should be a bool, got '{get_type_name(b)}' for input '{b}'.")
    return b


# https://stackoverflow.com/a/152596/1563072
def check_type(o, target_class: Type | tuple, accept_none: bool = False):
    if o is None:
        if accept_none:
            return None
        raise ValueError("input should not be null")
    if isinstance(o, target_class):
        return o
    target_class_name = (
        " | ".join([f"'{t.__name__}'" for t in target_class])
        if isinstance(target_class, tuple)
        else f"'{target_class.__name__}'"
    )
    raise TypeError(f"input should be of type {target_class_name}, got '{get_type_name(o)}'")


def check_is_int(n: int, accept_none: bool = False, accept_castable: bool = False) -> int | None:
    if n is None and accept_none:
        return None
    if isinstance(n, int):
        return n
    if accept_castable:
        return ensure_is_int(n, accept_none=accept_none)
    raise TypeError(f"input parameter should be an int, got '{get_type_name(n)}' for input '{n}'.")


def ensure_is_int(n: int, accept_none: bool = False) -> int | None:
    if n is None and accept_none:
        return None
    if isinstance(n, int):
        return n
    try:
        return int(n)
    except TypeError:
        raise TypeError(f"input parameter of type '{get_type_name(n)}' cannot be cast into an int: '{n}'.")


def is_number(n) -> bool:
    return isinstance(n, (int, float))


def ensure_is_number(n) -> int | float:
    if not is_number(n):
        try:
            return to_number(n)
        except TypeError:
            pass
        raise TypeError(f"input parameter should be a float or an int, got '{get_type_name(n)}' for input '{n}'.")
    return n


REGEX_INT = compile(r"^[+-]?[0-9]+$")
REGEX_FLOAT = compile(r"^[+-]?[0-9]*[.][0-9]+([eE][+-]?[0-9]+)?$")


def to_number(n: str | int | float) -> int | float:
    if is_number(n):
        return n
    if REGEX_INT.match(n):
        return int(n)
    if REGEX_FLOAT.match(n):
        return float(n)
    raise TypeError(f"input parameter of type '{get_type_name(n)}' cannot be cast into a float or an int: '{n}'.")


def to_float(val) -> float:
    try:
        f_val = float(val)
    except (TypeError, ValueError):
        raise ValueError(f"could not convert value into a float: '{val}'")
    return f_val


def is_def(val, strict: bool = True) -> bool:
    return not is_null(val, strict)


def check_is_def(val, strict: bool = False):
    """
    Makes sure it returns None if input val is 'null' or 'None'
    :param strict: True if the check should be strict, i.e. input is None, "None", "null", [], '', {}
    :param val:
    :return:
    """
    if not is_null(val, strict):
        return val
    raise ValueError("input value is required")


def is_null(val, strict: bool = False) -> bool:
    if val is None:
        return True
    if not strict:
        return (not val) or (val in ["null", "None"])
    # log_d("is_null", val, "strict=", strict)
    return val != 0 and not is_bool(val) and not val and not (val in ["null", "None", "[]", "{}"])
