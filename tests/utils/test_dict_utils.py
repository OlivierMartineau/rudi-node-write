from re import compile

import pytest

from rudi_node_write.utils.dict_utils import (
    check_get_key,
    check_is_dict_or_none,
    filter_dict_list,
    find_in_dict_list,
    is_dict,
    has_key,
    check_has_key,
    is_element_matching_one_of_filters,
    safe_get_key,
    pick_in_dict,
    is_element_matching_filter,
    check_is_dict,
    merge_dict_of_list,
)


def test_is_dict():
    assert is_dict({"arg": "val"})


def test_check_is_dict():
    assert check_is_dict_or_none(None) is None
    with pytest.raises(TypeError, match="input argument should be a Python 'dict'. Got: 'NoneType'"):
        check_is_dict(None)
    assert check_is_dict({"arg": "val"})
    assert check_is_dict({"arg": "val"}) == {"arg": "val"}


def test_has_key():
    assert has_key({"key": "val"}, "key")
    assert not has_key({"key": "val"}, "a")
    assert not has_key("key", "a")  # type: ignore


def test_check_has_key():
    assert check_has_key({"arg": "val"}, "arg") == "val"
    with pytest.raises(AttributeError):
        check_has_key({"arg": "val"}, "val")
    err_pattern = compile("attribute 'val' missing in \\{'arg1': 'val', 'arg2': 'long_val_\\[[0-9, ]+\\(\\.{3}\\)")
    with pytest.raises(AttributeError, match=err_pattern):
        check_has_key({"arg1": "val", "arg2": f"long_val_{[x for x in range(100)]}"}, "val")


def test_check_get_key():
    assert check_get_key({"arg": "val"}, "arg") == "val"
    with pytest.raises(AttributeError, match="attribute 'val' missing in {'arg': 'val'}"):
        check_get_key({"arg": "val"}, "val")
    with pytest.raises(TypeError, match="First input argument should be an object"):
        check_get_key(None)  # type: ignore
        check_get_key(None, None)  # type: ignore
    with pytest.raises(ValueError, match="An attribute should be given"):
        check_get_key({"arg": "val"})
    assert check_get_key({"one": {"two": "three"}}, "one", "two") == "three"


def test_safe_get_key():
    assert safe_get_key(None) is None
    assert safe_get_key("er") is None
    assert safe_get_key({"arg": "val"}) is None
    assert safe_get_key({"arg": "val"}, "arg") == "val"
    assert safe_get_key({"lvl1": {"a_dict": "val"}}, "lvl1") == {"a_dict": "val"}
    assert safe_get_key({"lvl1": {"a_dict": "val"}}, "lvl1", "lvl1") is None
    assert safe_get_key({"lvl1": {"a_dict": "val"}}, "lvl1", "a_dict") == "val"
    assert safe_get_key({"lvl1": {"a_dict": {"lvl3": "val"}}}, "lvl1", "a_dict", "lvl3") == "val"
    assert safe_get_key({"lvl1": {"a_dict": {"lvl3": "val"}}}, "lvl1", "a_dict", "lvl3", "lvl4") is None


def test_pick_in_dict():
    assert pick_in_dict({"key1": "val1", "key2": "val2"}, ["key1"]) == {"key1": "val1"}
    assert pick_in_dict({"key1": "val1", "key2": "val2"}, ["key3"]) == {}
    a_dict = {"key1": "val1", "key2": "val2", "key3": "val3"}
    assert pick_in_dict(a_dict, ["key1", "key3"]) == {"key1": "val1", "key3": "val3"}


obj_a = {"a": "val1", "b": "val2", "c": "val3"}
obj_b = {"d": "val4", "e": "val5", "f": "val6"}


def test_is_element_matching_one_of_filters():
    assert is_element_matching_one_of_filters(obj_a, [{"f": "val1", "b": "val2"}, {"a": "val1", "b": "val2"}])
    assert not is_element_matching_one_of_filters(obj_a, [{"f": "val1", "b": "val2"}, {"a": "val1", "t": "val2"}])


def test_filter_dict_list():
    assert filter_dict_list([{"f": "val1", "b": "val2"}, {"a": "val1", "b": "val2"}, obj_b], obj_b) == [obj_b]
    assert filter_dict_list([{"f": "val1", "b": "val2"}, obj_a, obj_b], [obj_b, obj_a]) == [obj_a, obj_b]


def test_find_in_dict_list():
    assert find_in_dict_list([{"f": "val1", "b": "val2"}, {"a": "val1", "b": "val2"}, obj_b], obj_b) == obj_b
    assert find_in_dict_list([{"f": "val1", "b": "val2"}, obj_a, obj_b], obj_a) == obj_a
    assert find_in_dict_list([{"f": "val1", "b": "val2"}], obj_a) is None


def test_is_element_matching_filter():
    assert not is_element_matching_filter("a", "1")
    list_a = ["1", "4", "5"]
    assert is_element_matching_filter(list_a, "1")
    assert is_element_matching_filter(list_a, ["1", "5"])
    assert not is_element_matching_filter(list_a, "2")

    list_b = [obj_a, obj_b]
    assert is_element_matching_filter(obj_a, {"a": "val1", "b": "val2"})
    assert is_element_matching_filter(obj_a, {"b": "val2", "a": "val1"})
    assert not is_element_matching_filter(obj_a, "a")
    assert not is_element_matching_filter(obj_a, {"a": "val1", "bb": "val2"})
    assert not is_element_matching_filter(obj_a, {"a": "val1", "b": "val2", "d": "val1"})
    assert not is_element_matching_filter(obj_b, {"a": "val1", "b": "val2"})
    assert is_element_matching_filter(list_b, {"a": "val1", "b": "val2"})
    assert not is_element_matching_filter(list_b, {"a": "val1", "b": "val1"})
    assert is_element_matching_filter(list_b, [{"d": "val4", "e": "val5", "f": "val6"}, {"a": "val1", "b": "val2"}])
    assert not is_element_matching_filter(list_b, [{"d": "val4", "e": "val5", "f": "val6"}, {"a": "val1", "b": "val3"}])
    assert is_element_matching_filter({"x": list_b}, {"x": {"a": "val1", "b": "val2"}})
    assert is_element_matching_filter({"x": [list_b]}, {"x": {"a": "val1", "b": "val2"}})
    assert is_element_matching_filter({"x": obj_a}, {"x": {"a": "val1", "b": "val2"}})
    assert not is_element_matching_filter({"x": obj_b}, {"x": {"a": "val1", "b": "val2"}})
    assert is_element_matching_filter({"x": [obj_a]}, {"x": {"a": "val1", "b": "val2"}})
    assert is_element_matching_filter({"x": [obj_a, obj_b]}, {"x": {"a": "val1", "b": "val2"}})
    assert is_element_matching_filter({"x": [obj_b, list_b]}, {"x": {"a": "val1", "b": "val2"}})
    assert not is_element_matching_filter({"x": list_b}, {"y": {"a": "val1", "b": "val2"}})
    assert not is_element_matching_filter({"x": [list_b]}, {"y": {"a": "val1", "b": "val2"}})


def test_merge_dict_of_list():
    assert merge_dict_of_list({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
