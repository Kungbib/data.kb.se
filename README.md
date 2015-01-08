data.kb.se
==========

Tools and templates to generate a catalog of file based datasets typically hosted on an Apache server. Files are stored in a folder together with an index file in yaml. A script collects the index files and generates a catalog index page in html. The catalog index page contains a machine readable representation in [RDFa](http://www.w3.org/TR/html-rdfa/).

## The yaml index file

The index file provides basic information about the dataset and its relation to catalog items in Libris.

Example:

```yaml
type: Dataset
name: Post- och inrikes tidningar

description: >
  Digitaliserad version av Post- och inrikes 
  tidningar från 1645-1701. Digitaliseringen genomfördes 1998
  och utgick från mikrofilmsversionen. Filerna är ordnade i en katalog
  per år med bildfiler och transkriberade versioner.

license: CC0

sameAs:
  - librisid:72389479
  - librisid:23443899
 
distribution:
  encodingFormat:
    - TIFF
    - DOC

provider:
  name: Example Name
  email: example.name@example.com
```



