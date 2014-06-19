#!/usr/bin/env python
from sqlite3 import connect as sqconnect
from uuid import uuid4
from hashlib import sha512
from optparse import OptionParser

opts = OptionParser()
opts.add_option(
    '-i', '--init-db', dest='initdb',
    action='store_true', default=False,
    help="Initialize the database"
)
opts.add_option(
    '-r', '--reset-admin', dest='resetadmin',
    action='store_true', default=False,
    help="Reset admin password"
)
opts.add_option(
    '-p', '--admin--password', dest='adminpw',
    metavar='adminpw', default=None,
    help="Admin password, if none is provided a random will be generated"
)

(options, args) = opts.parse_args()
salt = uuid4().hex
with open('./secrets', 'r') as sfile:
    salt = sfile.read()
if options.adminpw is None:
    adminPW = uuid4().hex
else:
    adminPW = options.adminpw

adminPWhashed = sha512(adminPW + salt).hexdigest()

if not options.resetadmin and not options.initdb and options.adminpw is None:
    opts.print_help()


def _create_db():
    lconn = sqconnect('./data.db')
    cur = lconn.cursor()
    try:
        cur.execute('''
            CREATE TABLE
            datasets(
            datasetID INTEGER PRIMARY KEY not null,
            type TEXT,
            name TEXT,
            description TEXT,
            license TEXT,
            path text,
            url text)
        ''')
        lconn.commit()
    except Exception as e:
        print(e)
    try:
        cur.execute('''
            CREATE TABLE
            sameAs(
            sameAsID INTEGER PRIMARY KEY not null,
            datasetID INT,
            librisid TEXT)
        ''')
        lconn.commit()
    except Exception as e:
        print(e)
    try:
        cur.execute('''
            CREATE TABLE
            distribution(
            distID INTEGER PRIMARY KEY not null,
            datasetID INT,
            encodingFormat TEXT)
        ''')
        lconn.commit()
    except Exception as e:
        print(e)
    try:
        cur.execute('''
            CREATE TABLE
            providor(
            prodvidorID INTEGER PRIMARY KEY not null,
            datasetID INT,
            name TEXT,
            email TEXT)
        ''')
    except Exception as e:
        print(e)
    try:
        cur.execute('''
            CREATE TABLE
            users(
            userID INTEGER PRIMARY KEY not null,
            username text unique,
            password text
            )
        ''')
        lconn.commit()
    except Exception as e:
        print(e)
    try:
        cur.execute('''
            INSERT INTO users
            (username, password)
            VALUES
            (?, ?)
            ''', ('admin', adminPWhashed)
        )
        lconn.commit()
        print("Admin password: %s" % adminPW)
    except Exception as e:
        print(e)
    cur.close()
if options.initdb is True:
    try:
        _create_db()
        print("Database initialized")
    except Exception as e:
        print("Could not initialize database: %s" % e)

if options.resetadmin is True:
    try:
        conn = sqconnect('./data.db')
        cur = conn.cursor()
        cur.execute('''
            UPDATE users
            SET password=?
            WHERE ROWID=1
        ''', (adminPWhashed, )
        )
        conn.commit()
        print("Admin password reset to %s" % adminPW)
    except Exception as e:
        print("Could not reset admin password %s" % e)
