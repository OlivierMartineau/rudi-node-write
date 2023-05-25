from time import time

from rudi_node_write.io_connectors.io_data_source import DataSourceConnector
from rudi_node_write.io_connectors.io_data_source_ods import OdsConnector_v2_1
from rudi_node_write.io_connectors.io_rudi_api_write import RudiNodeApiConnector
from rudi_node_write.io_connectors.io_rudi_jwt_factory import RudiNodeJwtFactory
from rudi_node_write.utils.file import read_file
from rudi_node_write.utils.log import log_d, log_e


class Controller_Correspondences:
    """
    This object takes a source (e.g. ODS portal) and a RUDI producer node as a destination.
    It compares both, establish correspondences between metadata and producers and establish the list of
    correspondences
    """

    def __init__(self, data_source_reader: DataSourceConnector, rudi_node_writer: RudiNodeApiConnector):
        self.data_source_reader = data_source_reader
        self.rudi_node_writer = rudi_node_writer

        self._src_producers = None
        self._node_producers = None
        self._producers_correspondences = None

        self._src_metadata = None
        self._node_metadata = None
        self._metadata_correspondences = None

    @property
    def data_source_producers(self):
        self._src_producers = self.data_source_reader.producers if self._src_producers is None else self._src_producers
        return self._src_producers

    @property
    def rudi_node_producers(self):
        self._node_producers = self.rudi_node_writer.producers if self._node_producers is None else self._node_producers
        return self._node_producers

    def get_rudi_node_producer_with_name(self, org_name):
        found_orgs = [org for org in self.rudi_node_producers if org.get('organization_name') == org_name]
        if len(found_orgs) == 0:
            return None
        if len(found_orgs) > 1:
            log_e('get_rudi_node_producers_by_name',
                  f"inconsistency on RUDI node: several organization were found with name '{org_name}'", found_orgs)
        return found_orgs[0]

    def get_rudi_node_producer_with_id(self, org_id):
        found_orgs = [org for org in self.rudi_node_producers if org.get('organization_id') == org_id]
        if len(found_orgs) == 0:
            return None
        if len(found_orgs) > 1:
            log_e('get_rudi_node_producers_by_name',
                  f"inconsistency on RUDI node: several organization were found with id '{org_id}'", found_orgs)
        return found_orgs[0]

    @property
    def data_source_metadata(self):
        if self._src_metadata is None:
            self._src_metadata = self.data_source_reader.metadata_list
        return self._src_metadata

    @property
    def rudi_node_metadata(self):
        if self._node_metadata is None:
            self._node_metadata = self.rudi_node_writer.metadata_list
        return self._node_metadata

    def get_rudi_node_metadata_with_name(self, org_name):
        found_meta = [meta for meta in self.rudi_node_metadata if meta.get('resource_title') == org_name]
        if len(found_meta) == 0:
            return None
        if len(found_meta) > 1:
            log_e('get_rudi_node_producers_by_name',
                  f"inconsistency on RUDI node: several organization were found with name '{org_name}'", found_meta)
        return found_meta[0]

    def get_rudi_node_producer_with_src_id(self, org_id):
        found_orgs = [org for org in self.rudi_node_producers if org.get('organization_id') == org_id]
        if len(found_orgs) == 0:
            return None
        if len(found_orgs) > 1:
            log_e('get_rudi_node_producers_by_name',
                  f"inconsistency on RUDI node: several organization were found with id '{org_id}'", found_orgs)
        return found_orgs[0]

    @property
    def producers_correspondences(self):
        if self._producers_correspondences is None:
            self._producers_correspondences = {'on_src_only': [], 'on_node_only': [], 'on_both': []}
            node_orgs = self.rudi_node_producers
            for org_name in self.data_source_producers:
                rudi_org = self.get_rudi_node_producer_with_name(org_name)
                if not rudi_org:
                    self._producers_correspondences['on_src_only'].append(org_name)
                else:
                    self._producers_correspondences['on_both'] = {'organization_name': org_name,
                                                                  'organization_id': rudi_org['organization_id']}
                    rudi_org['on_src'] = True
            self._producers_correspondences['on_node_only'] = [org for org in node_orgs if not org.get('on_src')]
        return self._producers_correspondences

    def get_metadata_correspondences(self):
        if self._metadata_correspondences is None:
            src_meta = self.data_source_reader.metadata_list
            rudi_meta = self.rudi_node_writer.metadata_list


if __name__ == '__main__':
    fun = 'Controller_Correspondences'
    begin = time()
    src_connector = OdsConnector_v2_1('https://data.rennesmetropole.fr/api/explore/v2.1')
    creds_file = '../../../creds/creds.json'
    rudi_node_creds = read_file(creds_file)
    node_jwt_factory = RudiNodeJwtFactory('https://bacasable.fenix.rudi-univ-rennes1.fr', rudi_node_creds)
    rudi_node = RudiNodeApiConnector(server_url='https://bacasable.fenix.rudi-univ-rennes1.fr',
                                     jwt_factory=node_jwt_factory)

    cc = Controller_Correspondences(src_connector, rudi_node)
    log_d(fun, 'producers correspondences', cc.producers_correspondences)
    log_d(fun, 'rudi_node_producers', cc.rudi_node_producers)
    log_d(fun, 'exec. time', time() - begin)
