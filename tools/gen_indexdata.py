import os
import sys
import json
import yaml
from rdflib import Graph
from rdflib_jsonld import parser

#example use: python gen_indexdata.py 2014 www/context.jsonld

# root filder of datasets
rootdir = sys.argv[1]

# context file
ctxpath = sys.argv[2]

graph = Graph()

# Load context for dataset metadata
with open(ctxpath) as fp:
    ctx = json.load(fp)

# get all index files and generate RDF dump
for root, dirs, files in os.walk(rootdir):
    for fname in files:
        if fname.endswith(".yaml"):
            data = yaml.load(open(os.path.join(root, fname)))
            parser.to_rdf(data, graph, context_data=ctx)

print graph.serialize(format='pretty-xml')
