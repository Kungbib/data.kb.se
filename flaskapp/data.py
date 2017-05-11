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
from lib.dataDB import directory_indexer, cleanDate, get_size
from flask.ext.admin.contrib.sqla import ModelView
from urllib2 import quote, unquote
from werkzeug.contrib.cache import SimpleCache
from rdflib import Graph
from lib import views
from lib import models
from lib import logon
from lib.dbShared import db
from StringIO import StringIO

MT_RDF_XML = 'application/rdf+xml'
APP_BASE_URI = 'https://data.kb.se/'

cache = SimpleCache()
app = Flask(__name__)
admin = Admin(app, base_template='admin/base_admin.html')
app.config.from_pyfile('settings.py')
db.init_app(app)
curDir = path.dirname(path.realpath(__file__))
secretsFile = path.join(curDir, 'secrets')
with open(secretsFile, 'r') as sfile:
    app.secret_key = sfile.read()
    salt = app.secret_key

with app.app_context():
    dirIndex = directory_indexer()
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


admin.add_view(views.UserView(db.session))
admin.add_view(Models(models.Role, db.session))
admin.add_view(Models(models.Provider, db.session))
admin.add_view(Models(models.License, db.session))
admin.add_view(Models(models.Format, db.session))
admin.add_view(views.DatasetsView(db.session))
admin.add_view(views.TorrentView(db.session))
admin.add_view(Models(models.Sameas, db.session))


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
    datasets = models.Datasets.query.options(db.lazyload('sameas')).all()
    return render_template(
        'index.html',
        datasets=datasets,
        datasetRoot=app.config['DATASET_ROOT']
    )


@app.route('/index.rdf')
def index_rdf():
    key = index_rdf.__name__
    data = cache.get(key)
    if data is None:
        data = Graph().parse(
            data=index_html(),
            publicID=APP_BASE_URI,
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
    datasetRoot = app.config['DATASET_ROOT']
    datasetPath = path.join(str(year), str(month), dataset)
    #datasetSize = get_size(start_path=path.join(datasetRoot, datasetPath))
    dataset = models.Datasets.query.filter(
        models.Datasets.path == datasetPath
    ).first()
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
               message="Could not find dataset2"))
    dataset.cleanDate = cleanDate(dataset.updated_at)
    pathDict = {}
    if not dataset.url:
        try:
            pathDict, dirUp, metadata = index_dir(
                directory,
                dataset
            )
        except Exception as e:
            return(render_template("error.html",
                   message="Could not generate index %s" % e))
    if dataset.url:
        pathDict = None
        dirUp = None

    # shuld use @memoize instead
    key=path.join(datasetRoot, datasetPath)
    datasetSize = cache.get(key)
    if datasetSize is None:
        datasetSize = get_size(start_path=path.join(datasetRoot, datasetPath))
        cache.set(key, datasetSize, 60*60)

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
            datasetID=dataset.datasetID,
            datasetSize=datasetSize
        )
    )


@app.route('/torrent/<torrentID>')
def getTorrent(torrentID):
    torrentFile = StringIO()
    torrent = models.Torrent.query.filter(
        models.Torrent.id == torrentID
    ).first()
    dataset = models.Datasets.query.filter(
        models.Datasets.datasetID == torrent.dataset
    ).first()
    filename = '%s.torrent' % path.basename(dataset.path)
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
    dataset = models.Datasets.query.filter(
        models.Datasets.name == datasetName
    ).first()
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
    return(logon.handle_logon())


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/del/confirm/<int:datasetID>')
def confirmDel(datasetID):
    if session.get('logged_in'):
        dataset = models.Datasets.query.filter(
            models.Datasets.datasetID == datasetID
        ).first()
        return(render_template('confirm.html', dataset=dataset))


@app.route('/del/<int:datasetID>')
def delDataset(datasetID):
    if session.get('logged_in'):
        try:
            dataset = models.Datasets.query.filter(
                models.Datasets.datasetID == datasetID
            ).first()
            db.session.delete(dataset)
            db.session.commit()
            flash('Deleted!')
            return redirect(url_for('index'))
        except Exception as e:
            return(render_template('error.html', message=e))


@app.after_request
def add_ua_compat(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge'
    return response

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        models.buildDB()
    app.run(host='0.0.0.0', port=8000)
