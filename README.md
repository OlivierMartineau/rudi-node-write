[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Caution: this librairy is still a work in progress.

# RUDI Node tools: _rudi-node-write_ library

This library offers tools to take advantage of
the [internal API](https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI) of a RUDI Producer node (
also
referred as RUDI node).

## Installation

```bash
$ pip install rudi_node_write
```

## Usage

```python
from rudi_node_write.connectors.io_rudi_api_write import RudiNodeApiConnector

rudi_api = RudiNodeApiConnector('https://bacasable.fenix.rudi-univ-rennes1.fr')
print(rudi_api.metadata_count)
print(len(rudi_api.metadata_list))
print(rudi_api.producer_names)
print(rudi_api.find_metadata_with_media_name('toucan.jpg'))

```

## Testing

```bash
$ pytest
```
