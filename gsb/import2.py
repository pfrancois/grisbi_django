# -*- coding: utf-8 -*-
from __future__ import absolute_import
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os.path

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from mysite import settings

    setup_environ(settings)

from django.db import connection, transaction

from .models import (Tiers, Titre, Cat, Ope, Banque, Ib, Exercice,
                     Rapp, Moyen, Echeance, Generalite, Compte, Compte_titre, Ope_titre)
import datetime
import time
import decimal
import logging
###from django.conf import settings #@Reimport
import django.utils.encoding as dj_encoding

liste_type_cat = Cat.typesdep
liste_type_moyen = Moyen.typesdep
liste_type_compte = Compte.typescpt
liste_type_period = Echeance.typesperiod
liste_type_period_perso = Echeance.typesperiodperso
liste_type_titre = [e[0] for e in Titre.typestitres]
logger = logging.getLogger('gsb.import2')
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et

def datefr2datesql(s):
    try:
        t = time.strptime(str(s), "%d/%m/%Y")
        return "{annee}-{mois}-{jour}".format(annee=t[0], mois=t[1], jour=t[2])
    except ValueError:
        return None


def fr2decimal(s):
    if s == "0,0000000":
        return decimal.Decimal()
    if s is not None:
        return decimal.Decimal(str(s).replace(',', '.'))
    else:
        return None


class Import_exception(Exception):
    pass


def import_gsb(nomfich, efface_table=True):
    """importe directement a partir des id sauf pour les cat et les moyens car on change la methode de comptage"""
    tabl_correspondance_moyen = {}
    tabl_correspondance_cat = {}
    tabl_correspondance_ib = {}
    if efface_table:
        for table in (
        'generalite', 'ope', 'echeance', 'rapp', 'moyen', 'compte', 'cpt_titre', 'cat', 'exercice', 'ib', 'banque',
        'titre', 'tiers', 'Ope_titre'):
            connection.cursor().execute("delete from %s;" % table) #@UndefinedVariable
            transaction.commit_unless_managed()
    logger.info(u"debut du chargement")
    time.clock()
    xml_tree = et.parse(nomfich)
    xml_tree.getroot()
    #verification du format
    xml_generalite = str(xml_tree.find('Generalites/Version_fichier').text)
    if xml_generalite != '0.5.0':
        logger.critical("le format n'est pas reconnu")
        raise Import_exception, "le format n'est pas reconnu"
    percent = 1
    #------------------------------generalites#------------------------------
    xml_generalite = xml_tree.find('Generalites')
    if not xml_generalite.find('Titre').text:
        titre_fichier = ""
    else:
        titre_fichier = xml_generalite.find('Titre').text

    element, created = Generalite.objects.get_or_create(
        id=1,
        defaults={
            'titre':titre_fichier,
            'utilise_exercices':bool(int(xml_generalite.find('Utilise_exercices').text)),
            'utilise_ib':bool(int(xml_generalite.find('Utilise_IB').text)),
            'utilise_pc':bool(int(xml_generalite.find('Utilise_PC').text))
        })
    logger.warning(u'generalites ok')
    #------------------------------devises---------------------------
    nb = 0
    nb_nx = 0
    nb_titre = 0
    if len(xml_tree.find('//Detail_des_devises')) > 1:
        raise Exception("attention ce ne sera pas possible d'importer car il y a plusieurs devises")
        #------------ TIERS et titres -------------------
    nb_tiers_final = len(xml_tree.find('//Detail_des_tiers'))
    for xml_tiers in xml_tree.find('//Detail_des_tiers'):
        affiche = False
        if nb == int(nb_tiers_final * int("%s0" % percent) / 100):#logging
            affiche = True
            logger.info("tiers %s soit %% %s" % (xml_tiers.get('No'), "%s0" % percent))
            percent += 1
        nb += 1
        query = {'nom':xml_tiers.get('Nom'), 'notes':xml_tiers.get('Informations'), 'id':xml_tiers.get('No')}
        if xml_tiers.get('Nom')[:6] != 'titre_':
            element, created = Tiers.objects.get_or_create(id=xml_tiers.get('No'), defaults=query)
        else:
            #test puis creation du titre (et donc du tiers automatiquement)
            try:
                Tiers.objects.get(id=xml_tiers.get('No'))
            except Tiers.DoesNotExist:
                nb_titre += 1
                s = dj_encoding.smart_unicode(xml_tiers.get('Informations'))
                nom = dj_encoding.smart_unicode(xml_tiers.get('Nom'))
                s = s.partition(
                    '@')#on utilise partition et non split car c'est pas sur et pas envie de mettre une usine a gaz
                titre = Titre(nom=nom[7:])
                if not s[1]:
                    if s[0] == '':
                        titre.isin = "ZZ%sN%s" % (datetime.date.today().strftime('%d%m%Y'), nb_titre)
                    else:
                        titre.isin = s[0]
                    titre.type = "ZZZ"
                else:
                    if s[0] == '':
                        titre.isin = "XX%sN%s" % (datetime.date.today().strftime('%d%m%Y'), nb_titre)
                    else:
                        titre.isin = s[0]
                    if s[2] in liste_type_titre:
                        titre.type = s[2]
                    else:
                        titre.type = 'ZZZ'
                element, created = Tiers.objects.get_or_create(nom=xml_tiers.get('Nom'), defaults=query)
                titre.tiers = element
                titre.save()
                element.notes = "%s@%s" % (titre.isin, titre.type)
                element.is_titre = True
                element.save()
                logger.debug(u'titre cree %s isin (%s) as %s' % (titre.nom, titre.isin, titre.type))
        if created:
            nb_nx += 1
            if affiche:
                logger.debug('tiers %s cree' % int(xml_tiers.get('No')))

    logger.warning(u'%s tiers et %s titres dont %s nx' % (nb, nb_titre, nb_nx))
    #-------------------------categories et des sous categories-----------------------
    nb_cat = 0
    nb_nx = 0
    for xml_cat in xml_tree.find('//Detail_des_categories'):
        nb_cat += 1
        query = {'nom':"%s :" % (xml_cat.get('Nom'),), 'type':liste_type_cat[int(xml_cat.get('Type'))][0]}
        element, created = Cat.objects.get_or_create(nom=query['nom'], defaults=query)
        tabl_correspondance_cat[xml_cat.get('No')] = {'0':element.id}
        if created:
            nb_nx += 1
            logger.debug('cat %s cree au numero %s' % (int(xml_cat.get('No')), element.id))
        for xml_scat in xml_cat:
            nb_cat += 1
            query = {'nom':"%s : %s" % (xml_cat.get('Nom'), xml_scat.get('Nom')),
                     'type':liste_type_cat[int(xml_cat.get('Type'))][0]}
            element, created = Cat.objects.get_or_create(nom=query['nom'], defaults=query)
            tabl_correspondance_cat[xml_cat.get('No')][xml_scat.get('No')] = element.id
            if created:
                nb_nx += 1
                logger.debug(
                    'scat %s:%s cree au numero %s' % (int(xml_cat.get('No')), int(xml_scat.get('No')), element.id))
    logger.warning(u"%s catégories dont %s nouveaux" % (nb_cat, nb_nx))

    #------------------------------imputations----------------------------------
    nb_ib = 0
    nb_nx = 0
    for xml_ib in xml_tree.find('//Detail_des_imputations'):
        nb_ib += 1
        query = {'nom':"%s:" % (xml_ib.get('Nom'),), 'type':liste_type_cat[int(xml_ib.get('Type'))][0]}
        element, created = Ib.objects.get_or_create(nom=query['nom'], defaults=query)
        tabl_correspondance_ib[xml_ib.get('No')] = {'0':element.id}
        if created:
            nb_nx += 1
            logger.debug('ib %s cree au numero %s' % (int(xml_ib.get('No')), element.id))
        for xml_sib in xml_ib:
            logger.debug("ib %s: sib %s" % (xml_ib.get('No'), xml_sib.get('No')))
            nb_ib += 1
            query = {'nom':"%s:%s" % (xml_ib.get('Nom'), xml_sib.get('Nom')),
                     'type':liste_type_cat[int(xml_ib.get('Type'))][0]}
            element, created = Ib.objects.get_or_create(nom=query['nom'], defaults=query)
            tabl_correspondance_ib[xml_ib.get('No')][xml_sib.get('No')] = element.id
            if created:
                logger.debug(
                    'sib %s:%s cree au numero %s' % (int(xml_ib.get('No')), int(xml_sib.get('No')), element.id))
    logger.warning(u"%s imputations dont %s nouveaux" % (nb_ib, nb_nx))


    #------------------------------banques------------------------------
    nb_bq = 0
    for xml_bq in xml_tree.find('Banques/Detail_des_banques'):
        nb_bq += 1
        logger.debug("banque %s" % xml_bq.get('No'))
        element, created = Banque.objects.get_or_create(id=xml_bq.get('No'), defaults={'cib':xml_bq.get('Code'),
                                                                                       'notes':xml_bq.get('Remarques'),
                                                                                       'id':xml_bq.get('No')})
    logger.warning(u'%s banques' % nb_bq)

    #------------------------------exercices#------------------------------
    nb = 0
    nb_nx = 0
    for xml_exercice in xml_tree.find('Exercices/Detail_des_exercices'):
        nb += 1
        logger.debug("exo %s" % xml_exercice.get('No'))
        element, created = Exercice.objects.get_or_create(nom=xml_exercice.get('Nom'),
                                                          defaults={'nom':xml_exercice.get('Nom'),
                                                                    'date_debut':datefr2datesql(
                                                                        xml_exercice.get('Date_debut')),
                                                                    'date_fin':datefr2datesql(
                                                                        xml_exercice.get('Date_fin')),
                                                                    'id':xml_exercice.get('No')})
        if created:
            nb_nx += 1
    logger.warning(u'%s exercices dont %s nouveaux' % (nb, nb_nx))

    #------------------------------rapp#------------------------------
    nb = 0
    nb_nx = 0
    for xml_rapp in xml_tree.find('Rapprochements/Detail_des_rapprochements'):
        nb += 1
        logger.debug("rapp %s" % xml_rapp.get('No'))
        element, created = Rapp.objects.get_or_create(nom=dj_encoding.smart_unicode(xml_rapp.get('Nom')),
                                                      defaults={'nom':xml_rapp.get('Nom'), 'id':xml_rapp.get('No')})
        if created:
            nb_nx += 1
    logger.warning(u'%s rapprochements dont %s nouveaux ' % (nb, nb_nx))

    #------------------------------comptes#------------------------------
    nb = 0
    nb_tot_moyen = 0
    nb_nx = 0
    for xml_cpt in xml_tree.findall('//Compte'):
        nb += 1
        nb_moyen = 0
        type = liste_type_compte[int(xml_cpt.find('Details/Type_de_compte').text)][0]
        if type in ('t',):
            logger.debug("cpt_titre %s" % (xml_cpt.find('Details/Nom').text))
            element, created = Compte_titre.objects.get_or_create(nom=xml_cpt.find('Details/Nom').text, defaults={
                'nom':xml_cpt.find('Details/Nom').text,
                'ouvert':not bool(int(xml_cpt.find('Details/Compte_cloture').text)),
                'id':int(xml_cpt.find('Details/No_de_compte').text)
            })
        else:
            logger.debug("cpt %s" % (xml_cpt.find('Details/Nom').text))
            element, created = Compte.objects.get_or_create(nom=xml_cpt.find('Details/Nom').text, defaults={
                'nom':xml_cpt.find('Details/Nom').text,
                'ouvert':not bool(int(xml_cpt.find('Details/Compte_cloture').text)),
                'id':int(xml_cpt.find('Details/No_de_compte').text)
            })
        if created:
            nb_nx += 1
            if xml_cpt.find('Details/Titulaire').text is None:
                element.titulaire = ''
            else:
                element.titulaire = xml_cpt.find('Details/Titulaire').text
            element.type = liste_type_compte[int(xml_cpt.find('Details/Type_de_compte').text)][0]
            if xml_cpt.find('Details/Banque') is None or int(xml_cpt.find('Details/Banque').text) == 0:
                element.banque = None
            else:
                element.banque_id = int(xml_cpt.find('Details/Banque').text)
            if xml_cpt.find('Details/Guichet').text is None:
                element.guichet = ''
            else:
                element.guichet = xml_cpt.find('Details/Guichet').text
            if xml_cpt.find('Details/No_compte_banque').text is not None:
                element.num_compte = xml_cpt.find('Details/No_compte_banque').text
            else:
                element.num_compte = ''
            if xml_cpt.find('Details/Cle_du_compte').text is not None:
                element.cle_compte = int(xml_cpt.find('Details/Cle_du_compte').text)
            else:
                element.cle_compte = None
            element.solde_init = fr2decimal(xml_cpt.find('Details/Solde_initial').text)
            element.solde_mini_voulu = fr2decimal(xml_cpt.find('Details/Solde_mini_voulu').text)
            element.solde_mini_autorise = fr2decimal(xml_cpt.find('Details/Solde_mini_autorise').text)
            element.solde_mini_autorise = fr2decimal(xml_cpt.find('Details/Solde_mini_autorise').text)
            if xml_cpt.find('Details/Commentaires').text is not None:
                element.notes = xml_cpt.find('Details/Commentaires').text
            else:
                element.notes = ''
            element.save()
            #---------------MOYENS---------------------
        nb_nx_moyens = 0
        tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text] = {}
        for xml_moyen in xml_cpt.find('Detail_de_Types'):
            nb_tot_moyen += 1
            nb_moyen += 1
            logger.debug("moyen %s" % xml_moyen.get('No'))
            moyen, created = Moyen.objects.get_or_create(nom=xml_moyen.get('Nom'),
                                                         defaults={'nom':xml_moyen.get('Nom'),
                                                                   'type':liste_type_moyen[int(xml_moyen.get('Signe'))][
                                                                          0], }
            )
            if created:
                nb_nx_moyens += 1
            tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text][xml_moyen.get('No')] = moyen.id
        try:
            element.moyen_credit_defaut_id = tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text][
                                             xml_cpt.find('Details/Type_defaut_credit').text]
        except (KeyError, TypeError):
            element.moyen_credit_defaut_id = None
        try:
            element.moyen_debit_defaut_id = tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text][
                                            xml_cpt.find('Details/Type_defaut_debit').text]
        except (KeyError, TypeError):
            element.moyen_debit_defaut_id = None
        element.save()
    logger.warning(u'%s comptes dont %s nouveaux' % (nb, nb_nx))
    nb_tot_ope = 0

    #------------------------------OPERATIONS-----------------------
    list_ope = xml_tree.findall('//Operation')
    nb_ope_final = len(list_ope)
    percent = 1
    for xml_ope in list_ope:
        logger.debug(u'opération %s' % xml_ope.get('No'))
        try:
            ope_tiers = Tiers.objects.get(id=int(xml_ope.get('T')))
        except KeyError:
            ope_tiers = None
        ope_montant = fr2decimal(xml_ope.get('M'))
        ope_date = datefr2datesql(xml_ope.get('D'))
        ope_date_val = datefr2datesql(xml_ope.get('Db'))
        ope_cpt = Compte.objects.get(id=int(xml_ope.find('../../Details/No_de_compte').text))
        if ope_tiers and ope_tiers.is_titre and ope_cpt.type == 't':
            #compta matiere et cours en meme tps
            ope_cpt_titre = Compte_titre.objects.get(id=ope_cpt.id)
            ope_notes = dj_encoding.smart_unicode(xml_ope.get('N'))
            s = ope_notes.partition('@')
            if s[1]:#TODO gestion des csl
                ope_nb = decimal.Decimal(str(s[0]))
                if str(s[2]):
                    ope_cours = decimal.Decimal(str(s[2]))
                else:
                    ope_cours = 1
                Ope_titre.objects.create(titre=ope_tiers.titre, compte=ope_cpt_titre, nombre=ope_nb, date=ope_date,
                                         cours=ope_cours)
                ope_tiers.titre.cours_set.get_or_create(date=ope_date, defaults={'date':ope_date, 'valeur':ope_cours})
            #on cree de toute facon l'operation
        nb_tot_ope += 1
        if nb_tot_ope == int(nb_ope_final * int("%s0" % percent) / 100):
            logger.info(
                "ope %s, ope %s sur %s soit %s%%" % (xml_ope.get('No'), nb_tot_ope, nb_ope_final, "%s0" % percent))
            affiche = True
            percent += 1

        ope = Ope(id=int(xml_ope.get('No')),
                  compte=ope_cpt,
                  date=ope_date,
                  date_val=ope_date_val, #date de valeur
                  montant=ope_montant, #montant
        )#on cree toujours car la proba que ce soit un doublon est bien bien plus faible que celle que ce soit une autre
        ope.save()
        #numero du moyen de paiment
        ope.num_cheque = xml_ope.get('Ct')
        #statut de pointage
        if int(xml_ope.get('P')) == 1:
            ope.pointe = True
        if int(xml_ope.get('A')) == 1:
            ope.automatique = True
            #gestion des tiers
        if ope_tiers:
            ope.tiers_id = ope_tiers
            #gestion des categories
        try:
            if xml_ope.get('C') and int(xml_ope.get('C')):
                ope.cat_id = tabl_correspondance_cat[xml_ope.get('C')][xml_ope.get('Sc')]
            else:
                ope.cat = None
        except KeyError:
            ope.cat = None
        try:
            if xml_ope.get('I') and int(xml_ope.get('I')):
                ope.ib_id = tabl_correspondance_ib[xml_ope.get('I')][xml_ope.get('Si')]
            else:
                ope.ib = None
        except KeyError:
            ope.ib = None
        try:#moyen de paiment
            ope.moyen_id = tabl_correspondance_moyen[str(ope.compte_id)][xml_ope.get('Ty')]
        except KeyError:
            ope.moyen = None
        try: #gestion des rapprochements
            if int(xml_ope.get('R')):
                ope.rapp_id = int(xml_ope.get('R'))
                #gestion de la date du rapprochement
                if datetime.datetime.combine(ope.rapp.date, datetime.time()) > datetime.datetime.strptime(ope.date,
                                                                                                          "%Y-%m-%d"):
                    ope.rapp.date = ope.date
                    ope.rapp.save()
        except TypeError:
            ope.rapp = None
        ope.notes = xml_ope.get('N')
        ope.piece_comptable = xml_ope.get('Pc')
        #exercices
        try:
            if int(xml_ope.get('E')):
                ope.exercice_id = int(xml_ope.get('E'))
            else:
                ope.exercice_id = None
        except TypeError:
            ope.exercice = None
        ope.save()
    nb_tot_ope = 0
    percent = 1
    for xml_ope in list_ope:
        nb_tot_ope += 1
        affiche = False
        if nb_tot_ope == int(nb_ope_final * int("%s0" % percent) / 100):
            logger.info(
                "2*ope %s, ope %s sur %s soit %s%%" % (xml_ope.get('No'), nb_tot_ope, nb_ope_final, "%s0" % percent))
            affiche = True
            percent += 1
            #gestion des virements
        if int(xml_ope.get('Ro')):
            logger.debug('virement vers %s' % xml_ope.get('Ro'))
            ope = Ope.objects.get(id=int(xml_ope.get('No')))
            ope.jumelle_id = int(xml_ope.get('Ro'))
            ope.save()
            #gestion des ventilations
        #bool(int(xml_ope.get('Ov'))) pas besoin car on regarde avec des requetes sql
        if int(xml_ope.get('Va')):
            logger.debug('ventilation de %s' % xml_ope.get('Va'))
            ope = Ope.objects.get(id=int(xml_ope.get('No')))
            ope.mere_id = int(xml_ope.get('Va'))
            ope.save()

    logger.warning(u"%s operations" % nb_tot_ope)


    #------------------------------echeances#------------------------------
    nb = 0
    for xml_ech in xml_tree.find('Echeances/Detail_des_echeances'):
        nb += 1
        logger.debug("echeance %s" % xml_ech.get('No'))
        element = Echeance(
            date=datefr2datesql(xml_ech.get('Date')),
            montant=fr2decimal(xml_ech.get('Montant')),
            compte_id=int(xml_ech.get('Compte')),
            )
        element.save()
        try:
            element.tiers_id = int(xml_ech.get('Tiers'))
        except TypeError:
            element.tiers = None
        element.inscription_automatique = bool(int(xml_ech.get('Automatique')))
        try:
            element.moyen_id = tabl_correspondance_moyen[xml_ech.get('Compte')][xml_ech.get('Type')]
        except TypeError:
            element.moyen = None
        try:
            element.exercice_id = int(xml_ech.get('Exercice'))
        except TypeError:
            element.moyen = None
        element.notes = xml_ech.get('Notes')
        try:
            element.cat_id = tabl_correspondance_cat[xml_ech.get('Categorie')][xml_ech.get('Sous-categorie')]
        except TypeError:
            element.cat = None
        try:
            element.ib_id = tabl_correspondance_ib[xml_ech.get('Imputation')][xml_ech.get('Sous-imputation')]
        except TypeError:
            element.ib = None
        if xml_ech.get('Virement_compte') != xml_ech.get('Compte'):
            element.compte_virement_id = int(xml_ech.get('Virement_compte'))
            try:
                element.moyen_virement_id = int(xml_ech.get('Type_contre_ope'))
            except TypeError:
                element.moyen_virement = None
        else:
            element.compte_virement = None
            element.moyen_virement = None
        element.periodicite = liste_type_period[int(xml_ech.get('Periodicite'))][0]
        if element.periodicite == 'p':
            element.intervalle = int(xml_ech.get('Intervalle_periodicite'))
            element.periode_perso = liste_type_period_perso[int(xml_ech.get('Periodicite_personnalisee'))][0]
        element.date_limite = datefr2datesql(xml_ech.get('Date_limite'))
        element.save()
    logger.warning(u"%s échéances" % nb)
    logger.warning(u'{!s}'.format(time.clock()))
    logger.warning(u'fini')

if __name__ == "__main__":
    nomfich = "%s/20040701.gsb" % (os.path.dirname(os.path.abspath(__file__)))
    #nomfich = "%s/test_files/test_original.gsb" % (os.path.dirname(os.path.abspath(__file__)))
    nomfich = os.path.normpath(nomfich)
    logger.setLevel(10)#change le niveau de log (10 = debug, 20=info)
    import_gsb(nomfich, efface_table=True)
    logger.info(u'fichier %s importe' % nomfich)
