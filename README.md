# Context

We have a data source, e.g. OpenDataSoft-powered or GeoServer-powered open data server.
And we have a RUDI node, that acts as an open-source server as well, but also feeds the RUDI portal.

This library makes it possible to

- access the data source (see [io_data_source.py](src%2Frudi_node_write%2Fio_connectors%2Fio_data_source.py))
- extract the metadata from the Data
  source ([metadata_factory.py](src%2Frudi_node_write%2Fconversion%2Fmetadata_factory.py))
- normalize them as a SourceMetadata [source_meta.py](src%2Frudi_node_write%2Fsrc_types%2Fsource_meta.py)
- connect to the RudiNode ([io_rudi_api_write.py](src%2Frudi_node_write%2Fio_connectors%2Fio_rudi_api_write.py))
- verify that the RudiMetadata is online, upload it otherwise ([metadata_factory.py](src%2Frudi_node_write%2Fconversion%2Fmetadata_factory.py))
- update the RudiMetadata if needed ([metadata_factory.py](src%2Frudi_node_write%2Fconversion%2Fmetadata_factory.py))
- update the associated Media if needed ([io_rudi_media_write.py](src%2Frudi_node_write%2Fio_connectors%2Fio_rudi_media_write.py))
