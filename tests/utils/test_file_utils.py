import pytest

from rudi_node_write.rudi_types.serializable import is_serializable
from rudi_node_write.utils.file_utils import (
    FileDetails,
    check_is_dir,
    check_is_file,
    exists_file,
    get_file_charset,
    get_file_extension,
    get_file_hash,
    get_file_mime,
    get_file_size,
    is_dir,
    is_file,
)

TEST_FILES_DIR = "./tests/_test_files"
YAML_FILE_PATH = f"{TEST_FILES_DIR}/RUDI node API.yml"
YAML_FILE_SIZE = 76685
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
    assert get_file_mime("README.md") == "text/markdown"
    with pytest.raises(FileNotFoundError):
        assert get_file_mime("test")


def test_get_file_charset():
    assert get_file_charset(YAML_FILE_PATH) == "utf-8"
    assert get_file_charset(PY_FILE_PATH) == "utf-8"
    assert get_file_charset("pyproject.toml") is None
    assert get_file_charset("README.md") == "ascii"
    with pytest.raises(FileNotFoundError):
        assert get_file_charset("test")


file_md5 = "bc2078171f346925337ee09d826b257b"
file_256 = "1a1e8bffeebd6d07be458137ec3386bd482b06e450dd172b09b45488a246ed70"
file_512 = "6f9e06a8458355da3c1cc53322e3489454f39f49acef7751b375bc244476e88a113865c53cbcf96bd24c69e4001d4fffd32838f791fb84b3c4a44e3097322be4"


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
    assert file_info.name == "RUDI node API.yml"
    assert file_info.extension == ".yml"
    assert file_info.mime == "text/x-yaml"
    assert file_info.charset == "utf-8"
    assert file_info.size == YAML_FILE_SIZE
    assert file_info.md5 == file_md5
    assert FileDetails.from_json({}) is None
