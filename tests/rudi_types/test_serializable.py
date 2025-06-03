import unittest
from unittest.mock import patch

import pytest

from rudi_node_write.rudi_types.serializable import Serializable, is_serializable, is_jsonable


def test_is_jsonable():
    assert is_jsonable({"field_1": "a_field"})


class Test_Serializable(unittest.TestCase):
    def test_from_json(self):
        with pytest.raises(NotImplementedError):
            Serializable.from_json({})

    # https://stackoverflow.com/a/28738073/1563072
    @patch.multiple(Serializable, __abstractmethods__=set())
    def test(self):
        self.instance = Serializable()
        self.instance.field_1 = "a_field"
        other = Serializable()
        other.field_1 = "a_field"
        assert not is_jsonable(other)
        assert self.instance.to_json() == {"field_1": "a_field"}
        assert self.instance.to_json_str() == '{"field_1": "a_field"}'
        assert is_serializable(self.instance)
        # assert is_jsonable(self.instance)
        assert self.instance.class_name == "Serializable"
        assert self.instance is not None
        assert self.instance != None
        assert self.instance != "None"
        assert self.instance != 0
        assert self.instance == other
        other.field_1 = "b_field"
        assert self.instance != other
        other.field_1 = "a_field"
        other.field_2 = "b_field"
        assert self.instance != other
        other.field_1 = None
        assert self.instance != other
        assert str(self.instance) == '{"field_1": "a_field"}'
        assert repr(self.instance) == '{"field_1": "a_field"}'

        assert other.to_json_str(keep_nones=True) == '{"field_1": null, "field_2": "b_field"}'

        self.instance.other = other
        self.instance.a_dict = {"2": "str"}
        self.instance.a_list = [1, 2]
        assert (
            self.instance.to_json_str() == '{"field_1": "a_field", "other": {"field_2": "b_field"}, "a_dict": {'
            '"2": "str"}, "a_list": [1, 2]}'
        )

        assert self.instance.to_json() == {
            "field_1": "a_field",
            "other": {"field_2": "b_field"},
            "a_dict": {"2": "str"},
            "a_list": [1, 2],
        }
