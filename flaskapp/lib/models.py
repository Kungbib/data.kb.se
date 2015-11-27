#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from flask import current_app, session
from dbShared import db


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


def buildDB():
    formats = Format.query.all()
    formats = [f.name for f in formats]
    excpectedFormats = [
        u'TIFF',
        u'JPEG',
        u'DOC',
        u'PDF',
        u'JPEG2000',
        u'MARC-21',
        u'RDF/XML',
        u'Turtle',
        u'XML'
    ]
    for f in excpectedFormats:
        if f not in formats:
            form = Format()
            form.name = f
            db.session.add(form)
    licenses = License.query.all()
    licenses = [l.name for l in licenses]
    licneseTemp = [
        (u'http://creativecommons.org/publicdomain/zero/1.0/', u'CC0')
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
        (u'Peter Krantz', u'peter.krantz@kb.se'),
        (u'Maria Kadesjo', u'maria.kadesjo@kb.se'),
        (u'Katinka Ahlbom', u'katinka.ahlbom@kb.se'),
        (u'Greger Bergvall', u'greger.bergvall@kb.se'),
        (u'Torsten Johansson', u'torsten.johansson@kb.se')
    ]
    for p in providerList:
        if not p[0] in providers:
            prov = Provider()
            prov.name = p[0].decode('utf8')
            prov.email = p[1]
            db.session.add(prov)
    userList = current_app.config.get('USER_LIST')
    users = Users.query.all()
    users = [u.username for u in users]
    for u in userList:
        if u not in users:
            user = Users()
            user.username = unicode(u)
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
