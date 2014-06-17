#!/usr/bin/env python

if __name__ != '__main__':
    from sys import path as syspath
    from os import path, chdir
    syspath.append(path.dirname(__file__))
    chdir(path.dirname(__file__))

from flask import Flask, request, render_template, g
from sqlite3 import connect as sqconnect
from yaml import load as yload
#from autobp import auto_bp, datasetRoot
#from flask.ext.autoindex import AutoIndex
from os import path, listdir
from mimetypes import guess_type


app = Flask(__name__)
#AutoIndex(app, browse_root=path.curdir)
datasetRoot = './datasets'
#app.register_blueprint(auto_bp, url_prefix='/datasets')
dbFile = ('./data.db')


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
        return(
            render_template(
                "error.html",
                message="Could not find dataset"
            )
        )
    pathDict = {}
    if dataset['url'] == '':
        try:
            pathDict, dirUp = _index_dir(directory, dataset)
        except:
            return(
                render_template(
                    "error.html",
                    message="Could not generate index",
                )
            )
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


@app.route('/new', methods=['GET', 'POST'])
def addDataset():
    if request.method == 'GET':
        return(render_template('newform.html'))
    if request.method == 'POST':
        create_dataset(request.form)
        return('Created!')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9443, debug=True)
