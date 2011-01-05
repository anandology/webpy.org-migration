import itertools
import os
import re
import sys

import simplejson
import web

db = web.database(dbn="postgres", db="webpy.org", user="anand", pw="")

def read():
    """
    rows = db.query("SELECT transaction.*, data.thing_id, data.data"
            + " FROM transaction, data, version"
            + " WHERE data.thing_id=version.thing_id"
            +     " AND transaction.id=version.transaction_id"
            + " ORDER BY transaction.id")
    """

    data = []
    
    for tx in db.query("SELECT * FROM transaction"):
        rows = db.query("SELECT data.thing_id, data.data"
                + " FROM data, version"
                + " WHERE data.thing_id=version.thing_id"
                +     " AND data.revision=version.revision"
                +     " AND version.transaction_id=$tx.id"
                , vars=locals())
        docs = [simplejson.loads(row.data) for row in rows]
        tokens = [tx.id, tx.author_id, tx.created, tx.comment, docs]

        yield tokens
        
        
def _x():
    for tx_id, chunk in itertools.groupby(rows, lambda row: row.id):
        docs = []

        for row in chunk:
            doc = simplejson.loads(row.data)
            doc['id'] = row.thing_id
            docs.append()

        if docs:
            tokens = [row.id, row.author_id, row.created, row.comment, docs]
            data.append(tokens)

    return data

def add_users(data):
    emails = {}
    for row in db.query("SELECT thing_id, email FROM account"):
        emails[row.thing_id] = row.email
        
    def get_author(id):
        u = users.get(id)
        if u:
            name = "%s <%s>" % (u.get('displayname') or u['key'].split("/")[-1], emails.get(id))
        else:
            name = "annonymous"
        return name.strip()

    users = {}    
    for id, aid, t, comment, docs in data:
        for doc in docs:
            if doc['key'].startswith("/user/"):
                users[doc['id']] = doc
        
        author = get_author(aid)
        yield [id, author, t, comment, docs]

def fix_lang(data):
    for doc in _get_docs(data):
        doc['key'] = re.sub("(.*)/([a-z][a-z](-[a-z][a-z])?)$", r"\1.\2", doc['key'])
    return data
    
def _get_docs(data):
    for row in data:
        docs = row[-1]
        for doc in docs:
            yield doc

def fix_dirs(data):
    keys = set(doc['key'] for doc in _get_docs(data))
    dirnames = set(os.path.dirname(k) for k in keys)

    for doc in _get_docs(data):
        if doc['key'] in dirnames:
            doc['key'] = doc['key'].rstrip("/") + "/index"
            
    return data

def print_data(data):
    for id, author, t, comment, docs in data:
        tokens = [id, author, t, simplejson.dumps(comment or "edit"), simplejson.dumps(docs)]
        print "\t".join(unicode(t).encode("utf-8") for t in tokens)
                
def main():
    data = read()
    data = add_users(data)
    print_data(data)
    
def fix():
    data = (line.strip().split("\t") for line in sys.stdin)
    data = fix_lang(data)
    data = fix_dirs(data)
    
def preview():
    data = (line.strip().split("\t") for line in sys.stdin)
    for tokens in data:
        d = simplejson.loads(tokens[-1])
        tokens[-1] = simplejson.dumps(["%s@%s" % (doc['key'], doc['revision']) for doc in d])
        print "\t".join(tokens)

if __name__ == "__main__":
    import sys
    if "--preview" in sys.argv:
        preview()
    else:
        main()
