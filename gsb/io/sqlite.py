# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sqlite3 as sqlite
from collections import Iterable


class sqlite_db(object):
    def __init__(self, db_file=':memory:'):
        try:
            self.conn = sqlite.connect(db_file)
            self.cur = self.conn.cursor()
        except:
            raise Exception("I am unable to connect to the database")
    def script(self,chaine,commit=True):
        self.cur.executescript(chaine)
        if commit:
            self.conn.commit()
    def param(self, chaine, params,commit=True):
        self.cur.execute(chaine,params)
        if commit:
            self.conn.commit()

    def dump(self):
        sql_dump = self.conn.iterdump()
        for line in sql_dump:
            yield '%s\n' % line

    def dump_txt(self):
        sql_dump = self.conn.iterdump()
        retour = ""
        for line in sql_dump:
            retour = "%s\n%s" % (retour, line)
        return retour

    def query_base(self, query, args=(),commit=True):
        if commit:
            self.conn.commit()
        # on gere les variables
        if not isinstance(args, Iterable) or isinstance(args, basestring):
            args = (args,)
        return self.cur.execute(query, args)

    def rep(self, query, args=()):
        cur = self.query_base(query, args)
        rep = [dict((cur.description[idx][0], value) for idx, value in enumerate(row)) for row in cur.fetchall()]
        return rep

    def rep_one(self, query, args=()):
        cur = self.query_base(query, args)
        rep = cur.fetchone()[0]
        return rep

    def commit(self):
        self.conn.commit()


