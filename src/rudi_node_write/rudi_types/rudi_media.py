from abc import ABC
from json import dumps

from rudi_node_write.rudi_types.rudi_const import MediaType, FileStorageStatus, HashAlgorithm, HASH_ALGORITHMS, \
    check_is_accepted, FILE_STORAGE_STATUSES, MEDIA_TYPE_FILE, MEDIA_TYPE_SERVICE, MIME_TYPES
from rudi_node_write.rudi_types.rudi_dates import RudiDates
from rudi_node_write.utils.date import ensure_date_str
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import check_is_dict, check_has_key, safe_get_key
from rudi_node_write.utils.type_string import ensure_uuid4, check_is_string
from rudi_node_write.utils.types import check_is_int


class RudiChecksum(Serializable):
    def __init__(self, algo: HashAlgorithm, hash_str: str):
        self.algo = check_is_accepted(algo, HASH_ALGORITHMS, 'the value was not recognized as a hash algorithm ')
        self.hash_str = check_is_string(hash_str)

    def to_json_str(self, should_keep_nones: bool = False, should_ensure_ascii: bool = False) -> str:
        log_d('RudiChecksum.to_json_str')
        return dumps({'hash': self.hash_str, 'algo': self.algo})

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)
        algo = check_is_accepted(check_has_key(o, 'algo'), HASH_ALGORITHMS,
                                 'the value was not recognized as a hash algorithm ')
        hash_str = check_is_string(check_has_key(o, 'hash'))
        return RudiChecksum(algo=algo, hash_str=hash_str)


class RudiMedia(Serializable, ABC):

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)
        media_type = check_has_key(o, 'media_type')
        if media_type == MEDIA_TYPE_FILE:
            return RudiMediaFile.from_dict(o)
        if media_type == MEDIA_TYPE_SERVICE:
            return RudiMediaService.from_dict(o)
        raise NotImplementedError(f"cannot create a media for type '{media_type}'")


class RudiMediaService(RudiMedia):
    def __init__(self, media_type: MediaType, media_id: str, media_name: str, media_caption: str = None,
                 media_dates: RudiDates = None, api_documentation_url: str = None):
        self.media_type = media_type
        self.media_id = media_id
        self.media_name = media_name
        self.media_caption = media_caption
        self.media_dates = media_dates
        self.api_documentation_url = api_documentation_url

    @staticmethod
    def from_dict(o:dict):
        check_is_dict(o)
        media_type = check_has_key(o, 'media_type')
        if media_type != MEDIA_TYPE_SERVICE:
            raise ValueError(f"This cannot be structured as a RudiMediaService: got 'media_type' = '{media_type}'")
        media_id = ensure_uuid4(check_has_key(o, 'media_id'))
        media_name = check_has_key(o, 'media_name')
        media_caption = o.get('media_caption')
        media_dates = RudiDates.from_dict(o.get('media_dates'))
        api_documentation_url = o.get('api_documentation_url')
        return RudiMediaService(media_type=media_type, media_id=media_id, media_name=media_name,
                                media_caption=media_caption, media_dates=media_dates,
                                api_documentation_url=api_documentation_url)


class RudiMediaFile(RudiMedia):
    def __init__(self, media_type: MediaType, media_id: str, media_name: str, file_type: str, file_size: int,
                 checksum_hash: str, checksum_algo: str, media_caption: str = None, media_dates: RudiDates = None,
                 file_encoding: str = None, file_structure: str = None, file_storage_status: FileStorageStatus = None,
                 file_status_update: str = None):
        # Media mandatory attributes
        self.media_type = check_is_accepted(media_type, [MEDIA_TYPE_FILE], 'wrong type for RudiMediaFile')
        self.media_id = ensure_uuid4(media_id)
        self.media_name = check_is_string(media_name)

        # MediaFile mandatory attributes
        self.file_type = check_is_accepted(file_type, MIME_TYPES, 'incorrect parameter for MIME type')
        log_d('RudiMediaFile', 'file_type', file_type)
        log_d('RudiMediaFile', 'file_size', file_size)
        self.file_size = check_is_int(file_size)

        self.checksum = RudiChecksum(
            algo=check_is_accepted(checksum_algo, HASH_ALGORITHMS, 'incorrect value for a hash algorithm '),
            hash_str=check_is_string(checksum_hash))

        # Media optional attributes
        if media_caption:
            check_is_string(media_caption)
        self.media_caption = media_caption
        self.media_dates = media_dates

        # MediaFile optional attributes
        if file_encoding:
            check_is_string(file_encoding)
        self.file_encoding = file_encoding
        if file_structure:
            check_is_string(file_structure)
        self.file_structure = file_structure
        if file_storage_status:
            check_is_accepted(file_storage_status, FILE_STORAGE_STATUSES, 'incorrect value for a file storage status')
        self.file_storage_status = file_storage_status
        self.file_status_update = ensure_date_str(file_status_update)

    @staticmethod
    def from_dict(o:dict):
        check_is_dict(o)

        # Media mandatory attributes
        media_type = check_has_key(o, 'media_type')
        check_is_accepted(media_type, [MEDIA_TYPE_FILE], 'this cannot be structured as a RudiMediaFile')

        media_id = ensure_uuid4(check_has_key(o, 'media_id'))
        media_name = check_is_string(check_has_key(o, 'media_name'))

        # MediaFile mandatory attributes
        file_type = check_is_accepted(check_has_key(o, 'file_type'), MIME_TYPES,
                                      'incorrect parameter for MIME type')
        file_size = check_is_int(check_has_key(o, 'file_size'))

        checksum_hash = check_is_string(safe_get_key(o, 'checksum', 'hash'))
        checksum_algo = check_is_accepted(safe_get_key(o, 'checksum', 'algo'), HASH_ALGORITHMS,
                                          'the value was not recognized as a hash algorithm ')
        # Media optional attributes
        media_caption = o.get('media_caption')
        if media_caption:
            check_is_string(media_caption)
        media_dates = o.get('media_dates')
        if media_dates:
            media_dates = RudiDates.from_dict(media_dates)

        # MediaFile optional attributes
        file_encoding = o.get('file_encoding')
        if file_encoding:
            check_is_string(file_encoding)
        file_structure = o.get('file_structure')
        file_storage_status = o.get('file_storage_status')
        if file_storage_status:
            check_is_accepted(file_storage_status, FILE_STORAGE_STATUSES, 'value not accepted as a file storage status')
        file_status_update = ensure_date_str(o.get('file_status_update'))

        log_d('RudiMediaFile.from_dict', 'preliminary checks OK')
        return RudiMediaFile(media_type=media_type, media_id=media_id, media_name=media_name, file_type=file_type,
                             file_size=file_size, checksum_hash=checksum_hash, checksum_algo=checksum_algo,
                             media_caption=media_caption, media_dates=media_dates, file_encoding=file_encoding,
                             file_structure=file_structure, file_storage_status=file_storage_status,
                             file_status_update=file_status_update)


if __name__ == '__main__':
    fun = 'RudiMedia tests'
    log_d(fun, 'RudiMediaFile.from_dict', RudiMediaFile.from_dict(
        {"checksum": {"algo": "SHA-256", "hash": "f72d0035896447b55ff27998d6fd8773a68b2770027336c09da2bc6fd67e2dcf"},
         "media_dates": {"created": "2022-01-21T10:40:28.781Z", "updated": "2022-01-21T10:40:28.781Z"}, "connector": {
            "url": "https://bacasable.fenix.rudi-univ-rennes1.fr/media/download/2611547a-42f1-4d7c-b736-2fef5cca30fe",
            "interface_contract": "dwnl"}, "file_type": "image/png", "file_size": 414931,
         "file_storage_status": "available", "file_status_update": "2023-04-14T13:57:15.859Z",
         "media_id": "2611547a-42f1-4d7c-b736-2fef5cca30fe", "media_type": "FILE", "media_name": "unicorn.png"}))
