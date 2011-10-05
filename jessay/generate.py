#! /usr/bin/env python

import os
import shutil
import re
import subprocess
import time

DATE_FORMAT = '%Y/%m/%d'
#Stuff directory
cdir = 'lib'
fileext='text'

#Publishing directory
pdir = 'web'

#Template directory
tdir = 'template'
tfile = os.path.join(tdir, 'template.html')
template = None

#Markdown script
markdown = 'Markdown.pl'

#Index:
index = []


def navigate_folder(tmppath):
    for item in os.listdir(tmppath):
        filepath = os.path.join(tmppath, item)
        if os.path.isfile(filepath) and item.endswith('.text'):
        #Its an item. Lets generate and add to the index
            print 'Generating {0}'.format(filepath)

            contents = []

            pip = subprocess.Popen(['perl', markdown, filepath], stdout=subprocess.PIPE)
            filehtml = pip.stdout.read()
            contents.append(filehtml)

            htmlname = item.replace('.text','.html')

            properties = parse_properties(filepath)
            properties['htmlname'] = htmlname

            insert_to_index(properties)

            #Generate main page for the component
            page = tplparts
            page[1] = properties['title']
            contentshtml = ''.join(contents)
            page[3] = contentshtml
            pagehtml = ''.join(page)

            with open(os.path.join(pdir, htmlname), 'w') as f:
                f.write(pagehtml)

def parse_properties(path):
    with open(os.path.join(path), 'r') as f:
        lines = f.readlines()
    date = time.strptime(lines[0].strip(), DATE_FORMAT)
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
        result.append('<li><a href="' + x['htmlname'] + '">' + x['title'] + ' <span>'+ time.strftime(DATE_FORMAT, x['date']) + '</span></a></li>')


    html = '<ul>' + ''.join(result) + '</ul>'
    return html


print 'Init generate wiki...'

if os.path.isdir(tdir) and os.path.isfile(tfile):
    print 'Reading the template...'
    with open(tfile, 'r') as f:
        template = f.read()
else:
    print '[ERROR] The template folder/file doesnt exist'
    exit()

if os.path.isdir(pdir):
    print 'Cleaning web folder...'
    shutil.rmtree(pdir)
#Copy the data from the template
shutil.copytree(tdir,pdir)

#Generate regex
retpl = re.compile("\{(%\w+%)\}")
tplparts = retpl.split(template)

print 'Generating components html...'
navigate_folder(cdir)

print 'Generating index ...'
gindexpath = os.path.join(pdir, 'index.text')
contents = []
if os.path.isfile(gindexpath):
    pip = subprocess.Popen(['perl', markdown, gindexpath], stdout=subprocess.PIPE)
    mainhtml = pip.stdout.read()
    contents.append(mainhtml)

print 'Render index ...'
contents.append(render_index())

page = tplparts
page[1] = 'Index'
contentshtml = ''.join(contents)
page[3] = contentshtml
pagehtml = ''.join(page)

with open(os.path.join(pdir,'index.html'), 'w') as f:
    f.write(pagehtml)


print 'End of generation...'

