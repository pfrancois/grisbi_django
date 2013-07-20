# -*- coding: utf-8 -*-
from __future__ import absolute_import
#import csv
from .. import models
from django.db import models as models_agg
import time
from .. import utils
#from datetime import date
import dateutil.rrule as rrule
from dateutil.relativedelta import relativedelta

from . import export_base
#from django.core import exceptions as django_exceptions
from django.http import HttpResponse
from sql.pg import sqlite_db

class Export_view_sql(export_base.ExportViewBase):
    extension_file = "sql"
    debug = True
    nomfich = "export_full"
    model_initial = models.Ope
    form_class = export_base.Exportform_ope
    titre = "export sql money"

    def export(self, query):
        sql = sqlite_db()
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

        sql.query("""CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type INTEGER,
    color INTEGER,
    place INTEGER,
    lastupdate DOUBLE);
            """)

        param = {}
        nbcat = 0
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
            id_placement = models.Cat.objects.exclude(type='v').aggregate(id=models_agg.Max('id'))['id']+1
            sql.query(u"insert into category VALUES(:id,:name,:type,:color,:place,:lastupdate);",
                    {'id': id_placement,
                     'name': 'placement',
                     'type': 2,
                     'color': 13369344,
                     'place': nbcat+1,
                     'lastupdate': utils.timestamp()}
            )

        chaine = """DROP TABLE IF EXISTS  currency;
            CREATE TABLE currency (
    id INTEGER PRIMARY KEY,
    name TEXT,
    sign TEXT,
    decimal INTEGER,
    lastupdate DOUBLE);
insert into currency VALUES(1,'Dollar','$',2,'');
insert into currency VALUES(2,'Euro','EUR',2,'');
DROP TABLE IF EXISTS payment;
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
        soldes = models.Compte.objects.select_related('ope').filter(
            ope__filles_set__isnull=True).annotate(solde=models_agg.Sum('ope__montant')).order_by('id')
        i = 0
        for cpt in soldes:
            if cpt.type == "b" or cpt.type == "e":
                i = i + 1
                param['id'] = cpt.id
                param['name'] = cpt.nom
                param['symbol'] = i
                param['color'] = utils.idtostr(cpt, membre="color", defaut="35840")
                param['place'] = i
                param['lastupdate'] = time.mktime(cpt.lastupdate.timetuple())
                sql.query(u"insert into payment VALUES(:id,:name,:symbol,:color,:place,:lastupdate);", param)
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
        #on elimine les ope mere ou les ope dans les compte non bq ni especes ou les virement interne
        for ope in models.Ope.objects.filter(compte__type__in=['b', 'e'],
                                             filles_set__isnull=True
                                    ).exclude(jumelle__compte__type__in=['b', 'e'],
                                    ).select_related('cat', "compte", "tiers", "ib", "rapp", "ope", "ope_pmv", "moyen"):
            nbope += 1
            param['id'] = ope.id
            #gestion des paiments on recupere l'id qui va bien
            param['payment'] = ope.compte.id
            if ope.cat == "Virement":
                param['category'] = id_placement
                param['memo'] = "%s => %s" % (ope.compte.nom, ope.jumelle.compte.nom)
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
