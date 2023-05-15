from re import compile
from typing import Literal, get_args

from rudi_node_write.utils.err import LiteralUnexpectedValueException

RUDI_API_VERSION = '1.3.0'
REGEX_RUDI_VERSION = compile(r'^[0-9]{1,2}\.[0-9]{1,2}(\.[0-9]{1,2})?[a-z]*$')

Language = Literal['cs', 'da', 'de', 'en', 'el', 'es', 'fr', 'hu', 'it', 'no', 'pl', 'pt', 'ro', 'ru', 'sk']
RECOGNIZED_LANGUAGES = get_args(Language)
DEFAULT_LANG: Language = 'fr'

StorageStatus = Literal['pending', 'online', 'archived', 'unavailable']
STORAGE_STATUSES = get_args(StorageStatus)

LicenceType = Literal['STANDARD', 'CUSTOM']
LICENCE_TYPES = get_args(LicenceType)
LICENCE_TYPE_STANDARD = 'STANDARD'
LICENCE_TYPE_CUSTOM = 'CUSTOM'

LicenceCode = Literal[
    "apache-2.0", "cc-by-nd-4.0", "etalab-1.0", "etalab-2.0", "gpl-3.0", "mit", "odbl-1.0", "public-domain-cc0"]
LICENCE_CODES = get_args(LicenceCode)

MediaType = Literal['FILE', 'SERVICE', 'SERIES']
MEDIA_TYPES = get_args(MediaType)
MEDIA_TYPE_FILE = 'FILE'
MEDIA_TYPE_SERVICE = 'SERVICE'

FileStorageStatus = Literal['nonexistant', 'available', 'missing', 'archived', 'removed']
FILE_STORAGE_STATUSES = get_args(FileStorageStatus)

HashAlgorithm = Literal['MD5', 'SHA-256', 'SHA-512']
HASH_ALGORITHMS = get_args(HashAlgorithm)

MimeTypes = Literal[
    'application/x-executable', 'application/graphql', 'application/javascript', 'application/json',
    'application/ld+json', 'application/msword', 'application/pdf', 'application/sql', 'application/vnd.api+json',
    'application/vnd.ms-excel', 'application/vnd.ms-powerpoint', 'application/vnd.oasis.opendocument.text',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/x-www-form-urlencoded',
    'application/xml', 'application/zip', 'application/zstd', 'audio/mpeg', 'audio/ogg', 'image/gif', 'image/apng',
    'image/flif', 'image/webp', 'image/x-mng', 'image/jpeg', 'image/png', 'multipart/form-data', 'text/css', 'text/csv',
    'text/html', 'text/php', 'text/plain', 'text/xml', 'application/x-executable+crypt', 'application/graphql+crypt',
    'application/javascript+crypt', 'application/json+crypt', 'application/ld+json+crypt', 'application/msword+crypt',
    'application/pdf+crypt', 'application/sql+crypt', 'application/vnd.api+json+crypt',
    'application/vnd.ms-excel+crypt', 'application/vnd.ms-powerpoint+crypt',
    'application/vnd.oasis.opendocument.text+crypt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation+crypt',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet+crypt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document+crypt',
    'application/x-www-form-urlencoded+crypt', 'application/xml+crypt', 'application/zip+crypt',
    'application/zstd+crypt', 'audio/mpeg+crypt', 'audio/ogg+crypt', 'image/gif+crypt', 'image/apng+crypt',
    'image/flif+crypt', 'image/webp+crypt', 'image/x-mng+crypt', 'image/jpeg+crypt', 'image/png+crypt',
    'multipart/form-data+crypt', 'text/css+crypt', 'text/csv+crypt', 'text/html+crypt', 'text/php+crypt',
    'text/plain+crypt', 'text/xml+crypt', 'text/x-yaml+crypt']
MIME_TYPES = get_args(MimeTypes)


def check_is_accepted(val, series: list, err_msg: str = 'incorrect value'):
    """
    Check if input value is in the given series, raise an error with input message otherwise
    :param val: the value to check
    :param series: the series of accepted values
    :param err_msg: error message raised if the value was not found in the series
    :return: the checked value
    """
    if val not in series:
        raise LiteralUnexpectedValueException(val, series, err_msg)
    return val


def check_rudi_version(version):
    if not REGEX_RUDI_VERSION.match(version):
        raise ValueError(f"Incorrect RUDI metadata version: '{version}'")
    return version
