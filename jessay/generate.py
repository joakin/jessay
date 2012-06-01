#! /usr/bin/env python

import sys
import os
import posixpath
import shutil
import re
import subprocess
import time
from ConfigParser import ConfigParser
from string import Template

script_path = os.path.dirname(os.path.realpath(__file__))
propertiesfile = posixpath.join(script_path, "jessay.properties")

template = None

conf = {}

#Index:
essays_index = []
articles_index = {}

IGNORE_PATTERNS = ('*.pyc','CVS','^.git','tmp','.svn')

def set_tpl(template_file):
    global template
    template = Template(template_file)

def html_from_tpl(title, content, relative_path='..'):
    d = dict(title = title, content = content, relpath = relative_path)
    return template.safe_substitute(d)

def read_configuration():
    cfg = ConfigParser()
    cfg.read(propertiesfile)

    conf['DATE_FORMAT'] = cfg.get('format', 'DATE_FORMAT')

    #Stuff directory
    conf['ESSAYS_DIR'] = posixpath.normpath(cfg.get('paths', 'ESSAYS_DIR'))
    conf['ARTICLES_DIR'] = posixpath.normpath(cfg.get('paths', 'ARTICLES_DIR'))
    conf['ESSAYS_EXT'] = cfg.get('paths', 'ESSAYS_EXT')
    conf['ARTICLES_EXT'] = posixpath.normpath(cfg.get('paths', 'ARTICLES_EXT'))
    conf['ARTICLES_FILENAME'] = cfg.get('paths', 'ARTICLES_FILENAME')

    #Publishing directory
    conf['PUBLICATION_DIR'] = posixpath.normpath(cfg.get('paths', 'PUBLICATION_DIR'))

    #Template directory
    conf['TEMPLATE_DIR'] = posixpath.normpath(cfg.get('paths', 'TEMPLATE_DIR'))
    tfilename = cfg.get('paths', 'TEMPLATE_FILE')
    conf['TEMPLATE_FILE'] = posixpath.join(conf['TEMPLATE_DIR'], tfilename)

    #Markdown script
    conf['ESSAY_PROCESSOR'] = posixpath.join(script_path, posixpath.normpath(cfg.get('paths', 'ESSAY_PROCESSOR')))

def navigate_essays(tmppath):
    for item in os.listdir(tmppath):
        filepath = posixpath.join(tmppath, item)
        if posixpath.isfile(filepath) and item.endswith(conf['ESSAYS_EXT']):
            #Its an item. Lets generate and add to the index
            print 'Generating {0}'.format(filepath)

            contents = []

            pip = subprocess.Popen(['perl', conf['ESSAY_PROCESSOR'], filepath], stdout=subprocess.PIPE)
            filehtml = pip.stdout.read()
            contents.append(filehtml)

            htmlname = item.replace(conf['ESSAYS_EXT'],'.html')

            properties = parse_essay_properties(filepath)
            properties['htmlname'] = htmlname
            properties['url'] = conf['ESSAYS_DIR']

            insert_to_essays_index(properties)

            pagehtml = html_from_tpl(properties['title'], ''.join(contents))

            with open(posixpath.join(conf['PUBLICATION_DIR'], conf['ESSAYS_DIR'], htmlname), 'w') as f:
                f.write(pagehtml)

def parse_essay_properties(path):
    with open(posixpath.join(path), 'r') as f:
        lines = f.readlines()
    date = time.strptime(lines[0].strip(), conf['DATE_FORMAT'])
    title = lines[1].strip()
    return { 'title': title, 'date':date }

def insert_to_essays_index(p):
    if len(essays_index) == 0 :
        essays_index.append(p)
    else:
        inserted = False
        for i in range(0, len(essays_index)):
            x = essays_index[i]
            if x.date < p.date :
                essays_index.insert(i, p)
                inserted = True
        if not inserted:
            essays_index.append(p)

def render_essays_index():
    result = []
    li_html = '<li><a href="{0}">{1} <span>{2}</span></a></li>'
    for i in range(0, len(essays_index)):
        x = essays_index[i]
        path = x['url'] + '/' + x['htmlname']
        title = x['title']
        date = time.strftime(conf['DATE_FORMAT'], x['date'])
        li = li_html.format(path, title, date)
        result.append(li)


    html = '<ul>' + ''.join(result) + '</ul>'
    return html

def deal_article_category(name, categories, path):
    if name is not '':
        properties = parse_article_properties(name)
        categories.append(properties)

    newpath = posixpath.join(path, name)
    #Create folder in publish
    os.makedirs(posixpath.join(conf['PUBLICATION_DIR'], newpath))
    navigate_articles(newpath, name, categories)

def deal_article_file(name, categories, path):
    print 'Generating {0} {1}'.format(path, name)

    properties = parse_article_properties(name)

    if properties['extension'] is conf['ARTICLES_EXT']:
        return

    ppath = posixpath.join(conf['PUBLICATION_DIR'], path)

    contents = []

    file_path = posixpath.join(path, name)
    if os.path.isfile(file_path):
        pip = subprocess.Popen(['perl', conf['ESSAY_PROCESSOR'], file_path], stdout=subprocess.PIPE)
        mainhtml = pip.stdout.read()
        contents.append(mainhtml)

    pagetitle = properties['title']

    #Add component to index
    item = {'name': pagetitle, 'url': path + '/' + name + '.html', 'categories': categories[:], 'order': properties['order']}
    category_tree(articles_index, categories, item)

    #Generate main page for the component
    relative_path = '..'
    relative_path += '/..' * len(categories)
    page_html = html_from_tpl(pagetitle, ''.join(contents), relative_path)

    with open(posixpath.join(ppath, name + '.html'), 'w') as f:
        f.write(page_html)

def navigate_articles(tmppath, name, categories):
    for sub in os.listdir(tmppath):
        spath = posixpath.join(tmppath, sub)
        if os.path.isdir(spath):
            deal_article_category(sub, categories[:], tmppath)
        if os.path.isfile(spath):
            deal_article_file(sub, categories[:], tmppath)

def parse_article_properties(name):
    file_vars = name.split('.')
    folder_vars = file_vars[0].split('_')
    title = folder_vars[1]
    order = int(float(folder_vars[0]))
    extension = file_vars[1] if len(file_vars)>1 else None
    return { 'title': title, 'order':order, 'extension': extension}

def category_tree(tree,cats,item):
    category_tree_iter(0, tree, cats, item)

def category_tree_iter(i, tree, cats, item):
    cat = cats[i]
    catname = cat['title']
    if not catname in tree:
        tree[catname] = { 'order': cat['order'], 'items': [], 'subcats': {} }

    if i+1 >= len(cats):
        items = tree[catname]['items']
        if len(items) == 0:
            items.append(item)
        else:
            x = 0
            for it in items:
                if it['order'] > item['order']:
                    items.insert(x, item)
                    break
                x += 1
            else:
                items.append(item)
    else:
        tree[catname]['subcats'] = category_tree_iter(i+1, tree[catname]['subcats'], cats, item)

    return tree

def render_articles_index(cats):
    if len(cats) == 0:
        return ''

    resultorder = []
    result = []

    list_html = '<ul>{0}</ul>'
    li_category = '<li class="category"><a>{0}</a></li>'
    li_item = '<li><a href="{0}">{1}</a></li>'

    for name, cat in cats.iteritems():
        tmphtml = li_category.format(name)
        itemshtml = ''
        for item in cat['items']:
            itemshtml += li_item.format(item['url'], item['name'])
        if len(cat['items']) > 0:
            tmphtml += list_html.format(itemshtml)
        tmphtml += render_articles_index(cat['subcats'])

        if len(result) == 0:
            resultorder.append(cat['order'])
            result.append(tmphtml)
        else:
            for x in range(0,len(result)):
                if resultorder[x] > cat['order']:
                    resultorder.insert(x, cat['order'])
                    result.insert(x, tmphtml)
                    break
                x += 1
            else:
                resultorder.append(cat['order'])
                result.append(tmphtml)

    html = list_html.format(''.join(result))
    return html


def main(args):
    try:

        print 'Init generate wiki...'

        print 'Reading configuration'
        if posixpath.isfile(propertiesfile):
            read_configuration()
        else:
            print '[ERROR] The configuration file doesnt exist'
            exit()

        template_file = None
        if posixpath.isdir(conf['TEMPLATE_DIR']) and posixpath.isfile(conf['TEMPLATE_FILE']):
            print 'Reading the template...'
            with open(conf['TEMPLATE_FILE'], 'r') as f:
                template_file = f.read()
        else:
            print '[ERROR] The template folder/file doesnt exist'
            exit()

        if posixpath.isdir(conf['PUBLICATION_DIR']):
            print 'Cleaning web folder...'
            shutil.rmtree(conf['PUBLICATION_DIR'])
        #Copy the data from the template
        shutil.copytree(conf['TEMPLATE_DIR'],conf['PUBLICATION_DIR'], ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))

        set_tpl(template_file)

        print 'Generating essays html...'
        os.mkdir(posixpath.join(conf['PUBLICATION_DIR'], conf['ESSAYS_DIR']))
        navigate_essays(conf['ESSAYS_DIR'])

        print 'Generating articles html...'
        os.mkdir(posixpath.join(conf['PUBLICATION_DIR'], conf['ARTICLES_DIR']))
        navigate_articles(conf['ARTICLES_DIR'], '', [])

        print 'Generating index ...'
        gindexpath = posixpath.join(conf['PUBLICATION_DIR'], 'index'+conf['ARTICLES_EXT'])
        contents = []
        if posixpath.isfile(gindexpath):
            pip = subprocess.Popen(['perl', conf['ESSAY_PROCESSOR'], gindexpath], stdout=subprocess.PIPE)
            mainhtml = pip.stdout.read()
            contents.append(mainhtml)

        print 'Render index ...'
        contents.append(render_essays_index())
        contents.append(render_articles_index(articles_index))

        pagehtml = html_from_tpl('Index', ''.join(contents), '.')

        with open(posixpath.join(conf['PUBLICATION_DIR'],'index.html'), 'w') as f:
            f.write(pagehtml)


        print 'End of generation...'

    except:
        print "Unexpected error:", sys.exc_info()
        raise
        return 1
    else:
        return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))


