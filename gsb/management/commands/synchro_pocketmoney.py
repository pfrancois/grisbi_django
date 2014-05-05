# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time
import os
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError

from ... import models
from ... import utils
from ...io import sqlite


def dec2float(d):
    return float(str(d))


def time2int(t):
    return time.mktime(t.timetuple())


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    @transaction.atomic
    def handle(self, *args, **options):
        table_de_passage_type_compte = {"b": 0, "e": 1, "p": 4, "t": 7, "a": 6}
        table_de_passage_compte_type = ("b"#compte bancaire std
                                        ,"e"#cash
                                        ,"b"#credit card
                                        ,"a"#asset
                                        ,"p"#liability
                                        ,"b"#online
                                        ,"a"#saving
                                        ,"t"#money market
                                        ,"b"#credit line
        )

        nomfich = os.path.join(settings.PROJECT_PATH, "Untitled.pocketmoney", "PocketMoneyDB.sql")
        sql = sqlite.sqlite_db(db_file=nomfich)
        config = models.config.objects.get_or_create(id=1, defaults={'id': 1})[0]
        lastmaj = config.derniere_import_money_journal
        log = self.stdout.write
        rep=sql.rep("select * from accounts where timestamp>%s;"%lastmaj)
        cpt_maj=0
        for cpt in rep:
            maj=False
            try:
                cpt_gsb=models.Compte.objects.get(uuid=cpt['serverID'])
            except models.Compte.DoesNotExist:
                if cpt['deleted']==1:
                    continue
                models.Compte.objects.get_or_create(uuid=cpt['serverID'],
                                                    defaults={'uuid': cpt['serverID'],
                                                              'nom': cpt['account'],
                                                              'type': table_de_passage_compte_type[cpt['type']]})
                cpt_maj +=1
                log('cpt %s: cree nom %s'%(cpt['id'],cpt['nom']))
                continue
            if cpt['deleted']==1:
                raise ValidationError(u'attention le compte %s a été supprimé'%cpt['account'])
            # si les deux ont été modifié depuis la derniere mise a jour
            if cpt['timestamp']<cpt_gsb.lastupdate:
                continue
            if cpt_gsb.nom!=cpt['account']:
                cpt_gsb.nom=cpt['account']
                log ('cpt %s: nom modife %s => %s'%(cpt['id'], cpt_gsb.nom, cpt['nom']))
                maj=True
            if cpt_gsb.type!=table_de_passage_compte_type[cpt['type']]:
                cpt_gsb.type=table_de_passage_compte_type[cpt['type']]
                log ('cpt %s: type modife %s => %s'%(cpt['id'],cpt_gsb.type, table_de_passage_compte_type[cpt['type']]))
                maj=True
            if cpt['institution']=='':
                if cpt_gsb.banque is not None:
                    cpt_gsb.banque=None
                    log("cpt %s: banque %s suprimee"%(cpt['id'],cpt_gsb.banque.nom))
                    maj=True
            else:
                if cpt_gsb.banque.nom!=cpt['institution']:
                    created, cpt_gsb.banque=models.Banque.objects.get_or_create(nom=cpt['institution'])
                    log('cpt %s:banque %s cree'%(cpt['id'],cpt['institution']))
                    maj=True
            if cpt['notes'] != cpt_gsb.notes:
                cpt['notes'] = cpt_gsb.notes
                log ('cpt %s : notes mise a jour' % cpt['id'])
                maj=True
            if maj:
                cpt_maj +=1
                cpt_gsb.save()
        log('%s comptes modifies ou cree'%cpt_maj)
        #------------------- cat
        rep=sql.rep("select * from categories where timestamp>%s;"%lastmaj)
        cat_maj=0
        table_de_passage_cat_type=('d','r')
        for obj_poc in rep:
            maj=False
            nom=obj_poc['category']
            try:
                obj_gsb=models.Cat.objects.get(uuid=obj_poc['serverID'])
            except models.Cat.DoesNotExist:
                if obj_poc['deleted']==1:
                    continue
                models.Cat.objects.get_or_create(uuid=obj_poc['serverID'],
                                                defaults={'uuid': obj_poc['serverID'],
                                                          'nom': nom,
                                                          'type': table_de_passage_cat_type[obj_poc['type']]})
                cat_maj +=1
                log('cat %s: cree nom %s'%(obj_poc['id'],nom))
                continue
            if obj_poc['deleted']==1:
                raise ValidationError(u'attention la cat %s a été supprimé'%nom)
            if obj_poc['timestamp']<obj_gsb.lastupdate:
                continue
            if obj_gsb.nom!=nom:
                obj_gsb.nom=nom
                log ('Cat %s: nom modife %s => %s'%(obj_poc['id'], obj_gsb.nom, nom))
                maj=True
            if obj_gsb.type!=table_de_passage_cat_type[obj_poc['type']]:
                obj_gsb.type=table_de_passage_cat_type[obj_poc['type']]
                log ('Cat %s: type modife %s => %s'%(obj_poc['id'],obj_gsb.type, table_de_passage_cat_type[obj_poc['type']]))
                maj=True
            if maj:
                cat_maj +=1
                obj_gsb.save()
        log('%s cat modifies'%cat_maj)
        #------------------- tiers
        rep=sql.rep("select * from payees where timestamp>%s;"%lastmaj)
        tiers_maj=0
        for obj_poc in rep:
            maj=False
            nom=obj_poc['payee']
            try:
                obj_gsb=models.Tiers.objects.get(uuid=obj_poc['serverID'])
            except models.Tiers.DoesNotExist:
                if obj_poc['deleted']==1:
                    continue
                models.Tiers.objects.get_or_create(uuid=obj_poc['serverID'],
                                                    defaults={'uuid': obj_poc['serverID'],
                                                              'nom': nom})
                tiers_maj +=1
                log('Tiers %s: cree nom %s'%(obj_poc['id'],nom))
                continue
            if obj_poc['deleted']==1:
                raise ValidationError(u'attention la cat %s a été supprimé'%nom)
            if obj_poc['timestamp']<obj_gsb.lastupdate:
                continue
            if obj_gsb.nom!=nom:
                obj_gsb.nom=nom
                log ('Tiers %s: nom modife %s => %s'%(obj_poc['id'], obj_gsb.nom, nom))
                maj=True
            if obj_poc['notes'] != obj_gsb.notes:
                obj_poc['notes'] = obj_gsb.notes
                log ('Tiers %s : notes mise a jour' % obj_poc['id'])
                maj=True
            if maj:
                tiers_maj +=1
                obj_gsb.save()
        log('%s Tiers modifies'%tiers_maj)
        #------------------- IB
        rep=sql.rep("select * from classes where timestamp>%s;"%lastmaj)
        Ib_maj=0
        for obj_poc in rep:
            maj=False
            nom=obj_poc['class']
            try:
                obj_gsb=models.Ib.objects.get(uuid=obj_poc['serverID'])
            except models.Ib.DoesNotExist:
                if obj_poc['deleted']==1:
                    continue
                models.Ib.objects.get_or_create(uuid=obj_poc['serverID'],
                                                defaults={'uuid': obj_poc['serverID'],
                                                          'nom': nom,
                                                          'type': 'd'})
                Ib_maj +=1
                log('Ib %s: cree nom %s'%(obj_poc['id'],nom))
                continue
            if obj_poc['deleted']==1:
                raise ValidationError(u'attention Ib %s a été supprimé'%nom)
            if obj_gsb.nom!=nom:
                obj_gsb.nom=nom
                log ('Ib %s: nom modife %s => %s'%(obj_poc['id'], obj_gsb.nom, nom))
                maj=True
            if maj:
                Ib_maj +=1
                obj_gsb.save()
        log('%s Ib modifies'%cat_maj)
        rep=sql.rep("SELECT * FROM transactions t2 where t2.timestamp>?;",lastmaj)
        ope_maj=0
        nbsplits={}
        for rep in sql.rep("select transactionId,count(splitId) as nb_split,type from splits group by transactionId;"):
            nbsplits[rep['transactionId']]={'nbsplits':rep['nb_split'],"type":rep['type']}

        for obj_poc in rep:
            try:
                obj_gsb=models.Ib.objects.get(uuid=obj_poc['serverID'])
            except models.Ib.DoesNotExist:
                if obj_poc['deleted']==1:
                    continue
                #on recupere le uuid du compte de l'operation
                compte_uuid=sql.rep_one("select serverId from accounts where accountID=%s"%obj_poc['accountID'])
                if sql.rep_one("select count(splitId) from splits where transactionId=?",obj_poc['transactionID']) == 1:
                    #c'est une stand alone ou virement
                    ope=sql.rep_one("SELECT t1.splitId, t1.amount, t1.xrate, t1.categoryID,"
                                    "t1.classID, t1.memo, t1.transfertoAccountId, t1.currencyCode, "
                                    "t2.transactionID "
                                    "FROM splits t1 left join transactions t2"
                                    "on (t1.transactionID = t2.transactionID)"
                                    " where transactionID=?",obj_poc['transactionID'])
                    obj_gsb=models.Ope.objects.get_or_create(uuid=obj_poc['serverID'],
                                                            defaults={
                                                                'uuid': obj_poc['serverID'],
                                                                'compte': models.Compte.objects.get(uuid=compte_uuid),
                                                                'date': datetime.datetime.utcfromtimestamp(int(obj_poc['date'])),
                                                                'montant': ope['amount'],
                                                                'tiers': models.Tiers.objects.get(nom=obj_poc['payee']),
                                                                'cat': models.Cat.objects.get(nom=ope['categoryID']),
                                                                'notes': ope['memo'],
                                                                'num_cheque': obj_poc['checkNum'],
                                                                'pointe': obj_poc['cleared'],
                                                                'ib': models.Cat.objects.get(nom=ope['classID'])
                                                            }
                                                        )










