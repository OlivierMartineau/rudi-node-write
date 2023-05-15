from uuid import uuid4, UUID

from rudi_node_write.rudi_types.rudi_const import RUDI_API_VERSION, StorageStatus, Language, check_rudi_version, \
    check_is_accepted, RECOGNIZED_LANGUAGES, STORAGE_STATUSES
from rudi_node_write.rudi_types.rudi_contact import RudiContact
from rudi_node_write.rudi_types.rudi_dates import RudiDates
from rudi_node_write.rudi_types.rudi_dictionary_entry import RudiDictionaryEntryList
from rudi_node_write.rudi_types.rudi_geometry import BoundingBox
from rudi_node_write.rudi_types.rudi_licence import RudiLicence
from rudi_node_write.rudi_types.rudi_media import RudiMedia
from rudi_node_write.rudi_types.rudi_org import RudiOrganization
from rudi_node_write.utils.date import ensure_date_str
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import check_is_dict, is_dict, check_has_key, safe_get_key
from rudi_node_write.utils.type_string import ensure_uuid4, check_is_string, is_string
from rudi_node_write.utils.types import is_list, get_type_name, check_type, is_type, check_is_bool, check_is_int


class RudiMetadataInfo(Serializable):
    def __init__(self, api_version: str, metadata_dates: RudiDates = None, metadata_provider: RudiOrganization = None,
                 metadata_contacts: list[RudiContact] = None):
        self.api_version = check_rudi_version(api_version)
        self.metadata_dates = metadata_dates
        self.metadata_provider = metadata_provider
        self.metadata_contacts = metadata_contacts

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)
        api_version = check_rudi_version(o.get('api_version'))
        metadata_dates = RudiDates.from_dict(o.get('metadata_dates'))
        provider = o.get('metadata_provider')
        metadata_provider = RudiOrganization.from_dict(provider) if provider else None
        contacts = o.get('metadata_contacts')
        log_d('RudiMetadataInfo.from_dict', 'metadata_contacts', contacts)
        if contacts is None:
            metadata_contacts = None
        elif is_dict(contacts):
            metadata_contacts = [RudiContact.from_dict(contacts)]
        elif is_list(contacts):
            metadata_contacts = [RudiContact.from_dict(contact) for contact in contacts]
        else:
            raise TypeError(
                f"incorrect object type for 'metadata_contacts'. Expected '{list[dict]}', "
                f"got '{get_type_name(contacts)}'")
        return RudiMetadataInfo(api_version=api_version, metadata_dates=metadata_dates,
                                metadata_provider=metadata_provider,
                                metadata_contacts=metadata_contacts)


class RudiMetadata(Serializable):
    def __init__(self, global_id: str | UUID, resource_title: str, synopsis: RudiDictionaryEntryList,
                 summary: RudiDictionaryEntryList, theme: str,
                 keywords: str | list[str], producer: RudiOrganization, contacts: list[RudiContact],
                 available_formats: list[RudiMedia], dataset_dates: RudiDates, storage_status: StorageStatus,
                 licence: RudiLicence, metadata_info: RudiMetadataInfo, local_id: str = None, doi: str = None,
                 resource_languages: list[Language] = None, dataset_start_date: str = None,
                 dataset_end_date: str = None, dataset_bounding_box: BoundingBox = None, dataset_geojson: dict = None,
                 dataset_projection: str = None, numbers_of_records: int = None, numbers_of_fields: int = None,
                 restricted_access: bool = False, gdpr_sensitive: bool = False, access_condition: dict = None,
                 collection_tag: str = None, metadata_source: str = None):

        # ---------- Mandatory parameters ----------
        self.global_id = ensure_uuid4(global_id)

        self.resource_title = check_is_string(resource_title)

        self.synopsis = check_type(synopsis, 'RudiDictionaryEntryList')
        self.summary = check_type(summary, 'RudiDictionaryEntryList')

        self.theme = check_is_string(theme)
        if is_string(keywords):
            kw_list = keywords.split(',')
        elif is_list(keywords):
            kw_list = keywords
        else:
            raise TypeError(f"keywords parameter should be a list of keywords, got type '{get_type_name(keywords)}'")

        self.keywords = [kw.strip() for kw in kw_list]

        self.producer = check_type(producer, 'RudiOrganization')
        self.contacts = [check_type(contact, 'RudiContact') for contact in contacts]

        self.available_formats = [check_type(media, ['RudiMediaFile', 'RudiMediaService']) for media in
                                  available_formats]
        self.dataset_dates = check_type(dataset_dates, 'RudiDates')

        if not is_type(licence, 'RudiLicenceStandard') and not is_type(licence, 'RudiLicenceCustom'):
            raise TypeError(f"licence parameter should be a RudiLicence, got '{get_type_name(licence)}'")
        self.access_condition = {'licence': licence}

        self.metadata_info = check_type(metadata_info, 'RudiMetadataInfo')

        # ---------- Optional parameters ----------
        self.local_id = None if local_id is None else check_is_string(local_id)
        self.doi = None if doi is None else check_is_string(doi)

        self.resource_languages = None if resource_languages is None else [
            check_is_accepted(lang, RECOGNIZED_LANGUAGES) for lang in resource_languages]

        if dataset_start_date:
            self.temporal_spread = {'start_date': ensure_date_str(dataset_start_date)}
            if dataset_end_date:
                self.temporal_spread['end_date'] = ensure_date_str(dataset_end_date)
        if dataset_bounding_box:
            self.geography = {'bounding_box': check_type(dataset_bounding_box, 'BoundingBox')}
            if dataset_geojson:
                self.geography['geographic_distribution'] = dataset_geojson
            if dataset_projection:
                self.geography['projection'] = dataset_projection
        if numbers_of_records:
            self.dataset_size = {'numbers_of_records': numbers_of_records}
        if numbers_of_fields:
            if numbers_of_records:
                self.dataset_size['numbers_of_fields'] = numbers_of_fields
            else:
                self.dataset_size = {'numbers_of_fields': numbers_of_fields}

        self.storage_status = check_is_accepted(storage_status, STORAGE_STATUSES)

        if restricted_access:
            self.access_condition['confidentiality'] = {'restricted_access', check_is_bool(restricted_access)}
            if gdpr_sensitive:
                # self.gdpr_sensitive =check_is_bool(gdpr_sensitive)
                raise NotImplementedError('No GDPR sensitive values are accepted on a RUDI node!!!')

        for constraint_label in ['usage_constraint', 'bibliographical_reference', 'mandatory_mention',
                                 'access_constraint', 'other_constraints']:
            constraint = access_condition.get(constraint_label)
            if constraint:
                # noinspection PyTypeChecker
                self.access_condition['confidentiality'][constraint_label] = RudiDictionaryEntryList.from_dict(
                    constraint)

        for constraint_label in ['usage_constraint', 'bibliographical_reference', 'mandatory_mention',
                                 'access_constraint', 'other_constraints']:
            constraint = access_condition.get(constraint_label)
            if constraint:
                # noinspection PyTypeChecker
                self.access_condition[constraint_label] = RudiDictionaryEntryList.from_dict(constraint)

        self.collection_tag = None if collection_tag is None else check_is_string(collection_tag)
        self.metadata_source = None if metadata_source is None else check_is_string(metadata_source)

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)

        # Mandatory attributes
        global_id = ensure_uuid4(check_has_key(o, 'global_id'))
        resource_title = check_is_string(check_has_key(o, 'resource_title'))

        synopsis = RudiDictionaryEntryList.from_dict(check_has_key(o, 'synopsis'))
        summary = RudiDictionaryEntryList.from_dict(check_has_key(o, 'summary'))

        theme = check_is_string(check_has_key(o, 'theme'))
        kw = check_has_key(o, 'keywords')
        if is_string(kw):
            kw_list = kw.split(',')
        elif is_list(kw):
            kw_list = kw
        else:
            raise TypeError(f"keywords parameter should be a list of keywords, got type '{get_type_name(kw)}'")

        keywords = [kw.strip() for kw in kw_list]

        producer = RudiOrganization.from_dict(check_has_key(o, 'producer'))
        contact_list = check_has_key(o, 'contacts')
        if is_list(contact_list):
            contacts = [RudiContact.from_dict(contact) for contact in contact_list]
        elif is_dict(contact_list):
            contacts = [RudiContact.from_dict(contact_list)]
        else:
            raise TypeError(f"incorrect type for contacts attribute, expected 'list', got "
                            f"'{get_type_name(contact_list)}'")

        available_formats = [RudiMedia.from_dict(media) for media in check_has_key(o, 'available_formats')]
        dataset_dates = RudiDates.from_dict(check_has_key(o, 'dataset_dates'))
        storage_status = check_is_accepted(check_has_key(o, 'storage_status'), STORAGE_STATUSES)
        licence = safe_get_key(o, 'access_condition', 'licence')
        if licence is None:
            raise ValueError(f"attribute 'access_condition.licence' is missing")
        licence = RudiLicence.from_dict(licence)
        access_condition = {'licence': licence}

        metadata_info = RudiMetadataInfo.from_dict(check_has_key(o, 'metadata_info'))

        # ---------- Optional parameters ----------
        local_id = o.get('local_id')
        doi = o.get('doi')
        languages = o.get('resource_languages')
        resource_languages = None if not languages else [
            check_is_accepted(lang, RECOGNIZED_LANGUAGES) for lang in languages]

        dataset_start_date = safe_get_key(o, 'temporal_spread', 'start_date')
        dataset_end_date = safe_get_key(o, 'temporal_spread', 'end_date') if dataset_start_date is not None else None

        dataset_geography = o.get('geography')
        dataset_bounding_box = BoundingBox.from_dict(check_has_key(dataset_geography, 'bounding_box')) if \
            dataset_geography else None
        dataset_geojson = dataset_geography.get('geographic_distribution')
        dataset_projection = dataset_geography.get('projection')

        numbers_of_records = safe_get_key(o, 'numbers_of_records')
        if numbers_of_records is not None:
            check_is_int(numbers_of_records)
        numbers_of_fields = safe_get_key(o, 'numbers_of_fields')
        if numbers_of_fields is not None:
            check_is_int(numbers_of_fields)

        restricted_access = safe_get_key(access_condition, 'confidentiality', 'restricted_access')
        gdpr_sensitive = safe_get_key(access_condition, 'confidentiality', 'gdpr_sensitive')
        if restricted_access:
            check_is_bool(restricted_access)
        if gdpr_sensitive:
            check_is_bool(gdpr_sensitive)
            raise NotImplementedError('No GDPR sensitive values are accepted on a RUDI node!!!')

        for constraint_label in ['usage_constraint', 'bibliographical_reference', 'mandatory_mention',
                                 'access_constraint', 'other_constraints']:
            constraint = access_condition.get(constraint_label)
            if constraint:
                # noinspection PyTypeChecker
                access_condition[constraint_label] = RudiDictionaryEntryList.from_dict(constraint)

        tag = o.get('collection_tag')
        collection_tag = None if tag is None else check_is_string(tag)

        return RudiMetadata(global_id=global_id, resource_title=resource_title, synopsis=synopsis, summary=summary,
                            theme=theme, keywords=keywords, producer=producer, contacts=contacts,
                            available_formats=available_formats, dataset_dates=dataset_dates,
                            storage_status=storage_status, licence=licence, metadata_info=metadata_info,
                            local_id=local_id, doi=doi, resource_languages=resource_languages,
                            dataset_start_date=dataset_start_date, dataset_end_date=dataset_end_date,
                            dataset_bounding_box=dataset_bounding_box, dataset_geojson=dataset_geojson,
                            dataset_projection=dataset_projection, numbers_of_records=numbers_of_records,
                            numbers_of_fields=numbers_of_fields, restricted_access=restricted_access,
                            gdpr_sensitive=gdpr_sensitive, access_condition=access_condition,
                            collection_tag=collection_tag)


if __name__ == '__main__':
    fun = 'RudiMetadataInfo tests'
    my_org = RudiOrganization(organization_id=uuid4(), organization_name='IRISA',
                              organization_address='263 avenue du Général Leclerc, 35000 RENNES')
    my_contact = RudiContact(contact_id=uuid4(), contact_name='Jean-Patrick Contactest',
                             email='jean-patrick@contact.test', contact_summary='I ♥ oranges')
    log_d(fun, 'my_contact', my_contact)
    meta_info_json = {
        "api_version": "1.3.0",
        "metadata_dates": {"created": "2023-05-12T16:40:39+02:00", "updated": "2023-05-12T16:40:39+02:00"},
        "metadata_contacts": [
            {"contact_id": "fc6975e8-4fa8-4b20-895a-b9a585498c45", "contact_name": "Jean-Patrick Contactest",
             "email": "jean-patrick@contact.test", "contact_summary": "I ♥ oranges"}],
        "metadata_provider": {"organization_id": "c99d6875-f2e5-4fca-af9c-68b7314be905",
                              "organization_name": "IRISA",
                              "organization_address": "263 avenue du Général Leclerc, 35000 RENNES"}}
    log_d(fun, 'meta_info_json', meta_info_json)
    log_d(fun, 'info_json', RudiMetadataInfo.from_dict(meta_info_json))
    meta_info = RudiMetadataInfo(RUDI_API_VERSION, RudiDates(), metadata_provider=my_org,
                                 metadata_contacts=[my_contact])
    log_d(fun, 'meta_info', meta_info)

    fun = 'RudiMetadata tests'
    meta = meta = {"temporal_spread": {"start_date": "2022-11-07T06:55:11.000Z"}, "geography": {
        "bounding_box": {"west_longitude": -1.677803, "east_longitude": 1.677803, "south_latitude": -48.112834,
                         "north_latitude": 48.112834}, "geographic_distribution": {"type": "Polygon",
                                                                                   "coordinates": [
                                                                                       [[-1.677803, -48.112834],
                                                                                        [1.677803, -48.112834],
                                                                                        [1.677803, 48.112834],
                                                                                        [-1.677803, 48.112834],
                                                                                        [-1.677803, -48.112834]]],
                                                                                   "bbox": [-1.677803, -48.112834,
                                                                                            1.677803, 48.112834]},
        "projection": "WGS 84 (EPSG:4326)"},
                   "dataset_dates": {"created": "2023-04-12T02:00:38.000Z", "published": "2023-04-12T09:39:28.562Z",
                                     "updated": "2023-04-12T02:00:38.000Z"},
                   "access_condition": {"licence": {"licence_type": "STANDARD", "licence_label": "etalab-1.0"},
                                        "confidentiality": {"restricted_access": False, "gdpr_sensitive": False}},
                   "metadata_info": {"api_version": "1.3.2", "metadata_provider": {
                       "organization_id": "44f5ac9d-34d6-44d0-99a9-0496654bde5c",
                       "organization_name": "Breitenberg - Legros",
                       "organization_address": "425 Hickle Crest, Duluth", "collection_tag": "rudi-seed"},
                                     "metadata_contacts": [{"contact_id": "f275bed9-6b62-43f1-b617-a392896a617c",
                                                            "contact_name": "Sherri Dickinson",
                                                            "email": "sherri.dickinson@irisa.fr",
                                                            "collection_tag": "rudi-seed"}],
                                     "metadata_dates": {"created": "2023-04-12T09:39:28.666Z",
                                                        "updated": "2023-04-12T09:39:28.696Z"}},
                   "global_id": "e8b513a1-8d0e-4824-9a7d-1087fc66af9d",
                   "resource_title": "Synergistic system-worthy encoding",
                   "synopsis": [{"lang": "fr", "text": "Tasty incentivize bricks-and-clicks systems"}], "summary": [
            {"lang": "fr",
             "text": "I'll index the wireless GB hard drive, that should capacitor the JSON firewall! You "
                     "can't index the interface without programming the neural RSS application! Aliquid quasi "
                     "earum. Debitis possimus sit aut voluptatum ut nostrum. At corrupti optio pariatur corrupti "
                     "autem ut."}],
                   "purpose": [{"lang": "fr", "text": "rudi-seed"}], "theme": "education",
                   "keywords": ["Compte administratif", "Santé"], "collection_tag": "rudi-seed",
                   "producer": {"organization_id": "fa557d8b-0892-47aa-809b-6da59081e0aa",
                                "organization_name": "Gusikowski LLC",
                                "organization_address": "4974 Altenwerth Wells, Brownville",
                                "collection_tag": "rudi-seed"}, "contacts": [
            {"contact_id": "f275bed9-6b62-43f1-b617-a392896a617c", "contact_name": "Sherri Dickinson",
             "email": "sherri.dickinson@irisa.fr", "collection_tag": "rudi-seed"},
            {"contact_id": "6371498a-f9df-46a5-b4e6-9dec377ada2b", "contact_name": "Wanda Torphy",
             "email": "wanda.torphy@irisa.fr", "collection_tag": "rudi-seed"}], "available_formats": [
            {"checksum": {"algo": "MD5", "hash": "4c9ee0f14e835927a1bbafde0eb89fb3"},
             "media_dates": {"created": "2023-03-03T11:15:57.226Z", "updated": "2023-03-03T11:15:57.226Z"},
             "connector": {"url": "https://shared-rudi.aqmo.org/media/9de29661-a53a-4eea-835c-b0799e181636",
                           "interface_contract": "dwnl"}, "file_type": "application/json", "file_size": 59016,
             "file_storage_status": "missing", "file_status_update": "2023-03-03T11:15:57.232Z",
             "media_id": "9de29661-a53a-4eea-835c-b0799e181636", "media_type": "FILE",
             "media_name": "Synergistic system-worthy encoding.json", "collection_tag": "rudi-seed"}],
                   "resource_languages": ["fr"], "storage_status": "pending"}
    log_d(fun, 'RudiMetadata.from_dict', RudiMetadata.from_dict(meta))
