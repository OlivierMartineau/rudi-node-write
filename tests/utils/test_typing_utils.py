import pytest

from rudi_node_write.utils.typing_utils import (
    get_type_name,
    is_type,
    check_type,
    to_float,
    is_type_name,
    are_same_type,
    does_inherit_from,
    check_is_bool,
    check_is_int,
    ensure_is_int,
    ensure_is_number,
    to_number,
    check_is_def,
    is_null,
)


def test_get_type_name():
    assert get_type_name({"arg": "val"}) == "dict"


def test_is_type_name():
    assert is_type_name("my_string", "str")
    assert not is_type_name("my_string", "int")


def test_is_type():
    assert is_type({"arg": "val"}, dict)
    assert is_type({"arg": "val"}, (dict, list))
    assert is_type(["e"], list)
    assert is_type("e", str)
    assert is_type(1, int)


def test_are_same_type():
    assert are_same_type("tre", "reouh")
    assert are_same_type(1, 5)
    assert not are_same_type(1, "55")


def test_does_inherit_from():
    assert does_inherit_from(4, int)
    assert does_inherit_from(TypeError(), Exception)


def test_check_is_bool():
    assert check_is_bool(None, accept_none=True) is None
    assert check_is_bool(True)
    assert not check_is_bool(False)
    with pytest.raises(TypeError):
        check_is_bool(None, accept_none=False)
    with pytest.raises(TypeError):
        check_is_bool("str", accept_none=False)


def test_check_type():
    assert check_type(["sr"], list) == ["sr"]
    assert check_type(["sr"], (list, dict)) == ["sr"]
    assert check_type(None, list, accept_none=True) is None
    with pytest.raises(TypeError):
        check_type("str", list)
    with pytest.raises(ValueError, match="input should not be null"):
        check_type(None, str)


def test_check_is_int():
    assert check_is_int(5) == 5
    assert check_is_int("5", accept_castable=True) == 5
    assert check_is_int(None, accept_none=True) is None
    with pytest.raises(TypeError):
        check_is_int("str")
    with pytest.raises(TypeError):
        check_is_int(None)


def test_ensure_is_int():
    assert ensure_is_int(4) == 4
    assert ensure_is_int(None, accept_none=True) is None
    with pytest.raises(TypeError):
        ensure_is_int(None)


def test_ensure_is_number():
    assert ensure_is_number(5) == 5
    assert ensure_is_number("5") == 5
    assert ensure_is_number(5.1) == 5.1
    assert ensure_is_number("5.1") == 5.1
    with pytest.raises(TypeError):
        assert ensure_is_number("str5.1") == 5.1


def test_to_number():
    assert to_number(5) == 5
    assert to_number("5") == 5
    assert to_number(5.1) == 5.1
    assert to_number("5.1") == 5.1
    with pytest.raises(TypeError):
        assert to_number("str5.1") == 5.1


def test_to_float():
    assert to_float("3") == 3.0
    assert to_float("3.0") == 3.0
    with pytest.raises(ValueError):
        to_float("str")
    with pytest.raises(ValueError):
        to_float(["4"])


def test_check_is_def():
    for val in [None, 0, False, [], "", {}]:
        with pytest.raises(ValueError, match="input value is required"):
            check_is_def(val)
    for val in [0, False, 4, "str", ["r"], {"key": "val"}]:
        assert check_is_def(val, strict=True) == val


def check_is_null():
    assert is_null(None)
    assert is_null("None")
    assert is_null("null")
    assert is_null(0)
    assert is_null(False)
    assert is_null([])
    assert is_null({})
    assert is_null("")
    assert not is_null(0, strict=True)
    assert not is_null(False, strict=True)
