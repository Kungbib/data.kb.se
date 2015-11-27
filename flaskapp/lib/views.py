from flask.ext.admin.contrib.sqla import ModelView
from flask import session
import models
from torrents import delete_torrent, add_torrent
from dbShared import db
from flask.ext.admin import consts


class DatasetsView(ModelView):
    def is_accessible(self):
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
        else:
            return False
    inline_model = (models.Format,)
    column_list = ('type', 'name', 'description', 'license', 'path', 'url')
    column_filter = ('type', 'name', 'description', 'license', 'path', 'url')
    form_columns = (
        'type', 'name',
        'description', 'license',
        'path', 'url', 'provider',
        'formats', 'sameas'
    )

    def __init__(self, session):
        super(DatasetsView, self).__init__(models.Datasets, db.session)


class UserView(ModelView):
    def is_accessible(self):
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
        else:
            return False

    def __init__(self, session):
        super(UserView, self).__init__(models.Users, db.session)
        self.menu_icon_type = consts.ICON_TYPE_GLYPH
    form_columns = ('username', 'role')


class TorrentView(ModelView):
    def is_accessible(self):
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
        else:
            return False

    def __init__(self, session):
        super(TorrentView, self).__init__(models.Torrent, db.session)
    column_list = ('torrent', 'updated_at')
    form_columns = ('torrent', )

    def on_model_delete(self, model):
            infoHash = model.infoHash
            try:
                delete_torrent(infoHash)
            except Exception as e:
                print("Could not delete {}: {}".format(infoHash, e))

    def on_model_change(self, form, model, is_created):
        datasetID = form.data['torrent'].datasetID
        if is_created:
            add_torrent(model, datasetID)
        return