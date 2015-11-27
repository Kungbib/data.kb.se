#!/usr/bin/env python
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import Admin
from models import (
    Users,
    Format,
    Sameas,
    Torrent,
    Datasets,
    Role,
    Provider,
    License,
    db
)
from flask import session
from xmlrpclib import ServerProxy
from makeTorrent import makeTorrent
from os import path
from requests import get, post

admin = Admin()


class Models(ModelView):

    def is_accessible(self):
        if session.get('username', None):
            if session.get('is_admin', 'False') == 'True':
                return True
            else:
                return False
        else:
            return False

    def index(self):
        return self.render('admindex.html')


def is_allowed(roles):
    print('Allowed: %s got %s' % (roles, session['role']))
    if session['role'] not in roles:
        return False
    if session['role'] in roles:
        return True


class DatasetsView(ModelView):

    def is_accessible(self):
        if session.get('username', None):
            if session.get('is_admin', 'False') == 'True':
                return True
            else:
                return False
        else:
            return False

    inline_model = (Format,)
    column_list = ('type', 'name', 'description', 'license', 'path', 'url')
    column_filter = ('type', 'name', 'description', 'license', 'path', 'url')
    form_columns = (
        'type', 'name',
        'description', 'license',
        'path', 'url', 'provider',
        'formats', 'sameas'
    )

    def __init__(self, session):
        super(DatasetsView, self).__init__(Datasets, db.session)


class UserView(ModelView):

    def is_accessible(self):
        if session.get('username', None):
            if session.get('is_admin', 'False') == 'True':
                return True
            else:
                return False
        else:
            return False

    def __init__(self, session):
        super(UserView, self).__init__(Users, db.session)
    form_columns = ('username', 'role')


class TorrentView(ModelView):

    def is_accessible(self):
        if session.get('username', None):
            if session.get('is_admin', 'False') == 'True':
                return True
            else:
                return False
        else:
            return False

    def __init__(self, session):
        super(TorrentView, self).__init__(Torrent, db.session)
    column_list = ('torrent', 'updated_at')
    form_columns = ('torrent', )

    def on_model_delete(self, model):
        appConf = admin.app.config
        infoHash = model.infoHash
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer %s' % appConf.get('DATASETKEY')
        }
        if appConf.get('SUNET', False):
            try:
                r = get(
                    'https://datasets.sunet.se'
                    '/api/dataset/%s/delete' % infoHash,
                    headers=headers,
                    verify=appConf.get('VERIFY_SSL', True)
                )
                r.raise_for_status()
            except Exception as e:
                print("Could not delete torrent %s" % e)
        if appConf.get('RTORRENT', False):
            try:
                rtorrent = ServerProxy(appConf.get('XMLRPC_URI'))
                rtorrent.d.erase(infoHash)
            except Exception as e:
                print("Could not remove torrent: %s" % e)

    def on_model_change(self, form, model, is_created):
        datasetID = form.data['torrent'].datasetID
        if is_created:
            dataset = Datasets.query.filter(
                Datasets.datasetID == datasetID
            ).first()
            appConf = admin.app.config
            mk = makeTorrent(announce=appConf.get('ANNOUNCE'))
            mk.multi_file(path.join(appConf.get('DATASET_ROOT'), dataset.path))
            torrentData = mk.getBencoded()
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer %s' % appConf.get('DATASETKEY')
            }
            tData = {'torrent': torrentData}
            if appConf.get('SUNET', False):
                try:
                    r = post(
                        'https://datasets.sunet.se/api/dataset',
                        headers=headers,
                        files=tData,
                        verify=appConf.get('VERIFY_SSL', True)
                    )
                    r.raise_for_status()
                except Exception as e:
                    print("Could not upload torrent: %s" % e)
            model.infoHash = mk.info_hash()
            model.torrentData = torrentData
            torrentFile = path.join(
                appConf.get('TORRENT_WATCH_DIR'),
                model.infoHash + '.torrent'
            )
            with open(torrentFile, 'w') as tf:
                tf.write(torrentData)
            if appConf.get('RTORRENT'):
                try:
                    rtorrent = ServerProxy(appConf.get('XMLRPC_URI'))
                    rtorrent.load(torrentFile)
                    downloadPath = path.dirname(
                        path.join(
                            appConf.get('DATASET_ROOT'),
                            dataset.path
                        )
                    )
                    rtorrent.d.set_directory(model.infoHash, downloadPath)
                except Exception as e:
                    print("Could not add torrent to rtorrent: %s" % e)

        return


admin.add_view(UserView(db.session))
admin.add_view(Models(Role, db.session))
admin.add_view(Models(Provider, db.session))
admin.add_view(Models(License, db.session))
admin.add_view(Models(Format, db.session))
admin.add_view(DatasetsView(db.session))
admin.add_view(TorrentView(db.session))
admin.add_view(Models(Sameas, db.session))
