from json import load
from os import stat
from os.path import exists
from pathlib import Path
from time import time
from typing import Literal

from chardet import detect
from puremagic import magic_file

from rudi_node_write.utils.log import log_d


def exists_file(file_local_path: str):
    return exists(file_local_path)


def is_file(file_local_path: str):
    return Path(file_local_path).is_file()


def ensure_is_file(file_local_path: str):
    if not Path(file_local_path).is_file():
        raise FileNotFoundError(f"No such file: '{file_local_path}'")


def get_file_size(file_local_path: str):
    """
    Returns a file size in bytes
    :param file_local_path:
    :return:
    """
    return stat(file_local_path).st_size


def get_file_extension(file_local_path: str):
    """
    Returns a file size in bytes
    :param file_local_path:
    :return:
    """
    return ''.join(Path(file_local_path).suffixes)


def get_file_mime(file_local_path: str) -> str:
    """
    Returns the MIME type of a file
    (Based on 'puremagic' lib https://pypi.org/project/puremagic)
    :param file_local_path:
    :return:
    """
    file_info = magic_file(file_local_path)
    if not file_info:
        return 'application/octet-stream'
    mime_type = file_info[0].mime_type
    if mime_type == 'application/x-gzip':
        return 'application/gzip'
    return mime_type


def get_file_charset(file_local_path):
    """
    Returns the encoding of a file
    (Uses the library 'chardet': https://pypi.org/project/chardet)
    :param file_local_path: the path of a local file
    :return: the encoding of the file
    """
    mime_type = get_file_mime(file_local_path)
    if not mime_type.startswith('text'):
        # not detecting application/* as 'utf-8' is the norm
        # and mime_type not in ['application/x-yaml', 'application/json', 'application/geo+json', 'application/xml',
        # 'application/javascript']
        return None
    with open(file_local_path, "rb") as file_stream:
        data = file_stream.read()
        charset = detect(data, True)["encoding"]
        return charset


def get_file_info(file_local_path: str):
    """
    Returns the file information: size, extension, MIME type
    (Uses the library 'puremagic': https://pypi.org/project/puremagic)
    (Uses the library 'chardet': https://pypi.org/project/chardet)
    :param file_local_path: the path of a local file
    :return: the name, the extension, the MIME type, the size and the encoding of a file
    """
    return {'name': Path(file_local_path).name,
            'extension': get_file_extension(file_local_path),
            'mime_type': get_file_mime(file_local_path),
            'size': get_file_size(file_local_path),
            'charset': get_file_charset(file_local_path)}


def read_file(file_path):
    with open(file_path, 'r') as file_content:
        content = load(file_content)
    return content


def write_file(destination_file_path: str, content, mode: Literal['b', 't'] = 't'):
    """

    :param destination_file_path: the path of the file
    :param content:
    :param mode: use 'b'for binary mode, 't' for text mode (default)
    :return:
    """
    with open(destination_file_path, f'w{mode}') as file:
        file.write(content)


if __name__ == '__main__':
    fun = 'FileUtils'
    begin = time()
    yaml_file_path = '../../../doc/rudi-api/RUDI producer internal API - 1.3.0.yml'
    test_file_dir = '../../../dwnld/'
    right_path = test_file_dir + 'unicorn.png'
    bin_file = test_file_dir + 'WERTSTOFFE.m8s'
    tar_gz_file = test_file_dir + 'rudi-node-read.tar.gz'
    txt_file = test_file_dir + 'RUDI producer internal API.txt'
    wrong_path = test_file_dir + 'toto'
    log_d(fun, 'exists file OK', exists_file(right_path))
    log_d(fun, 'exists file KO', exists_file(wrong_path))
    log_d(fun, 'is file OK', is_file(right_path))
    log_d(fun, 'is file', is_file(wrong_path))
    log_d(fun, 'exists file (dir)', exists_file(test_file_dir))
    log_d(fun, 'is dir a file', is_file(test_file_dir))
    # log_d(fun, 'ensure_is_file', ensure_is_file(test_file_dir))
    log_d(fun, 'file size', get_file_size(right_path))
    log_d(fun, 'file extension', get_file_extension(right_path))
    log_d(fun, 'file extension', get_file_extension('foobar.tar.gz'))
    log_d(fun, 'file extension', get_file_extension('.bashrc'))
    log_d(fun, 'file mime', get_file_mime(right_path))
    log_d(fun, 'file charset', get_file_charset(yaml_file_path))
    log_d(fun, 'file info', get_file_info(right_path))
    log_d(fun, 'file info', get_file_info(yaml_file_path))
    log_d(fun, 'file info', get_file_info(bin_file))
    log_d(fun, 'file info', get_file_info(tar_gz_file))
    log_d(fun, 'file info', get_file_info(txt_file))
    # log_d(fun, 'file info', get_file_info(wrong_path))
    write_file(test_file_dir + 'toto', 'tut0156')

    log_d(fun, 'exec. time', time() - begin)
