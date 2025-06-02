from rudi_node_write.utils.jwt import is_base64_url, is_jwt_expired, is_jwt_valid, pad_b64_str, get_basic_auth


def test_is_base64_url():
    assert not is_base64_url("/")
    assert is_base64_url("aaaa")
    assert is_base64_url(bytes("1001", "ascii"))
    assert is_base64_url("d2Vlay1lbmQgaGFzIGZpbmFsbHkgYXJyaXZlZA==")
    assert not is_base64_url("d2Vlay1lbmQgaGFzIGZpbmFsbHkgYXJyaXZlZA")
    long_string = "dGhpcyBpcyBhIHJlYXNvbmFibHkgbG9uZyBVUkwtc2FmZSBiYXNlIDY0IGVuY29kZWQgc3RyaW5n"
    assert is_base64_url(long_string)
    assert not is_base64_url({"testing": "dict"})


def test_pad_b64_str():
    assert pad_b64_str("") == ""
    assert pad_b64_str("e") == "e==="
    assert pad_b64_str("ee") == "ee=="
    assert pad_b64_str("eee") == "eee="
    assert pad_b64_str("eeee") == "eeee"
    assert pad_b64_str("eeeee") == "eeeee==="


def test_get_jwt_basic_auth():
    assert get_basic_auth("usér", "pwÆéd") == "Basic dXPDqXI6cHfDhsOpZA=="


def test_is_jwt_expired():
    assert is_jwt_expired("eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJleHAiOjE2ODE5OTMzMjV9Cg.lZV3hzSWl3aWNtVnhYM1kNJNklt")
    assert not is_jwt_expired("eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJleHAiOjMzMjM4OTAxNjg5fQo.lZV3hzSWl3aWNtVM1Z5YkN")
    assert is_jwt_expired(None)
    assert is_jwt_expired("")
    assert is_jwt_expired("not_a_jwt")


def test_is_jwt_valid():
    assert is_jwt_valid("eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJleHAiOjMzMjM4OTAxNjg5fQo.lZV3hzSWl3aWNtVM1Z5YkN")

    assert not is_jwt_valid("eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJleHAiOjE2ODE5OTMzMjV9Cg.lZV3hzSWl3aWNtVnhYM1kNJNk")
    assert not is_jwt_valid(
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJleHAiOjE2ODE5OTMzMjV9Cg.lZV3hzSWl3aWNtVnhYM1kNJNklt"
    )
    assert not is_jwt_valid(None)
    assert not is_jwt_valid("")
    assert not is_jwt_valid("not_a_jwt")
