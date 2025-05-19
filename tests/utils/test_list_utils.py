import pytest

from rudi_node_write.utils.list_utils import (
    check_is_list_or_none,
    is_iterable,
    check_is_list,
    ensure_is_str_list,
    get_first_list_elt_or_none,
    list_diff,
    list_deep_diff,
    are_list_different,
    are_list_equal,
    merge_lists,
    is_list,
    is_list_or_dict,
    is_array,
    clean_nones,
)


def test_is_iterable():
    assert not is_iterable(6)
    assert is_iterable([6])


def test_ensure_is_list():
    assert check_is_list([6, 7]) == [6, 7]
    assert check_is_list_or_none(None) is None
    for not_list in [6, "5,6,7", None]:
        with pytest.raises(TypeError, match=f"input should be a list, got '.*'"):
            check_is_list(not_list)


def test_ensure_is_str_list():
    assert ensure_is_str_list("6,7") == ["6", "7"]
    assert ensure_is_str_list("6, 7") == ["6", "7"]
    assert ensure_is_str_list(["6", "aa"]) == ["6", "aa"]
    with pytest.raises(TypeError, match=f"input should be a list, got 'int'"):
        ensure_is_str_list(6)


def test_get_first_list_elt_or_none():
    assert get_first_list_elt_or_none(None) is None
    assert get_first_list_elt_or_none([]) is None
    assert get_first_list_elt_or_none("") is None
    assert get_first_list_elt_or_none([6, "7"]) == 6


def test_list_diff():
    assert list_diff([0, 1, 2], [2, 1, 3]) == [0, 3]


def test_list_deep_diff():
    print("ttoo", list_deep_diff([{"a": [0, 1, 2]}], [{"a": [0, 2, 1]}]))
    assert list_deep_diff([{"a": [0, 1, 2]}], [{"a": [0, 2, 1]}]) == {}
    assert list_deep_diff([{"a": [0, 1, 2]}], [{"a": [0, 2, 1]}], ignore_order=False) == {
        "values_changed": {
            "root[0]['a'][1]": {"new_value": 2, "old_value": 1},
            "root[0]['a'][2]": {"new_value": 1, "old_value": 2},
        }
    }
    assert list_deep_diff([{"a": [0, 1, 2]}], [{"a": [0, 2, 1, 4]}]) == {"iterable_item_added": {"root[0]['a'][3]": 4}}

    # assert str(
    #     list_deep_diff([{"a": [0, 1, 2]}], [{"a": [2, 3, 1]}])) == "list_diff([{'a': [0, 1, 2]}], [{'a': [2, 3, 1]}])"
    # assert list_diff([{"a": [0, 1, 2]}, {"b": [1, 2, 3]}], [{"a": [1, 2, 3]}, {"b": [2, 3, 4]}]) == [0, 3]


def test_are_list_different():
    assert not are_list_different([0, 1, 2], [0, 2, 1])
    assert are_list_different([0, 1, 2], [0, 2, 1], ignore_order=False)
    assert are_list_different(None, [0, 2, 1])
    assert are_list_different([0, 2, 1], None)


def test_are_list_equal():
    assert are_list_equal([0, 1, 2], [0, 2, 1])
    assert not are_list_equal([0, 1, 2], [0, 2, 1], ignore_order=False)
    assert not are_list_equal(None, [0, 2, 1])
    assert not are_list_equal([0, 2, 1], None)
    with pytest.raises(TypeError, match="input should be a list, got 'dict'"):
        are_list_equal({"0": 1}, {"0": 1})  # type: ignore


def test_merge_lists():
    assert merge_lists(None, [0, 2, 1]) == [0, 2, 1]
    assert merge_lists([0, 2, 1], None) == [0, 2, 1]
    assert merge_lists([0, 1, 2], [0, 2, 1]) == [0, 1, 2, 0, 2, 1]
    assert merge_lists([0, 1, 2], 5) == [0, 1, 2, 5]
    assert merge_lists(5, [0, 1, 2]) == [5, 0, 1, 2]


def test_is_list():
    assert is_list([3, 4, "dfg"])
    assert not is_list(3)
    assert not is_list({"e": 3})
    assert not is_list("e")


def test_is_array():
    assert is_array(["obj"])


def test_is_list_or_dict():
    assert is_list_or_dict(["r4"])
    assert is_list_or_dict({"r4": 4})
    assert is_list_or_dict({"r4": [4]})


def test_clean_nones():
    assert clean_nones([1, None, 3]) == [1, 3]
    assert clean_nones({"A": "str", "B": None}) == {"A": "str"}
    assert clean_nones("str") == "str"
