import unittest
import mock
import lib.dataDB
from flask import Flask
from testfixtures import TempDirectory


class DirectoryTest(unittest.TestCase):
    def test_directorybuilder_root(self):
        app = Flask(__name__)
        app.config['SUMMARIZE_METS'] = 'FALSE'
        dataset = mock.PropertyMock
        dataset.path = 'AFTONBLADET'
        with TempDirectory() as d:
            expects = {
                'testImage.jpg': {
                    'mimetype': 'image/jpeg',
                    'realPath':  '%s/AFTONBLADET/testImage.jpg' % d.path,
                    'type': 'file',
                    'name': 'testImage.jpg',
                    'size': '3.0 bytes'
                },
                'testPDF.pdf': {
                    'mimetype': 'application/pdf',
                    'realPath':  '%s/AFTONBLADET/testPDF.pdf' % d.path,
                    'type': 'file',
                    'name': 'testPDF.pdf',
                    'size': '3.0 bytes'
                },
                'testdir': {
                    'mimetype': '-',
                    'type': 'folder-open',
                    'name': 'testdir',
                    'size': '-'
                }
            }
            app.config['DATASET_ROOT'] = d.path
            d.makedir('AFTONBLADET/testdir')
            d.write('AFTONBLADET/testImage.jpg', 'AAA')
            d.write('AFTONBLADET/testPDF.pdf', 'AAA')
            with app.app_context():
                dirIndex = lib.dataDB.directory_indexer()
                indexed, dirup, md = dirIndex.index_dir(None, dataset)
            self.assertEqual(expects, indexed)
            self.assertIsNone(md)
            self.assertIsNone(dirup)

    def test_directorybuilder_sub_folder(self):
        app = Flask(__name__)
        app.config['SUMMARIZE_METS'] = 'FALSE'
        dataset = mock.PropertyMock
        dataset.path = 'AFTONBLADET'
        with TempDirectory() as d:
            expects = {
                'testImage.jpg': {
                    'mimetype': 'image/jpeg',
                    'realPath':  '%s/AFTONBLADET/testdir/testImage.jpg' % d.path,
                    'type': 'file',
                    'name': 'testImage.jpg',
                    'size': '3.0 bytes'
                },
                'testPDF.pdf': {
                    'mimetype': 'application/pdf',
                    'realPath':  '%s/AFTONBLADET/testdir/testPDF.pdf' % d.path,
                    'type': 'file',
                    'name': 'testPDF.pdf',
                    'size': '3.0 bytes'
                }
            }
            app.config['DATASET_ROOT'] = d.path
            d.makedir('AFTONBLADET/testdir')
            d.write('AFTONBLADET/testdir/testImage.jpg', 'AAA')
            d.write('AFTONBLADET/testdir/testPDF.pdf', 'AAA')
            with app.app_context():
                dirIndex = lib.dataDB.directory_indexer()
                indexed, dirup, md = dirIndex.index_dir('testdir', dataset)
            self.assertEqual(expects, indexed)
            self.assertIsNone(md)
            self.assertEquals(dirup, '')

    def test_directorybuilder_with_secon_level_sub_folder(self):
        app = Flask(__name__)
        app.config['SUMMARIZE_METS'] = 'FALSE'
        dataset = mock.PropertyMock
        dataset.path = 'AFTONBLADET'
        with TempDirectory() as d:
            expects = {
                'testImage.jpg': {
                    'mimetype': 'image/jpeg',
                    'realPath':  '%s/AFTONBLADET/testdir/sub/testImage.jpg' % d.path,
                    'type': 'file',
                    'name': 'testImage.jpg',
                    'size': '3.0 bytes'
                },
                'testPDF.pdf': {
                    'mimetype': 'application/pdf',
                    'realPath':  '%s/AFTONBLADET/testdir/sub/testPDF.pdf' % d.path,
                    'type': 'file',
                    'name': 'testPDF.pdf',
                    'size': '3.0 bytes'
                }
            }
            app.config['DATASET_ROOT'] = d.path
            d.makedir('AFTONBLADET/testdir/sub')
            d.write('AFTONBLADET/testdir/sub/testImage.jpg', 'AAA')
            d.write('AFTONBLADET/testdir/sub/testPDF.pdf', 'AAA')
            with app.app_context():
                dirIndex = lib.dataDB.directory_indexer()
                indexed, dirup, md = dirIndex.index_dir('testdir/sub', dataset)
            self.assertEqual(expects, indexed)
            self.assertIsNone(md)
            self.assertEquals(dirup, 'testdir')
