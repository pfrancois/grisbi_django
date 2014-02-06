# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time

from django.db import models as models_agg

from .. import models
from .. import utils
from . import export_base

# from django.core import exceptions as django_exceptions
from django.http import HttpResponse
from sql.pg import sqlite_db as db


class Export_view_sql_pocket_money(export_base.ExportViewBase):
    extension_file = "sql"
    debug = True
    nomfich = "export_full"
    model_initial = models.Ope
    form_class = export_base.Exportform_ope
    titre = "export sql pocket money"

    def export(self, query):
        self.debug = True
        sql = db()
        sql.query("""CREATE TABLE preferences
    (
    'databaseVersion'       INTEGER,
    'databaseID'            INTEGER,
    'multipleCurrencies'        BOOLEAN,
    'nextServerID'          INTEGER                                 -- db version 20
    );""")

        sql.query("INSERT INTO preferences VALUES(33, -6085268008074527042, NULL, NULL);")
        sql.query("""CREATE TABLE accounts(
    'deleted'           BOOLEAN DEFAULT 0,
    'timestamp'         INTEGER,
    'accountID'         INTEGER PRIMARY KEY AUTOINCREMENT,
    'displayOrder'          INTEGER,
    'account'           TEXT,
    'balanceOverall'        REAL,                                   -- not used
    'balanceCleared'        REAL,                                   -- not used
    'type'              INTEGER,
    'accountNumber'         TEXT,
    'institution'           TEXT,
    'phone'             TEXT,
    'expirationDate'        TEXT,
    'checkNumber'           TEXT,
    'notes'             TEXT,
    'iconFileName'          TEXT,
    'url'               TEXT,
    'ofxid'             TEXT,
    'ofxurl'            TEXT,
    'password'          TEXT,
    'fee'               REAL,
    'fixedPercent'          INTEGER,
    'limitAmount'           REAL,
    'noLimit'           BOOLEAN DEFAULT 1,
    'totalWorth'            BOOLEAN DEFAULT 1,
    'exchangeRate'          REAL,
    'currencyCode'          TEXT,
    'lastSyncTime'          INTEGER DEFAULT 0,
    'routingNumber'         TEXT,                                   -- db version 14
    'overdraftAccountID'        INTEGER,                                -- db version 17
    'keepTheChangeAccountID'    INTEGER,                                -- db version 22
    'keepChangeRoundTo'     REAL,                                   -- db version 26
    'serverID'          TEXT                                    -- db version 20
    );""")
        i = 0
        soldes = models.Compte.objects.select_related('ope').filter(ope__filles_set__isnull=True).annotate(
            solde=models_agg.Sum('ope__montant')).order_by('id')
        table_de_passage_type_compte = {"b": 0, "e": 1, "p": 6, "t": 7, "a": 3}
        for cpt in soldes:
            i += 1
            param = {}
            param['deleted'] = 0
            param['timestamp'] = utils.timestamp()
            param['accountID'] = utils.idtostr(cpt, defaut='0', membre='id')
            param['displayOrder'] = i
            param['account'] = utils.idtostr(cpt, membre='nom', defaut='')
            param['balanceOverall'] = utils.idtostr(cpt, membre='solde', defaut=0.0)
            param['balanceCleared'] = 0.0
            param['type'] = table_de_passage_type_compte[cpt.type]
            param['accountNumber'] = utils.idtostr(cpt, membre='nom', defaut='')
            param['institution'] = utils.idtostr(cpt.banque, membre='nom', defaut='')
            param['phone'] = ''
            param['expirationDate'] = ''
            param['checkNumber'] = ''
            param['notes'] = utils.idtostr(cpt, membre='notes', defaut='')
            param['iconFileName'] = ''
            param['url'] = ''
            param['ofxid'] = ''
            param['ofxurl'] = ""
            param['password'] = ''
            param['fee'] = 0.0
            param['fixedPercent'] = 0
            param['limitAmount'] = '0, '
            param['noLimit'] = 0
            param['totalWorth'] = 1
            param['exchangeRate'] = 1
            param['currencyCode'] = 'EUR'
            param['lastSyncTime'] = 0
            param['routingNumber'] = ''
            param['overdraftAccountID'] = ''
            param['keepTheChangeAccountID'] = ''
            param['keepChangeRoundTo'] = ''
            param['serverID'] = utils.idtostr(cpt)
            sql.query("""insert into category VALUES(:deleted,:timestamp,:accountID,:displayOrder,:account,:balanceOverall,:type,
                                                     :accountNumber,:institution,:phone,:expirationDate,:checkNumber,:notes,
                                                     :iconFileName,:url, :ofxid, :ofxurl,:password, :fee, :fixedPercent,
                                                     :limitAmount, :noLimit, :totalWorth, :exchangeRate, :currencyCode, :lastSyncTime,
                                                     :routingNumber, :overdraftAccountID, :keepTheChangeAccountID, :keepChangeRoundTo, :serverID);""",
                      param)

        return HttpResponse(sql.dump(), content_type="text/plain")


class Export_view_sql2(export_base.ExportViewBase):
    extension_file = "sql"
    debug = True
    nomfich = "export_full"
    model_initial = models.Ope
    form_class = export_base.Exportform_ope
    titre = "export sql pocket money"

    def export(self, query):
        self.titre = "export sql pocket money"
        self.debug = True
        sql = db()
        s = ("""BEGIN TRANSACTION;
CREATE TABLE preferences
    (
    'databaseVersion'       INTEGER,
    'databaseID'            INTEGER,
    'multipleCurrencies'        BOOLEAN,
    'nextServerID'          INTEGER                                 -- db version 20
    );
INSERT INTO "preferences" VALUES(33, -6085268008074527042, NULL, NULL);
CREATE TABLE accounts
    (
    'deleted'           BOOLEAN DEFAULT 0,
    'timestamp'         INTEGER,
    'accountID'         INTEGER PRIMARY KEY AUTOINCREMENT,
    'displayOrder'          INTEGER,
    'account'           TEXT,
    'balanceOverall'        REAL,                                   -- not used
    'balanceCleared'        REAL,                                   -- not used
    'type'              INTEGER,
    'accountNumber'         TEXT,
    'institution'           TEXT,
    'phone'             TEXT,
    'expirationDate'        TEXT,
    'checkNumber'           TEXT,
    'notes'             TEXT,
    'iconFileName'          TEXT,
    'url'               TEXT,
    'ofxid'             TEXT,
    'ofxurl'            TEXT,
    'password'          TEXT,
    'fee'               REAL,
    'fixedPercent'          INTEGER,
    'limitAmount'           REAL,
    'noLimit'           BOOLEAN DEFAULT 1,
    'totalWorth'            BOOLEAN DEFAULT 1,
    'exchangeRate'          REAL,
    'currencyCode'          TEXT,
    'lastSyncTime'          INTEGER DEFAULT 0,
    'routingNumber'         TEXT,                                   -- db version 14
    'overdraftAccountID'        INTEGER,                                -- db version 17
    'keepTheChangeAccountID'    INTEGER,                                -- db version 22
    'keepChangeRoundTo'     REAL,                                   -- db version 26
    'serverID'          TEXT                                    -- db version 20
    );"""
        )
        sql.w(s)
        i = 0
        soldes = models.Compte.objects.select_related('ope').filter(ope__filles_set__isnull=True).annotate(
            solde=models_agg.Sum('ope__montant')).order_by('id')
        table_de_passage_type_compte = {"b": 0, "e": 1, "p": 6, "t": 7, "a": 3}
        for cpt in soldes:
            i += 1
            param = {}
            param['deleted'] = 0
            param['timestamp'] = utils.timestamp()
            param['accountID'] = utils.idtostr(cpt, defaut='0', membre='id')
            param['displayOrder'] = i
            param['account'] = utils.idtostr(cpt, membre='nom', defaut='')
            param['balanceOverall'] = utils.idtostr(cpt, membre='solde', defaut=0.0)
            param['balanceCleared'] = 0.0
            param['type'] = table_de_passage_type_compte[cpt.type]
            param['accountNumber'] = utils.idtostr(cpt, membre='nom', defaut='')
            param['institution'] = utils.idtostr(cpt.banque, membre='nom', defaut='')
            param['phone'] = ''
            param['expirationDate'] = ''
            param['checkNumber'] = ''
            param['notes'] = utils.idtostr(cpt, membre='notes', defaut='')
            param['iconFileName'] = ''
            param['url'] = ''
            param['ofxid'] = ''
            param['ofxurl'] = ""
            param['password'] = ''
            param['fee'] = 0.0
            param['fixedPercent'] = 0
            param['limitAmount'] = '0, '
            param['noLimit'] = 0
            param['totalWorth'] = 1
            param['exchangeRate'] = 1
            param['currencyCode'] = 'EUR'
            param['lastSyncTime'] = 0
            param['routingNumber'] = ''
            param['overdraftAccountID'] = ''
            param['keepTheChangeAccountID'] = ''
            param['keepChangeRoundTo'] = ''
            param['serverID'] = utils.uuid()
            s = u"INSERT INTO 'accounts' VALUES({deleted}, {timestamp}, {accountID}, {displayOrder}, '{account}', {balanceOverall}, {balanceCleared}, {type}, '{accountNumber}', '{institution}', '{phone}', '{expirationDate}', '{checkNumber}', '{notes}', '{iconFileName}', '{url}', '{ofxid}', '{ofxurl}', '{password}', {fee}, {fixedPercent}, {limitAmount}, {noLimit}, {totalWorth}, {exchangeRate}, '{currencyCode}', {lastSyncTime}, '{routingNumber}', {overdraftAccountID}, {keepTheChangeAccountID}, {keepChangeRoundTo}, '{serverID}');".format(
                **param)
            sql.w(s)
            # TODO gerer les splits
        s = ("""CREATE TABLE splits
    (
    'splitID'           INTEGER PRIMARY KEY AUTOINCREMENT,
    'transactionID'         INTEGER,
    'amount'            REAL,
    'xrate'             REAL,
    'categoryID'            TEXT,
    'classID'           TEXT,
    'memo'              TEXT,
    'transferToAccountID'       INTEGER,
    'currencyCode'          TEXT,
    'ofxid'             TEXT
    );
""")
        # gestion des categories
        sql.w(s)
        s = ("""CREATE TABLE categories
    (
    'deleted'               BOOLEAN DEFAULT 0,
    'timestamp'             INTEGER,
    'categoryID'            INTEGER PRIMARY KEY AUTOINCREMENT,
    'category'              TEXT UNIQUE,
    'type'                  INTEGER,        -- 0 = expenseType 1 = incomeType
    'budgetPeriod'          INTEGER,        -- 0 = day, 1 = week, 2 = month, 3 = qtr, 4 = year, 5 = biweekly
    'budgetLimit'           REAL,
    'includeSubcategories'  BOOLEAN DEFAULT 0,
    'rollover'              BOOLEAN DEFAULT 0,                          -- db version 29
--  'startDate'             INTEGER,
    'serverID'              TEXT                                    -- db version 20
    );""")
        sql.w(s)
        i = 0
        for cat in models.Cat.objects.exclude(type='v').order_by('id'):
            i += 1
            param['deleted'] = 0
            param['timestamp'] = utils.timestamp()
            param['categoryID'] = cat.id
            param['category'] = utils.idtostr(cat, membre="nom", defaut="")
            if cat.type == 'r':
                param['type'] = 1
            else:
                param['type'] = 0
            param['budgetPeriod'] = 2
            param['budgetLimit'] = 0
            param['includeSubcategories'] = 0
            param['rollover'] = 0
            param['serverID'] = utils.uuid()
            s = u"INSERT INTO 'categories' VALUES(0, {timestamp}, {categoryID}, '{category}', {type}, {budgetPeriod}, {budgetLimit}, {includeSubcategories}, {rollover}, '{serverID}');".format(
                **param)
            sql.w(s)
        sql.w("""
CREATE TABLE payees
    (
    'deleted'               BOOLEAN DEFAULT 0,
    'timestamp'             INTEGER,
    'payeeID'               INTEGER PRIMARY KEY AUTOINCREMENT,
    'payee'                 TEXT UNIQUE,
    'latitude'              REAL,
    'longitude'             REAL,
    'serverID'              TEXT                                    -- db version 20
    );""")
        i = 0
        for tiers in models.Tiers.objects.order_by('id'):
            i += 1
            param['deleted'] = 0
            param['timestamp'] = utils.timestamp()
            param['payeeID'] = tiers.id
            param['payee'] = utils.idtostr(tiers, membre="nom", defaut="")
            param['latitude'] = ''
            param['longitude'] = ''
            param['serverID'] = utils.uuid()
            s = u"INSERT INTO 'payees' VALUES(0, {timestamp}, {payeeID}, '{payee}', {latitude}, {longitude}, '{serverID}');".format(**param)
            sql.w(s)
        sql.w("""CREATE TABLE categorypayee
    (
    'categoryID'                INTEGER,                                -- these need to be text will be a serverID
    'payeeID'               INTEGER,                                -- these need to be text will be a serverid
    'deleted'               BOOLEAN DEFAULT 0,                          -- db version 20
    'serverID'              TEXT,                                   -- db version 20
    'timestamp'             INTEGER,                                -- db version 20
    PRIMARY KEY (categoryID, payeeID)
    );""")
        sql.w("""CREATE TABLE classes
    (
    'deleted'               BOOLEAN DEFAULT 0,
    'timestamp'             INTEGER,

    'classID'               INTEGER PRIMARY KEY AUTOINCREMENT,
    'class'                 TEXT UNIQUE,
    'serverID'              TEXT                                    -- db version 20
    );""")
        i = 0
        for ib in models.Ib.objects.order_by('id'):
            i += 1
            param['deleted'] = 0
            param['timestamp'] = utils.timestamp()
            param['classID'] = ib.id
            param['class'] = utils.idtostr(ib, membre="nom", defaut="")
            param['serverID'] = utils.uuid()
            s = "INSERT INTO 'classes' VALUES(0, {timestamp}, {classID}, '{class}', '{serverID}');".format(**param)
        sql.w("""
CREATE TABLE ids
    (
    'deleted'               BOOLEAN DEFAULT 0,
    'timestamp'             INTEGER,
    'idID'                  INTEGER PRIMARY KEY AUTOINCREMENT,
    'id'                    TEXT UNIQUE,
    'serverID'              TEXT                                    -- db version 20
    );
INSERT INTO "ids" VALUES(0, 1366406971, 1, '#', '385F481E-CDD3-4EF1-90A8-8A7B13A66BD0');
INSERT INTO "ids" VALUES(0, 1366406971, 2, 'ATM', 'D82E9ACD-7CE6-4964-9DBE-DC5490F2750B');
INSERT INTO "ids" VALUES(0, 1366406971, 3, 'Credit Card #', 'DE4E2495-7420-4DF9-AF2F-C27922C573F7');
INSERT INTO "ids" VALUES(0, 1366406971, 4, 'Debit Card#', '84998884-DE88-479F-B45A-4C686EA4635B');
INSERT INTO "ids" VALUES(0, 1366406971, 5, 'ETF#', '5B873FE7-6406-4915-8A27-3232DA2C48AC');
CREATE TABLE exchangeRates
    (
    'deleted'           BOOLEAN DEFAULT 0,
    'timestamp'         INTEGER,
    'currencyCode'          TEXT PRIMARY KEY,
    'exchangeRate'          REAL
    );
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'SAR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BGN', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'EUR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'TWD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'CZK', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'DKK', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'USD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'ILS', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'HUF', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'ISK', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'JPY', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'KRW', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'NOK', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'PLN', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BRL', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'CHF', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'RON', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'RUB', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'HRK', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'ALL', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'SEK', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'THB', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'TRY', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'PKR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'IDR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'UAH', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BYR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'LVL', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'LTL', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'TJS', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'IRR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'VND', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'AMD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'AZN', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'MKD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'ZAR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'GEL', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'INR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'MYR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'KZT', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'KGS', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'KES', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'TMT', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'UZS', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'MNT', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'CNY', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'GBP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'KHR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'LAK', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'SYP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'LKR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'CAD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'ETB', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'NPR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'AFN', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'PHP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'MVR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'NIO', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BOB', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'CLP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'NZD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'GTQ', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'RWF', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'XOF', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'IQD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'MXN', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'CSD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BND', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BDT', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'DZD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'EGP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'HKD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'AUD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'PEN', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'LYD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'SGD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BAM', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'MOP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'CRC', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'MAD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'PAB', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'TND', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'DOP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'OMR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'JMD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'VEF', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'YER', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'COP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'RSD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BZD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'JOD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'TTD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'ARS', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'LBP', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'ZWL', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'KWD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'AED', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'UYU', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'BHD', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'PYG', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'QAR', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'HNL', '');
INSERT INTO "exchangeRates" VALUES(0, 1366406972, 'TZS', '');
""")
        reponse = HttpResponse(sql.getvalue(), content_type="text/plain")
        if not self.debug:
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse['Pragma'] = "public"
            reponse["Content-Disposition"] = "attachment; filename=%s_%s.%s" % (self.nomfich,
                                                                                time.strftime("%d_%m_%Y-%H_%M_%S", utils.timestamp()),
                                                                                self.extension_file
            )
        return reponse
