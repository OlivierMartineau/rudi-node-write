from uuid import UUID

from rudi_node_write.rudi_types.rudi_const import DEFAULT_LANG, REGEX_RUDI_VERSION, StorageStatus, \
    Language
from rudi_node_write.rudi_types.rudi_contact import RudiContact
from rudi_node_write.rudi_types.rudi_dates import RudiDates
from rudi_node_write.rudi_types.rudi_geometry import BoundingBox
from rudi_node_write.rudi_types.rudi_media import RudiMedia
from rudi_node_write.rudi_types.rudi_meta import RudiMetadata
from rudi_node_write.rudi_types.rudi_org import RudiOrganization
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.type_string import is_string, ensure_uuid4


def make_keywords(keywords: str | list[str]):
    if is_string(keywords):
        return [kw.strip() for kw in keywords.split(',')]
    return [kw.strip() for kw in keywords]



class MetadataFactory:
    def __init__(self, default_language=DEFAULT_LANG):
        self.default_language = default_language

    def make_rudi_metadata(self, global_id: str | UUID, resource_title: str, synopsis: PotentialDictionaryEntryList,
                           summary: PotentialDictionaryEntryList, theme: str,
                           keywords: str | list[str], producer: RudiOrganization, contacts: list[RudiContact],
                           media_list: list[RudiMedia], dataset_dates: RudiDates, storage_status: StorageStatus,
                           licence,
                           api_version: str, local_id: str = None, doi: str = None,
                           dataset_languages: list[Language] = None,
                           dataset_start_date: str = None, dataset_end_date: str = None,
                           dataset_bounding_box: BoundingBox = None,
                           dataset_geojson: dict = None, dataset_projection: str = None, numbers_of_records: int = None,
                           numbers_of_fields: int = None, metadata_dates: RudiDates = None,
                           metadata_provider: RudiOrganization = None, metadata_contacts: list[RudiContact] = None,
                           restricted_access: bool = False, gdpr_sensitive: bool = False):
        return RudiMetadata(
            global_id=ensure_uuid4(global_id),
            resource_title=resource_title,
            synopsis=make_list_of_dictionary_entries(synopsis),
            summary=make_list_of_dictionary_entries(summary),
            theme=theme,
            keywords=make_keywords(keywords),
            producer=RudiOrganizationFactory.make_producer(producer)

        )
        log_d('MetadataFactory.make_rudi_metadata', 'WIP')


if __name__ == '__main__':
    fun = 'MetadataFactory'
    # meta = RudiMetadata(global_id=uuid4(), resource_title='Testing metadata',
    #                     summary=[{'lang': 'fr', 'text': 'quite something'}], synopsis='truc', theme='theme', keywords=[
    #         'keywords'], producer='producer', metadata_contacts='metadata_contacts', available_formats='available_formats',
    #                     dataset_dates='dataset_dates', storage_status='storage_status', licence='licence',
    #                     api_version=RUDI_API_VERSION)
    # log_d(fun, make_dictionary_entry({'lang': 'en', 'text': 'quite something'}))
    # log_d(fun, make_dictionary_entry('quite something'))
    # log_d(fun, make_list_of_dictionary_entries('quite something'))
    # log_d(fun, make_list_of_dictionary_entries({'lang': 'en', 'text': 'quite something'}))
    # dict_entries_list = [{'lang': 'en', 'text': 'quite something'}, {'lang': 'fr', 'text': "n'est-ce pas ?"}]
    # dict_entries_obj = make_list_of_dictionary_entries(dict_entries_list)
    # log_d(fun, make_list_of_dictionary_entries(dict_entries_list))
    # log_d(fun, make_list_of_dictionary_entries(dict_entries_obj))
    # log_d(fun, dict_entries_obj)
    # log_d(fun, {"in_dict": dict_entries_obj})
    # log_d(fun, str({"in_dict": dict_entries_obj}))

    log_d(fun, 'make_keywords', make_keywords('toto , tata'))
    log_d(fun, 'make_keywords', make_keywords(['toto ', ' tata']))
