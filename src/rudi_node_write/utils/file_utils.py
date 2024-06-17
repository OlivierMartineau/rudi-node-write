from hashlib import md5, sha256, sha512
from http.client import ACCEPTED
from json import load, dump
from os import stat
from os.path import exists
from pathlib import Path
from time import time
from typing import Literal

from chardet import detect
from puremagic import magic_file

from rudi_node_write.rudi_types.rudi_const import FileExtensions
from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.log import log_d, log_w


def is_dir(dir_local_path: str):
    return Path(dir_local_path).is_dir()


def check_is_dir(dir_local_path: str, err_msg: str | None = None):
    if not is_dir(dir_local_path):
        raise FileNotFoundError(err_msg if err_msg is not None else f"No such file: '{dir_local_path}'")
    return dir_local_path


def exists_file(file_local_path: str):
    return exists(file_local_path)


def is_file(file_local_path: str):
    return Path(file_local_path).is_file()


def check_is_file(file_local_path: str, err_msg: str | None = None):
    if not is_file(file_local_path):
        raise FileNotFoundError(err_msg if err_msg is not None else f"No such file: '{file_local_path}'")
    return file_local_path


def get_file_size(file_local_path: str):
    """
    Returns a file size in bytes
    :param file_local_path:
    :return:
    """
    return stat(file_local_path).st_size


# @decorator_timer
def get_file_extension(file_local_path: str):
    """
    Returns a file size in bytes
    :param file_local_path:
    :return:
    """
    ext = "".join(Path(file_local_path).suffixes)
    # log_d('get_file_extension', 'ext', ext)
    if FileExtensions.get(ext) is not None:
        return ext
    recognized_ext = [key for key in FileExtensions.keys() if ext.endswith(key)]
    return recognized_ext[-1] if len(recognized_ext) else ext


def get_file_mime(file_local_path: str) -> str:
    """
    Returns the MIME type of a file
    (Based on 'puremagic' lib https://pypi.org/project/puremagic)
    :param file_local_path:
    :return:
    """
    file_info = magic_file(file_local_path)
    if not file_info:  # pragma: no cover
        return "application/octet-stream"
    mime_type = file_info[0].mime_type
    if mime_type == "application/x-gzip":  # pragma: no cover
        return "application/gzip"
    if mime_type.endswith("yaml"):
        return "text/x-yaml"
    return mime_type


def get_file_charset(file_local_path: str):
    """
    Returns the encoding of a file
    (Uses the library 'chardet': https://pypi.org/project/chardet)
    :param file_local_path: the path of a local file
    :return: the encoding of the file
    """
    mime_type = get_file_mime(file_local_path)
    if not mime_type.startswith("text"):
        # not detecting application/* as 'utf-8' is the norm
        # and mime_type not in ['application/x-yaml', 'application/json', 'application/geo+json', 'application/xml',
        # 'application/javascript']
        return None
    with open(file_local_path, "rb") as file_stream:
        data = file_stream.read()
        charset = detect(data, True)["encoding"]
        return charset


ACCEPTED_HASH_ALGOS = ("MD5", "SHA-256", "SHA256", "SHA-512", "SHA512")


def get_file_hash(file_local_path: str, hash_algo: str = "md5") -> str:
    file_content = open(check_is_file(file_local_path), "rb").read()
    if not isinstance(hash_algo, str) or (upper_algo := hash_algo.upper()) not in ACCEPTED_HASH_ALGOS:
        raise ValueError(f"Hash algorithm should be MD5, SHA-256 or SHA-512, got: '{hash_algo}'")
    if upper_algo == "MD5":
        return md5(file_content).hexdigest()
    if upper_algo in ("shA256", "SHA-256"):
        return sha256(file_content).hexdigest()
        # if upper_algo in ("SHA512", "SHA-512"):
    return sha512(file_content).hexdigest()


def read_json_file(file_path, mode: Literal["b", "t"] = "t"):  # pragma: no cover
    with open(file_path, f"r{mode}") as json_file_content:
        json_dict = load(json_file_content)
    return json_dict


def write_file(destination_file_path: str, content, mode: Literal["b", "t"] = "t"):  # pragma: no cover
    """

    :param destination_file_path: the path of the file
    :param content:
    :param mode: use 'b'for binary mode, 't' for text mode (default)
    :return:
    """
    with open(destination_file_path, f"w{mode}") as file:
        file.write(content)


def write_json_file(destination_file_path: str, json_dict):  # pragma: no cover
    with open(destination_file_path, "w") as file:
        dump(json_dict, file, ensure_ascii=False)


class FileDetails(Serializable):
    def __init__(self, file_local_path: str):
        check_is_file(file_local_path)
        self.path: str = file_local_path
        self.name: str = Path(file_local_path).name
        self.extension: str = get_file_extension(file_local_path)
        self.mime: str = get_file_mime(file_local_path)
        self.charset: str | None = get_file_charset(self.path) if self.mime.startswith("text") else None
        self.size: int = get_file_size(file_local_path)
        self.md5: str = get_file_hash(file_local_path)

    @staticmethod
    def from_json(o):
        pass


if __name__ == "__main__":  # pragma: no cover
    tests = "FileUtils"
    begin = time()
    yaml_file_path = "../../../doc/rudi-api/RUDI producer internal API - 1.3.0.yml"
    test_file_dir = "../../../dwnld/"
    right_path = test_file_dir + "unicorn.png"
    bin_file = test_file_dir + "WERTSTOFFE.m8s"
    tar_gz_file = test_file_dir + "rudi-node-read.tar.gz"
    txt_file = test_file_dir + "RUDI producer internal API.txt"
    wrong_path = test_file_dir + "toto"
    log_d(tests, "exists file OK", exists_file(right_path))
    log_d(tests, "exists file KO", exists_file(wrong_path))
    log_d(tests, "is file OK", is_file(right_path))
    log_d(tests, "is file", is_file(wrong_path))
    log_d(tests, "exists file (dir)", exists_file(test_file_dir))
    log_d(tests, "is dir a file", is_file(test_file_dir))
    # log_d(here, 'check_is_file', check_is_file(test_file_dir))
    log_d(tests, "file size", get_file_size(right_path))
    log_d(tests, "file extension", get_file_extension(right_path))
    log_d(tests, "file extension", get_file_extension("foobar.tar.gz"))
    log_d(tests, "file extension", get_file_extension("foo.bar.tar.gz"))
    log_d(tests, "file extension", get_file_extension(".bashrc"))
    log_d(tests, "file extension", get_file_extension(yaml_file_path))
    log_d(tests, "file mime", get_file_mime(right_path))
    log_d(tests, "file charset", get_file_charset(yaml_file_path))
    log_d(tests, "file info", FileDetails(right_path))
    log_d(tests, "file info", FileDetails(yaml_file_path))
    log_d(tests, "file info", FileDetails(bin_file))
    log_d(tests, "file info", FileDetails(tar_gz_file))
    log_d(tests, "file info", FileDetails(txt_file))
    # log_d(here, 'file info', get_file_info(wrong_path))
    unicode_file_path = test_file_dir + "unicode_chars.txt"
    write_file(unicode_file_path, "tut0156êµîƒﬁÌπÏ“{ëôøÇ¡¶{µœ≤é≤")

    log_d(tests, "file MD5 hash", get_file_hash(unicode_file_path))
    log_d(tests, "file SHA-256 hash", get_file_hash(unicode_file_path, "sha256"))
    log_d(tests, "file SHA-512 hash", get_file_hash(unicode_file_path, "sha-512"))

    log_d(tests, "file hash MD5", get_file_hash(yaml_file_path))
    log_d(tests, "file hash MD5", get_file_hash(yaml_file_path, "MD5"))
    log_d(tests, "file hash SHA-256", get_file_hash(yaml_file_path, "sHa256"))
    log_d(tests, "file hash SHA-512", get_file_hash(yaml_file_path, "shA-512"))
    log_d(tests, "file MD5 hash", FileDetails(unicode_file_path).md5)

    log_d(tests, "exec. time", time() - begin)
