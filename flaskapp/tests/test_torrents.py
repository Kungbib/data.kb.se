from flask import Flask
import lib.models
import lib.torrents
import unittest
from testfixtures import TempDirectory
from lib.dbShared import db
from makeTorrent import makeTorrent


class TestTorrents(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['USER_LIST'] = ['Test Admin']
        db.init_app(self.app)
        d = TempDirectory()
        d.makedir('dataset')
        d.write('dataset/files/testfile.jpg', 'abc')
        d.write('dataset/testfile2.jpg', 'abc')
        self.directory = d
        self.app.config['DATASET_ROOT'] = d.path
        with self.app.app_context(), TempDirectory() as d:
            db.create_all()
            lib.models.buildDB()
            dataset = lib.models.Datasets()
            dataset.name = 'Test'
            dataset.path = "dataset"
            db.session.add(dataset)
            db.session.commit()

    def test_add_torrent_to_model(self):
        with self.app.app_context():
            dataset = lib.models.Datasets.query.first()
            mk = makeTorrent(announce='http://kb.se')
            mk.multi_file('{}/{}'.format(dataset.path, 'dataset'))
            torrent_model = lib.models.Torrent()
            torrent_model.datasetID = dataset.datasetID
            db.session.add(torrent_model)
            torrent_model = lib.torrents._add_torrent_to_model(
                torrent_model, mk
            )
            db.session.commit()
            self.assertEqual(mk.info_hash(), torrent_model.infoHash)
            self.assertEqual(torrent_model.datasetID, 1)
            self.assertEqual(torrent_model.torrentData, mk.getBencoded())
            self.assertIsNotNone(torrent_model.updated_at)

    def test_add_torrent_method_without_announce(self):
        with self.app.app_context():
            torrent_model = lib.models.Torrent()
            exceptText = "ANNOUNCE is required to create torrents"
            with self.assertRaisesRegexp(KeyError, exceptText):
                lib.torrents.add_torrent(torrent_model, 1)

    def test_add_torrent_method(self):
        with self.app.app_context():
            self.app.config['ANNOUNCE'] = 'http://kb.se'
            torrent_model = lib.models.Torrent()
            torrent_model = lib.torrents.add_torrent(torrent_model, 1)
            self.assertEqual(
                torrent_model.infoHash,
                'cf3010468fd2c2f048d2fd3162bcdcc937fcb06f'
            )

    def tearDown(self):
        self.directory.cleanup()
