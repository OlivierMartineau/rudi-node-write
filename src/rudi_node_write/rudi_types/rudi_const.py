from re import compile
from typing import Literal, get_args, Final

from rudi_node_write.utils.err import LiteralUnexpectedValueException

RUDI_API_VERSION: Final[str] = '1.3.0'
REGEX_RUDI_VERSION = compile(r'^[0-9]{1,2}\.[0-9]{1,2}(\.[0-9]{1,2})?[a-z]*$')

Language = Literal['cs', 'da', 'de', 'en', 'el', 'es', 'fr', 'hu', 'it', 'no', 'pl', 'pt', 'ro', 'ru', 'sk']
RECOGNIZED_LANGUAGES = get_args(Language)
DEFAULT_LANG: Language = 'fr'

StorageStatus: Final = Literal['pending', 'online', 'archived', 'unavailable']
STORAGE_STATUSES = get_args(StorageStatus)

LicenceType: Final = Literal['STANDARD', 'CUSTOM']
LICENCE_TYPES = get_args(LicenceType)
LICENCE_TYPE_STANDARD: Final[str] = 'STANDARD'
LICENCE_TYPE_CUSTOM: Final[str] = 'CUSTOM'

LicenceCode = Literal[
    "apache-2.0", "cc-by-nd-4.0", "etalab-1.0", "etalab-2.0", "gpl-3.0", "mit", "odbl-1.0", "public-domain-cc0"]
LICENCE_CODES = get_args(LicenceCode)

MediaType: Final = Literal['FILE', 'SERVICE', 'SERIES']
MEDIA_TYPES = get_args(MediaType)
MEDIA_TYPE_FILE: Final[str] = 'FILE'
MEDIA_TYPE_SERVICE: Final[str] = 'SERVICE'

FileStorageStatus = Literal['nonexistant', 'available', 'missing', 'archived', 'removed']
FILE_STORAGE_STATUSES = get_args(FileStorageStatus)

HashAlgorithm = Literal['MD5', 'SHA-256', 'SHA-512']
HASH_ALGORITHMS = get_args(HashAlgorithm)

FileExtensions: Final = {'.3gp': 'video/3gpp', '.3gpp': 'video/3gpp', '.7z': 'application/x-7z-compressed',
                         '.aac': 'audio/aac', '.apng': 'image/apng', '.avi': 'video/x-msvideo',
                         '.bin': 'application/octet-stream', '.bmp': 'image/bmp', '.bz': 'application/x-bzip',
                         '.bz2': 'application/x-bzip2', '.css': 'text/css', '.csv': 'text/csv',
                         '.doc': 'application/msword',
                         '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         '.epub': 'application/epub+zip', '.exe': 'application/x-executable', '.flif': 'image/flif',
                         '.geojson': 'application/geo+json', '.gif': 'image/gif', '.gz': 'application/gzip',
                         '.gzip': 'application/gzip', '.htm': 'text/html', '.html': 'text/html',
                         '.ico': 'image/vnd.microsoft.icon', '.jpeg': 'image/jpeg', '.jpg': 'image/jpeg',
                         '.js': 'application/javascript', '.json': 'application/json', '.jsonld': 'application/ld+json',
                         '.m4a': 'audio/m4a', '.mkv': 'video/x-matroska', '.mng': 'image/x-mng',
                         '.mov': 'video/quicktime', '.mp3': 'audio/mpeg', '.mp4': 'video/mp4', '.mpeg': 'video/mpeg',
                         '.mpg': 'video/mpeg', '.odp': 'application/vnd.oasis.opendocument.presentation',
                         '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
                         '.odt': 'application/vnd.oasis.opendocument.text', '.oga': 'audio/ogg', '.ogg': 'audio/ogg',
                         '.ogv': 'video/ogg', '.otf': 'font/otf', '.pdf': 'application/pdf', '.php': 'text/php',
                         '.png': 'image/png', '.ppt': 'application/vnd.ms-powerpoint',
                         '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                         '.sql': 'application/sql', '.tar': 'application/x-tar', 'tar.bz': 'application/x-bzip',
                         'tar.bz2': 'application/x-bzip2', 'tar.gz': 'application/gzip', '.tgz': 'application/gzip',
                         '.tif': 'image/tiff', '.tiff': 'image/tiff', '.ttf': 'font/ttf', '.txt': 'text/plain',
                         '.wav': 'audio/wav', '.weba': 'audio/webm', '.webm': 'video/webm', '.webp': 'image/webp',
                         '.wmv': 'video/x-ms-wmv', '.xls': 'application/vnd.ms-excel',
                         '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         '.xml': 'text/xml', '.yaml': 'text/x-yaml', '.yml': 'text/x-yaml', '.zip': 'application/zip',
                         '.zst': 'application/zstd', }

MimeTypes = Literal[
    'application/x-executable', 'application/graphql', 'application/javascript', 'application/json', 'application/ld+json', 'application/msword', 'application/pdf', 'application/sql', 'application/vnd.api+json', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint', 'application/vnd.oasis.opendocument.text', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/x-www-form-urlencoded', 'application/xml', 'application/zip', 'application/zstd', 'audio/mpeg', 'audio/ogg', 'image/gif', 'image/apng', 'image/flif', 'image/webp', 'image/x-mng', 'image/jpeg', 'image/png', 'multipart/form-data', 'text/css', 'text/csv', 'text/html', 'text/php', 'text/plain', 'text/xml', 'application/x-executable+crypt', 'application/graphql+crypt', 'application/javascript+crypt', 'application/json+crypt', 'application/ld+json+crypt', 'application/msword+crypt', 'application/pdf+crypt', 'application/sql+crypt', 'application/vnd.api+json+crypt', 'application/vnd.ms-excel+crypt', 'application/vnd.ms-powerpoint+crypt', 'application/vnd.oasis.opendocument.text+crypt', 'application/vnd.openxmlformats-officedocument.presentationml.presentation+crypt', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet+crypt', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document+crypt', 'application/x-www-form-urlencoded+crypt', 'application/xml+crypt', 'application/zip+crypt', 'application/zstd+crypt', 'audio/mpeg+crypt', 'audio/ogg+crypt', 'image/gif+crypt', 'image/apng+crypt', 'image/flif+crypt', 'image/webp+crypt', 'image/x-mng+crypt', 'image/jpeg+crypt', 'image/png+crypt', 'multipart/form-data+crypt', 'text/css+crypt', 'text/csv+crypt', 'text/html+crypt', 'text/php+crypt', 'text/plain+crypt', 'text/xml+crypt', 'text/x-yaml+crypt']
MIME_TYPES = get_args(MimeTypes)


def check_is_accepted(val, series: tuple, err_msg: str = 'incorrect value'):
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
