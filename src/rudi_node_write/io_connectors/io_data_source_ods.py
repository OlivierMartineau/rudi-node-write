from time import time
from typing import Final, Literal, get_args

from rudi_node_write.io_connectors.io_data_source import DataSourceConnector
from rudi_node_write.utils.err import LiteralUnexpectedValueException
from rudi_node_write.utils.log import log_d

ODS_REQ_LIMIT = 100
# ODS_DELIMITERS = [';', ',', '\\t', '|']

OdsOutputFormat: Final = Literal['csv', 'json', 'xlsx', 'geojson']
ODS_OUTPUT_FORMATS: Final = get_args(OdsOutputFormat)


class OdsConnector_v2_1(DataSourceConnector):

    def __init__(self, server_url: str):
        super().__init__(server_url)
        self.test_connection()

    def test_connection(self):
        return self.metadata_count > 0

    @property
    def metadata_count(self) -> int:
        count = self.request('catalog/datasets?limit=1').get('total_count')
        if count is None:
            raise ConnectionError(f"Cannot seem to connect with the data source at {self.base_url}")
        return count

    def get_metadata_list(self, req_params: str = 'order_by=default.metadata_processed desc', max_number: int = 0):
        src_dataset = []
        req_offset = 0
        src_data_nb = ODS_REQ_LIMIT  # we'll adjust this later
        max_nb = src_data_nb if not max_number else max_number
        while req_offset < max_nb:
            req_limit = ODS_REQ_LIMIT if req_offset + ODS_REQ_LIMIT < max_nb else max_nb - req_offset
            src_data = self.request(
                f'catalog/datasets?limit={req_limit}&offset={req_offset}&{req_params}', keep_alive=True)
            src_dataset += self._get_metadata_list(src_data)
            src_data_nb = src_data.get('total_count')  # adjusting the number of data
            if src_data_nb and (not max_number or max_nb > src_data_nb):
                max_nb = src_data_nb
            req_offset += ODS_REQ_LIMIT
        self.close_connection()
        return src_dataset

    @property
    def metadata_list(self):
        return self.get_metadata_list()

    def get_meta_records(self, meta_ods_id, output_format: OdsOutputFormat = 'json'):
        if output_format not in ODS_OUTPUT_FORMATS:
            raise LiteralUnexpectedValueException('incorrect type for output format', ODS_OUTPUT_FORMATS, output_format)
        return self.request(self._get_exports_url(meta_ods_id, output_format))

    @property
    def producers(self):
        publisher_list = self.get_metadata_list('group_by=publisher')
        return [entry['publisher'] for entry in publisher_list]

    @staticmethod
    def _get_exports_url(ods_meta_id, output_format: OdsOutputFormat = 'json'):
        if output_format not in ODS_OUTPUT_FORMATS:
            raise LiteralUnexpectedValueException('incorrect type for output format', ODS_OUTPUT_FORMATS, output_format)
        return f"catalog/datasets/{ods_meta_id}/exports/{output_format}?lang=fr&timezone=" \
               f"Europe/Paris&use_labels=true&delimiter=;"

    @staticmethod
    def _get_metadata_list(datasets_request_result):
        return datasets_request_result['results']

    @staticmethod
    def _get_ods_meta_id(ods_metadata):
        return ods_metadata['dataset_id']

    @staticmethod
    def _get_ods_meta_fields(ods_metadata):
        return ods_metadata['default']


if __name__ == '__main__':
    fun = 'OdsConnector_v2_1'
    begin = time()

    data_source_connector = OdsConnector_v2_1('https://data.rennesmetropole.fr/api/explore/v2.1')
    log_d(fun, 'data count', data_source_connector.metadata_count)
    data = data_source_connector.get_metadata_list('order_by=publisher asc,default.metadata_processed desc')
    log_d(fun, 'data count', len(data))
    # log_d(fun, 'data', data)
    data0 = data[0]
    log_d(fun, 'first dataset', data0)
    # pprint(data[0]['dataset'], width=250)
    log_d(fun, 'first dataset ID', data0['dataset_id'])
    for d in data:
        log_d(fun, f"{d['default']['metadata_processed'][2:16]} - {d['default']['publisher']}",
              d['dataset_id'], d['default']['title'], d['features'])
    # data0_records = data_source_connector.get_meta_records(data0['dataset_id'], 'json')
    # log_d(fun, 'data0_records', data0_records[1])

    # Howto:
    # - export the records as a JSON w/
    #       - dataset: fields + features + visibility
    #       - records: total_count + results
    # - get a JSON + CSV as a file
    # - if features == 'geo', get a geojson
    producers = data_source_connector.producers
    log_d(fun, 'producers', producers)

    log_d(fun, 'exec. time', time() - begin)
