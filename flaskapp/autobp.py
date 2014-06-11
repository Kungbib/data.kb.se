from flask import Blueprint
from flask.ext.autoindex import AutoIndexBlueprint
from os import path
datasetRoot = 'datasets'
auto_bp = Blueprint('auto_bp', __name__)
AutoIndexBlueprint(auto_bp, browse_root=path.join(path.curdir, datasetRoot))
