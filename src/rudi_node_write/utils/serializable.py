from abc import abstractmethod, ABC
from json import dumps

from rudi_node_write.utils.log import log_d


def clean_nones(value):
    """
    Recursively remove all None values from dictionaries and lists, and returns
    the result as a new dictionary or list.
    https://stackoverflow.com/a/60124334/1563072
    """
    if isinstance(value, list):
        return [clean_nones(x) for x in value if x is not None]
    elif isinstance(value, dict):
        return {key: clean_nones(val) for key, val in value.items() if val is not None}
    else:
        return value


class Serializable(ABC):

    @property
    def class_name(self):
        return self.__class__.__name__

    def to_json_str(self, should_keep_nones: bool = False, should_ensure_ascii: bool = False) -> str:
        """
        Makes sure every attribute can be serialized.
        :return: a JSON representation of the object as a string
        """
        return dumps(self.__dict__ if should_keep_nones else clean_nones(self.__dict__),
                     default=lambda o: (
                         o.to_json_dict(should_keep_nones) if issubclass(type(o), Serializable) else o.__dict__ if
                         should_keep_nones else clean_nones(o.__dict__)), ensure_ascii=should_ensure_ascii)

    def to_json_dict(self, should_keep_nones: bool = False) -> dict:
        """
        Transform the object into a Python object
        :return: a Python object
        """
        self_dict = self.__dict__ if should_keep_nones else clean_nones(self.__dict__)
        json_dict = {}
        for o in self_dict:
            json_dict[o] = o.to_json_dict(should_keep_nones) if issubclass(type(o), Serializable) else self_dict[o]
        return json_dict

    def __str__(self) -> str:
        # log_d('Serializable.toString', self.class_name)
        return str(self.to_json_str())

    @staticmethod
    @abstractmethod
    def from_dict(obj: dict):
        raise NotImplementedError()


if __name__ == '__main__':
    fun = 'Serializable tests'
    log_d(fun, 'clean_nones', clean_nones({'toto': None}))
    log_d(fun, 'clean_nones', clean_nones({'toto': ''}))
    log_d(fun, 'clean_nones', clean_nones({'toto': None, 'tata': 5}))
    log_d(fun, 'clean_nones', clean_nones({'toto': {'tutu': None}, 'tata': 5}))
