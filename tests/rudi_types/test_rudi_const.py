import pytest

from rudi_node_write.rudi_types.rudi_const import check_is_literal, check_rudi_version
from rudi_node_write.utils.err import LiteralUnexpectedValueException


def test_check_is_literal():
    assert check_is_literal(val=1, series=(1, 2)) == 1
    assert check_is_literal(val=None, series=(1, 2), accept_none=True) is None
    with pytest.raises(LiteralUnexpectedValueException, match="incorrect value"):
        check_is_literal(val=3, series=(1, 2))


def test_check_rudi_version():
    assert check_rudi_version("1.2.3") == "1.2.3"
    assert check_rudi_version("2.3") == "2.3"
    for version in [3, 3.1, "3", "v3", "v3.2", "str"]:
        with pytest.raises(ValueError):
            check_rudi_version(version)
