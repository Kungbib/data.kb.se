#!/usr/bin/env python

if __name__ != '__main__':
    from sys import path as syspath
    from os import path, chdir
    syspath.append(path.dirname(__file__))
    chdir(path.dirname(__file__))

from flask import Flask, render_template
from yaml import load as yload
from autobp import auto_bp, datasetRoot
from os import path

app = Flask(__name__)
app.register_blueprint(auto_bp, url_prefix='/datasets')


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


if __name__ == "__main__":
    app.run(debug=True)
