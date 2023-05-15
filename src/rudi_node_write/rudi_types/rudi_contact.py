from uuid import uuid4, UUID

from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import check_is_dict, check_has_key
from rudi_node_write.utils.type_string import ensure_uuid4, ensure_is_email


class RudiContact(Serializable):
    def __init__(self, contact_id: str | UUID, contact_name: str, email: str, contact_summary: str = None,
                 organization_name: str = None):
        self.contact_id = ensure_uuid4(contact_id)
        self.contact_name = contact_name
        self.email = ensure_is_email(email)
        self.contact_summary = contact_summary
        self.organization_name = organization_name

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)

        # TODO: contact_id -> retrieve the key from the RudiNode
        contact_id = ensure_uuid4(check_has_key(o, 'contact_id'))
        contact_name = check_has_key(o, 'contact_name')
        email = ensure_is_email(o.get('email'))
        contact_summary = o.get('contact_summary')
        organization_name = o.get('organization_name')

        return RudiContact(
            contact_id=contact_id,
            contact_name=contact_name,
            email=email,
            contact_summary=contact_summary,
            organization_name=organization_name)


if __name__ == '__main__':
    a_contact = RudiContact(
        contact_id=uuid4(),
        contact_name='Tintin',
        email='tintin@irisa.fr',
        organization_name='IRISA')
    log_d('RudiContact', 'a_contact', a_contact)
