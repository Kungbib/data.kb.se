import data
import unittest
from lib.dbShared import db
from testfixtures import TempDirectory
import lib.models


class RdfTests(unittest.TestCase):
    def setUp(self):
        data.app.config['TESTING'] = True
        data.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        data.app.config['USER_LIST'] = ['Test Admin']
        db.init_app(data.app)
        d = TempDirectory()
        d.makedir('dataset')
        d.write('dataset/files/testfile.jpg', 'abc')
        d.write('dataset/testfile2.jpg', 'abc')
        self.directory = d
        data.app.config['DATASET_ROOT'] = d.path
        with data.app.app_context(), TempDirectory() as d:
            db.create_all()
            lib.models.buildDB()
            license = lib.models.License.query.first()
            provider = lib.models.Provider.query.first()
            dataset = lib.models.Datasets()
            dataset.name = 'Test'
            dataset.license = [license]
            dataset.provider = [provider]
            dataset.path = "dataset"
            db.session.add(dataset)
            db.session.commit()
        self.app = data.app.test_client()

    def tearDown(self):
        self.directory.cleanup()
