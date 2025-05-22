import pytest

from rudi_node_write.rudi_types.serializable import is_serializable
from rudi_node_write.utils.file_utils import (
    exists_file,
    get_file_hash,
    is_file,
    is_dir,
    check_is_dir,
    check_is_file,
    get_file_size,
    get_file_extension,
    get_file_mime,
    get_file_charset,
    FileDetails,
)

TEST_FILES_DIR = "./tests/_test_files"
YAML_FILE_PATH = f"{TEST_FILES_DIR}/RUDI producer internal API - 1.3.0.yml"
YAML_FILE_SIZE = 91045
PY_FILE_PATH = "./src/rudi_node_write/utils/file_utils.py"
CSV_FILE_PATH = f"{TEST_FILES_DIR}/dummy.csv"


def test_is_dir():
    assert is_dir(TEST_FILES_DIR)
    assert not is_dir("./not_a_dir")


def test_check_is_dir():
    assert check_is_dir(TEST_FILES_DIR) == TEST_FILES_DIR
    with pytest.raises(FileNotFoundError):
        check_is_dir("./not_a_dir")


def test_exists_file():
    assert exists_file(YAML_FILE_PATH)
    assert not exists_file("not_a_file.txt")


def test_is_file():
    assert is_file(YAML_FILE_PATH)
    assert not is_file("not_a_file.txt")


def test_is_check_is_file():
    assert check_is_file(YAML_FILE_PATH) == YAML_FILE_PATH
    with pytest.raises(FileNotFoundError):
        check_is_file("not_a_file.txt")


def test_get_file_size():
    assert get_file_size(YAML_FILE_PATH) == YAML_FILE_SIZE


def test_get_file_extension():
    assert get_file_extension(YAML_FILE_PATH) == ".yml"
    assert get_file_extension("YAML_FILE_PATH.txt") == ".txt"
    assert get_file_extension("YAML_FILE_PATH.tar.gz") == ".tar.gz"


def test_get_file_mime():
    assert get_file_mime(YAML_FILE_PATH) == "text/x-yaml"
    assert get_file_mime(PY_FILE_PATH) == "text/x-python"
    assert get_file_mime(CSV_FILE_PATH) == "text/csv"
    assert get_file_mime("pyproject.toml") == "application/toml"
    assert get_file_mime("README.md") == "text/plain"
    with pytest.raises(FileNotFoundError):
        assert get_file_mime("test")


def test_get_file_charset():
    assert get_file_charset(YAML_FILE_PATH) == "utf-8"
    assert get_file_charset(PY_FILE_PATH) == "utf-8"
    assert get_file_charset("pyproject.toml") == None
    assert get_file_charset("README.md") == "ascii"
    with pytest.raises(FileNotFoundError):
        assert get_file_charset("test")


file_md5 = "2de58479e1940a7cf577d2d0bacd14b6"
file_256 = "6e4630952e5f17ba46bd75a1ac5c01a92865bf6ac664f724d851813be91c3951"
file_512 = "f69ee0c673f6d7ccbc8c66be1a93470bf34a1a531148c511fa5ffac6b1fec59998dedcd17310cce1462fea36d3137a5f267bee0ea3ef9d2735ec180c9ac84b8a"


def test_get_file_hash():
    # assert get_file_hash(YAML_FILE_PATH) == "e669b0fe80e47ca0a0ceadaceb8e0f9c"
    assert get_file_hash(YAML_FILE_PATH, "MD5") == file_md5
    assert get_file_hash(YAML_FILE_PATH, "sHa-256") == file_256
    assert get_file_hash(YAML_FILE_PATH, "sHa256") == file_256
    assert get_file_hash(YAML_FILE_PATH, "shA512") == file_512
    assert get_file_hash(YAML_FILE_PATH, "shA-512") == file_512
    with pytest.raises(ValueError):
        assert get_file_hash(YAML_FILE_PATH, "sha1024")


def test_FileDetails():
    file_info = FileDetails(YAML_FILE_PATH)
    assert is_serializable(file_info)
    assert file_info.path == YAML_FILE_PATH
    assert file_info.name == "RUDI producer internal API - 1.3.0.yml"
    assert file_info.extension == ".yml"
    assert file_info.mime == "text/x-yaml"
    assert file_info.charset == "utf-8"
    assert file_info.size == YAML_FILE_SIZE
    assert file_info.md5 == file_md5
    assert FileDetails.from_json({}) is None
