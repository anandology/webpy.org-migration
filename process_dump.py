import os
import re
import string
import sys
import datetime

import simplejson
import web

def write(filename, title, body):
    dirname = os.path.dirname(filename)
    os.system("mkdir -p %s" % dirname)
    
    title = title and title.encode('utf-8') or ""
    body = body and body.encode('utf-8')
        
    f = open(filename, 'w')
    
    f.write("---\n")
    f.write("layout: default\n")
    f.write("title: %s\n" % title)
    f.write("---\n\n")
    
    if title:
        f.write("# " + title + "\n\n")
    f.write(body)
    f.close()
    
def system(cmd):
    print cmd
    try:
        os.system(cmd + ">> git.log 2>&1")
    except:
        import traceback
        print >> sys.syderr, "ERROR", repr(cmd)
        traceback.print_exc()
    
def fix_lang(data):
    def f(doc):
        doc['key'] = re.sub("(.*)/([a-z][a-z](?:-[a-z][a-z])?)$", r"\1.\2", doc['key'])
        doc['key'] = re.sub("(.*)/([a-z][a-z](?:-[a-z][a-z])?)/(.*)$", r"\1.\2/\3", doc['key'])
        if doc['key'].startswith("."):
            doc['key'] = "/index" + doc['key']
        return doc
    
    return _map_docs(f, data)    

def _map_docs(f, data):
    for id, author, t, comment, docs in data:
        docs = [f(doc) for doc in docs]
        yield id, author, t, comment, docs

def fix_dirs(data):
    data = list(data)
    
    keys = set()
    for id, author, t, comment, docs in data:
        keys.update(doc['key'] for doc in docs if web.listget(doc['key'].split("/"), 1) not in skip_dirs)

    dirnames = set(os.path.dirname(k) for k in keys)

    def f(doc):
        if doc['key'] in dirnames:
            doc['key'] = doc['key'].rstrip("/") + "/index"
        return doc
        
    return _map_docs(f, data)
    
def git_date(datestr):
    tokens = re.split("[: -\.]", datestr)
    return datetime.datetime(*map(int, tokens)).strftime("%a %b %d %H:%M:%S %Y +0000")
    
def read():
    for line in sys.stdin:
        id, author, t, comment, json = line.strip().split("\t")
        docs = simplejson.loads(json)
        d = {}
        for doc in docs:
            key = doc['key']
            if key not in d or doc['revision'] > d[key]['revision']:
                d[key] = doc
        yield [id, author, t, simplejson.loads(comment), d.values()]

def main():
    data = read()
    data = fix_lang(data)
    data = fix_dirs(data)
    data = sorted(data, key=lambda d: d[2])
    
    spammers = [email.strip() for email in open("data/spammers.txt")]
    spamedits = [id.strip() for id in open("data/spamedits.txt")]

    skip_dirs = "user permission macros templates type user group usergroup".split()
    
    system("rm -rf build && mkdir build && cd build && git init")
    
    for id, author, t, comment, docs in data:
        if "http://" in comment and "webpy.org" not in comment:
            print "ignoring changeset: %s" % str((id, author, t, comment))
            continue

        author = re.sub(" +", " ", author)
        if author.strip() in spammers or id in spamedits:
            print "ignoring spam: %s" % str((id, author, t, comment))
            continue
            
        bad_keys = ['\xe0\xb1\x86recentchanges.md', ').md']
        
        print "** processing changeset", id, t
        added = False
        for doc in docs:
            key = doc['key'][1:].encode('utf-8') + ".md"
            if doc['type']['key'] == '/type/page' and web.listget(doc['key'].split("/"), 1) not in skip_dirs and key not in bad_keys:
                title = doc.get('title', '')
                body = doc.get("body", {})
                if isinstance(body, dict):
                    body = body.get("value", "").replace("\r\n", "\n")
                    
                write("build/" + key, title, body)
                system("cd build && git add '%s'" % key)
                added = True
                
        if author == "annonymous":
            author = "anonymous <anonymous@webpy.org>"

        if added:
            system("cd build && git commit -m %s --date='%s' --author='%s'" % (simplejson.dumps(comment), git_date(t), author))
            
    system("cp -r _layouts static build")
    system("cd build && git add _layouts static && git commit -m 'Added layouts and static file'")
        
if __name__ == "__main__":
    main()
