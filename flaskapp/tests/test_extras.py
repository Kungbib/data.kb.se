from os import path
import unittest
import lib.dataDB
from flask import Flask

filePath = path.join(
    path.dirname(path.realpath(__file__)),
    'testdata'
)


def getXMLFile(filename):
    xmlPath = path.join(filePath, filename)
    return(open(xmlPath).read())


class ExtrasTests(unittest.TestCase):
    def test_mets_summary_with_missing_element(self):
        app = Flask(__name__)
        app.config['SUMMARIZE_METS'] = 'FALSE'
        with app.app_context():
            dirIndex = lib.dataDB.directory_indexer()
            result = dirIndex.summarizeMets(getXMLFile('testmets_noissn.xml'))
            expects = {
                'language': 'und', 'title': 'AFTONBLADET',
                'issued': '1830-12-06', 'urn': 'urn:nbn:se:kb:dark-37623',
                'issn': '', 'uri': 'http://libris.kb.se/resource/bib/4345612'
            }
            self.assertEqual(result, expects)

    def test_mets_summary(self):
        app = Flask(__name__)
        app.config['SUMMARIZE_METS'] = 'FALSE'
        with app.app_context():
            dirIndex = lib.dataDB.directory_indexer()
            result = dirIndex.summarizeMets(getXMLFile('testmets.xml'))
            expects = {
                'language': 'und', 'title': 'AFTONBLADET',
                'issued': '1830-12-06', 'urn': 'urn:nbn:se:kb:dark-37623',
                'issn': '14039656', 'uri': 'http://libris.kb.se/resource/bib/4345612'
            }
            self.assertEqual(result, expects)
