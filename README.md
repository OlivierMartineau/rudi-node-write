[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# RUDI Node tools: _rudi-node-write_ library

This library offers tools to take advantage of
the [internal API](https://app.swaggerhub.com/apis/OlivierMartineau/RudiProducer-InternalAPI) of a RUDI Producer node (
also
referred as RUDI node), through the API of the backend of the user interface, the "Producer node manager" or "Prodmanager" module.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install rudi_node_write
```

## Usage: RudiNodeWriter

The Jupyter notebook [`README.ipynb`](https://github.com/OlivierMartineau/rudi-node-write/blob/release/README.ipynb) details how to use the library through the [`RudiNodeWriter`](https://github.com/OlivierMartineau/rudi-node-write/blob/release/src/rudi_node_write/rudi_node_writer.py) object.

## Testing

The [tests](https://github.com/OlivierMartineau/rudi-node-write/tree/release/tests) can be analyzed for further
information about how to call the API

```bash
$ pytest
```
