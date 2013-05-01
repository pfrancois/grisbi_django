# -*- coding: utf-8 -*-
from __future__ import absolute_import
#import csv
from . import models
from django.db import models as models_agg
import time
from . import utils
from cStringIO import StringIO
import codecs
#from datetime import date
import dateutil.rrule as rrule
from dateutil.relativedelta import relativedelta

from gsb import export_base
#from django.core import exceptions as django_exceptions
from django.http import HttpResponse


class Writer_sql(export_base.Writer_base):

    def __init__(self, encoding="utf-8", fich=None, **kwds):
        self.queue = StringIO()
        codecinfo = codecs.lookup("utf8")
        wrapper = codecs.StreamReaderWriter(
            self.queue, codecinfo.streamreader, codecinfo.streamwriter)
        if fich is not None:
            self.stream = fich
        else:
            self.stream = wrapper
        self.encoding = encoding

    def writerow(self, row):
        self.stream.write(row)
        self.stream.write('\n')
    def w(self, row):
        self.writerow(row)


class Export_view_sql(export_base.ExportViewBase):
    extension_file = "sql"
    debug = True
    nomfich = "export_full"
    model_initial = models.Ope
    form_class = export_base.Exportform_ope
    titre = "export sql money"

    def export(self, query):
        sql = Writer_sql()
        s = ("""CREATE TABLE account (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    place INTEGER
                    , lastUpdate DOUBLE);

insert into account VALUES (1,'&account.name1',0,'');

                    CREATE TABLE budget (
                    id INTEGER PRIMARY KEY,
                    month INTEGER,
                    year INTEGER,
                    amount    AT
                , lastUpdate DOUBLE);
            """)
        sql.w(s)
        nb_bud = 0
        date_min = self.model_initial.objects.aggregate(
            element=models_agg.Min('date'))['element']
        date_max = self.model_initial.objects.aggregate(
            element=models_agg.Max('date'))['element']
        for dt in rrule.rrule(rrule.MONTHLY, dtstart=date_min + relativedelta(day=1), until=date_max + relativedelta(day=1)):
            nb_bud = nb_bud + 1
            sql.w("insert into budget VALUES({id},{month},{year},{amount},{lastUpdate});".format(id=nb_bud, month=dt.month, year=dt.year, amount=0, lastUpdate=1363046040.062428))
        sql.w("""CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type INTEGER,
    color INTEGER,
    place INTEGER
, lastUpdate DOUBLE);
            """)
        param = {}
        nbcat = 0
        for cat in models.Cat.objects.exclude(type='v').order_by('id'):
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
            param['lastUpdate'] = utils.idtostr(cat, membre="lastUpdate", defaut=utils.timestamp())
            sql.w(u"insert into category VALUES({id},'{name}',{type},{color},{place},{lastUpdate});".format(
                **param))
        try:
            id_placement = utils.idtostr(models.Cat.objects.get(nom='placement'))
            if id_placement == 0:
                raise models.Cat.DoesNotExist
        except models.Cat.DoesNotExist:
            id_placement = models.Cat.objects.exclude(type='v').aggregate(id=models_agg.Max('id'))['id']+1
            sql.w(u"insert into category VALUES({id},'{name}',{type},{color},{place},{lastUpdate});".format(
                **{'id': id_placement, 'name': 'placement', 'type': 2, 'color': 13369344, 'place': nbcat+1, 'lastUpdate': utils.timestamp()}
            ))
        sql.w("""CREATE TABLE currency (
    id INTEGER PRIMARY KEY,
    name TEXT,
    sign TEXT,
    decimal INTEGER,
    lastUpdate DOUBLE);
insert into currency VALUES(1,'Dollar','$',2,'');
insert into currency VALUES(2,'Euro','EUR',2,'');

CREATE TABLE payment (
    id INTEGER PRIMARY KEY,
    name TEXT,
    symbol INTEGER,
    color INTEGER,
    place INTEGER,
    lastUpdate DOUBLE);
            """)
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
                param['lastUpdate'] = utils.idtostr(cpt, membre="lastUpdate", defaut=utils.timestamp())
                sql.w(u"insert into payment VALUES({id},'{name}',{symbol},{color},{place},{lastUpdate});".format(
                    **param))
        sql.w("""CREATE TABLE record (
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
    lastUpdate DOUBLE
, day INTEGER);
            """)
        param = {}
        nbope = 0
        #on elimine les ope mere ou les ope dans les compte non bq ni especes
        for ope in models.Ope.objects.filter(compte__type__in=['b', 'e']).filter(filles_set__isnull=True).select_related('cat', "compte", "tiers", "ib", "rapp", "ope", "ope_pmv", "moyen"):
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
            param['subcategory'] = 'null'
            param['currency'] = 2
            param['amount'] = ope.montant
            param['date'] = ope.date.strftime('%Y-%m-%d')
            param['photo'] = 0
            param['voice'] = 0
            param['payee'] = 'null'
            param['note'] = ''
            param['account'] = 0
            if ope.moyen.type == 'r':
                param['type'] = 1
            else:
                param['type'] = 2
            param['repeat'] = 0
            param['place'] = nbope
            param['day'] = ope.date.strftime('%Y%m%d')
            param['lastUpdate'] = utils.idtostr(cpt, membre="lastUpdate", defaut=utils.timestamp())
            sql.w(u"""insert into record VALUES({id},{payment},{category},{subcategory},'{memo}',{currency},{amount},{date},{photo},{voice},{payee},'{note}',{account},{type},{repeat},{place},{day},{lastUpdate});""".format(**param))

        reponse = HttpResponse(sql.getvalue(), mimetype="text/plain")
        if not self.debug:
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse['Pragma'] = "public"
            reponse[
                "Content-Disposition"] = "attachment; filename=%s_%s.%s" % (self.nomfich,
                                                                            time.strftime(
                                                                            "%d_%m_%Y-%H_%M_%S",
                                                                            utils.timestamp()), self.extension_file
                                                                            )
        return reponse
