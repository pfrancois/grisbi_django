# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .. import models
from django.db import models as models_agg
import time
from .. import utils

import dateutil.rrule as rrule
from dateutil.relativedelta import relativedelta

from . import export_base

from django.http import HttpResponse
from sql.pg import sqlite_db

class Export_view_sql(export_base.ExportViewBase):
    extension_file = "sql"
    debug = False
    nomfich = "export_full"
    model_initial = models.Ope
    form_class = export_base.Exportform_ope
    titre = "export sql money"

    def export(self, query):
        sql = sqlite_db()
        # attention ce n'est les comptes
        s = ("""DROP TABLE IF EXISTS account;
CREATE TABLE account (id INTEGER PRIMARY KEY,
                    name TEXT,
                    place INTEGER
                    , lastupdate DOUBLE);

insert into account VALUES (1,'account.name1',0,null);
DROP TABLE IF EXISTS budget;
CREATE TABLE budget (id INTEGER PRIMARY KEY,
                    month INTEGER,
                    year INTEGER,
                    amount    Double
                , lastupdate DOUBLE);
            """)
        sql.conn.cursor().executescript(s)
        sql.conn.commit()
        # calcul des budgets
        nb_bud = 0
        date_min = self.model_initial.objects.aggregate(element=models_agg.Min('date'))['element']
        date_max = self.model_initial.objects.aggregate(element=models_agg.Max('date'))['element']
        for dt in rrule.rrule(rrule.MONTHLY, dtstart=date_min + relativedelta(day=1), until=date_max + relativedelta(day=1)):
            nb_bud = nb_bud + 1
            sql.query("insert into budget VALUES(:id,:month,:year,:amount,:lastupdate);", {'id': nb_bud,
                                                                                           'month': dt.month,
                                                                                           'year': dt.year,
                                                                                           'amount': 0,
                                                                                           'lastupdate': time.mktime(dt.timetuple())})
# les categories
        sql.query("""CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type INTEGER,
    color INTEGER,
    place INTEGER,
    lastupdate DOUBLE);
            """)
        sql.query("""CREATE TABLE subcategory (
    id INTEGER PRIMARY KEY,
    category INTEGER,
    name TEXT,
    place INTEGER,
    lastupdate DOUBLE);
            """)

        param = {}
        nbcat = 0
        # comme il ne gere pas les virements
        for cat in models.Cat.objects.exclude(type='v').order_by('nom'):
            nbcat = nbcat + 1
            param['id'] = cat.id
            param['name'] = cat.nom
            if cat.type == 'r':
                param['type'] = 1
                param['color'] = 35840
            else:
                param['type'] = 2
                param['color'] = 13369344
            param['place'] = nbcat
            param['lastupdate'] = time.mktime(cat.lastupdate.timetuple())
            sql.query(u"insert into category VALUES(:id,:name,:type,:color,:place,:lastupdate);", param)
        try:
            id_placement = utils.idtostr(models.Cat.objects.get(nom='placement'))
            if id_placement == 0:
                raise models.Cat.DoesNotExist
        except models.Cat.DoesNotExist:
            id_placement = models.Cat.objects.exclude(type='v').aggregate(id=models_agg.Max('id'))['id'] + 1
            sql.query(u"insert into category VALUES(:id,:name,:type,:color,:place,:lastupdate);",
                    {'id': id_placement,
                     'name': 'placement',
                     'type': 2,
                     'color': 13369344,
                     'place': nbcat + 1,
                     'lastupdate': utils.timestamp()}
            )
# les devises
        chaine = """DROP TABLE IF EXISTS  currency;
            CREATE TABLE currency (
    id INTEGER PRIMARY KEY,
    name TEXT,
    sign TEXT,
    decimal INTEGER,
    lastupdate DOUBLE);
insert into currency VALUES(1,'Dollar','$',2,'');
insert into currency VALUES(2,'Euro','EUR',2,'');
"""
        sql.conn.cursor().executescript(chaine)
        sql.conn.commit()
# les comptes
        chaine = """DROP TABLE IF EXISTS payment;
CREATE TABLE payment (
    id INTEGER PRIMARY KEY,
    name TEXT,
    symbol INTEGER,
    color INTEGER,
    place INTEGER,
    lastupdate DOUBLE);
            """
        sql.conn.cursor().executescript(chaine)
        sql.conn.commit()
        param = {}
        # on ne prend que les comptes bancaire ou cash
        liste_compte = models.Compte.objects.filter(type__in=['b', 'e'])
        i = 0
        for cpt in liste_compte:
            if cpt.type == "b" or cpt.type == "e":
                i = i + 1
                param['id'] = cpt.id
                param['name'] = cpt.nom
                param['symbol'] = i
                param['color'] = utils.idtostr(cpt, membre="color", defaut="35840")
                param['place'] = i
                param['lastupdate'] = time.mktime(cpt.lastupdate.timetuple())
                sql.query(u"insert into payment VALUES(:id,:name,:symbol,:color,:place,:lastupdate);", param)
# operation
        sql.query("""CREATE TABLE record (
    id INTEGER PRIMARY KEY,
    payment INTEGER,
    category INTEGER,
    subcategory INTEGER,
    memo TEXT,
    currency INTEGER,
    amount FLOAT,
    date DOUBLE,
    photo INTEGER,
    voice INTEGER,
    payee TEXT,
    note TEXT,
    account INTEGER,
    type INTEGER,
    repeat INTEGER,
    place INTEGER,
    lastupdate DOUBLE,
    day INTEGER);""")
        param = {}
        nbope = 0
        # on elimine les ope mere ou les ope dans les compte non bq ni especes ou les virement interne
        for ope in models.Ope.objects.filter(compte__type__in=['b', 'e'],
                                             filles_set__isnull=True
                                    ).select_related('cat', "compte", "tiers", "ib", "rapp", "ope", "ope_pmv", "moyen"):
            nbope += 1
            param['id'] = ope.id
            # gestion des paiments on recupere l'id qui va bien
            param['payment'] = ope.compte.id
            if ope.cat == "Virement":
                if ope.jumelle.compte.type not in ('b', 'e'):
                    param['category'] = id_placement
                    param['memo'] = "%s => %s" % (ope.compte.nom, ope.jumelle.compte.nom)
                else:
                    # on ne gere pas les virement internes
                    continue
            else:
                param['category'] = utils.nulltostr(ope.cat.id)
                param['memo'] = ope.tiers.nom
            param['subcategory'] = None
            param['currency'] = 2
            param['amount'] = float(str(ope.montant))
            param['date'] = ope.date.strftime('%Y-%m-%d')
            param['photo'] = 0
            param['voice'] = 0
            param['payee'] = None
            param['note'] = ''
            param['account'] = 0
            if ope.moyen.type == 'r':
                param['type'] = 1
            else:
                param['type'] = 2
            param['repeat'] = 0
            param['place'] = nbope
            param['day'] = ope.date.strftime('%Y%m%d')
            param['lastupdate'] = time.mktime(cpt.lastupdate.timetuple())
            sql.query(u"""insert into record VALUES(:id,:payment,:category,:subcategory,:memo,:currency,
                :amount,:date,:photo,:voice,:payee,:note,:account,:type,:repeat,:place,:day,:lastupdate);""", param)
            sql.query('DROP INDEX IF EXISTS budget_month_index;')
            sql.query('CREATE INDEX budget_month_index on budget(month);')
            sql.query('DROP INDEX IF EXISTS record_day_index;')
            sql.query('CREATE INDEX record_day_index on record(day);')
            sql.query('DROP INDEX IF EXISTS record_repeat_index;')
            sql.query('CREATE INDEX record_repeat_index on record(repeat);')
        reponse = HttpResponse(sql.dump(), mimetype="text/plain")
        if not self.debug:
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse['Pragma'] = "public"
            reponse["Content-Disposition"] = "attachment; filename=%s_%s.%s" % (self.nomfich,
                                                                                time.strftime(
                                                                                "%d_%m_%Y-%H_%M_%S",
                                                                                utils.timestamp()), self.extension_file
                                                                                )
        return reponse
