from json import dumps

from rudi_node_write.rudi_types.rudi_org import RudiOrganization

TEST_ORG = {
    "organization_id": "6f663470-f042-49bd-8426-e766bd3793cf",
    "organization_name": "IRISA",
    "organization_address": "263 avenue du Général Leclerc, 35000 RENNES",
    "organization_coordinates": {"latitude": 0, "longitude": 1.456},
}


def test_RudiOrganization_from_json():
    test_org = RudiOrganization.from_json(TEST_ORG)
    assert test_org.organization_name == "IRISA"
    assert test_org.to_json_str(sort_keys=True, ensure_ascii=False) == dumps(
        TEST_ORG, sort_keys=True, ensure_ascii=False
    )
