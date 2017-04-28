# -*- coding: utf-8 -*-
from os import path, listdir, walk
from mimetypes import guess_type, add_type
from urllib2 import quote
from flask import current_app


add_type('text/x-yaml', '.yaml')
add_type('application/xml', '.metadata')
add_type('application/xml', '.mets')
add_type('application/xml', '.mets.metadata')


def cleanDate(timestamp):
    dateFormat = '%Y-%m-%d %H:%M'
    return(timestamp.strftime(dateFormat))


def sizeof_fmt(num):
    for x in ['bytes', 'kB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def get_size(start_path=None):
    total_size = 0
    for dirpath, dirnames, filenames in walk(start_path):
        for f in filenames:
            fp = path.join(dirpath, f)
            total_size += path.getsize(fp)
    return sizeof_fmt(total_size)


class directory_indexer():
    def __init__(self):
        self.getMets = current_app.config.get('SUMMARIZE_METS', None)

    def _get_mets_element(self, mets, xpath):
        namespaces = {
            'mets': 'http://www.loc.gov/METS/',
            'mods': 'http://www.loc.gov/mods/v3'
        }
        metsElement = mets.findall(
            xpath,
            namespaces
        )
        if len(metsElement) == 0:
            return('')
        else:
            return(metsElement[0].text)

    def summarizeMets(self, rawMeta):
        from xml.etree import ElementTree as etree
        mets = etree.XML(rawMeta)
        title = self._get_mets_element(
            mets,
            './/mods:relatedItem/mods:titleInfo/mods:title'
        )
        issued = self._get_mets_element(
            mets,
            './/mods:originInfo/mods:dateIssued'
        )
        urn = self._get_mets_element(mets, './/mods:identifier[@type="urn"]')
        langs = self._get_mets_element(mets, './/mods:languageTerm')
        uri = self._get_mets_element(mets, './/mods:identifier[@type="uri"]')
        issn = self._get_mets_element(mets, './/mods:identifier[@type="issn"]')
        summary = {
            'issn': issn,
            'uri': uri,
            'issued': issued,
            'title': title,
            'language': langs,
            'urn': urn
        }
        return(summary)

    def index_dir(self, directory, dataset):
        datasetRoot = current_app.config['DATASET_ROOT']
        dTemp = directory
        pathDict = {}
        if directory is None and dataset.path != '':
            directory = dataset.path
        if directory != dataset.path:
            directory = path.join(dataset.path, directory)
        if directory is not None:
            if directory != dataset.path and dTemp is not None:
                dirUp = path.split(dTemp)[0]
            if directory == dataset.path:
                dirUp = None
            metadata = None
            if self.getMets:
                thisDir = path.join(datasetRoot, directory)
                dirList = listdir(thisDir)
                if 'aip.mets.metadata' in dirList:
                    print("Mets found")
                    with open(path.join(thisDir, 'aip.mets.metadata')) as m:
                        metadata = self.summarizeMets(m.read())
            for f in listdir(path.join(datasetRoot, directory)):
                fullPath = path.join(datasetRoot, directory, f)
                if path.isfile(fullPath):
                    pathDict[f] = {}
                    pathDict[f]['mimetype'] = guess_type(fullPath)[0]
                    pathDict[f]['name'] = f
                    pathDict[f]['realPath'] = path.join(
                        datasetRoot,
                        quote(directory),
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
        return(pathDict, dirUp, metadata)
