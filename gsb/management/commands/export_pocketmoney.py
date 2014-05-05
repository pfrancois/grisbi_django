# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time
import os
import sqlite3

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from django.conf import settings
from django.core.exceptions import ValidationError

from ... import models
from ... import utils
from ...io import sqlite
import pprint

def dec2float(d):
    return float(str(d))


def time2int(t):
    return time.mktime(t.timetuple())


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def log(self,msg):
        self.stdout.write(unicode(pprint.pformat(msg),'latin1'))

    @transaction.atomic
    def handle(self, *args, **options):
        nomfich = os.path.join(settings.PROJECT_PATH, "Untitled.pocketmoney", "test.sql")
        try:
            os.remove(nomfich)
            self.log('db pocketmoney efface')
        except (OSError,WindowsError) as e:
            self.log(e)
            quit()
        sql = sqlite.sqlite_db(db_file=nomfich)
        config = models.config.objects.get_or_create(id=1, defaults={'id': 1})[0]
        lastmaj = config.derniere_import_money_journal
        log = self.log
        log('test preablables')
        log('test pas deux nom de tiers identiques en cours')
        verif = list(models.Tiers.objects.values_list('nom', flat=True))
        doublons = [row for row in verif if verif.count(row.lower()) > 1]
        if len(doublons) > 0:
            raise ValidationError(doublons)
        sql.script("CREATE TABLE preferences(\n"
                   "    'databaseVersion'       INTEGER,\n"
                   "    'databaseID'            INTEGER,\n"
                   "    'multipleCurrencies'        BOOLEAN,\n"
                   "    'nextServerID'          INTEGER                                 -- db version 20\n"
                   ");"
        )
        sql.script("INSERT INTO preferences VALUES (33,3818511773711874600,null,null);")
        sql.script("CREATE TABLE repeatingTransactions(\n"
                   "'repeatingID'   INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                   "'deleted'   BOOLEAN DEFAULT 0,\n"
                   "'timestamp'   INTEGER,\n"
                   "'lastProcessedDate'  INTEGER,\n"
                   "'transactionID'   INTEGER,\n"
                   "'type'    INTEGER,  -- none = 0, daily=1, weekly=2, monthlybyday = 3, monthlybydate = 4, yearly = 5\n"
                   "'endDate'   INTEGER,\n"
                   "'frequency'   INTEGER,\n"
                   "'repeatOn'   INTEGER,\n"
                   "'startOfWeek'   INTEGER,\n"
                   "'serverID'   TEXT,         -- db version 20\n"
                   "'sendLocalNotifications' INTEGER,        -- db version 29\n"
                   "'notifyDaysInAdvance'  INTEGER         -- db version 29\n"
                   ");\n")
        log('preference ok')
        sql.script(
            "CREATE TABLE accounts(\n"
            "'deleted'   BOOLEAN DEFAULT 0,\n"
            "'timestamp'   INTEGER,\n"
            "'accountID'   INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "'displayOrder'   INTEGER,\n"
            "'account'    TEXT,\n"
            "'balanceOverall'   REAL,         -- not used\n"
            "'balanceCleared'   REAL,         -- not used\n"
            "'type'     INTEGER,\n"
            "'accountNumber'   TEXT,\n"
            "'institution'    TEXT,\n"
            "'phone'    TEXT,\n"
            "'expirationDate'   TEXT,\n"
            "'checkNumber'    TEXT,\n"
            "'notes'    TEXT,\n"
            "'iconFileName'    TEXT,\n"
            "'url'     TEXT,\n"
            "'ofxid'    TEXT,\n"
            "'ofxurl'   TEXT,\n"
            "'password'   TEXT,\n"
            "'fee'     REAL,\n"
            "'fixedPercent'    INTEGER,\n"
            "'limitAmount'    REAL,\n"
            "'noLimit'    BOOLEAN DEFAULT 1,\n"
            "'totalWorth'    BOOLEAN DEFAULT 1,\n"
            "'exchangeRate'    REAL,\n"
            "'currencyCode'   TEXT,\n"
            "'lastSyncTime'   INTEGER DEFAULT 0,\n"
            "'routingNumber'   TEXT,         -- db version 14\n"
            "'overdraftAccountID'  INTEGER,        -- db version 17\n"
            "'keepTheChangeAccountID' INTEGER,        -- db version 22\n"
            "'keepChangeRoundTo'  REAL,         -- db version 26\n"
            "'serverID'   TEXT         -- db version 20\n"
            ")\n"
        )
        i = 0
        for cpt in models.Compte.objects.order_by('id'):
            i += 1
            cpt_type=None
            if cpt.type == "b":
                cpt_type = 0
            if cpt.type == "e":
                cpt_type = 1
            if cpt.type == "a":
                cpt_type = 6
            if cpt.type == "t":
                cpt_type = 9
            if models.Ope.objects.filter(compte_id=cpt.id).exists():
                cpt_chknumber="%s" % models.Ope.objects.filter(compte_id=cpt.id).aggregate(Max('num_cheque'))['num_cheque__max']
            else:
                cpt_chknumber=''
            param = {'deleted': 0,
                     'timestamp': time2int(cpt.lastupdate),
                     'accountID': cpt.id,
                     'displayOrder': i,
                     'account': utils.idtostr(cpt, membre='nom', defaut=''),
                     'balanceOverall': 0.0,
                     'balanceCleared': 0.0,
                     'type': cpt_type,
                     'accountNumber': utils.idtostr(cpt, membre='num_compte', defaut=''),
                     'institution': utils.idtostr(cpt.banque, membre='nom', defaut=''),
                     'phone': '',
                     'expirationDate': '',
                     'checkNumber': cpt_chknumber,
                     'notes': utils.idtostr(cpt, membre='notes', defaut=''),
                     'iconFileName': '',
                     'url': '',
                     'ofxid': '',
                     'ofxurl': "",
                     'password': '',
                     'fee': 0.0,
                     'fixedPercent': 0,
                     'limitAmount': 0,
                     'noLimit': 0,
                     'totalWorth': dec2float(cpt.solde_espece()),
                     'exchangeRate': 1,
                     'currencyCode': 'EUR',
                     'lastSyncTime': time2int(lastmaj),
                     'routingNumber': '',
                     'overdraftAccountID': None,
                     'keepTheChangeAccountID': None,
                     'keepChangeRoundTo': None,
                     'serverID': cpt.uuid
            }
            sql.param("""insert into accounts VALUES(:deleted, :timestamp, :accountID, :displayOrder, :account,
                                                :balanceOverall, :balanceCleared, :type, :accountNumber, :institution,
                                                :phone, :expirationDate, :checkNumber, :notes,
                                                :iconFileName, :url, :ofxid, :ofxurl, :password,
                                                :fee, :fixedPercent, :limitAmount, :noLimit, :totalWorth,
                                                :exchangeRate, :currencyCode, :lastSyncTime, :routingNumber,
                                                :overdraftAccountID, :keepTheChangeAccountID, :keepChangeRoundTo, :serverID);""",
                      param, commit=False)
        sql.commit()
        log('compte ok')
        log("cat")
        sql.script("CREATE TABLE categories(\n"
                   " 'deleted'    BOOLEAN DEFAULT 0,\n"
                   " 'timestamp'    INTEGER,\n"
                   " 'categoryID'    INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                   " 'category'    TEXT UNIQUE,\n"
                   " 'type'     INTEGER,  -- 0=expenseType 1=incomeType\n"
                   " 'budgetPeriod'    INTEGER,  -- 0=day, 1=week, 2=month, 3=qtr, 4=year, 5=biweekly\n"
                   " 'budgetLimit'    REAL,\n"
                   " 'includeSubcategories'    BOOLEAN DEFAULT 0,\n"
                   " 'rollover'    BOOLEAN DEFAULT 0,       -- db version 29\n"
                   "-- 'startDate'    INTEGER,\n"
                   " 'serverID'    TEXT         -- db version 20\n"
                   " );"
        )
        i = 0
        param = {}
        for cat in models.Cat.objects.all().order_by('id'):
            i += 1
            param['deleted'] = 0
            param['timestamp'] = time2int(cat.lastupdate)
            param['categoryID'] = cat.id
            param['category'] = utils.idtostr(cat, membre="nom", defaut="")
            if param['category'] == u"Opération Ventilée":
                param['category']="<--Splits-->"
            if cat.type == 'r':
                param['type'] = 1
            else:
                param['type'] = 0
            param['budgetPeriod'] = 2
            param['budgetLimit'] = 0
            param['includeSubcategories'] = 1
            param['rollover'] = 0
            param['serverID'] = cat.uuid
            chaine = u"INSERT INTO 'categories' VALUES(:deleted, :timestamp, :categoryID, :category, :type" \
                     u", :budgetPeriod, :budgetLimit, :includeSubcategories, :rollover, :serverID);"
            sql.param(chaine, param, commit=False)
        sql.commit()
        nbsql = sql.rep_one('select count(categoryID) from categories')
        nb_django = models.Cat.objects.count()
        if nbsql != nb_django:
            raise ValidationError("attention probleme (%s != %s)" % (nbsql, nb_django))
        log("cat ok")
        log("tiers")
        sql.script("CREATE TABLE payees(\n"
                   "    'deleted'               BOOLEAN DEFAULT 0,\n"
                   "    'timestamp'             INTEGER,\n"
                   "    'payeeID'               INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                   "    'payee'                 TEXT UNIQUE,\n"
                   "    'latitude'              REAL,\n"
                   "    'longitude'             REAL,\n"
                   "    'serverID'              TEXT                                    -- db version 20\n"
                   "    );"
        )
        param = {}
        for tiers in models.Tiers.objects.order_by('id'):
            i += 1
            param['deleted'] = True
            param['timestamp'] = time2int(tiers.lastupdate)
            param['payeeID'] = tiers.id
            param['payee'] = tiers.nom
            param['latitude'] = 0
            param['longitude'] = 0
            param['serverID'] = tiers.uuid
            chaine = u"INSERT INTO 'payees' VALUES(0, :timestamp, :payeeID, :payee, :latitude," \
                     u" :longitude, :serverID);"
            try:
                sql.param(chaine, param, commit=False)
            except sqlite3.IntegrityError:
                print "-%s-" % param
                raise ValidationError(param)
        sql.commit()
        sql.script("CREATE TABLE categorypayee\n"
                   "    (\n"
                   "    'categoryID'                INTEGER,                                -- these need to be text will be a serverID\n"
                   "    'payeeID'               INTEGER,                                -- these need to be text will be a serverid\n"
                   "    'deleted'               BOOLEAN DEFAULT 0,                          -- db version 20\n"
                   "    'serverID'              TEXT,                                   -- db version 20\n"
                   "    'timestamp'             INTEGER,                                -- db version 20\n"
                   "    PRIMARY KEY (categoryID, payeeID)\n"
                   "    );"
        )
        nbsql = sql.rep_one('select count(payeeID) from payees')
        nb_django = models.Tiers.objects.count()
        if nbsql != nb_django:
            raise ValidationError("attention probleme (%s != %s)" % (nbsql, nb_django))
        log("tiers ok")
        log('ib')
        sql.script("""CREATE TABLE classes
                    (
                    'deleted'               BOOLEAN DEFAULT 0,
                    'timestamp'             INTEGER,
                    'classID'               INTEGER PRIMARY KEY AUTOINCREMENT,
                    'class'                 TEXT UNIQUE,
                    'serverID'              TEXT                                    -- db version 20
                    );""")
        param = {}
        for ib in models.Ib.objects.order_by('id'):
            i += 1
            param['deleted'] = 0
            param['timestamp'] = time2int(ib.lastupdate)
            param['classID'] = ib.id
            param['class'] = utils.idtostr(ib, membre="nom", defaut="")
            param['serverID'] = ib.uuid
            chaine = "INSERT INTO 'classes' VALUES(0, :timestamp, :classID, :class, :serverID);"
            try:
                sql.param(chaine, param, commit=False)
                pass
            except sqlite3.IntegrityError:
                print "-%s-" % param
                raise ValidationError(param)
        sql.commit()
        log('ib ok')
        sql.script("CREATE TABLE ids\n"
                   "    (\n"
                   "    'deleted'               BOOLEAN DEFAULT 0,\n"
                   "    'timestamp'             INTEGER,\n"
                   "    'idID'                  INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                   "    'id'                    TEXT UNIQUE,\n"
                   "    'serverID'              TEXT                                    -- db version 20\n"
                   "    );\n"
                   "INSERT INTO ids VALUES(0, 1366406971, 1, '#', '385F481E-CDD3-4EF1-90A8-8A7B13A66BD0');\n"
                   "INSERT INTO ids VALUES(0, 1366406971, 2, 'ATM', 'D82E9ACD-7CE6-4964-9DBE-DC5490F2750B');\n"
                   "INSERT INTO ids VALUES(0, 1366406971, 3, 'Credit Card #', 'DE4E2495-7420-4DF9-AF2F-C27922C573F7');\n"
                   "INSERT INTO ids VALUES(0, 1366406971, 4, 'Debit Card#', '84998884-DE88-479F-B45A-4C686EA4635B');\n"
                   "INSERT INTO ids VALUES(0, 1366406971, 5, 'ETF#', '5B873FE7-6406-4915-8A27-3232DA2C48AC');\n"
                   "CREATE TABLE exchangeRates\n"
                   "    (\n"
                   "    'deleted'           BOOLEAN DEFAULT 0,\n"
                   "    'timestamp'         INTEGER,\n"
                   "    'currencyCode'          TEXT PRIMARY KEY,\n"
                   "    'exchangeRate'          REAL\n"
                   "    );\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'SAR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BGN', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'EUR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'TWD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'CZK', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'DKK', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'USD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'ILS', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'HUF', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'ISK', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'JPY', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'KRW', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'NOK', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'PLN', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BRL', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'CHF', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'RON', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'RUB', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'HRK', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'ALL', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'SEK', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'THB', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'TRY', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'PKR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'IDR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'UAH', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BYR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'LVL', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'LTL', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'TJS', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'IRR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'VND', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'AMD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'AZN', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'MKD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'ZAR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'GEL', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'INR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'MYR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'KZT', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'KGS', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'KES', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'TMT', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'UZS', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'MNT', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'CNY', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'GBP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'KHR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'LAK', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'SYP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'LKR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'CAD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'ETB', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'NPR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'AFN', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'PHP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'MVR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'NIO', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BOB', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'CLP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'NZD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'GTQ', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'RWF', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'XOF', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'IQD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'MXN', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'CSD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BND', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BDT', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'DZD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'EGP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'HKD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'AUD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'PEN', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'LYD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'SGD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BAM', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'MOP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'CRC', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'MAD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'PAB', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'TND', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'DOP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'OMR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'JMD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'VEF', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'YER', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'COP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'RSD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BZD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'JOD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'TTD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'ARS', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'LBP', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'ZWL', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'KWD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'AED', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'UYU', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'BHD', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'PYG', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'QAR', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'HNL', '');\n"
                   "INSERT INTO exchangeRates VALUES(0, 1366406972, 'TZS', '');\n"
                   "CREATE TABLE filters ("
                   "        'filterID' INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                   "        'deleted' BOOLEAN DEFAULT 0,\n"
                   "        'timestamp' INTEGER,\n"
                   "        'filterName' TEXT,\n"
                   "        'type' INTEGER,\n"
                   "        'dateFrom' INTEGER,\n"
                   "        'dateTo' INTEGER,\n"
                   "        'accountID' INTEGER,\n"
                   "        'categoryID' TEXT,\n"
                   "        'payee' TEXT,\n"
                   "        'classID' TEXT,\n"
                   "        'checkNumber' TEXT,\n"
                   "        'cleared' INTEGER,\n"
                   "        'spotlight' TEXT,\n"
                   "        'selectedFilterName' TEXT,\n"
                   "        'serverID' TEXT \n"
                   " );"
        )
        log('ope')
        sql.script(("CREATE TABLE splits (\n"
                    "    'splitID'           INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                    "    'transactionID'     INTEGER,\n"
                    "    'amount'            REAL,\n"
                    "    'xrate'             REAL,\n"
                    "    'categoryID'        TEXT,\n"
                    "    'classID'           TEXT,\n"
                    "    'memo'              TEXT,\n"
                    "    'transferToAccountID'       INTEGER,\n"
                    "    'currencyCode'      TEXT,\n"
                    "    'ofxid'             TEXT\n"
                    ");\n"
        ))
        sql.script(("CREATE TABLE transactions (\n"
                    " 'deleted'        BOOLEAN DEFAULT 0,\n"
                    " 'transactionID'  INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                    " 'timestamp'      INTEGER,\n"
                    " 'type'           INTEGER, -- 0 depense 1 recette 2 vir envoye 3 vir recu\n"
                    " 'date'           INTEGER, -- date au format timestamp\n"
                    " 'cleared'        BOOLEAN, -- si c'est rapp ou non\n"
                    " 'accountID'      INTEGER,\n"
                    " 'payee'          TEXT,\n"
                    " 'checkNumber'    TEXT,\n"
                    " 'subTotal'       REAL,\n"
                    " 'ofxID'          TEXT,         -- db version 15\n"
                    " 'image'          BLOB,         -- db version 15  semi-colon separated list of filenames\n"
                    " 'serverID'       TEXT,         -- db version 20\n"
                    " 'overdraftID'    TEXT         -- db version 23\n"
                    " )"
        ))
        type_ope=""
        for ope in models.Ope.objects.order_by('id').select_related('cat', 'moyen', 'tiers', 'ib'):
            param = {}
            try:
                if ope.id % 1000 == 0:
                    log("%s" % ope.id)
                if not ope.is_fille:# dans ce cas, on cree une transaction (c'est pour les stand alone et les mere)
                    param = {
                        'transactionID': ope.id,
                        'deleted': 0,
                        'timestamp': time2int(ope.lastupdate),
                        'date': time2int(ope.date),
                        'cleared': True if ope.rapp else False,
                        'accountID': ope.compte_id,
                        'payee': ope.tiers.nom,
                        'checkNumber': ope.num_cheque,
                        'subTotal': dec2float(ope.montant),
                        'image':'',
                        'ofxID': '',
                        'serverID': ope.uuid,
                        'overdraftID': ''
                    }
                    if ope.moyen.type == "d":
                        param['type'] = 0
                    if ope.moyen.type == "r":
                        param['type'] = 1
                    if ope.moyen.type == "v":
                        if ope.montant < 0:
                        #ope virement branche origine
                            param['type'] = 2
                        else:
                        #ope virement branche destination
                            param['type'] = 3
                    if not param["cleared"] and ope.is_mere:
                        filles = ope.filles_set.all()
                        for o in filles.values('id', 'pointe', 'rapp'):
                            if o['rapp'] is not None:
                                log("attention l'ope %s n'est pas rapproche alors q'une de ses filles l'est " % ope.id)
                                param['cleared'] = True
                    type_ope="transact"
                    chaine = u"INSERT INTO transactions (deleted, transactionID, timestamp,type, date, cleared, accountID, " \
                             u" payee, checkNumber, subTotal, ofxID, image, serverID, overdraftID) " \
                             u"   VALUES(0, :transactionID, :timestamp, :type, :date," \
                             u" :cleared, :accountID, :payee, :checkNumber, :subTotal, :ofxID, :image, :serverID, :overdraftID);"
                    sql.param(chaine, param, commit=False)
                if not ope.is_mere:
                    param['amount'] = dec2float(ope.montant)
                    param['xrate'] = 1
                    if ope.cat.nom == u"Opération Ventilée":
                        param['categoryID']="<--Splits-->"
                    else:
                        param['categoryID']= ope.cat.nom
                    param['classID'] = utils.idtostr(ope.ib, 'nom', '')
                    param['memo'] = ope.notes
                    param['transferToAccountID'] = utils.idtostr(ope.jumelle, "compte_id", '')
                    param['currencyCode'] = 'EUR'
                    param['ofxid'] = ""
                    if ope.is_fille:
                        type_ope="split_fille"
                        param['splitID'] = ope.id
                        param['transactionID'] = ope.mere.id
                    else:
                        type_ope="split_alone"
                        param['splitID'] = ope.id
                    chaine = u"INSERT INTO splits  " \
                             u"   VALUES(:splitID, :transactionID, :amount, :xrate, :categoryID, :classID," \
                             u" :memo, :transferToAccountID, :currencyCode, :ofxid);"
                    sql.param(chaine, param, commit=False)
            except Exception as e:
                print type_ope
                log(param)
                print ope.id
                print ope
                raise e
        sql.commit()
        sql.script("CREATE TABLE categoryBudgets -- db version 29\n"
                   "(\n"
                   "'categoryBudgetID' 		INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                   "'deleted' 			BOOLEAN DEFAULT 0,\n"
                   "'serverID' 			TEXT,\n"
                   "'timestamp' 			INTEGER,\n"
                   "'categoryName' 			TEXT,\n"
                   "'date' 				INTEGER,\n"
                   "'budgetLimit' 			REAL,\n"
                   "'resetRollover' 		BOOLEAN DEFAULT 0\n"
                   ");\n" )
        sql.script("""CREATE TABLE databaseSyncList
	                ('databaseID'	TEXT PRIMARY KEY,
	                'lastSyncTime'	INTEGER    );""")
        sql.script("INSERT INTO databaseSyncList VALUES('1928cc8254761f60874d3cccae2e88abf01080ed',1396478218);")
        sql.script(("CREATE INDEX accountDisplayOrder ON accounts (displayOrder);\n"
                    "CREATE INDEX accountNames ON accounts (account);\n"
                    "CREATE INDEX accountServerIDs ON accounts (serverID);\n"
                    "CREATE INDEX categoryIDs ON categories (categoryID);\n"
                    "CREATE INDEX categoryName ON categories (category);\n"
                    "CREATE INDEX categoryServerIDs ON categories (serverID);\n"
                    "CREATE INDEX classIDs ON classes (classID);\n"
                    "CREATE INDEX className ON classes (class);\n"
                    "CREATE INDEX classServerIDs ON classes (serverID);\n"
                    "CREATE INDEX cpCategoryIDs ON categorypayee (categoryID);\n"
                    "CREATE INDEX cpPayeeIDs ON categorypayee (payeeID);\n"
                    "CREATE INDEX currencyCodes ON exchangeRates (currencyCode);\n"
                    "CREATE INDEX idIDs ON ids (idID);\n"
                    "CREATE INDEX idName ON ids (id);\n"
                    "CREATE INDEX idServerIDs ON ids (serverID);\n"
                    "CREATE INDEX payeeIDs ON payees (payeeID);\n"
                    "CREATE INDEX payeeName ON payees (payee);\n"
                    "CREATE INDEX payeeServerIDs ON payees (serverID);\n"
                    "CREATE INDEX repeatingIDs ON repeatingTransactions (repeatingID);\n"
                    "CREATE INDEX repeatingTransactionServerIDs ON repeatingTransactions (serverID);\n"
                    "CREATE INDEX splitCategories ON splits (categoryID);\n"
                    "CREATE INDEX transactionIDs ON transactions (transactionID);\n"
                    "CREATE INDEX transactionOFXIDs ON transactions (ofxID);\n"
                    "CREATE INDEX transactionPayees ON transactions (payee);\n"
                    "CREATE INDEX transactionServerIDs ON transactions (serverID);\n"
                    "CREATE INDEX transactionSplitIDs ON splits (transactionID);\n"
                    "CREATE INDEX transactionTypes ON transactions (type);\n"
                    "CREATE INDEX transactionsByAccount ON transactions (accountID, date);\n"
                    "CREATE INDEX transactionsByDate ON transactions (date);\n"
                    "CREATE INDEX typeaccount ON accounts (type, account);"
        ))
