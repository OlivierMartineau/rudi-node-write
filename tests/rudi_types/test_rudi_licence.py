import pytest

from rudi_node_write.rudi_types.rudi_licence import RudiLicence, RudiConfidentialityFlags, RudiAccessCondition

STD_LICENCE = {"licence_label": "mit", "licence_type": "STANDARD"}
CST_LICENCE = {
    "custom_licence_label": {"lang": "fr", "text": "EUPL-1.2"},
    "custom_licence_uri": "https://opensource.org/license/eupl-1-2/",
    "licence_type": "CUSTOM",
}
NOT_LICENCE = {
    "custom_licence_label": {"lang": "fr", "text": "EUPL-1.2"},
    "custom_licence_uri": "https://opensource.org/license/eupl-1-2/",
    "licence_type": "NOT",
}


def test_RudiLicence_from_json():
    assert RudiLicence.from_json(STD_LICENCE)
    assert RudiLicence.from_json(CST_LICENCE)
    with pytest.raises(NotImplementedError):
        RudiLicence.from_json(NOT_LICENCE)


def test_RudiConfidentialityFlags_init():
    for flag in [None, False]:
        assert RudiConfidentialityFlags(flag)
        assert not RudiConfidentialityFlags(flag).restricted_access
        assert not RudiConfidentialityFlags(flag).gdpr_sensitive

    assert RudiConfidentialityFlags()
    assert not RudiConfidentialityFlags().restricted_access
    assert not RudiConfidentialityFlags().gdpr_sensitive

    assert RudiConfidentialityFlags(True)
    assert RudiConfidentialityFlags(True).restricted_access
    assert not RudiConfidentialityFlags().gdpr_sensitive

    assert RudiConfidentialityFlags(restricted_access=True, gdpr_sensitive=False)
    assert RudiConfidentialityFlags(restricted_access=True, gdpr_sensitive=False).restricted_access
    assert not RudiConfidentialityFlags(restricted_access=True, gdpr_sensitive=False).gdpr_sensitive

    assert RudiConfidentialityFlags(gdpr_sensitive=False)
    assert not RudiConfidentialityFlags(gdpr_sensitive=False).restricted_access
    assert not RudiConfidentialityFlags(gdpr_sensitive=False).gdpr_sensitive

    with pytest.raises(NotImplementedError):
        RudiConfidentialityFlags(gdpr_sensitive=True)
    with pytest.raises(TypeError):
        RudiConfidentialityFlags(restricted_access="area 51")  # type: ignore
    with pytest.raises(TypeError):
        RudiConfidentialityFlags(0)  # type: ignore


def test_RudiConfidentialityFlags_from_json():
    assert RudiConfidentialityFlags.from_json(None)
    assert RudiConfidentialityFlags.from_json({})
    assert RudiConfidentialityFlags.from_json({"restricted_access": False})
    assert RudiConfidentialityFlags.from_json({"restricted_access": True})
    assert RudiConfidentialityFlags.from_json({"restricted_access": True, "gdpr_sensitive": False})
    assert RudiConfidentialityFlags.from_json({"gdpr_sensitive": False})
    with pytest.raises(NotImplementedError):
        RudiConfidentialityFlags.from_json({"gdpr_sensitive": True})
    with pytest.raises(TypeError):
        RudiConfidentialityFlags.from_json("Area 51")  # type: ignore


def test_RudiAccessCondition():
    assert RudiAccessCondition.from_json({"licence": {"licence_label": "mit", "licence_type": "STANDARD"}})
    assert RudiAccessCondition.from_json(
        {
            "licence": {"licence_type": "STANDARD", "licence_label": "odbl-1.0"},
            "confidentiality": {"restricted_access": False},
        }
    )
