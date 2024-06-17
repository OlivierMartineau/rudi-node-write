from rudi_node_write.utils.err import (
    MissingEnvironmentVariableException,
    IniMissingValueException,
    IniUnexpectedValueException,
    UnexpectedValueException,
    LiteralUnexpectedValueException,
    rudi_api_http_error_to_string,
    NoNullException,
    MissingParameterException,
    ExpiredTokenException,
    HttpError,
    HttpErrorNotFound,
)


def test_MissingEnvironmentVariableException():
    err = MissingEnvironmentVariableException("ENV_VAR", "for testing")
    target_err_msg = "an environment variable should be defined for testing: ENV_VAR"
    assert str(err) == target_err_msg
    try:
        raise err
    except MissingEnvironmentVariableException as e:
        assert str(e) == target_err_msg


def test_IniMissingValueException():
    err = IniMissingValueException("SECTION", "SUBSECTION", "testing")
    target_err_msg = "Missing value in INI config file for parameter SECTION.SUBSECTION: testing"
    assert str(err) == target_err_msg
    try:
        raise err
    except IniMissingValueException as e:
        assert str(e) == target_err_msg


def test_IniUnexpectedValueException():
    err = IniUnexpectedValueException("SECTION", "SUBSECTION", "testing")
    target_err_msg = "Unexpected value in INI config file for parameter SECTION.SUBSECTION: testing"
    assert str(err) == target_err_msg
    try:
        raise err
    except IniUnexpectedValueException as e:
        assert str(e) == target_err_msg


def test_NoNullException():
    target_err_msg = "a value is required"
    err = NoNullException(target_err_msg)
    assert str(err) == target_err_msg
    try:
        raise err
    except NoNullException as e:
        assert str(e) == target_err_msg


def test_MissingParameterException():
    target_err_msg = "no value was provided for parameter 'para1'"
    err = MissingParameterException("para1")
    assert str(err) == target_err_msg
    try:
        raise err
    except MissingParameterException as e:
        assert str(e) == target_err_msg


def test_UnexpectedValueException():
    err = UnexpectedValueException("param", "val1", "val2")
    target_err_msg = "Unexpected value for parameter 'param': expected 'val1', got 'val2'"
    assert str(err) == target_err_msg
    try:
        raise err
    except UnexpectedValueException as e:
        assert str(e) == target_err_msg


def test_ULiteralUnexpectedValueException():
    err = LiteralUnexpectedValueException("val", ("valA", "valB"), "Literal value error")
    target_err_msg = "Literal value error. Expected ('valA', 'valB'), got 'val'"
    assert str(err) == target_err_msg
    try:
        raise err
    except LiteralUnexpectedValueException as e:
        assert str(e) == target_err_msg


def test_ExpiredTokenException():
    default_err_msg = "a JWT is required"
    assert str(ExpiredTokenException()) == default_err_msg
    try:
        raise ExpiredTokenException()
    except ExpiredTokenException as e:
        assert str(e) == default_err_msg

    target_err_msg = "JWT has expired: "
    a_jwt = (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9"
        ".eyJleHAiOjYwNDM4MDYsInN1YiI6InJ1ZGlfcHJvZF90b2tlbiIsImNsaWVudF9pZCI6ImFtcGxpc2ltIiwicmVxX210ZCI6ImFsbCIsInJlcV91cmwiOiJhbGwiLCJpYXQiOjE2ODkwOTEwMDIsImp0aSI6ImUzOTE2NGI1LTViNzYtNDNjNy1iNTI3LWU5ODliMjA1MWQyOCJ9.xxxxx"
    )
    assert str(ExpiredTokenException(a_jwt)).startswith(target_err_msg)
    try:
        raise ExpiredTokenException(a_jwt)
    except ExpiredTokenException as e:
        assert str(e).startswith(target_err_msg)


def test_HttpError():
    msg = "An error occurred"
    err_obj = {"status": 404, "error": "Not found", "message": msg}
    assert str(HttpError(msg)) == f"HTTP ERR 500 {msg}"
    print(str(HttpError(err_obj)))
    assert str(HttpError(err_obj)) == ("HTTP ERR 404 Not found: An error occurred")
    assert str(
        HttpError(
            err=err_obj,
            req_method="GET",
            base_url="https://bacasable.fenix.rudi-univ-rennes1.fr",
        )
    ) == (
        "HTTP ERR for request 'GET https://bacasable.fenix.rudi-univ-rennes1.fr' -> {'status': 404, 'error': 'Not found', 'message': 'An error occurred'}"
    )


def test_HttpErrorNotFound():
    msg = "X not found"
    assert str(HttpErrorNotFound(msg)) == f"HTTP ERR 404 Not found: {msg}"


def test_rudi_api_http_error_to_string():
    assert (
        rudi_api_http_error_to_string(444, "TestError", "testing err msg") == "HTTP ERR 444 TestError: testing err msg"
    )
