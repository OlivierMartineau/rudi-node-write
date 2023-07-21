from abc import ABC

from rudi_node_write.rudi_types.rudi_const import (
    LICENCE_TYPE_STANDARD,
    LICENCE_TYPE_CUSTOM,
    LicenceCode,
    check_is_literal,
    LICENCE_CODES,
)
from rudi_node_write.rudi_types.rudi_dictionary_entry import (
    RudiDictionaryEntryList,
)
from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.dict_utils import check_is_dict, check_has_key
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.str_utils import check_is_string
from rudi_node_write.utils.typing_utils import check_is_bool, check_type


class RudiLicence(Serializable, ABC):
    @staticmethod
    def from_json(o: dict):
        check_is_dict(o)
        # log_d('RudiLicence.from_dict', o)
        licence_type = check_has_key(o, "licence_type")
        if licence_type == LICENCE_TYPE_STANDARD:
            return RudiLicenceStandard.from_json(o)
        if licence_type == LICENCE_TYPE_CUSTOM:
            return RudiLicenceCustom.from_json(o)
        raise NotImplementedError(f"cannot create a licence with type '{licence_type}'")


class RudiLicenceStandard(RudiLicence):
    def __init__(self, licence_label: LicenceCode):
        self.licence_label = check_is_literal(licence_label, LICENCE_CODES)
        self.licence_type = LICENCE_TYPE_STANDARD

    @staticmethod
    def from_json(o: dict):
        check_is_dict(o)
        licence_label = check_is_literal(check_has_key(o, "licence_label"), LICENCE_CODES)
        return RudiLicenceStandard(licence_label=licence_label)


class RudiLicenceCustom(RudiLicence):
    def __init__(self, custom_licence_label: RudiDictionaryEntryList, custom_licence_uri: str):
        self.custom_licence_label = check_type(custom_licence_label, RudiDictionaryEntryList)
        self.custom_licence_uri = check_is_string(custom_licence_uri)
        self.licence_type = LICENCE_TYPE_CUSTOM

    @staticmethod
    def from_json(o: dict):
        check_is_dict(o)
        custom_licence_uri = check_is_string(check_has_key(o, "custom_licence_uri"))
        licence_label = check_has_key(o, "custom_licence_label")
        custom_licence_label = RudiDictionaryEntryList.from_json(licence_label)
        return RudiLicenceCustom(
            custom_licence_label=custom_licence_label,
            custom_licence_uri=custom_licence_uri,
        )


class RudiConfidentialityFlags(Serializable):
    def __init__(self, restricted_access: bool = None, gdpr_sensitive: bool = None):
        self.restricted_access = check_is_bool(restricted_access, accept_none=True)
        self.gdpr_sensitive = check_is_bool(gdpr_sensitive, accept_none=True)
        if gdpr_sensitive:
            raise NotImplementedError("Beware, this was not designed for use with GDPR sensitive data")

    @staticmethod
    def from_json(o: dict | None):
        if o is None:
            return RudiConfidentialityFlags()
        check_is_dict(o)
        return RudiConfidentialityFlags(
            restricted_access=o.get("restricted_access"),
            gdpr_sensitive=o.get("gdpr_sensitive"),
        )


class RudiAccessCondition(Serializable):
    def __init__(
        self,
        licence: RudiLicence,
        confidentiality: RudiConfidentialityFlags = None,
        usage_constraint: RudiDictionaryEntryList = None,
        bibliographical_reference: RudiDictionaryEntryList = None,
        mandatory_mention: RudiDictionaryEntryList = None,
        access_constraint: RudiDictionaryEntryList = None,
        other_constraints: RudiDictionaryEntryList = None,
    ):
        self.licence: RudiLicence = check_type(licence, RudiLicence, accept_none=False)
        self.confidentiality = check_type(confidentiality, RudiConfidentialityFlags, accept_none=True)
        self.usage_constraint = check_type(usage_constraint, RudiDictionaryEntryList, accept_none=True)
        self.bibliographical_reference = check_type(
            bibliographical_reference, RudiDictionaryEntryList, accept_none=True
        )
        self.mandatory_mention = check_type(mandatory_mention, RudiDictionaryEntryList, accept_none=True)
        self.access_constraint = check_type(access_constraint, RudiDictionaryEntryList, accept_none=True)
        self.other_constraints = check_type(other_constraints, RudiDictionaryEntryList, accept_none=True)

    @staticmethod
    def from_json(o: dict):
        check_is_dict(o)
        return RudiAccessCondition(
            licence=RudiLicence.from_json(check_has_key(o, "licence")),
            confidentiality=RudiConfidentialityFlags.from_json(o.get("confidentiality")),
            usage_constraint=RudiDictionaryEntryList.from_json(o.get("usage_constraint")),
            bibliographical_reference=RudiDictionaryEntryList.from_json(o.get("bibliographical_reference")),
            mandatory_mention=RudiDictionaryEntryList.from_json(o.get("mandatory_mention")),
            access_constraint=RudiDictionaryEntryList.from_json(o.get("access_constraint")),
            other_constraints=RudiDictionaryEntryList.from_json(o.get("other_constraints")),
        )


if __name__ == "__main__":  # pragma: no cover
    tests = "RudiLicence tests"
    log_d(
        tests,
        RudiLicence.from_json({"licence_type": LICENCE_TYPE_STANDARD, "licence_label": "mit"}),
    )
    log_d(
        tests,
        RudiLicenceStandard.from_json({"licence_type": LICENCE_TYPE_STANDARD, "licence_label": "mit"}),
    )
    log_d(
        tests,
        RudiLicenceCustom.from_json(
            {
                "licence_type": LICENCE_TYPE_CUSTOM,
                "custom_licence_label": "EUPL-1.2",
                "custom_licence_uri": "https://opensource.org/license/eupl-1-2/",
            }
        ),
    )
    log_d(
        tests,
        RudiAccessCondition.from_json(
            {
                "licence": {"licence_type": "STANDARD", "licence_label": "odbl-1.0"},
                "confidentiality": {
                    "restricted_access": False,
                    "gdpr_sensitive": False,
                },
            }
        ),
    )
