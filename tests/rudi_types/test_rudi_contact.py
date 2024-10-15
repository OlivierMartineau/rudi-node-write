from rudi_node_write.rudi_types.rudi_contact import RudiContact


def test_RudiContact_from_json():
    RudiContact.from_json(
        {
            "contact_id": "cf70d5cd-c8cc-43a0-9d4f-71241b0349d4",
            "contact_name": "Test contact",
            "email": "contact@irisa.fr",
            "organization_name": "IRISA",
        }
    )
