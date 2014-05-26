import json
import yaml
from rdflib import Graph
from rdflib_jsonld import parser

import sys
ctxpath = sys.argv[1]
fpath = sys.argv[2]

with open(fpath) as fp:
    data = yaml.load(fp)

with open(ctxpath) as fp:
    ctx = json.load(fp)

graph = Graph()
parser.to_rdf(data, graph, context_data=ctx)
print graph.serialize(format='turtle')
