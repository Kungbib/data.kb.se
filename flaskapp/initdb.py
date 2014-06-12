#!/usr/bin/env python
from sqlite3 import connect as sqconnect


def _create_db():
    lconn = sqconnect('./data.db')
    cur = lconn.cursor()
    cur.execute('''
        CREATE TABLE
        datasets(
        datasetID INTEGER PRIMARY KEY not null,
        type TEXT,
        name TEXT,
        description TEXT,
        license TEXT,
        path text)
    ''')
    lconn.commit()
    cur.execute('''
        CREATE TABLE
        sameAs(
        sameAsID INTEGER PRIMARY KEY not null,
        datasetID INT,
        librisid TEXT)
    ''')
    lconn.commit()
    cur.execute('''
        CREATE TABLE
        distribution(
        distID INTEGER PRIMARY KEY not null,
        datasetID INT,
        encodingFormat TEXT)
    ''')
    lconn.commit()
    cur.execute('''
        CREATE TABLE
        providor(
        prodvidorID INTEGER PRIMARY KEY not null,
        datasetID INT,
        name TEXT,
        email TEXT)
    ''')
    lconn.commit()
    cur.close()

try:
    _create_db()
    print("Database initialized")
except Exception as e:
    print("Could not initialize database: %s" % e)
