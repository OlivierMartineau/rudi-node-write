from abc import ABC, abstractmethod

from rudi_node_write.io_connectors.io_connector import Connector


class DataSourceConnector(Connector, ABC):

    def __init__(self, server_url: str):
        super().__init__(server_url)

    @abstractmethod
    def test_connection(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def metadata_count(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def metadata_list(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def producers(self):
        raise NotImplementedError()
