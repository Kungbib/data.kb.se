#!/usr/bin/env python

if __name__ != '__main__':
    from sys import path as syspath
    from os import path, chdir
    syspath.append(path.dirname(__file__))
    chdir(path.dirname(__file__))

from flask import (
    Flask, request,
    render_template, session,
    redirect, g, url_for,
    flash
)
from sqlite3 import connect as sqconnect
from yaml import load as yload
#from autobp import auto_bp, datasetRoot
#from flask.ext.autoindex import AutoIndex
from os import path, listdir
from mimetypes import guess_type
from hashlib import sha512
from uuid import uuid4
from datetime import datetime


app = Flask(__name__)
#AutoIndex(app, browse_root=path.curdir)
datasetRoot = './datasets'
#app.register_blueprint(auto_bp, url_prefix='/datasets')
dbFile = ('./data.db')
app.secret_key = uuid4().hex

with open('./secrets', 'r') as sfile:
    salt = sfile.read()


def redirect_url(default='index'):
    return request.args.get('next') or \
        request.referrer or \
        url_for(default)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqconnect(dbFile)
    db.row_factory = dict_factory
    return db


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def create_dataset(formdata):
#    try:
        librisIDs = formdata['librisIDs'].split(',')
        encodingFormats = formdata['encodingFormats'].split(',')
        cur = get_db().cursor()
        print formdata.get('url', None)
        print formdata.get('path', None)
        cur.execute('''
            INSERT INTO datasets
            (type, name, description, license, path, url)
            VALUES (?, ?, ?, ?, ?, ?)''', (
            formdata['type'],
            formdata['title'],
            formdata['description'],
            formdata['license'],
            formdata.get('path', None),
            formdata.get('url', None)
            )
        )
        datasetID = cur.lastrowid
        for librisID in librisIDs:
            cur.execute('''
                INSERT INTO sameAs
                (datasetID, librisID)
                VALUES
                (?, ?)''', (
                datasetID, librisID
                )
            )
        for format in encodingFormats:
            cur.execute('''
                INSERT INTO distribution
                (datasetID, encodingFormat)
                VALUES (?, ?)''', (
                datasetID, format
                )
            )
        cur.execute('''
            INSERT INTO providor
            (datasetID, name, email)
            VALUES (?, ?, ?)''', (
            datasetID, formdata['name'], formdata['email']
            )
        )
        get_db().commit()
#    except Exception as e:
#        return("Couldn't create dataset: %s" % e)


def del_dataset(datasetid):
    cur = get_db().cursor()
    cur.execute('''
        DELETE from datasets WHERE
        datasetID = ?''', (
        datasetid,
        )
    )
    cur.execute('''
        DELETE from sameAs WHERE
        datasetID = ?''', (
        datasetid,
        )
    )
    cur.execute('''
        DELETE from distribution WHERE
        datasetID = ?''', (
        datasetid,
        )
    )
    cur.execute('''
        DELETE from providor WHERE
        datasetID = ?''', (
        datasetid,
        )
    )
    get_db().commit()


def update_dataset(updateDict):
    cur = get_db().cursor()
    datasetID = updateDict['datasetid']
    datasetDict = updateDict['dataset']
#    sameAsDict = updateDict['sameAs']
#    formatDict = updateDict['formats']
    cur.execute('''
        UPDATE dataset SET
        description=?, name=?, license=?,
        type=?, path=?, url=?, updated=?
        WHERE
        datasetID=?
        ''', (
        datasetDict.get('description'),
        datasetDict.get('name'),
        datasetDict.get('license'),
        datasetDict.get('type'),
        datasetDict.get('path', None),
        datasetDict.get('url', None),
        datetime.now(),
        datasetID
        )
    )


def loadDatasets():
    datasets = []
    datasetFile = yload(open('datasets.yml', 'r'))
    for dataset in datasetFile['datasets']:
        try:
            data = yload(
                open(path.join(
                    datasetRoot,
                    dataset,
                    'index.yaml')
                )
            )
            data['path'] = dataset
            datasets.append(data)
        except:
            pass
    return(datasets, datasetFile)


def loadDatasetsDB(datasetID=None):
    datasetList = []
    cur = get_db().cursor()
    if datasetID is None:
        cur.execute('''SELECT * from datasets''')
        datasets = cur.fetchall()
    elif datasetID is not None:
        cur.execute(
            '''SELECT * from datasets WHERE
                ROWID = ?''', (datasetID, )
        )
        datasets = cur.fetchall()
    for dataset in datasets:
        cur.execute(
            '''
            SELECT librisID from sameAs WHERE
            datasetID = ?''', (dataset['datasetID'], )
        )
        dataset['sameAs'] = []
        librisIDs = cur.fetchall()
        for librisID in librisIDs:
            dataset['sameAs'].append(librisID)
        #cur.execute(
        #    '''
        #    SELECT format from distribution WHERE
        #    datasetID = ?''', (dataset['datasetID'], )
        #)
        #formats = cur.fetchall()
        formats = []
        dataset['distribution'] = {}
        dataset['distribution']['encodingFormat'] = []
        for format in formats:
            dataset['distribution']['encodingFormat'].append(format)
        cur.execute(
            '''
            SELECT name, email FROM providor WHERE
            datasetID = ?''', (dataset['datasetID'], )
        )
        providor = cur.fetchone()
        dataset['providor'] = {
            'name': providor['name'],
            'email': providor['email']
        }
        datasetList.append(dataset)
    return datasetList

#for dataset in loadDatasetsDB():
#        datasets.append(dataset)


def _index_dir(directory, dataset):
    dTemp = directory
    pathDict = {}
    if directory is None and dataset['path'] != '':
        directory = dataset['path']
    if directory != dataset['path']:
        directory = path.join(dataset['path'], directory)
    if directory is not None:
        if directory != dataset['path'] and dTemp is not None:
            dirUp = path.split(dTemp)[0]
        if directory == dataset['path']:
            dirUp = None
        for f in listdir(path.join(datasetRoot, directory)):
            fullPath = path.join(datasetRoot, directory, f)
            if path.isfile(fullPath):
                pathDict[f] = {}
                pathDict[f]['mimetype'] = guess_type(fullPath)[0]
                pathDict[f]['name'] = f
                pathDict[f]['realPath'] = fullPath
                pathDict[f]['type'] = 'file'
                pathDict[f]['size'] = sizeof_fmt(path.getsize(fullPath))
            if path.isdir(fullPath):
                pathDict[f] = {}
                pathDict[f]['name'] = f
                pathDict[f]['mimetype'] = '-'
                pathDict[f]['type'] = 'folder-open'
                pathDict[f]['size'] = '-'
    return(pathDict, dirUp)


@app.route('/')
def index():
#    datasets = []
    print request.accept_languages
    datasets, datasetPaths = loadDatasets()
    for dataset in loadDatasetsDB():
        datasets.append(dataset)
    return(
        render_template(
            'index.html',
            datasets=datasets,
            datasetRoot=datasetRoot
        )
    )


@app.route('/dset/<int:datasetID>/<path:directory>/')
@app.route('/dset/<int:datasetID>/')
def viewDataset(datasetID, directory=None):
    dataset = loadDatasetsDB(datasetID)
    if len(dataset) > 0:
        dataset = dataset[0]
    else:
        return(render_template("error.html",
               message="Could not find dataset"))
    pathDict = {}
    if dataset['url'] == '':
        try:
            pathDict, dirUp = _index_dir(directory, dataset)
        except:
            return(render_template("error.html",
                   message="Could not generate index"))
    if dataset['url'] != '':
        pathDict = None
        dirUp = None
    return(
        render_template(
            'dataset.html',
            dataset=dataset,
            pathDict=pathDict,
            dirUp=dirUp,
            datasetID=datasetID
        )
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        pwHashed = sha512(password + salt).hexdigest()
        cur = get_db().cursor()
        cur.execute('SELECT * from users where username = ?', (username, ))
        res = cur.fetchone()
        if res['password'] == pwHashed:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid password!'
    return(render_template('login.html', error=error))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/new', methods=['GET', 'POST'])
def addDataset():
    if request.method == 'GET':
        if not session.get('logged_in'):
            return(render_template("error.html",
                   message="You must be logged in!"))
        if session.get('logged_in'):
            return(render_template('newform.html', dataset=None))
    if request.method == 'POST':
        if session.get('logged_in'):
            create_dataset(request.form)
            flash('Created!')
            return redirect(url_for('index'))
        else:
            return(render_template("error.html",
                   message="You must be logged in!"))


@app.route('/del/confirm/<int:datasetID>')
def confirmDel(datasetID):
    if session.get('logged_in'):
        cur = get_db().cursor()
        cur.execute('SELECT * FROM datasets where datasetid=?', (datasetID, ))
        dataset = cur.fetchone()
        return(render_template(
               'confirm.html', dataset=dataset)
               )


@app.route('/del/<int:datasetID>')
def delDataset(datasetID):
    if session.get('logged_in'):
        try:
            del_dataset(datasetID)
            flash('Deleted!')
            return redirect(url_for('index'))
        except Exception as e:
            return(render_template(
                   'error.html', message=e)
                   )


@app.route('/edit/<int:datasetID>')
def editDataset(datasetID):
    dataset = loadDatasetsDB(datasetID)
    dataset = dataset[0]
    print type(dataset)
    return render_template('newform.html', dataset=dataset)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9443, debug=True)
