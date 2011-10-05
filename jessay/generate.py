#! /usr/bin/env python

import os
import posixpath
import shutil
import re
import subprocess
import time
from ConfigParser import ConfigParser

propertiesfile = "jessay.properties"

template = None

conf = {}

#Index:
index = []

def read_configuration():
    cfg = ConfigParser()
    cfg.read(propertiesfile)

    conf['dateformat'] = cfg.get('format', 'DATE_FORMAT')

    #Stuff directory
    conf['essaysdir'] = posixpath.normpath(cfg.get('paths', 'ESSAYS_DIR'))
    conf['essaysext'] = cfg.get('paths', 'ESSAYS_EXT')

    #Publishing directory
    conf['publicationdir'] = posixpath.normpath(cfg.get('paths', 'PUBLICATION_DIR'))

    #Template directory
    conf['templatedir'] = posixpath.normpath(cfg.get('paths', 'TEMPLATE_DIR'))
    tfilename = cfg.get('paths', 'TEMPLATE_FILE')
    conf['templatefile'] = posixpath.join(conf['templatedir'], tfilename)

    #Markdown script
    conf['essayprocessor'] = posixpath.normpath(cfg.get('paths', 'ESSAY_PROCESSOR'))

def navigate_folder(tmppath):
    for item in os.listdir(tmppath):
        filepath = posixpath.join(tmppath, item)
        if posixpath.isfile(filepath) and item.endswith(conf['essaysext']):
        #Its an item. Lets generate and add to the index
            print 'Generating {0}'.format(filepath)

            contents = []

            print conf['essayprocessor']
            print filepath
            pip = subprocess.Popen(['perl', conf['essayprocessor'], filepath], stdout=subprocess.PIPE)
            filehtml = pip.stdout.read()
            contents.append(filehtml)

            htmlname = item.replace(conf['essaysext'],'.html')

            properties = parse_properties(filepath)
            properties['htmlname'] = htmlname

            insert_to_index(properties)

            #Generate main page for the component
            page = tplparts
            page[1] = properties['title']
            contentshtml = ''.join(contents)
            page[3] = contentshtml
            pagehtml = ''.join(page)

            with open(posixpath.join(conf['publicationdir'], htmlname), 'w') as f:
                f.write(pagehtml)

def parse_properties(path):
    with open(posixpath.join(path), 'r') as f:
        lines = f.readlines()
    date = time.strptime(lines[0].strip(), conf['dateformat'])
    title = lines[1].strip()
    return { 'title': title, 'date':date }

def insert_to_index(p):
    if len(index) == 0 :
        index.append(p)
    else:
        inserted = False
        for i in range(0, len(index)):
            x = index[i]
            if x.date < p.date :
                index.insert(i, p)
                inserted = True
        if not inserted:
            index.append(p)

def render_index():
    result = []
    for i in range(0, len(index)):
        x = index[i]
        result.append('<li><a href="' + x['htmlname'] + '">' + x['title'] + ' <span>'+ time.strftime(conf['dateformat'], x['date']) + '</span></a></li>')


    html = '<ul>' + ''.join(result) + '</ul>'
    return html


print 'Init generate wiki...'

print 'Reading configuration'
if posixpath.isfile(propertiesfile):
    read_configuration()
else:
    print '[ERROR] The configuration file doesnt exist'
    exit()

if posixpath.isdir(conf['templatedir']) and posixpath.isfile(conf['templatefile']):
    print 'Reading the template...'
    with open(conf['templatefile'], 'r') as f:
        template = f.read()
else:
    print '[ERROR] The template folder/file doesnt exist'
    exit()

if posixpath.isdir(conf['publicationdir']):
    print 'Cleaning web folder...'
    shutil.rmtree(conf['publicationdir'])
#Copy the data from the template
shutil.copytree(conf['templatedir'],conf['publicationdir'])

#Generate regex
retpl = re.compile("\{(%\w+%)\}")
tplparts = retpl.split(template)

print 'Generating components html...'
navigate_folder(conf['essaysdir'])

print 'Generating index ...'
gindexpath = posixpath.join(conf['publicationdir'], 'index.text')
contents = []
if posixpath.isfile(gindexpath):
    pip = subprocess.Popen(['perl', conf['essayprocessor'], gindexpath], stdout=subprocess.PIPE)
    mainhtml = pip.stdout.read()
    contents.append(mainhtml)

print 'Render index ...'
contents.append(render_index())

page = tplparts
page[1] = 'Index'
contentshtml = ''.join(contents)
page[3] = contentshtml
pagehtml = ''.join(page)

with open(posixpath.join(conf['publicationdir'],'index.html'), 'w') as f:
    f.write(pagehtml)


print 'End of generation...'

