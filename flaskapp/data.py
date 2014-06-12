#!/usr/bin/env python

if __name__ != '__main__':
    from sys import path as syspath
    from os import path, chdir
    syspath.append(path.dirname(__file__))
    chdir(path.dirname(__file__))

from flask import Flask, request, render_template
from sqlite3 import connect as sqconnect
from yaml import load as yload
from autobp import auto_bp, datasetRoot
from os import path


app = Flask(__name__)
app.register_blueprint(auto_bp, url_prefix='/datasets')
gconn = sqconnect('./data.db')


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

gconn.row_factory = dict_factory


def _create_db():
    lconn = sqconnect('./data.db')
    cur = lconn.cursor()
    cur.execute('''
        CREATE TABLE
        datasets(
        datasetID INT PRIMARY KEY,
        type TEXT,
        name TEXT,
        description TEXT,
        license TEXT,
        PATH text)
    ''')
    lconn.commit()
    cur.execute('''
        CREATE TABLE
        sameAs(
        sameAsID INT PRIMARY KEY,
        datasetID INT,
        librisid TEXT)
    ''')
    lconn.commit()
    cur.execute('''
        CREATE TABLE
        distribution(
        distID INT PRIMARY KEY,
        datasetID INT,
        encodingFormatID INT)
    ''')
    lconn.commit()
    cur.execute('''
        CREATE TABLE
        providor(
        prodvidorID, INT PRIMARY KEY
        datasetID INT,
        name TEXT,
        email TEXT)
    ''')
    lconn.commit()
    cur.close()

try:
    _create_db()
except Exception as e:
    print("Could not create database: %s" % e)


def create_dataset(formdata):
#    try:
        conn = sqconnect('./data.db')
        librisIDs = formdata['librisIDs'].split(',')
        encodingFormats = formdata['encodingFormats'].split(',')
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO datasets
            VALUES (?, ?, ?, ?, ?, ?)''', (
            None,
            formdata['type'],
            formdata['title'],
            formdata['description'],
            formdata['license'],
            formdata['path']
            )
        )
        conn.commit()
        datasetID = cur.lastrowid
        for librisID in librisIDs:
            cur.execute('''
                INSERT INTO sameAs VALUES
                (?, ?, ?)''', (
                None, datasetID, librisID
                )
            )
            conn.commit()
        for format in encodingFormats:
            cur.execute('''
                INSERT INTO distribution
                VALUES (?, ?, ?)''', (
                None, datasetID, format
                )
            )
            conn.commit()
        cur.execute('''
            INSERT INTO providor
            VALUES (?, ?, ?, ?)''', (
            None, datasetID, formdata['name'], formdata['email']
            )
        )
        conn.commit()
#    except Exception as e:
#        print("Couldn't create dataset: %s" % e)


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

datasets, datasetPaths = loadDatasets()


def loadDatasetsDB():
    datasetList = []
    cur = gconn.cursor()
    cur.execute('''SELECT * from datasets''')
    datasets = cur.fetchall()
    for dataset in datasets:
        print dataset
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

print loadDatasetsDB()


@app.route('/')
def index():
    print datasets
    return(
        render_template(
            'index.html',
            datasets=datasets,
            datasetRoot=datasetRoot
        )
    )


@app.route('/new', methods=['GET', 'POST'])
def addDataset():
    if request.method == 'GET':
        return(render_template('newform.html'))
    if request.method == 'POST':
        create_dataset(request.form)
        return('Created!')

if __name__ == "__main__":
    app.run(debug=True)
