import data
import unittest
from lib.dbShared import db
from testfixtures import TempDirectory
import lib.models


class RouteTests(unittest.TestCase):
    def setUp(self):
        data.app.config['TESTING'] = True
        data.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        data.app.config['USER_LIST'] = ['Test Admin']
        db.init_app(data.app)
        d = TempDirectory()
        d.makedir('2015/05/myDataset')
        d.write('2015/05/myDataset/files/testfile.jpg', 'abc')
        d.write('2015/05/myDataset/testfile2.jpg', 'abc')
        self.directory = d
        data.app.config['DATASET_ROOT'] = d.path
        with data.app.app_context(), TempDirectory() as d:
            db.create_all()
            lib.models.buildDB()
            license = lib.models.License.query.first()
            provider = lib.models.Provider.query.first()
            dataset = lib.models.Datasets()
            dataset.name = 'My Test Dataset'
            dataset.license = [license]
            dataset.provider = [provider]
            dataset.path = "2015/05/myDataset"
            db.session.add(dataset)
            db.session.commit()
        self.app = data.app.test_client()

    def test_index(self):
        res = self.app.get('/')
        self.assertIn('My Test Dataset', res.data)
        self.assertIn('/datasets/2015/05/myDataset', res.data)

    def test_dataset_mainpage(self):
        res = self.app.get(
            '/datasets/2015/05/myDataset',
            follow_redirects=True
        )
        self.assertIn('My Test Dataset', res.data)
        self.assertIn('./testfile2.jpg', res.data)
        self.assertIn('./files', res.data)
        self.assertIn('image/jpeg', res.data)

    def test_dataset_with_subfolder(self):
        res = self.app.get(
            '/datasets/2015/05/myDataset/files',
            follow_redirects=True
        )
        self.assertIn('My Test Dataset', res.data)
        self.assertIn('./testfile.jpg', res.data)
        self.assertIn('image/jpeg', res.data)

    def test_dataset_does_not_exist_is_handeled(self):
        res = self.app.get(
            '/datasets/2014/04/idonotexist',
            follow_redirects=True
        )
        self.assertIn('Could not find dataset', res.data)

    def test_malformed_dataset_is_handled(self):
        res = self.app.get('/datasets/idonotexist', follow_redirects=True)
        self.assertIn('Could not find dataset', res.data)

    def test_logon_dev_mode(self):
        data.app.config['APP_ENV'] = 'Test'
        res = self.app.get('/login2', follow_redirects=True)
        self.assertIn('Test Admin', res.data)

    def tearDown(self):
        self.directory.cleanup()
