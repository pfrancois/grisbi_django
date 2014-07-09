# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time
import os
import sqlite3 as sqlite

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.db import models as models_agg
import dateutil.rrule as rrule
from dateutil.relativedelta import relativedelta

from ... import models
from ... import utils
from django.utils.encoding import smart_unicode
import pprint

class Command(BaseCommand):
    option_list = BaseCommand.option_list

    @transaction.atomic
    def handle(self, *args, **options):
        nomfich = os.path.join(settings.PROJECT_PATH, "MoneyDatabase.sql")
        try:
            os.remove(nomfich)
            self.stdout.write('db effacee')
        except OSError:
            pass
        sql = sqlite.connect(nomfich)
        retour = proc_sql_export(sql, self.stdout.write)
        self.stdout.write(retour)


def proc_sql_export(sql, log=None):
    cur = sql.cursor()
    if log is None:
        log = lambda x: None
        # attention ce n'est pas les comptes
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
    cur.executescript(s)
    sql.commit()
    # calcul des budgets
    nb_bud = 0
    date_min = models.Ope.objects.aggregate(element=models_agg.Min('date'))['element']
    date_max = models.Ope.objects.aggregate(element=models_agg.Max('date'))['element']
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=date_min + relativedelta(day=1), until=date_max + relativedelta(day=1)):
        nb_bud += 1
        cur.execute("insert into budget VALUES(:id,:month,:year,:amount,:lastupdate);", {'id': nb_bud,
                                                                                         'month': dt.month,
                                                                                         'year': dt.year,
                                                                                         'amount': 0,
                                                                                         'lastupdate': time.mktime(dt.timetuple())})
    sql.commit()
    log('budget')
    # les categories
    cur.execute("""CREATE TABLE category (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type INTEGER,
            color INTEGER,
            place INTEGER,
            lastupdate DOUBLE);
        """)
    cur.execute("""CREATE TABLE subcategory (
            id INTEGER PRIMARY KEY,
            category INTEGER,
            name TEXT,
            place INTEGER,
            lastupdate DOUBLE);
        """)
    param = {}
    list_cat_id=list(models.Cat.objects.order_by('id').values_list('id',flat=True))
    for cat in models.Cat.objects.order_by('nom'):
        param['id'] = cat.id
        param['name'] = smart_unicode(cat.nom)
        param['color'] = int(utils.idtostr(cat, membre="couleur", defaut="#FFFFFF")[1:], 16)
        param['place'] = list_cat_id.index(cat.id)
        param['lastupdate'] = utils.datetotimestamp(cat.lastupdate)
        if cat.type == 'r':
            param['type'] = 1
        else:
            param['type'] = 2
        cur.execute(u"insert into category VALUES(:id,:name,:type,:color,:place,:lastupdate);", param)
    sql.commit()
    log('cat et sous cat')
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
    cur.executescript(chaine)
    sql.commit()
    log('devises')
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
    cur.executescript(chaine)
    sql.commit()
    param = {}
    liste_compte = models.Compte.objects.all().order_by('id')
    i = 0
    for cpt in liste_compte:
        i += 1
        param['id'] = cpt.id
        param['name'] = smart_unicode(cpt.nom)
        param['symbol'] = i//9
        param['color'] = int(utils.idtostr(cpt, membre="couleur", defaut="FFFFFF")[1:], 16)
        param['place'] = i
        param['lastupdate'] = utils.datetotimestamp(cpt.lastupdate)
        cur.execute(u"insert into payment VALUES(:id,:name,:symbol,:color,:place,:lastupdate);", param)
    sql.commit()
    log('comptes')
    log('debut ope')
    # operation
    cur.execute("""CREATE TABLE record (
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
                    day INTEGER);"""
    )
    param = {}
    nbope = 0
    pk_avance=models.Cat.objects.get_or_create(nom='Avance',  defaults={"nom":'Avance'})[0]
    pk_remboursement=models.Cat.objects.get_or_create(nom='remboursement',  defaults={"nom":'remboursement'})[0]
    for ope in models.Ope.objects.select_related('cat', "compte", "tiers", "moyen"):
        nbope += 1
        param['id'] = ope.id
        # gestion des paiments on recupere l'id qui va bien
        param['payment'] = ope.compte.id
        param['category'] = utils.nulltostr(ope.cat.id)
        param['memo'] = ope.tiers.nom
        param['amount'] = abs(float(utils.idtostr(ope, membre="montant",defaut=0)))
        param['subcategory'] = None
        param['currency'] = 2
        param['date'] = 0
        param['photo'] = 0
        param['voice'] = 0
        param['payee'] = None
        param['note'] = None
        param['account'] = 0
        if ope.moyen.type == 'r':
            param['type'] = 1
        elif ope.moyen.type == 'd':
            param['type'] = 2
        else:
            if ope.montant > 0:
                param['type'] = 1
            else:
                param['type'] = 2
        param['repeat'] = 0
        param['place'] = None
        param['day'] = ope.date.strftime('%Y%m%d')
        param['lastupdate'] = time.mktime(ope.lastupdate.timetuple())
        if ope.cat.nom not in (u"Opération Ventilée","Virement"):
            if ope.montant > 0:
                if ope.cat.type == 'r':
                    param['category'] = utils.nulltostr(ope.cat.id)
                else:
                    param['category'] = utils.nulltostr(pk_avance.pk)
            else:
                if ope.cat.type == 'd':
                    param['category'] = utils.nulltostr(ope.cat.id)
                else:
                    param['category'] = utils.nulltostr(pk_remboursement.pk)
        else:
            param['category'] = utils.nulltostr(ope.cat.id)
            param['amount'] = 0
        cur.execute(u"""insert into record VALUES(:id,:payment,:category,:subcategory,:memo,:currency,
            :amount,:date,:photo,:voice,:payee,:note,:account,:type,:repeat,:place,:lastupdate,:day);""", param)
        if nbope % 1000 == 0:
            log("%s" % nbope)
    sql.commit()
    log('ope')
    cur.execute('DROP INDEX IF EXISTS budget_month_index;')
    cur.execute('CREATE INDEX budget_month_index on budget(month);')
    cur.execute('DROP INDEX IF EXISTS record_day_index;')
    cur.execute('CREATE INDEX record_day_index on record(day);')
    cur.execute('DROP INDEX IF EXISTS record_repeat_index;')
    cur.execute('CREATE INDEX record_repeat_index on record(repeat);')
    log('fini')
    return "ok"
