from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import check_is_dict, check_has_key
from rudi_node_write.utils.types import check_is_number


def ensure_is_latitude(latitude: float, alt_err_msg: str = None) -> float:
    check_is_number(latitude)
    if not -90 < latitude < 90:
        raise ValueError(f"{'latitude' if not alt_err_msg else alt_err_msg}"
                         f" should be a decimal between -90 and 90, got '{latitude}'")
    return float(latitude)


def ensure_is_longitude(longitude: float, alt_err_msg: str = None) -> float:
    check_is_number(longitude)
    if not -180 < longitude < 180:
        raise ValueError(f"{'longitude' if not alt_err_msg else alt_err_msg}"
                         f" should be a decimal between -180 and 180, got '{longitude}'")
    return float(longitude)


class BoundingBox(Serializable):
    def __init__(self, south_latitude: float, west_longitude: float, north_latitude: float, east_longitude: float):
        """
        Coordinates of a bounding box, given as decimal numbers (ISO 6709)
        :param south_latitude: southernmost latitude
        :param west_longitude: westernmost longitude
        :param north_latitude: northernmost latitude
        :param east_longitude: easternmost longitude
        """
        self.south_latitude = ensure_is_latitude(south_latitude, 'southernmost latitude')
        self.north_latitude = ensure_is_latitude(north_latitude, 'northernmost latitude')
        if south_latitude > north_latitude:
            raise ValueError('southernmost latitude should be lower than northernmost latitude')
        self.west_longitude = ensure_is_longitude(west_longitude, 'westernmost longitude')
        self.east_longitude = ensure_is_longitude(east_longitude, 'easternmost longitude')
        if west_longitude > east_longitude:
            print(f'! BoundingBox warning: westernmost latitude is generally lower than easternmost latitude. Got W: '
                  f'{west_longitude} > E: {east_longitude}')

    @staticmethod
    def from_dict(o: dict):
        check_is_dict(o)
        south_latitude = ensure_is_latitude(check_has_key(o, 'south_latitude'), 'southernmost latitude')
        north_latitude = ensure_is_latitude(check_has_key(o, 'north_latitude'), 'northernmost latitude')
        west_longitude = ensure_is_longitude(check_has_key(o, 'west_longitude'), 'westernmost longitude')
        east_longitude = ensure_is_longitude(check_has_key(o, 'east_longitude'), 'easternmost longitude')
        return BoundingBox(south_latitude=south_latitude, north_latitude=north_latitude, west_longitude=west_longitude,
                           east_longitude=east_longitude)


if __name__ == '__main__':
    bb1 = BoundingBox(10, 120, 30, 40)
    bb = BoundingBox.from_dict(
        {'south_latitude': -10, 'north_latitude': 24.8, 'west_longitude': 40.7, 'east_longitude': 104.8})
    print('BoundingBox', bb)
