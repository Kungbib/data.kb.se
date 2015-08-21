#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import (
    Flask, request,
    render_template, session,
    redirect, url_for,
    flash, send_file,
    Response
)
from flask.ext.admin import Admin
from os import path
from lib.dataDB import directory_indexer, cleanDate
from makeTorrent import makeTorrent
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from StringIO import StringIO
import settings
from requests import post, get
from urllib2 import quote, unquote
from werkzeug.contrib.cache import SimpleCache
from rdflib import Graph
from xmlrpclib import ServerProxy


MT_RDF_XML = 'application/rdf+xml'
cache = SimpleCache()
app = Flask(__name__)
admin = Admin(app, base_template='admin/kbmaster.html')

app.config.from_object('settings')
appMode = settings.APPENV
db = SQLAlchemy(app)
datasetKey = settings.DATASETKEY
announce = settings.ANNOUNCE
torrentWatchDir = settings.TORRENT_WATCH_DIR
datasetRoot = settings.DATASET_ROOT
verifySSL = settings.VERIFY_SSL
useRtorrent = settings.RTORRENT
useSunet = settings.SUNET
curDir = path.dirname(path.realpath(__file__))
secretsFile = path.join(curDir, 'secrets')
with open(secretsFile, 'r') as sfile:
    app.secret_key = sfile.read()
    salt = app.secret_key
sumMets = settings.SUMMARIZE_METS
dirIndex = directory_indexer(getMets=sumMets)
index_dir = dirIndex.index_dir


class Models(ModelView):
    def is_accessible(self):
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
        else:
            return False

    def index(self):
        return self.render('admindex.html')


def login_required(f):
    def decorated_function(*args, **kwargs):
        if session['username'] is None:
            return redirect(url_for('login2', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def is_allowed(roles):
    print('Allowed: %s got %s' % (roles, session['role']))
    if session['role'] not in roles:
        return False
    if session['role'] in roles:
        return True


dataset_format_table = db.Table(
    'dataset_format', db.Model.metadata,
    db.Column('dataset_id', db.Integer, db.ForeignKey('datasets.datasetID')),
    db.Column('format_id', db.Integer, db.ForeignKey('format.id')),
    db.Column('provider_id', db.Integer, db.ForeignKey('provider.providerID')),
    db.Column('license_id', db.Integer, db.ForeignKey('license.id')),
    db.Column('sameas_id', db.Integer, db.ForeignKey('sameas.id'))
)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roleName = db.Column(db.String(80), unique=True)
    users = db.relationship('Users', uselist=False, backref="role_name")

    def __unicode__(self):
        return self.roleName


class Users(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(128), unique=True)
    role = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __unicode__(self):
        return self.username


class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)
    url = db.Column(db.Unicode(255))

    def __unicode__(self):
        return self.name


class Datasets(db.Model):
    def is_accessible(self):
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
        else:
            return False
    datasetID = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(256))
    name = db.Column(db.String(256), unique=True)
    description = db.Column(db.Text, unique=True)
    license = db.Column(db.String(256))
    path = db.Column(db.String(256), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )
    url = db.Column(db.String(256), unique=True)
    sameas = db.relationship('Sameas', secondary=dataset_format_table)
    formats = db.relationship('Format', secondary=dataset_format_table)
    license = db.relationship('License', secondary=dataset_format_table)
    provider = db.relationship('Provider', secondary=dataset_format_table)
    torrent = db.relationship('Torrent', uselist=False, backref="torrent")

    def __unicode__(self):
        return self.name


class Provider(db.Model):
    providerID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(80), unique=True)
    email = db.Column(db.Unicode(128))

    def __unicode__(self):
        return self.name


class Format(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)

    def __unicode__(self):
        return self.name


class Torrent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset = db.Column(db.Integer, db.ForeignKey('datasets.datasetID'))
    torrentData = db.Column(db.BLOB)
    infoHash = db.Column(db.Text)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    def __unicode__(self):
        return self.dataset


class Sameas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    librisID = db.Column(db.String(256), unique=True)

    def __unicode__(self):
        return self.librisID


class DatasetsView(ModelView):
    def is_accessible(self):
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
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
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
        else:
            return False
    def __init__(self, session):
        super(UserView, self).__init__(Users, db.session)
    form_columns = ('username', 'role')


class TorrentView(ModelView):
    def is_accessible(self):
        if session.get('username', None) and session.get('is_admin', 'False') == 'True':
            return True
        else:
            return False
    def __init__(self, session):
        super(TorrentView, self).__init__(Torrent, db.session)
    column_list = ('torrent', 'updated_at')
    form_columns = ('torrent', )

    def on_model_delete(self, model):
            infoHash = model.infoHash
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer %s' % datasetKey
            }
            if useSunet:
                try:
                    r = get(
                        'https://datasets.sunet.se/api/dataset/%s/delete' % infoHash,
                        headers=headers,
                        verify=False
                        )
                    r.raise_for_status()
                except Exception as e:
                    print("Could not delete torrent %s" % e)
            if useRtorrent:
                try:
                    rtorrent = ServerProxy(settings.XMLRPC_URI)
                    rtorrent.d.erase(infoHash)
                except Exception as e:
                    print("Could not remove torrent: %s" % e)

    def on_model_change(self, form, model, is_created):
        datasetID = form.data['torrent'].datasetID
        if is_created:
            dataset = Datasets.query.filter(
                Datasets.datasetID == datasetID
            ).first()
            mk = makeTorrent(announce=announce)
            mk.multi_file(path.join(datasetRoot, dataset.path))
            torrentData = mk.getBencoded()
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer %s' % datasetKey
            }
            tData = {'torrent': torrentData}
            if useSunet:
                try:
                    r = post(
                        'https://datasets.sunet.se/api/dataset',
                        headers=headers,
                        files=tData,
                        verify=verifySSL
                    )
                    r.raise_for_status()
                except Exception as e:
                    print("Could not upload torrent: %s" % e)
            model.infoHash = mk.info_hash()
            model.torrentData = torrentData
            torrentFile = path.join(
                torrentWatchDir,
                model.infoHash + '.torrent'
            )
            with open(torrentFile, 'w') as tf:
                tf.write(torrentData)
            if useRtorrent:
                try:
                    rtorrent = ServerProxy(settings.XMLRPC_URI)
                    rtorrent.load(torrentFile)
                    downloadPath = path.dirname(
                        path.join(
                            datasetRoot,
                            dataset.path
                        )
                    )
                    rtorrent.d.set_directory(model.infoHash, downloadPath)
                except Exception as e:
                    print("Could not add torrent to rtorrent: %s" % e)

        return


db.create_all()


def buildDB():
    formats = Format.query.all()
    formats = [f.name for f in formats]
    excpectedFormats = [
        'TIFF',
        'JPEG',
        'DOC',
        'PDF',
        'JPEG2000',
        'MARC-21',
        'RDF/XML',
        'Turtle',
        'XML'
    ]
    for f in excpectedFormats:
        if f not in formats:
            form = Format()
            form.name = f
            db.session.add(form)
    licenses = License.query.all()
    licenses = [l.name for l in licenses]
    licneseTemp = [
        ('http://creativecommons.org/publicdomain/zero/1.0/', 'CC0')
    ]
    for l in licneseTemp:
        if not l[1] in licenses:
            lic = License()
            lic.name = l[1]
            lic.url = l[0]
            db.session.add(lic)
    providers = Provider.query.all()
    providers = [p.name.encode('utf8') for p in providers]
    providerList = [
        ('Peter Krantz', 'peter.krantz@kb.se'),
        (u'Maria Kadesjö'.encode('utf8'), 'maria.kadesjo@kb.se'),
        ('Katinka Ahlbom', 'katinka.ahlbom@kb.se'),
        ('Greger Bergvall', 'greger.bergvall@kb.se'),
        ('Torsten Johansson', 'torsten.johansson@kb.se')
    ]
    for p in providerList:
        if not p[0] in providers:
            prov = Provider()
            prov.name = p[0].decode('utf8')
            prov.email = p[1]
            db.session.add(prov)
    userList = settings.USER_LIST
    users = Users.query.all()
    users = [u.username for u in users]
    for u in userList:
        if u not in users:
            user = Users()
            user.username = u
            user.role = 1
            db.session.add(user)
    roles = Role.query.all()
    roles = [r.roleName for r in roles]
    roleList = ['admin', 'editor']
    for r in roleList:
        if r not in roles:
            role = Role()
            role.roleName = r
            db.session.add(role)

    db.session.commit()
    return

admin.add_view(UserView(db.session))
admin.add_view(Models(Role, db.session))
admin.add_view(Models(Provider, db.session))
admin.add_view(Models(License, db.session))
admin.add_view(Models(Format, db.session))
admin.add_view(DatasetsView(db.session))
admin.add_view(TorrentView(db.session))
admin.add_view(Models(Sameas, db.session))


def redirect_url(default='index'):
    return request.args.get('next') or \
        request.referrer or \
        url_for(default)


@app.route('/')
def index():
    accepts = request.accept_mimetypes
    best = accepts.best_match([MT_RDF_XML, 'text/html'])
    if best == MT_RDF_XML and accepts[best] > accepts['text/html']:
        return index_rdf()
    else:
        return index_html()


@app.route('/index.html')
def index_html():
    datasets = Datasets.query.options(db.lazyload('sameas')).all()
    return render_template('index.html',
            datasets=datasets,
            datasetRoot=datasetRoot)


@app.route('/index.rdf')
def index_rdf():
    key = index_rdf.__name__
    data = cache.get(key)
    if data is None:
        data = Graph().parse(
            data=index_html(),
            format='rdfa',
            media_type='text/html'
        ).serialize(format='pretty-xml')
        cache.set(key, data, timeout=60 * 60)
    return Response(data, mimetype=MT_RDF_XML)


@app.before_request
def log_request():
    if app.config.get('LOG_REQUESTS'):
        app.logger.debug('whatever')


@app.route('/datasets/<int:year>/<month>/<dataset>/<path:directory>/')
@app.route('/datasets/<int:year>/<month>/<dataset>/')
def viewDataset(year, month, dataset, directory=None):
    datasetPath = path.join(str(year), str(month), dataset)
    dataset = Datasets.query.filter(Datasets.path == datasetPath).first()
    if directory:
        wholePath = path.join(datasetRoot, datasetPath, directory)
        if path.isfile(wholePath):
            return send_file(
                wholePath,
                as_attachment=True,
                attachment_filename=path.basename(wholePath)
            )
    if not dataset:
        return(render_template("error.html",
               message="Could not find dataset"))
    dataset.cleanDate = cleanDate(dataset.updated_at)
    pathDict = {}
    if not dataset.url:
        try:
            pathDict, dirUp, metadata = index_dir(
                directory,
                dataset,
                datasetRoot
            )
            print metadata
        except Exception as e:
            return(render_template("error.html",
                   message="Could not generate index %s" % e))
    if dataset.url:
        pathDict = None
        dirUp = None
    return(
        render_template(
            'dataset.html',
            datasetRoot=datasetRoot,
            dataset=dataset,
            pathDict=pathDict,
            dirUp=dirUp,
            quote=quote,
            metadata=metadata,
            unquote=unquote,
            datasetID=dataset.datasetID
        )
    )


@app.route('/torrent/<torrentID>')
def getTorrent(torrentID):
    torrentFile = StringIO()
    torrent = Torrent.query.filter(Torrent.id == torrentID).first()
    dataset = Datasets.query.filter(
        Datasets.datasetID == torrent.dataset
    ).first()
    filename = '%s.torrent' % dataset.name
    torrentFile.write(torrent.torrentData)
    torrentFile.seek(0)
    return send_file(
        torrentFile,
        as_attachment=True,
        attachment_filename=filename,
        mimetype='application/x-bittorrent'
    )


@app.route('/datasets/<datasetName>')
def viewDatasetURL(datasetName):
    dataset = Datasets.query.filter(Datasets.name == datasetName).first()
    if not dataset:
        return(render_template("error.html",
               message="Could not find dataset"))

    dataset.cleanDate = cleanDate(dataset.updated_at)
    return(
        render_template(
            'dataset.html',
            dataset=dataset,
            dirUp=None,
            pathDict=None
        )
    )


@app.route('/login2')
def login2():
    print request.authorization
    redirectTo = request.args.get('next', '/')
    if appMode == 'dev':
        session['username'] = 'testadmin'
        session['logged_in'] = True
        session['real_name'] = 'Test Admin'
        session['is_admin'] = 'True'
        session['role'] = 'editor'
        return redirect(redirectTo)
    if appMode == 'production':
        if request.authorization:
            session['username'] = request.authorization['username']
            user = Users.query.filter(
                Users.username == session['username']
            ).first()
            if not user:
                session['logged_in'] = False
                return("Couldn't authenticate")
            role = Role.query.filter(
                Role.id == user.role
            ).first()
            session['role'] = role.roleName
            session['logged_in'] = True
        elif request.headers['schacHomeOrganization'] == 'kb.se':
            session['username'] = request.headers['eppn']
            user = Users.query.filter(
                Users.username == session['username']
            ).first()
            if not user:
                session['logged_in'] = False
                return("Couldn't authenticate")
            session['logged_in'] = True
            session['real_name'] = request.headers['displayName']
            role = Role.query.filter(
                Role.id == user.role
            ).first()
            session['role'] = role.roleName
            return redirect(redirectTo)
        else:
            return('Can not authenticate')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/del/confirm/<int:datasetID>')
def confirmDel(datasetID):
    if session.get('logged_in'):
        dataset = Datasets.query.filter(
            Datasets.datasetID == datasetID
        ).first()
        return(render_template(
               'confirm.html', dataset=dataset)
               )


@app.route('/del/<int:datasetID>')
def delDataset(datasetID):
    if session.get('logged_in'):
        try:
            dataset = Datasets.query.filter(
                Datasets.datasetID == datasetID
            ).first()
            db.session.delete(dataset)
            db.session.commit()
            flash('Deleted!')
            return redirect(url_for('index'))
        except Exception as e:
            return(render_template(
                   'error.html', message=e)
                   )


@app.after_request
def add_ua_compat(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge'
    return response

if __name__ == "__main__":
    buildDB()
    app.run(host='0.0.0.0', port=8000, debug=True)
