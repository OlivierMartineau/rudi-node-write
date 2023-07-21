import pytest

from rudi_node_write.rudi_types.rudi_geo import check_is_latitude, check_is_longitude, BoundingBox, RudiGeography
from rudi_node_write.utils.typing_utils import to_number


def test_check_is_latitude():
    for latitude in [-90, "-45", 0, 1.5123, "45", 90]:
        assert check_is_latitude(latitude) == to_number(latitude)
    for latitude in [-91, 91]:
        with pytest.raises(ValueError):
            check_is_latitude(latitude)
    for latitude in ["lat 45", {"lat": 45}]:
        with pytest.raises(TypeError):
            check_is_latitude(latitude)


def test_check_is_longitude():
    for longitude in [-180, "-45", 0, 1.55123, "45", 180]:
        assert check_is_longitude(longitude) == to_number(longitude)
    for longitude in [-181, 181]:
        with pytest.raises(ValueError):
            check_is_longitude(longitude)
    for longitude in ["lat 45", {"lat": 45}]:
        with pytest.raises(TypeError):
            check_is_longitude(longitude)


def test_BoundingBox_init():
    assert BoundingBox(1, 2, 3, 4)
    assert BoundingBox(1, 12, 6, 4)
    with pytest.raises(ValueError):
        BoundingBox(11, 2, 3, 4)


def test_BoundingBox_from_json():
    assert BoundingBox.from_json(
        {"south_latitude": -10.0, "north_latitude": 24.8, "west_longitude": 40.7, "east_longitude": 104.8}
    )


def test_BoundingBox_merge_bbox_list():
    bb1 = BoundingBox(south_latitude=1, west_longitude=2, north_latitude=3, east_longitude=4)
    bb2 = BoundingBox(south_latitude=4, west_longitude=5, north_latitude=6, east_longitude=7)
    assert BoundingBox.merge_bbox_list([bb1, bb2]) == BoundingBox(
        south_latitude=1, west_longitude=2, north_latitude=6, east_longitude=7
    )


def test_RudiGeography():
    bbox = BoundingBox(south_latitude=1, west_longitude=2, north_latitude=3, east_longitude=4)
    assert RudiGeography(bbox)


def test_RudiGeography_from_json():
    geo = {
        "bounding_box": {
            "west_longitude": -1.96327,
            "east_longitude": -1.46558,
            "south_latitude": 47.93192,
            "north_latitude": 48.30684,
        },
        "geographic_distribution": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-1.96327, 47.93192],
                    [-1.46558, 47.93192],
                    [-1.46558, 48.30684],
                    [-1.96327, 48.30684],
                    [-1.96327, 47.93192],
                ]
            ],
            "bbox": [-1.96327, 47.93192, -1.46558, 48.30684],
        },
        "projection": "WGS 84 (EPSG:4326)",
    }
    assert RudiGeography.from_json(geo)
    assert RudiGeography.from_json(None) is None
