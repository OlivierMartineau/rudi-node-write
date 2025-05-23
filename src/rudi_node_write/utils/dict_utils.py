from rudi_node_write.utils.list_utils import merge_lists
from rudi_node_write.utils.str_utils import check_is_string
from rudi_node_write.utils.typing_utils import get_type_name


def is_dict(obj) -> bool:
    """
    :return: True of input o is an object, False otherwise
    """
    return isinstance(obj, dict)


def check_is_dict(o) -> dict:
    """
    :return: True of input o is an object, False otherwise
    """
    if not isinstance(o, dict):
        raise TypeError(f"input argument should be a Python 'dict'. Got: '{get_type_name(o)}'")
    return o


def check_is_dict_or_none(o) -> dict | None:
    if o is None:
        return None
    return check_is_dict(o)


def has_key(obj: dict | None, key_name: str | None) -> bool:
    """
    :param obj: an object
    :param key_name: the name of the attribute, that we need to ensure the input object has
    :return: True if input object has an attribute with input key name. False otherwise.
    """
    return isinstance(obj, dict) and obj.get(key_name) is not None


MAX_STR_LEN = 200


def check_has_key(obj: dict, key_name: str):
    if not has_key(check_is_dict(obj), check_is_string(key_name)):
        if len(obj_str := str(obj)) > MAX_STR_LEN:
            obj_str = obj_str[:MAX_STR_LEN] + " (...)"
        raise AttributeError(f"attribute '{key_name}' missing in {obj_str}")
    return obj[key_name]


def check_get_key(obj: dict, *args):
    if not isinstance(obj, dict):
        raise TypeError("First input argument should be an object")
    if len(args) == 0:
        raise ValueError("An attribute should be given")
    val = check_has_key(obj, args[0])
    if len(args) == 1:
        return val
    return check_get_key(val, *args[1:])


def safe_get_key(obj, *args):
    """
    Offers a way to access an object attribute hierarchy without raising an error if the attribute doesn't exist
    :param root: an object
    :param args: hierarchy of attributes we need to access.
    :return: None if the operation doesn't succeed. o['arg1']['arg2']...['argN'] otherwise.
    """
    if not isinstance(obj, dict):
        return None
    leaf = obj
    nb_args = len(args)
    for i, key_name in enumerate(args):
        leaf = leaf.get(key_name)
        if leaf is None:
            return None
        if i + 1 == nb_args:
            return leaf
        if not isinstance(leaf, dict):
            return None
    return None


def pick_in_dict(obj: dict, props: list[str]):
    """
    From a given object, returns a partial object with only the given attributes
    :param obj: an object
    :param props: the attributes to keep from the input object
    :return:
    """
    return dict((k, obj[k]) for k in props if k in obj)


def is_element_matching_filter(element, match_filter) -> bool:
    """
    An element is considered to be matching a filter if all the key/value pairs in the filter are found in the element
    :param element: element that is tested
    :param match_filter: object whose key/value pairs must be found in the tested element
    :return: True if the element is matching the filter object
    """
    if element == match_filter:
        return True
    if not isinstance(element, (list, dict)):
        return False
    if isinstance(element, dict):
        if not isinstance(match_filter, dict):
            return False
        for key, val in match_filter.items():
            if not has_key(element, key) or not is_element_matching_filter(element[key], val):
                return False
        return True
    if isinstance(match_filter, dict):
        for e in element:
            if is_element_matching_filter(e, match_filter):
                return True
        return False
    if isinstance(match_filter, list):
        for mf in match_filter:
            if not is_element_matching_filter(element, mf):
                return False
        return True
    return match_filter in element


def merge_dict_of_list(dict_a: dict, dict_b: dict):
    return {
        key: merge_lists(dict_a.get(key), dict_b.get(key)) for key in set(list(dict_a.keys()) + list(dict_b.keys()))
    }


def is_element_matching_one_of_filters(element, search_filter_list: list) -> bool:
    """
    An element is matching a filter list if it matches at least one of the filters in the filter list.
    An element is considered to be matching a filter if all the key/value pairs in the filter are found in the element
    :param element: element to be tested
    :param search_filter_list: list of filter objects
    :return: True if the element is matching at least one of the filter object of the filter list
    """
    for i, filter_dict in enumerate(search_filter_list):
        if is_element_matching_filter(element, filter_dict):
            return True
    return False


def filter_dict_list(searched_list: list, search_filter: dict | list[dict]) -> list:
    """
    Select the elements of a list that match one or several filters.
    If the filter is a list of filter dict, an element is kept if it matches at least one of the filter
    objects.
    An element matches a filter objects if its properties match every key/value pair in the filter.
    :param searched_list: a list to filter
    :param search_filter: a filter object or a list of filter object
    :return:
    """
    found_elements = []
    for element in searched_list:
        if isinstance(search_filter, dict):
            if is_element_matching_filter(element, search_filter):
                found_elements.append(element)
        elif isinstance(search_filter, list):
            if is_element_matching_one_of_filters(element, search_filter):
                found_elements.append(element)
    return found_elements


def find_in_dict_list(searched_list: list, search_filter: dict) -> dict | None:
    """
    Returns the first element in list that matches the input filter.
    None otherwise
    :param searched_list:
    :param search_filter:
    :return: the first element in list that matches the input filter. None otherwise.
    """
    for element in searched_list:
        if is_element_matching_filter(element, search_filter):
            return element
    return None
