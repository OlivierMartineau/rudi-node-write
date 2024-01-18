from json import dumps

from rudi_node_write.conf.meta_defaults import DEFAULT_LANG
from rudi_node_write.rudi_types.rudi_const import (
    RECOGNIZED_LANGUAGES,
    Language,
    check_is_literal,
)
from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.dict_utils import check_is_dict, check_has_key
from rudi_node_write.utils.list_utils import is_list, are_list_equal
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.str_utils import check_is_string
from rudi_node_write.utils.typing_utils import get_type_name


class RudiDictionaryEntry(Serializable):
    def __init__(self, lang: Language, text: str):
        if lang is None:
            raise ValueError("parameter 'lang' cannot be null.")
        if text is None:
            raise ValueError("parameter 'text' cannot be null.")
        self.lang = check_is_literal(lang, RECOGNIZED_LANGUAGES, "parameter is not a recognized language")
        self.text = check_is_string(text)

    @staticmethod
    def from_json(o: dict | str):
        if isinstance(o, str):
            return RudiDictionaryEntry(lang=DEFAULT_LANG, text=o)
        check_is_dict(o)
        lang = check_is_literal(
            check_has_key(o, "lang"),
            RECOGNIZED_LANGUAGES,
            "parameter is not a recognized language",
        )
        text = check_is_string(check_has_key(o, "text"))
        return RudiDictionaryEntry(lang=lang, text=text)


class RudiDictionaryEntryList(Serializable, list):
    def __init__(self, list_entries: list[RudiDictionaryEntry]):
        if not is_list(list_entries):
            raise ValueError("input parameter should be a list")
        super().__init__()
        for entry in list_entries:
            self.append(RudiDictionaryEntry(lang=entry.lang, text=entry.text))

    def __eq__(self, other=None):
        here = f"{self.class_name}.eq"
        if other is None:
            log_d(here, f"Target is null. {self} ≠ {other}")
            return False
        if not isinstance(other, RudiDictionaryEntryList):
            log_d(here, f"Type '{get_type_name(other)}' is not a RudiDictionaryEntryList. {self} ≠ {other}")
            return False
        return are_list_equal(self, other, ignore_order=True)

    def to_json_str(self, **kwargs) -> str:
        return dumps([entry.to_json() for entry in self])

    def to_json(self, keep_nones: bool = False) -> list:
        """
        Transform the object into a Python object
        :return: a Python object
        """
        return [entry.to_json() for entry in self]

    @staticmethod
    def from_json(o: list | dict | str | RudiDictionaryEntry | None):
        if o is None:
            return None
        if isinstance(o, str):
            return RudiDictionaryEntryList([RudiDictionaryEntry(lang=DEFAULT_LANG, text=o)])
        if isinstance(o, dict):
            return RudiDictionaryEntryList([RudiDictionaryEntry.from_json(o)])
        if isinstance(o, RudiDictionaryEntry):
            return RudiDictionaryEntryList([o])
        if not isinstance(o, list):
            raise TypeError("input parameter should be a list")

        return RudiDictionaryEntryList([RudiDictionaryEntry.from_json(entry) for entry in o])


if __name__ == "__main__":  # pragma: no cover
    tests = "RudiDictionaryEntry tests"
    log_d(tests, dico := RudiDictionaryEntry("en", "quite something"))
    log_d(tests, dico.to_json())
    log_d(tests, dico := RudiDictionaryEntry.from_json("quite something"))
    log_d(tests, dico.to_json())
    log_d(tests, dico_list := RudiDictionaryEntryList.from_json("quite something"))
    log_d(tests, dico_list.to_json())
