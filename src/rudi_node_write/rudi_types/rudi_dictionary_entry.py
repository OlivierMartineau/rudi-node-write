from json import dumps

from rudi_node_write.rudi_types.rudi_const import RECOGNIZED_LANGUAGES, Language, DEFAULT_LANG, check_is_accepted
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import is_dict, check_is_dict
from rudi_node_write.utils.type_string import is_string, check_is_string
from rudi_node_write.utils.types import is_list


class RudiDictionaryEntry(Serializable):
    def __init__(self, lang: Language, text: str):
        if lang is None:
            raise ValueError("parameter 'lang' cannot be null.")
        if text is None:
            raise ValueError("parameter 'text' cannot be null.")
        self.lang = check_is_accepted(lang, RECOGNIZED_LANGUAGES, 'parameter is not a recognized language')
        self.text = check_is_string(text)

    @staticmethod
    def from_dict(o: dict | str):
        if is_string(o):
            return RudiDictionaryEntry(lang=DEFAULT_LANG, text=o)
        check_is_dict(o)
        lang = check_is_accepted(o.get('lang'), RECOGNIZED_LANGUAGES, 'parameter is not a recognized language')
        text = check_is_string(o.get('text'))
        return RudiDictionaryEntry(lang=lang, text=text)


class RudiDictionaryEntryList(Serializable):
    def __init__(self, list_entries: list[RudiDictionaryEntry]):
        if not is_list(list_entries):
            raise ValueError('input parameter should be a list')
        self._list_entries = [{'lang': entry.lang, 'text': entry.text} for entry in list_entries]

    def to_json_str(self, should_keep_nones: bool = False, should_ensure_ascii: bool = False) -> str:
        return dumps(self._list_entries)

    def to_json_dict(self, should_keep_nones: bool = False) -> list:
        """
        Transform the object into a Python object
        :return: a Python object
        """
        return self._list_entries

    @staticmethod
    def from_dict(o: list | dict | str):
        if is_string(o):
            entry = RudiDictionaryEntry(DEFAULT_LANG, o)
            return RudiDictionaryEntryList([entry])
        if is_dict(o):
            entry = RudiDictionaryEntry.from_dict(o)
            return RudiDictionaryEntryList([entry])
        if not is_list(o):
            raise TypeError('input parameter should be a list')

        list_entries = []
        for obj in o:
            list_entries.append(RudiDictionaryEntry.from_dict(obj))
        return RudiDictionaryEntryList(list_entries)


if __name__ == '__main__':
    fun = 'RudiDictionaryEntry tests'
    log_d(fun, RudiDictionaryEntry('en', 'quite something'))
    log_d(fun, RudiDictionaryEntry.from_dict('quite something'))
    log_d(fun, RudiDictionaryEntryList.from_dict('quite something'))
