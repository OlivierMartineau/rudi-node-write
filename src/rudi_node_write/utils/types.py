def get_type_name(obj):
    return type(obj).__name__


def is_type(obj, type_name: str):
    return get_type_name(obj) == type_name


def is_bool(b):
    return get_type_name(b) == 'bool'


def check_is_bool(b):
    if not is_bool(b):
        raise TypeError(f"input parameter should be a bool, got '{get_type_name(b)}' for input '{b}'.")


def is_list(obj):
    return get_type_name(obj) == 'list'


def is_array(obj):
    return is_list(obj)


def is_list_or_dict(obj):
    return get_type_name(obj) in ['dict', 'list']


def get_first_list_elt_or_none(elt_list):
    if len(elt_list) > 0:
        return elt_list[0]
    else:
        return None


def check_type(obj, type_name: str | list[str], param_name: str = None):
    param_str = 'Parameter' if param_name is None else f"Parameter '{param_name}'"
    obj_type_name = get_type_name(obj)
    if is_type(type_name, 'str'):
        type_list = [type_name]
    elif is_type(type_name, 'list'):
        type_list = type_name
    else:
        raise NotImplementedError(
            f"Parameter 'type_name' should be either a string or a list of strings, got '{obj_type_name}'")
    if obj_type_name not in type_list:
        raise TypeError(f"{param_str} should be in '{type_list}', got '{get_type_name(obj)}'")
    return obj


def check_is_int(n):
    if not is_type(n, 'int'):
        raise TypeError(f"input parameter should be an int, got '{get_type_name(n)}' for input '{n}'.")
    return n


def is_number(n):
    return get_type_name(n) in ['int', 'float']


def check_is_number(n):
    if not is_number(n):
        raise TypeError(f"input parameter should be a float or an int, got '{get_type_name(n)}' for input '{n}'.")
    return n


def to_float(val):
    try:
        f_val = float(val)
    except (TypeError, ValueError):
        raise ValueError(f"could not convert value into a float: '{val}'")
    return f_val
