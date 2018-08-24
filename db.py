import pymongo


def getdb(g={}):
    if 'db' not in g:
        g['db'] = pymongo.MongoClient().auther
    return g['db']
