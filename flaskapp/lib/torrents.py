from flask import current_app
from requests import get, post
from xmlrpclib import ServerProxy
from makeTorrent import makeTorrent
from os import path
import models


def delete_torrent(info_hash):
    if current_app.conf['SUNET']:
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer %s' % current_app.conf['DATASETKEY']
        }
        try:
            r = get(
                'https://datasets.sunet.se/api/dataset/%s/delete' % info_hash,
                headers=headers,
                verify=False
                )
            r.raise_for_status()
        except Exception as e:
            raise Exception("Could not delete torrent %s" % e)
    if current_app.conf['RTORRENT']:
        try:
            rtorrent = ServerProxy(current_app.conf['XMLRPC_URI'])
            rtorrent.d.erase(info_hash)
        except Exception as e:
            raise Exception("Could not remove torrent: %s" % e)


def _add_sunet(torrentObj):
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer %s' % current_app.conf['DATASETKEY']
    }
    torrentData = torrentObj.getBencoded()
    tData = {'torrent': torrentData}
    try:
        r = post(
            'https://datasets.sunet.se/api/dataset',
            headers=headers,
            files=tData,
            verify=current_app.conf['VERIFY_SSL']
        )
        r.raise_for_status()
        return('%s added to sunet' % torrentObj.info_hash())
    except Exception as e:
        raise Exception("Could not upload torrent: %s" % e)


def _add_torrent_to_model(model, torrentObj):
    model.infoHash = torrentObj.info_hash()
    model.torrentData = torrentObj.getBencoded()
    return(model)


def _add_rtorrent(torrentObj, datasetPath):
    infoHash = torrentObj.info_hash()
    torrentFile = path.join(
        current_app.conf['TORRENT_WATCH_DIR'],
        infoHash + '.torrent'
    )
    rtorrent = ServerProxy(current_app.conf['XMLRPC_URI'])
    rtorrent.load(torrentFile)
    downloadPath = path.dirname(
        path.join(
            current_app.conf['DATASET_ROOT'],
            datasetPath
        )
    )
    with open(torrentFile, 'w') as tf:
        tf.write(torrentObj.getBencoded())

    rtorrent.d.set_directory(infoHash, downloadPath)
    rtorrent.d.start(infoHash)
    return("Torrent Added")


def add_torrent(model, datasetID):
    datasetRoot = current_app.config['DATASET_ROOT']
    dataset = models.Datasets.query.filter(
        models.Datasets.datasetID == datasetID
    ).first()
    try:
        torrentObj = makeTorrent(announce=current_app.config['ANNOUNCE'])
    except KeyError:
        raise KeyError("ANNOUNCE is required to create torrents")
    torrentObj.multi_file(path.join(datasetRoot, dataset.path))
    model = _add_torrent_to_model(model, torrentObj)
    if current_app.config.get('SUNET'):
        _add_sunet(torrentObj)
    if current_app.config.get('RTORRENT'):
        _add_rtorrent(torrentObj, dataset.path)
    return(model)
