from re import compile

import pytest

from rudi_node_write.utils.dict_utils import (
    is_dict,
    has_key,
    check_has_key,
    safe_get_key,
    pick_in_dict,
    is_element_matching_filter,
    check_is_dict,
    merge_dict_of_list,
)


def test_is_dict():
    assert is_dict({"arg": "val"})


def test_check_is_dict():
    assert check_is_dict(None, accept_none=True) is None
    with pytest.raises(TypeError, match="input argument should be a Python 'dict'. Got: 'NoneType'"):
        check_is_dict(None, accept_none=False)
    assert check_is_dict({"arg": "val"})
    assert check_is_dict({"arg": "val"}) == {"arg": "val"}


def test_has_key():
    assert has_key({"key": "val"}, "key")
    assert not has_key({"key": "val"}, "a")
    assert not has_key("key", "a")


def test_check_has_key():
    assert check_has_key({"arg": "val"}, "arg") == "val"
    with pytest.raises(AttributeError):
        check_has_key({"arg": "val"}, "val")
    err_pattern = compile("attribute 'val' missing in \\{'arg1': 'val', 'arg2': 'long_val_\\[[0-9, ]+\\(\\.{3}\\)")
    with pytest.raises(AttributeError, match=err_pattern):
        check_has_key({"arg1": "val", "arg2": f"long_val_{[x for x in range(100)]}"}, "val")


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


def test_is_element_matching_filter():
    assert not is_element_matching_filter("a", "1")
    list_a = ["1", "4", "5"]
    assert is_element_matching_filter(list_a, "1")
    assert is_element_matching_filter(list_a, ["1", "5"])
    assert not is_element_matching_filter(list_a, "2")

    obj_a = {"a": "val1", "b": "val2", "c": "val3"}
    obj_b = {"d": "val4", "e": "val5", "f": "val6"}
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
