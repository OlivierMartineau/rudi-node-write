import pytest

from rudi_node_write.utils.typing_utils import (
    check_is_bool_or_none,
    check_is_int_or_none,
    check_type_or_null,
    ensure_is_int_or_none,
    get_type_name,
    is_def,
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
    assert check_is_bool(True)
    assert not check_is_bool(False)
    with pytest.raises(TypeError):
        check_is_bool(None)  # type: ignore
    with pytest.raises(TypeError):
        check_is_bool("str")  # type: ignore


def test_check_is_bool_or_none():
    assert check_is_bool_or_none(None) is None
    assert check_is_bool_or_none(True)
    assert not check_is_bool_or_none(False)
    with pytest.raises(TypeError):
        check_is_bool_or_none("str")  # type: ignore


def test_check_type():
    assert check_type(["sr"], list) == ["sr"]
    assert check_type(["sr"], (list, dict)) == ["sr"]
    with pytest.raises(ValueError, match="input should not be null"):
        check_type(None, list)
    with pytest.raises(TypeError):
        check_type("str", list)
    with pytest.raises(ValueError, match="input should not be null"):
        check_type(None, str)


def test_check_type_or_null():
    assert check_type_or_null(["sr"], list) == ["sr"]
    assert check_type_or_null(["sr"], (list, dict)) == ["sr"]
    assert check_type_or_null(None, list) is None
    assert check_type_or_null(None, str) is None
    with pytest.raises(TypeError):
        check_type_or_null("str", list)


def test_check_is_int():
    assert check_is_int(5) == 5
    assert check_is_int("5", accept_castable=True) == 5
    with pytest.raises(ValueError):
        check_is_int(None)
    with pytest.raises(TypeError):
        check_is_int("str")


def test_check_is_int_or_none():
    assert check_is_int_or_none(5) == 5
    assert check_is_int_or_none("5", accept_castable=True) == 5
    assert check_is_int_or_none(None) is None
    with pytest.raises(TypeError):
        check_is_int_or_none("str")


def test_ensure_is_int():
    assert ensure_is_int(4) == 4
    assert ensure_is_int("4") == 4
    with pytest.raises(ValueError):
        ensure_is_int(None)
    with pytest.raises(TypeError):
        ensure_is_int("str")
    with pytest.raises(TypeError):
        ensure_is_int("x0x")


def test_ensure_is_int_or_none():
    assert ensure_is_int_or_none(4) == 4
    assert ensure_is_int_or_none("4") == 4
    assert ensure_is_int_or_none(None) is None
    with pytest.raises(TypeError):
        ensure_is_int_or_none("str")


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


def test_is_def():
    assert is_def("l")
    assert not is_def(None)
    assert not is_def(False, strict=False)
    assert not is_def("null", strict=False)
    assert not is_def("None", strict=False)
    assert is_def(0)
    assert is_def("null", strict=True)
    assert is_def("None", strict=True)
    assert is_def(1)


def test_check_is_def():
    for val in [None, "None", "null", 0, False, [], "", {}]:
        with pytest.raises(ValueError, match="input value is required"):
            check_is_def(val)
    for val in [4, "str", ["r"], {"key": "val"}]:
        assert check_is_def(val, strict=True) == val
        assert check_is_def(val) == val
    assert check_is_def(False, strict=True) == False
    assert check_is_def(0, strict=True) == 0


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
