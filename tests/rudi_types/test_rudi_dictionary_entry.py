import pytest

from rudi_node_write.conf.meta_defaults import DEFAULT_LANG
from rudi_node_write.rudi_types.rudi_dictionary_entry import RudiDictionaryEntry, RudiDictionaryEntryList
from rudi_node_write.utils.dict_utils import has_key
from rudi_node_write.utils.err import LiteralUnexpectedValueException


def test_RudiDictionaryEntry_init():
    assert RudiDictionaryEntry("en", "testing")
    with pytest.raises(ValueError):
        RudiDictionaryEntry(None, "testing")
    with pytest.raises(ValueError):
        RudiDictionaryEntry("testing", None)
    with pytest.raises(LiteralUnexpectedValueException):
        RudiDictionaryEntry("testing", "testing")


def test_RudiDictionaryEntry_eq():
    entry_a = RudiDictionaryEntry.from_json({"lang": DEFAULT_LANG, "text": "testing"})
    entry_b = RudiDictionaryEntry.from_json("testing")
    assert entry_a == entry_b


def test_RudiDictionaryEntry_ne():
    entry_a = RudiDictionaryEntry.from_json({"lang": "cs", "text": "testing"})
    entry_b = RudiDictionaryEntry.from_json("testing")
    assert entry_a != entry_b


def test_RudiDictionaryEntry_from_json():
    entry_a = RudiDictionaryEntry.from_json({"lang": "en", "text": "quite something"})
    assert entry_a.lang == "en"
    assert entry_a.text == "quite something"

    entry_b = RudiDictionaryEntry.from_json("quite something")
    assert entry_b.lang == DEFAULT_LANG
    assert entry_b.text == "quite something"


def test_RudiDictionaryEntry_to_json():
    entry = RudiDictionaryEntry("en", "testing")
    entry_json = entry.to_json()
    assert isinstance(entry_json, dict)
    assert has_key(entry_json, "text")
    assert entry_json["lang"] == "en"
    assert entry_json["text"] == "testing"


def test_RudiDictionaryEntryList_init():
    with pytest.raises(ValueError, match="input parameter should be a list"):
        RudiDictionaryEntryList("testing")
    entry_a = RudiDictionaryEntry.from_json({"lang": "en", "text": "quite something"})
    entry_b = RudiDictionaryEntry.from_json("testing")
    rudi_dict_entry_list = RudiDictionaryEntryList([entry_a, entry_b])
    assert rudi_dict_entry_list
    assert rudi_dict_entry_list[0].lang == "en"
    assert rudi_dict_entry_list[0].text == "quite something"


def test_RudiDictionaryEntryList_eq():
    entry_a = RudiDictionaryEntry.from_json({"lang": DEFAULT_LANG, "text": "quite something"})
    entry_b = RudiDictionaryEntry.from_json("testing")
    assert RudiDictionaryEntryList([entry_a, entry_b]) == RudiDictionaryEntryList([entry_b, entry_a])


def test_RudiDictionaryEntryList_to_json():
    entry_a = RudiDictionaryEntry.from_json({"lang": "en", "text": "quite something"})
    entry_b = RudiDictionaryEntry.from_json("testing")
    dict_list = RudiDictionaryEntryList([entry_a, entry_b])
    assert dict_list.to_json() == [{"lang": "en", "text": "quite something"}, {"lang": DEFAULT_LANG, "text": "testing"}]


def test_RudiDictionaryEntryList_ne():
    entry_a = RudiDictionaryEntry.from_json({"lang": DEFAULT_LANG, "text": "quite something"})
    entry_b = RudiDictionaryEntry.from_json("testing")
    assert RudiDictionaryEntryList([entry_a, entry_b]) != [entry_a, entry_b]
    assert RudiDictionaryEntryList([entry_a]) != entry_a
    assert RudiDictionaryEntryList([entry_a]) != None


def test_RudiDictionaryEntryList_to_json_str():
    entry_a = RudiDictionaryEntry.from_json({"lang": "en", "text": "quite something"})
    entry_b = RudiDictionaryEntry.from_json("testing")
    dict_list = RudiDictionaryEntryList([entry_a, entry_b])
    assert (
        dict_list.to_json_str()
        == '[{"lang": "en", "text": "quite something"}, {"lang": "' + DEFAULT_LANG + '", "text": "testing"}]'
    )


def test_RudiDictionaryEntryList_from_json():
    assert RudiDictionaryEntryList.from_json(None) is None
    dict_list_a: RudiDictionaryEntryList = RudiDictionaryEntryList.from_json("quite something")  # type: ignore
    assert dict_list_a[0].text == "quite something"
    dict_list_b: RudiDictionaryEntryList = RudiDictionaryEntryList.from_json({"lang": "en", "text": "quite something"})  # type: ignore
    assert dict_list_b[0].text == "quite something"
    dict_list_c: RudiDictionaryEntryList = RudiDictionaryEntryList.from_json(  # type: ignore
        [{"lang": "en", "text": "testing"}, {"lang": "en", "text": "quite something"}]
    )
    assert dict_list_c[1].text == "quite something"
    dict_list_d: RudiDictionaryEntryList = RudiDictionaryEntryList.from_json(  # type: ignore
        RudiDictionaryEntry.from_json({"lang": "en", "text": "quite something"})
    )
    assert dict_list_d[0].text == "quite something"
    with pytest.raises(TypeError):
        RudiDictionaryEntryList.from_json(2)  # type: ignore
