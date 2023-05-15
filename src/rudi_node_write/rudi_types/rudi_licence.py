from abc import ABC

from rudi_node_write.rudi_types.rudi_const import LICENCE_TYPE_STANDARD, LICENCE_TYPE_CUSTOM, LicenceCode, \
    check_is_accepted, LICENCE_CODES
from rudi_node_write.rudi_types.rudi_dictionary_entry import RudiDictionaryEntry
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import check_is_dict, check_has_key
from rudi_node_write.utils.type_string import check_is_string, is_string
from rudi_node_write.utils.types import check_type


class RudiLicence(Serializable, ABC):

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)
        log_d('RudiLicence.from_dict', o)
        licence_type = check_has_key(o, 'licence_type')
        if licence_type == LICENCE_TYPE_STANDARD:
            return RudiLicenceStandard.from_dict(o)
        if licence_type == LICENCE_TYPE_CUSTOM:
            return RudiLicenceCustom.from_dict(o)
        raise NotImplementedError(f"cannot create a licence with type '{licence_type}'")


class RudiLicenceStandard(RudiLicence):
    def __init__(self, licence_label: LicenceCode):
        self.licence_label = check_is_accepted(licence_label, LICENCE_CODES)
        self.licence_type = LICENCE_TYPE_STANDARD

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)
        licence_label = check_is_accepted(check_has_key(o, 'licence_label'), LICENCE_CODES)
        return RudiLicenceStandard(licence_label=licence_label)


class RudiLicenceCustom(RudiLicence):
    def __init__(self, custom_licence_label: RudiDictionaryEntry | str, custom_licence_uri: str):
        if is_string(custom_licence_label):
            self.custom_licence_label = RudiDictionaryEntry.from_dict(custom_licence_label)
        else:
            self.custom_licence_label = check_type(custom_licence_label, 'RudiDictionaryEntry')
        self.custom_licence_uri = check_is_string(custom_licence_uri)
        self.licence_type = LICENCE_TYPE_CUSTOM

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)
        licence_label = check_has_key(o, 'custom_licence_label')
        if is_string(licence_label):
            custom_licence_label = RudiDictionaryEntry.from_dict(licence_label)
        else:
            custom_licence_label = check_type(licence_label, 'RudiDictionaryEntry')
        custom_licence_uri = check_is_string(check_has_key(o, 'custom_licence_uri'))
        return RudiLicenceCustom(custom_licence_label=custom_licence_label, custom_licence_uri=custom_licence_uri)


if __name__ == '__main__':
    fun = 'RudiLicence'
    log_d(fun, RudiLicence.from_dict({'licence_type': LICENCE_TYPE_STANDARD, 'licence_label': 'mit'}))
    log_d(fun, RudiLicenceStandard.from_dict({'licence_type': LICENCE_TYPE_STANDARD, 'licence_label': 'mit'}))
    log_d(fun, RudiLicenceCustom.from_dict({'licence_type': LICENCE_TYPE_CUSTOM, 'custom_licence_label': 'EUPL-1.2',
                                            'custom_licence_uri': 'https://opensource.org/license/eupl-1-2/'}))
