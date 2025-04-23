from re import escape

import pytest

from rudi_node_write.utils.str_utils import (
    check_is_email,
    check_is_string_or_none,
    check_is_string,
    check_is_uuid4,
    ensure_startswith,
    is_email,
    is_string,
    is_uuid_v4,
    REGEX_UUID,
    slash_join,
    uuid4_str,
)


def test_is_string():
    assert is_string("e")
    assert not is_string(None)
    assert not is_string(["e"])


def test_check_is_string():
    assert check_is_string("e") == "e"
    with pytest.raises(TypeError):
        assert not check_is_string(None)  # type: ignore
    with pytest.raises(TypeError):
        assert not check_is_string(["e"])  # type: ignore


def test_is_string_or_none():
    assert check_is_string_or_none("e") == "e"
    assert check_is_string_or_none(None) is None
    with pytest.raises(TypeError):
        assert not check_is_string_or_none(["e"])  # type: ignore


def test_is_email():
    assert is_email("e@test.org")
    assert not is_email("e@test")
    assert not is_email("e.test.org")
    assert not is_email("e(a)test.org")


def test_check_is_email():
    assert check_is_email("e@test.org") == "e@test.org"
    with pytest.raises(ValueError, match="a valid email should be provided"):
        assert not check_is_email(None)  # type: ignore
    for email in ["e@test", "e.test.org", "e(a)test.org"]:
        with pytest.raises(ValueError, match=escape(f"this is not a valid email: '{email}'")):
            assert not check_is_email(email)


def test_uuid4_str():
    assert REGEX_UUID.match(uuid4_str())


def test_is_uuid_v4():
    assert not is_uuid_v4(None)
    assert not is_uuid_v4("")
    assert not is_uuid_v4([])
    assert not is_uuid_v4("1")
    assert not is_uuid_v4("1d8b8d5d5-82d4-4a93-96e8-451daa124a70")
    assert not is_uuid_v4("d8b8d5d5-82d4-1a93-96e8-451daa124a70")
    assert bool(is_uuid_v4("d8b8d5d5-82d4-4a93-96e8-451daa124a70"))


def test_check_is_uuid4():
    with pytest.raises(ValueError):
        check_is_uuid4(None)
    with pytest.raises(ValueError):
        check_is_uuid4([])
    with pytest.raises(ValueError):
        check_is_uuid4("")
    with pytest.raises(ValueError):
        check_is_uuid4("1")
    assert check_is_uuid4("d8b8d5d5-82d4-4a93-96e8-451daa124a70") == "d8b8d5d5-82d4-4a93-96e8-451daa124a70"


def test_slash_join():
    assert slash_join("a", "b", "4") == "a/b/4"
    assert slash_join("a/", "/b", "/4/") == "a/b/4"
    assert slash_join("/a//", "////b", "/4/") == "a/b/4"
    assert slash_join("http://a//", "////b", "/4/") == "http://a/b/4"
    assert slash_join("/", "////b", "/4/") == "/b/4"
    with pytest.raises(AttributeError):
        slash_join("a", "b", 4)


def test_ensure_startswith():
    assert ensure_startswith("test_str", "test") == "test_str"
    assert ensure_startswith("tested_str", "test_str", "added_") == "added_tested_str"
    assert ensure_startswith("test.org", "http", transform=lambda x: slash_join("http:", "/", x)) == "http://test.org"
