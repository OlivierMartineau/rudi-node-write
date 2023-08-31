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

## Authentication

To use the RUDI node internal API `/api/admin/...`, you'll need an authentication JWT in every header request.

This library provides a `RudiNodeJwtFactory` connector that calls a [JWT
server](https://github.com/sigrennesmetropole/rudi_producer_node/tree/main/rudi-jwt) running locally or on the RUDI
node to create/renew the JWT.

```python
rudi_node_credentials = {
    "url": "<rudi node url>",
    "usr": "<my user name>",  # either use 'usr' & 'pwd', or the base64url encoded usr:pwd pair in 'b64auth'
    "pwd": "<my password>",
    "b64auth": "<base64url encoded usr:pwd pair>"  # optional / alternative way of declaring the usr:pwd pair
}

from rudi_node_write.connectors.io_rudi_jwt_factory import RudiNodeJwtFactory

node_jwt_factory = RudiNodeJwtFactory(rudi_node_credentials["url"], rudi_node_credentials)
```

## Usage: RudiNodeApiConnector

One can create, read, update or delete metadata with a RudiNodeApiConnector object using the [RUDI API](.
/doc/rudi-api/RUDI producer internal API - 1.3.0.yml).

```python
from rudi_node_write.connectors.io_rudi_jwt_factory import RudiNodeJwtFactory
from rudi_node_write.connectors.io_rudi_api_write import RudiNodeApiConnector

rudi_node_url = 'https://bacasable.fenix.rudi-univ-rennes1.fr'
node_jwt_factory = RudiNodeJwtFactory(rudi_node_url, {"usr": "<my user name>", "pwd": "<my password>"})

rudi_api = RudiNodeApiConnector(server_url=rudi_node_url, jwt_factory=node_jwt_factory)
print("metadata count:", rudi_api.metadata_count)
print("metadata alt count:", len(rudi_api.metadata_list))
print("metadata producers declared on the node:", rudi_api.producer_names)
print("searching a metadata with a file name:", rudi_api.find_metadata_with_media_name('toucan.jpg'))

```

## Usage: RudiNodeMediaConnector

The upload of file is done with a RudiNodeMediaConnector that let you connect to a RUDI node Media server.
This also needs an authentication in the request header, that is created with the RudiMediaHeadersFactoryBasicAuth
object.

```python
from rudi_node_write.connectors.io_rudi_media_write import RudiMediaHeadersFactoryBasicAuth, RudiNodeMediaConnector

rudi_node_url = 'https://bacasable.fenix.rudi-univ-rennes1.fr'
media_headers_factory = RudiMediaHeadersFactoryBasicAuth(usr="<my user name>", pwd="<my password>")
rudi_media = RudiNodeMediaConnector(server_url=rudi_node_url, headers_factory=media_headers_factory)

print("listing the media stored on the RUDI node: ", rudi_media.media_list)
```

## Testing

The [tests](./tests) can be analyzed for further information about how to call the "RUDI API" and the "RUDI Media"
servers.

```bash
$ pytest
```
