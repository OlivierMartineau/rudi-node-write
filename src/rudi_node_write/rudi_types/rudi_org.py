from uuid import UUID, uuid4

from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import check_has_key, safe_get_key, check_is_dict
from rudi_node_write.utils.type_string import ensure_uuid4


class RudiOrganization(Serializable):
    def __init__(self, organization_id: str | UUID, organization_name: str, organization_caption: str = None,
                 organization_summary: str = None, organization_address: str = None,
                 organization_coordinates: dict = None):
        self.organization_id = ensure_uuid4(organization_id)
        self.organization_name = organization_name
        self.organization_caption = organization_caption
        self.organization_summary = organization_summary
        self.organization_address = organization_address
        latitude = safe_get_key(organization_coordinates, 'latitude')
        longitude = safe_get_key(organization_coordinates, 'longitude')
        self.organization_coordinates = None if latitude is None and longitude is None else {
            'latitude': latitude, 'longitude': longitude}

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)

        # TODO: organization_id -> retrieve the key from the RudiNode
        organization_id = ensure_uuid4(check_has_key(o, 'organization_id'))
        organization_name = check_has_key(o, 'organization_name')
        organization_caption = o.get('organization_caption')
        organization_summary = o.get('organization_summary')
        organization_address = o.get('organization_address')
        latitude = safe_get_key(o, 'organization_coordinates', 'latitude')
        longitude = safe_get_key(o, 'organization_coordinates', 'longitude')
        organization_coordinates = None if latitude is None and longitude is None else {
            'latitude': latitude, 'longitude': longitude}

        return RudiOrganization(
            organization_id=organization_id,
            organization_name=organization_name,
            organization_caption=organization_caption,
            organization_summary=organization_summary,
            organization_address=organization_address,
            organization_coordinates=organization_coordinates)


if __name__ == '__main__':
    my_org = RudiOrganization(
        organization_id=uuid4(),
        organization_name='IRISA',
        organization_address='263 avenue du Général Leclerc, 35000 RENNES',
        organization_coordinates={'longitude': 1.456, 'latitude': 0})
    log_d('RudiOrganization', 'constructor', RudiOrganization(
        organization_id=uuid4(),
        organization_name='IRISA',
        organization_address='263 avenue du Général Leclerc, 35000 RENNES',
        organization_coordinates={'longitude': 1.456, 'latitude': 0}))
    log_d('RudiOrganization', 'make_producer', RudiOrganization.from_dict(
        {'organization_id': uuid4(),
         'organization_name': 'IRISA',
         'organization_address': '263 avenue du Général Leclerc, 35000 RENNES',
         'organization_coordinates': {'longitude': 1.456, 'latitude': 0}}))
