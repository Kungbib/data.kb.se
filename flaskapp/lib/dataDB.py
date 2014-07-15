from sqlite3 import connect as sqconnect
from datetime import datetime
from flask import g
from os import path, listdir
from mimetypes import guess_type
from time import time
from urllib2 import quote


with open('./secrets', 'r') as sfile:
    salt = sfile.read()

dbFile = ('./data.db')


def cleanDate(timestamp):
    timeTup = datetime.fromtimestamp(timestamp)
    dateFormat = '%Y-%m-%d %H:%M'
    return(timeTup.strftime(dateFormat))


def sizeof_fmt(num):
    for x in ['bytes', 'kB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


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


def create_dataset(formdata):
    #try:
        librisIDs = formdata['librisIDs'].split(',')
        encodingFormats = formdata['encodingFormats'].split(',')
        cur = get_db().cursor()
        cur.execute('''
            INSERT INTO datasets
            (type, name, description, license, path, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', (
            formdata['type'],
            formdata['title'],
            formdata['description'],
            formdata['license'],
            formdata.get('path', None),
            formdata.get('url', None),
            time()
            )
        )
        datasetID = cur.lastrowid
        for librisID in librisIDs:
            cur.execute('''
                INSERT INTO sameAs
                (datasetID, librisID)
                VALUES
                (?, ?)''', (
                datasetID, librisID.strip()
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
            INSERT INTO provider
            (datasetID, name, email)
            VALUES (?, ?, ?)''', (
            datasetID, formdata['name'], formdata['email']
            )
        )
        get_db().commit()
    #except Exception as e:
        #return("Couldn't create dataset: %s" % e)


def update_dataset(formdata, datasetID):
    #try:
        librisIDs = formdata['librisIDs'].split(',')
        encodingFormats = formdata['encodingFormats'].split(',')
        cur = get_db().cursor()
        cur.execute('''
            UPDATE datasets
            SET type = ?, name = ?, description = ?, license = ?, path = ?, url = ?,
            updated_at = ?
            WHERE datasetID=?''', (
            formdata['type'],
            formdata['title'],
            formdata['description'],
            formdata['license'],
            formdata.get('path', None),
            formdata.get('url', None),
            time(),
            datasetID
            )
        )
        cur.execute('''
            DELETE from sameAs WHERE
            datasetID = ?''', (datasetID, )
        )
        for librisID in librisIDs:
            cur.execute('''
                INSERT INTO sameAs
                (datasetID, librisID)
                VALUES
                (?, ?)''', (
                datasetID, librisID.strip()
                )
            )
        cur.execute('''
            DELETE from distribution
            WHERE datasetID = ?''', (datasetID, )
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
            UPDATE provider
            SET name = ?, email = ?
            WHERE datasetID = ?''', (
            formdata['name'], formdata['email'], datasetID
            )
        )
        get_db().commit()
    #except Exception as e:


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
        DELETE from provider WHERE
        datasetID = ?''', (
        datasetid,
        )
    )
    get_db().commit()


def loadDatasetsDB(datasetID=None, **kw):
    datasetList = []
    cur = get_db().cursor()
    if datasetID is None and kw.get('singleLookup', False) is False:
        cur.execute('''SELECT * from datasets''')
        datasets = cur.fetchall()
    elif kw.get('singleLookup'):
        if kw.get('datasetPath'):
            cur.execute(
                '''SELECT * from datasets WHERE
                    path = ?''', (kw.get('datasetPath'), )
            )
        elif kw.get('datasetName'):
            cur.execute(
                '''SELECT * from datasets WHERE
                   name = ?''', (kw.get('datasetName'), )
            )
        elif kw.get('useID', False):
            cur.execute(
               '''SELECT * from datasets WHERE
                  datasetID = ?''', (datasetID, )
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
            dataset['sameAs'].append(librisID['librisid'])
        cur.execute(
            '''
            SELECT encodingFormat from distribution WHERE
            datasetID = ?''', (dataset['datasetID'], )
        )
        formats = cur.fetchall()
        dataset['distribution'] = {}
        dataset['distribution']['encodingFormat'] = []
        for format in formats:
            dataset['distribution']['encodingFormat'].append(format['encodingFormat'])
        cur.execute(
            '''
            SELECT name, email FROM provider WHERE
            datasetID = ?''', (dataset['datasetID'], )
        )
        provider = cur.fetchone()
        dataset['provider'] = {
            'name': provider['name'],
            'email': provider['email']
        }
        datasetList.append(dataset)
    return datasetList


def index_dir(directory, dataset, datasetRoot):
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
                pathDict[f]['realPath'] = path.join(
                    datasetRoot,
                    directory,
                    quote(f)
                )
                pathDict[f]['type'] = 'file'
                pathDict[f]['size'] = sizeof_fmt(path.getsize(fullPath))
            if path.isdir(fullPath):
                pathDict[f] = {}
                pathDict[f]['name'] = f
                pathDict[f]['mimetype'] = '-'
                pathDict[f]['type'] = 'folder-open'
                pathDict[f]['size'] = '-'
    return(pathDict, dirUp)
