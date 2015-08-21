data.kb.se
==========

# Overview

A basic webservice for displaying and providing large datasets.

# Installation

In the `flaskapp` folder, run the command:

`pip install -r requirements.txt`

# Usage

## Basic Configuration

Before starting the app copy the `settings.py.example` file:

`cp settings.py.example settings.py`

The required settings are marked in the configuration file, with the only real changes needed are:

```python
USER_LIST = ['user1', 'user2']
ANNOUNCE = 'http://example.com/announce'
```

`USER_LIST` are the users in the `REMOTE_USER` that are authorized to add/change/edit datasets. If set in dev mode, /login2 will automatically log you in as an admin

`ANNOUNCE` the torrent announcer used for all torrent files

## Starting the App:

To start the app, run:

`python data.py`

Browse to:

`localhost:8000`

To login, browse to:

`localhost:8000/login2`

If in dev mode, you'll be authenticated as an admin, when put in prod another authenication method is expected.

## Authentication

A handler for swamid authentication and basic authentication are provided.

Before you're able to authenticate, the user will need to be populated with a role in the database. If a user for basic auth is provided in the `USER_LIST` it will get admin priviledges from the get go, otherwise they can be added later (or in dev mode).

## Optional configuration

There are several optional configuration settings:

### Rtorrent
A few simple methods for managing rtorrent via xmlrpc are provided, however they must be enabled and configured to work:

```python
TORRENT_WATCH_DIR = '/path/to/torrent/dir'
RTORRENT = False
XMLRPC_URI = 'http://example.com:5000/RPC2'
```

* `TORRENT_WATACH_DIR` is the directory torrent files will be placed
* `RTORRENT` set to `False` to disable rtorrent functions, or `True` to enable them
* `XMLRPC_URI` The xmlrpc url to use for commands. See: [RPC setup](https://github.com/rakshasa/rtorrent/wiki/RPC-Setup-XMLRPC)

### Sunet datasets
Support for https://datasets.sunet.se is also available:

```python
SUNET = False
DATASETKEY = 'YOURAPIKEY'
```

* `SUNET` if set to `False` datasets.sunet.se will not be used
* `DATASETKEY` the api key for datasets.sunet.se

### Summarize mets
If mets files are present (with the name `aip.mets.metadata`) they can be summarized and viewed in directories.

* `SUMMARIZE_METS` Enable mets summaries

If this is enabled, you'll also have to run:

`pip install lxml`

## Previous Static Generation Design

Tools and templates to generate a catalog of file based datasets typically hosted on an Apache server. Files are stored in a folder together with an index file in yaml. A script collects the index files and generates a catalog index page in html. The catalog index page contains a machine readable representation in [RDFa](http://www.w3.org/TR/html-rdfa/).

## The yaml index file

The index file provides basic information about the dataset and its relation to catalog items in Libris.

Example:

```yaml
type: Dataset
name: Post- och inrikes tidningar

description: >
  Digitaliserad version av Post- och inrikes 
  tidningar från 1645-1701. Digitaliseringen genomfördes 1998
  och utgick från mikrofilmsversionen. Filerna är ordnade i en katalog
  per år med bildfiler och transkriberade versioner.

license: CC0

sameAs:
  - librisid:72389479
  - librisid:23443899
 
distribution:
  encodingFormat:
    - TIFF
    - DOC

provider:
  name: Example Name
  email: example.name@example.com
```



