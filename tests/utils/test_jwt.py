from rudi_node_write.utils.jwt import is_jwt_expired, pad_b64_str, get_jwt_basic_auth


def test_pad_b64_str():
    assert pad_b64_str("") == ""
    assert pad_b64_str("e") == "e==="
    assert pad_b64_str("ee") == "ee=="
    assert pad_b64_str("eee") == "eee="
    assert pad_b64_str("eeee") == "eeee"
    assert pad_b64_str("eeeee") == "eeeee==="


def test_get_jwt_basic_auth():
    assert get_jwt_basic_auth("usér", "pwÆéd") == "Basic dXPDqXI6cHfDhsOpZA=="


def test_is_jwt_expired():
    assert is_jwt_expired("eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJleHAiOjE2ODE5OTMzMjV9Cg.lZV3hzSWl3aWNtVnhYM1kNJNklt")
    assert not is_jwt_expired("eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJleHAiOjMzMjM4OTAxNjg5fQo.lZV3hzSWl3aWNtVM1Z5YkN")
    assert is_jwt_expired(None)
    assert is_jwt_expired("")
    assert is_jwt_expired("not_a_jwt")
