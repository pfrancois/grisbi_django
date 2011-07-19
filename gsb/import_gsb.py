# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '..','..')))
    from mysite import settings

    setup_environ(settings)

from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from mysite.gsb.models import *
import os, time
import decimal
import logging

liste_type_cat = Cat.typesdep
liste_type_moyen = Cat.typesdep
liste_type_compte = Compte.typescpt
liste_type_period = Echeance.typesperiod
liste_type_period_perso = Echeance.typesperiodperso
liste_type_titre = [e[0] for e in Titre.typestitres]
logger=logging.getLogger('gsb.import')
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
        return decimal.Decimal('0')
    if s is not None:
        return decimal.Decimal(str(s).replace(',', '.'))
    else:
        return None


class Import_exception(Exception):
    pass


def import_gsb(nomfich,efface_table=True):
    tabl_correspondance_moyen={}
    tabl_correspondance_compte={}
    tabl_correspondance_tiers={}
    tabl_correspondance_banque={}
    tabl_correspondance_cat={}
    tabl_correspondance_ib={}
    tabl_correspondance_exo={}
    tabl_correspondance_rapp={}
    tabl_correspondance_ech={}
    tabl_correspondance_ope={}
    tabl_correspondance_devise={}
    if efface_table:
        for table in ('titres_detenus','generalite', 'ope', 'echeance', 'rapp', 'moyen', 'compte','cpt_titre', 'cat', 'exercice', 'ib', 'banque', 'titre', 'tiers'):
            connection.cursor().execute("delete from %s;"%table)
            transaction.commit_unless_managed()
    logger.info(u"debut du chargement")
    time.clock()
    xml_tree = et.parse(nomfich)
    root = xml_tree.getroot()
    #verification du format
    xml_element = str(xml_tree.find('Generalites/Version_fichier').text)
    if xml_element != '0.5.0':
        logger.critical("le format n'est pas reconnu")
        raise Import_exception, "le format n'est pas reconnu"
    nb = 0
    nb_sous = 0
    nb_nx=0
    percent=1
        #------------------------------generalites#------------------------------
    xml_element = xml_tree.find('Generalites')
    if not xml_element.find('Titre').text:
        titre_fichier=""
    else:
        titre_fichier=xml_element.find('Titre').text

    element,created = Generalite.objects.get_or_create(
        id=1,
        defaults={
        'titre':titre_fichier,
        'utilise_exercices':bool(int(xml_element.find('Utilise_exercices').text)),
        'utilise_ib':bool(int(xml_element.find('Utilise_IB').text)),
        'utilise_pc':bool(int(xml_element.find('Utilise_PC').text))
    })
    if settings.UTIDEV:
        id=tabl_correspondance_devise[xml_element.find('Numero_devise_totaux_ib').text]
        if Generalite.dev_g() != Titre.objects.get(type=u'DEV',id=id):
            if settings.DEVISE_GENERALE != Generalite.dev_g():
                raise Exception("attention ce ne sera pas possible d'importer car la devise principale n'est pas la meme")
    logger.warning(u'generalites ok')
    #------------ TIERS et titres -------------------
    nb_tiers_final=len(xml_tree.find('//Detail_des_tiers'))
    for xml_element in xml_tree.find('//Detail_des_tiers'):
        affiche=False
        if nb==int(nb_tiers_final*int("%s0"%percent)/100):
            affiche=True
            logger.info("tiers %s soit %% %s"%(xml_element.get('No'),"%s0"%percent))
            percent += 1
        nb += 1
        query={'nom':xml_element.get('Nom'),'notes':xml_element.get('Informations')}
        element,created = Tiers.objects.get_or_create(nom=xml_element.get('Nom'),defaults=query)
        tabl_correspondance_tiers[xml_element.get('No')]=element.id
        if created:
            nb_nx += 1
            if affiche:
                logger.debug('tiers %s cree au numero %s'%(int(xml_element.get('No')),element.id))
            if element.nom[:6] == "titre_":
                nb_sous += 1
                element.is_titre = True
                element.save()
                s= unicode(xml_element.get('Informations'))
                s = s.partition('@')#on utilise partition et non split car c'est pas sur et pas envie de mettre une usine a gaz
                sous = Titre(nom=element.nom[7:])
                if not s[1]:
                    if s[0] == '':
                        sous.isin = "XX%sN%s"%(datetime.date.today().strftime('%d%m%Y'),nb_sous)
                    else:
                        sous.isin = s[0]
                    sous.type = "XXX"
                else:
                    if s[0] == '':
                        sous.isin = "XX%sN%s"%(datetime.date.today().strftime('%d%m%Y'),nb_sous)
                    else:
                        sous.isin = s[0]
                    if s[2] in liste_type_titre:
                        sous.type = s[2]
                    else:
                        sous.type = 'XXX'
                sous.tiers = element
                sous.save()
                logger.debug(u'titre cree %s isin (%s) as %s'%(sous.nom,sous.isin,sous.type))
    logger.warning(u'%s tiers et %s titres dont %s nx'%(nb, nb_sous,nb_nx))
    #-------------------------categories et des sous categories-----------------------
    nb_cat = 0
    nb_nx = 0
    for xml_element in xml_tree.find('//Detail_des_categories'):
        logger.debug("cat %s"%xml_element.get('No'))
        nb_cat += 1
        query={'nom':"%s :"%(xml_element.get('Nom'),),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
        element,created=Cat.objects.get_or_create(nom=query['nom'],defaults=query)
        tabl_correspondance_cat[xml_element.get('No')]={'0':element.id}
        if created:
            nb_nx += 1
            logger.debug('cat %s cree au numero %s'%(int(xml_element.get('No')),element.id))
        for xml_sous in xml_element:
            logger.debug("cat %s : scat %s"%(xml_element.get('No'),xml_sous.get('No')))
            nb_cat += 1
            query={'nom':"%s : %s"%(xml_element.get('Nom'),xml_sous.get('Nom')),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
            element,created=Cat.objects.get_or_create(nom=query['nom'],defaults=query)
            tabl_correspondance_cat[xml_element.get('No')][xml_sous.get('No')]=element.id
            if created:
                logger.debug('scat %s:%s cree au numero %s'%(int(xml_element.get('No')),int(xml_sous.get('No')),element.id))
    logger.warning(u"%s catégories dont %s nouveaux"%(nb_cat,nb_nx))

    #------------------------------imputations----------------------------------
    nb_ib=0
    nb_nx=0
    for xml_element in xml_tree.find('//Detail_des_imputations'):
        logger.debug("ib %s"%xml_element.get('No'))
        nb_ib += 1
        query={'nom':"%s:"%(xml_element.get('Nom'),),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
        element,created=Ib.objects.get_or_create(nom=query['nom'],defaults=query)
        tabl_correspondance_ib[xml_element.get('No')]={'0':element.id}
        if created:
            nb_nx += 1
            logger.debug('ib %s cree au numero %s'%(int(xml_element.get('No')),element.id))
        for xml_sous in xml_element:
            logger.debug("ib %s: sib %s"%(xml_element.get('No'),xml_sous.get('No')))
            nb_ib += 1
            query={'nom':"%s:%s"%(xml_element.get('Nom'),xml_sous.get('Nom')),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
            element,created=Ib.objects.get_or_create(nom=query['nom'],defaults=query)
            tabl_correspondance_ib[xml_element.get('No')][xml_sous.get('No')]=element.id
            if created:
                logger.debug('sib %s:%s cree au numero %s'%(int(xml_element.get('No')),int(xml_sous.get('No')),element.id))
    logger.warning(u"%s imputations dont %s nouveaux"%(nb_ib,nb_nx))

    #------------------------------devises---------------------------
    nb = 0
    nb_nx = 0
    for xml_element in xml_tree.find('//Detail_des_devises'):
        nb += 1
        logger.debug("devise %s"%xml_element.get('No'))
        query = {'nom':xml_element.get('Nom'), 'isin':xml_element.get('IsoCode'), 'tiers':None, 'type':'DEV'}
        element,created=Titre.objects.get_or_create(type='DEV',isin=xml_element.get('IsoCode'),defaults=query)
        tabl_correspondance_devise[xml_element.get('No')]=element.id
        if created:
            nb_nx += 1
        if fr2decimal(xml_element.get('Change')) != decimal.Decimal('0'):
            element.cours_set.get_or_create(titre=element.isin,date=datefr2datesql(xml_element.get('Date_dernier_change')),defaults={'date':datefr2datesql(xml_element.get('Date_dernier_change')),'valeur':fr2decimal(xml_element.get('Change'))})
        else:
            element.cours_set.get_or_create(titre=element.isin,date=datetime.datetime.today(),defaults={'date':datetime.datetime.today(),'valeur':fr2decimal('1')})
        element.save()
    logger.warning(u'%s devises dont %s nouvelles'%(nb,nb_nx))

    #------------------------------banques------------------------------
    nb = 0
    for xml_element in xml_tree.find('Banques/Detail_des_banques'):
        nb += 1
        logger.debug("banque %s"%xml_element.get('No'))
        element,created=Banque.objects.get_or_create(nom=xml_element.get('Nom'),defaults={'cib':xml_element.get('Code'), 'notes':xml_element.get('Remarques')})
        tabl_correspondance_banque[xml_element.get('No')]=element.id
    logger.warning(u'%s banques'%nb)

    #------------------------------exercices#------------------------------
    nb = 0
    nb_nx=0
    for xml_element in xml_tree.find('Exercices/Detail_des_exercices'):
        nb += 1
        logger.debug("exo %s"%xml_element.get('No'))
        element,created= Exercice.objects.get_or_create(nom=xml_element.get('Nom'),defaults={'nom':xml_element.get('Nom'),'date_debut':datefr2datesql(xml_element.get('Date_debut')), 'date_fin':datefr2datesql(xml_element.get('Date_fin'))})
        tabl_correspondance_exo[xml_element.get('No')]=element.id
        if created:
            nb_nx+=1
    logger.warning(u'%s exercices dont %s nouveaux'%(nb,nb_nx))

    #------------------------------rapp#------------------------------
    nb = 0
    nb_nx=0
    for xml_element in xml_tree.find('Rapprochements/Detail_des_rapprochements'):
        nb += 1
        logger.debug("rapp %s"%xml_element.get('No'))
        element,created= Rapp.objects.get_or_create(nom=xml_element.get('Nom'),defaults={'nom':xml_element.get('Nom')})
        if created:
           nb_nx+=1
        tabl_correspondance_rapp[xml_element.get('No')]=element.id
    logger.warning(u'%s rapprochements dont %s nouveaux '%(nb,nb_nx))

    #------------------------------comptes#------------------------------
    nb = 0
    nb_tot_moyen = 0
    nb_nx=0
    for xml_element in xml_tree.findall('//Compte'):
        nb += 1
        nb_moyen = 0
        type = liste_type_compte[int(xml_element.find('Details/Type_de_compte').text)][0]
        if type in ('t',):
            logger.debug("cpt_titre %s"%(xml_element.find('Details/Nom').text))
            element,created= Compte_titre.objects.get_or_create(nom=xml_element.find('Details/Nom').text,defaults={
            'nom':xml_element.find('Details/Nom').text,
            'devise':Titre.objects.get(id=tabl_correspondance_devise[xml_element.find('Details/Devise').text]),
            'ouvert':not bool(int(xml_element.find('Details/Compte_cloture').text)),
        })
        else:
            logger.debug("cpt %s"%(xml_element.find('Details/Nom').text))
            element,created= Compte.objects.get_or_create(nom=xml_element.find('Details/Nom').text,defaults={
            'nom':xml_element.find('Details/Nom').text,
            'devise':Titre.objects.get(id=tabl_correspondance_devise[xml_element.find('Details/Devise').text]),
            'ouvert':not bool(int(xml_element.find('Details/Compte_cloture').text)),
        })

        tabl_correspondance_compte[xml_element.find('Details/No_de_compte').text]=element.id
        if created:
            nb_nx += 1
            if xml_element.find('Details/Titulaire').text is None:
                element.titulaire = ''
            else:
                element.titulaire = xml_element.find('Details/Titulaire').text
            element.type = liste_type_compte[int(xml_element.find('Details/Type_de_compte').text)][0]
            if xml_element.find('Details/Banque') is None or int(xml_element.find('Details/Banque').text) == 0:
                element.banque = None
            else:
                element.banque_id = tabl_correspondance_banque[xml_element.find('Details/Banque').text]
            if xml_element.find('Details/Guichet').text is None:
                element.guichet = ''
            else:
                element.guichet = xml_element.find('Details/Guichet').text
            if xml_element.find('Details/No_compte_banque').text is not None:
                element.num_compte = xml_element.find('Details/No_compte_banque').text
            else:
                element.num_compte = ''
            if xml_element.find('Details/Cle_du_compte').text is not None:
                element.cle_compte = int(xml_element.find('Details/Cle_du_compte').text)
            else:
                element.cle_compte = None
            element.solde_init = fr2decimal(xml_element.find('Details/Solde_initial').text)
            element.solde_mini_voulu = fr2decimal(xml_element.find('Details/Solde_mini_voulu').text)
            element.solde_mini_autorise = fr2decimal(xml_element.find('Details/Solde_mini_autorise').text)
            element.solde_mini_autorise = fr2decimal(xml_element.find('Details/Solde_mini_autorise').text)
            if xml_element.find('Details/Commentaires').text is not None:
                element.notes = xml_element.find('Details/Commentaires').text
            else:
                element.notes = ''
            element.save()
        #---------------MOYENS---------------------
        nb_nx_moyens=0
        tabl_correspondance_moyen[xml_element.find('Details/No_de_compte').text]={}
        for xml_sous in xml_element.find('Detail_de_Types'):
            nb_tot_moyen += 1
            nb_moyen += 1
            logger.debug("moyen %s"%xml_sous.get('No'))
            moyen,created = Moyen.objects.get_or_create(nom=xml_sous.get('Nom'),
                                                        defaults={'nom':xml_sous.get('Nom'),
                                                                    'type':liste_type_moyen[int(xml_sous.get('Signe'))][0],}
            )
            if created:
                nb_nx_moyens+=1
            tabl_correspondance_moyen[xml_element.find('Details/No_de_compte').text][xml_sous.get('No')]=moyen.id
        try:
            element.moyen_credit_defaut_id = tabl_correspondance_moyen[xml_element.find('Details/No_de_compte').text][xml_element.find('Details/Type_defaut_credit').text]
        except (KeyError, TypeError):
            element.moyen_credit_defaut_id = None
        try:
            element.moyen_debit_defaut_id = tabl_correspondance_moyen[xml_element.find('Details/No_de_compte').text][xml_element.find('Details/Type_defaut_debit').text]
        except (KeyError, TypeError):
            element.moyen_debit_defaut_id = None
        element.save()
    logger.warning(u'%s comptes dont %s nouveaux'%(nb,nb_nx))
    nb_tot_ope=0

    #------------------------------OPERATIONS-----------------------
    nb_nx_ope=0
    list_ope=xml_tree.findall('//Operation')
    nb_ope_final=len(list_ope)
    percent=1
    for xml_sous in list_ope:
        nb_tot_ope += 1
        affiche=False
        if nb_tot_ope==int(nb_ope_final*int("%s0"%percent)/100):
            logger.info("ope %s, ope %s sur %s soit %s%%"%(xml_sous.get('No'),nb_tot_ope,nb_ope_final,"%s0"%percent))
            affiche=True
            percent +=1
        cpt = Compte.objects.get(id=tabl_correspondance_compte[xml_sous.find('../../Details/No_de_compte').text])
        sous = Ope(compte = cpt,
                   date = datefr2datesql(xml_sous.get('D')),
                   date_val = datefr2datesql(xml_sous.get('Db')),#date de valeur
                   montant = fr2decimal(xml_sous.get('M')),#montant
        )#on cree toujours car la proba que ce soit un doublon est bien bien plus faible que celle que ce soit une autre
        sous.save()
        tabl_correspondance_ope[xml_sous.get('No')]=sous.id
        if affiche:
            logger.debug('ope %s cree id %s'%(xml_sous.get('No'),sous.id))
        #gestion des devises
        if tabl_correspondance_devise[xml_sous.get('De')] != sous.compte.devise_id:
            if int(xml_sous.get('Rdc')):
                sous.montant = fr2decimal(xml_sous.get('M')) / fr2decimal(xml_sous.get('Tc')) - fr2decimal(xml_sous.get('Fc'))
                Titre.objects.get(type=u'DEV',id=tabl_correspondance_devise[xml_sous.get('De')]).cours_set.get_or_create(date=sous.date,defaults={'valeur':fr2decimal(xml_sous.get('Tc'))})
            else:
                sous.montant = fr2decimal(xml_sous.get('M')) * fr2decimal(xml_sous.get('Tc')) - fr2decimal(xml_sous.get('Fc'))
                Titre.objects.get(type=u'DEV',id=tabl_correspondance_devise[xml_sous.get('De')]).cours_set.get_or_create(date=sous.date,defaults={'valeur':1/fr2decimal(xml_sous.get('Tc'))})
        #numero du moyen de paiment
        sous.num_cheque = xml_sous.get('Ct')
        #statut de pointage
        if int(xml_sous.get('P')) == 1:
            sous.pointe = True
        if int(xml_sous.get('A')) == 1:
            sous.automatique = True
        try:
            sous.tiers_id = tabl_correspondance_tiers[xml_sous.get('T')]
        except KeyError:
            sous.tiers = None
        try:
            if xml_sous.get('C') and (int(xml_sous.get('C'))):
                sous.cat_id = tabl_correspondance_cat[xml_sous.get('C')][xml_sous.get('Sc')]
            else:
                sous.cat = None
        except KeyError:
            sous.cat = None
        try:
            if xml_sous.get('I') and int(xml_sous.get('I')):
                sous.ib_id = tabl_correspondance_ib[xml_sous.get('I')][xml_sous.get('Si')]
            else:
                sous.ib = None
        except KeyError:
            sous.ib=None
        try:#moyen de paiment
            sous.moyen_id=tabl_correspondance_moyen[str(sous.compte_id)][xml_sous.get('Ty')]
        except KeyError:
            sous.moyen = None
        try: #gestion des rapprochements
            sous.rapp_id = tabl_correspondance_rapp[xml_sous.get('R')]
            if datetime.datetime.combine(sous.rapp.date, datetime.time()) > datetime.datetime.strptime(sous.date, "%Y-%m-%d"):
                sous.rapp.date = sous.date
                sous.rapp.save()
        except KeyError:
            sous.tapp = None
        sous.notes = xml_sous.get('N')
        sous.piece_comptable = xml_sous.get('Pc')
        #exercices
        try:
            sous.exercice_id = tabl_correspondance_exo[xml_sous.get('E')]
        except KeyError:
            sous.exercice = None
        sous.save()
    nb_tot_ope=0
    percent=1
    for xml_sous in list_ope:
        nb_tot_ope +=1
        affiche=False
        if nb_tot_ope==int(nb_ope_final*int("%s0"%percent)/100):
            logger.info("2*ope %s, ope %s sur %s soit %s%%"%(xml_sous.get('No'),nb_tot_ope,nb_ope_final,"%s0"%percent))
            affiche=True
            percent +=1
        #gestion des virements
        if int(xml_sous.get('Ro')):
            logger.debug('virement vers %s'%xml_sous.get('Ro'))
            sous=Ope.objects.get(id=tabl_correspondance_ope[xml_sous.get('No')])
            sous.jumelle_id = tabl_correspondance_ope[xml_sous.get('Ro')]
            sous.save()
        #gestion des ventilations
        #bool(int(xml_sous.get('Ov'))) pas besoin car on regarde avec des requetes sql
        if int(xml_sous.get('Va')):
            logger.debug('ventilation de %s'%tabl_correspondance_ope[xml_sous.get('Va')])
            sous=Ope.objects.get(id=tabl_correspondance_ope[xml_sous.get('No')])
            sous.mere_id = tabl_correspondance_ope[xml_sous.get('Va')]
            sous.save()

    logger.warning(u"%s operations" % nb_tot_ope)


    #------------------------------echeances#------------------------------
    nb = 0
    for xml_element in xml_tree.find('Echeances/Detail_des_echeances'):
        nb += 1
        logger.debug("echeance %s"%xml_element.get('No'))
        element = Echeance(
            date=datefr2datesql(xml_element.get('Date')),
            montant=fr2decimal(xml_element.get('Montant')),
            compte_id = tabl_correspondance_compte[xml_element.get('Compte')],
            devise_id =tabl_correspondance_devise[xml_element.get('Devise')]
        )
        element.save()
        tabl_correspondance_ech[xml_element.get('No')]=element.id
        try:
            element.tiers_id =tabl_correspondance_tiers[xml_element.get('Tiers')]
        except KeyError:
            element.tiers = None
        element.inscription_automatique=bool(int(xml_element.get('Automatique')))
        try:
            element.moyen_id =tabl_correspondance_moyen[xml_element.get('Compte')][xml_element.get('Type')]
        except KeyError:
            element.moyen = None
        try:
            element.exercice_id = tabl_correspondance_exo[xml_element.get('Exercice')]
        except KeyError:
            element.moyen = None
        element.notes = xml_element.get('Notes')
        try:
            element.cat_id = tabl_correspondance_cat[xml_element.get('Categorie')][xml_element.get('Sous-categorie')]
        except KeyError:
            element.cat= None
        try:
            element.ib_id= tabl_correspondance_ib[xml_element.get('Imputation')][xml_element.get('Sous-imputation')]
        except KeyError:
            element.ib= None
        if xml_element.get('Virement_compte') != xml_element.get('Compte'):
            element.compte_virement_id = tabl_correspondance_compte[xml_element.get('Virement_compte')]
            try:
                element.moyen_virement_id = tabl_correspondance_compte[xml_element.get('Type_contre_ope')]
            except KeyError:
                element.moyen_virement = None
        else :
            element.compte_virement = None
            element.moyen_virement = None
        element.periodicite=liste_type_period[int(xml_element.get('Periodicite'))][0]
        if element.periodicite == 'p':
            element.intervalle=int(xml_element.get('Intervalle_periodicite'))
            element.periode_perso=liste_type_period_perso[int(xml_element.get('Periodicite_personnalisee'))][0]
        element.date_limite=datefr2datesql(xml_element.get('Date_limite'))
        element.save()
    logger.warning(u"%s échéances" % nb)
    logger.warning(u'{!s}'.format(time.clock()))
    logger.warning(u'fini')

if __name__ == "__main__":
    nomfich="%s/20040701.gsb"%(os.path.dirname(os.path.abspath(__file__)))
    #~ nomfich="%s/test_files/test_original.gsb"%(os.path.dirname(os.path.abspath(__file__)))
    nomfich = os.path.normpath(nomfich)
    logger.setLevel(20)#change le niveau de log (10 = debug, 20=info)
    import_gsb(nomfich,efface_table=True)
    logger.info(u'fichier %s importe'%nomfich)
