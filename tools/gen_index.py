# -*- coding: utf-8 -*-
import argparse
import os
import sys
import time
import json
import yaml
import jinja2

# help + args
parser = argparse.ArgumentParser(description='Script to generate the catalog index html file.')
parser.add_argument('datafolder', help='The root folder where data files are stored')
parser.add_argument('templatefolder', help='Path where template is stored.')
parser.add_argument('destination', help='Path to output folder where index.html will be written.')
args = parser.parse_args()


datasets = []

# get all index files
for root, dirs, files in os.walk(args.datafolder):
    for fname in files:
        if fname.endswith("index.yaml"):
            data = yaml.load(open(os.path.join(root, fname)))

            # append info about path and updated date
            data["path"] = os.path.join(root)
            data["dateModified"] = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(os.path.join(root, fname))))

            datasets.append(data)


# sort datasets by dateModified
datasets = sorted(datasets, key=lambda k: k['dateModified'], reverse=True)


# set up template
tenv = jinja2.Environment(loader=jinja2.FileSystemLoader(args.templatefolder))
template = tenv.get_template('index.html')


# render index html file and write to disk
html = template.render(datasets=datasets)

with open(os.path.join(args.destination, "index.html"), "wb") as fh:
    fh.write(html.encode('utf-8'))


