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
liste_type_moyen = Moyen.typesdep
liste_type_compte = Compte.typescpt
liste_type_period = Echeance.typesperiod
liste_type_period_perso = Echeance.typesperiodperso

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


def import_gsb(nomfich,info=''):
    logger=logging.getLogger('gsb.import')
    for table in ('generalite', 'ope', 'echeance', 'rapp', 'moyen', 'compte',  'cat', 'exercice', 'ib', 'banque', 'titre', 'tiers'):
        connection.cursor().execute("delete from %s;"%table)
        logger.info(u'table %s effacée'%table)
    logger.debug(u"debut du chargement")
    time.clock()
    xml_tree = et.parse(nomfich)
    root = xml_tree.getroot()
    #verification du format
    xml_element = str(xml_tree.find('Generalites/Version_fichier').text)
    if xml_element != '0.5.0':
        logger.critical("le format n'est pas reconnu")
        raise Import_exception, "le format n'est pas reconnu"
        #import des tiers
    nb = 0
    nb_sous = 0
    for xml_element in xml_tree.find('//Detail_des_tiers'):
        nb += 1
        element = Tiers(id=xml_element.get('No'), nom=xml_element.get('Nom'), notes=xml_element.get('Informations'))
        element.save()
        if element.nom[:6] == "titre_":
            nb_sous += 1
            element.is_titre = True
            element.save()
            s= unicode(xml_element.get('Informations'))
            s = s.split('@')
            sous = Titre(nom=element.nom[7:])
            if not s[1]:
                if s[0] == '':
                    sous.isin = "XX%s"%nb_sous
                else:
                    sous.isin = s[0]
                sous.type = "XXX"
            else:
                if s[0] == '':
                    sous.isin = "XX%s"%nb_sous
                else:
                    sous.isin = s[0]
                    liste_type = {
                        'ACT': 'ACT',
                        'action': 'ACT',
                        'OBL': 'OBL',
                        'obligation': 'OBL',
                        'CSL': 'CSL',
                        'csl': 'CSL',
                        'compte sur livret': 'CSL',
                        'opcvm': 'OPC',
                        'sicav': 'OPC',
                        'OPC': 'OPC',
                        }
                    sous.type = liste_type.get(s[1], 'XXX')
            sous.tiers = element
            sous.save()
        logger.debug(nb)

    logger.debug(u'%s tiers enregistrés et %s titres'%(nb, nb_sous))
    logger.debug(time.clock())
    #import des categories et des sous categories
    nb_cat = 0
    cat_dic={}
    for xml_element in xml_tree.find('//Detail_des_categories'):
        nb_cat += 1
        cat_dic[int(xml_element.get('No'))]={0:nb_cat}
        query={'id':nb_cat,'nom':"%s:"%(xml_element.get('Nom'),),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
        Cat.objects.create(**query)
        for xml_sous in xml_element:
            nb_cat += 1
            cat_dic[int(xml_element.get('No'))][int(xml_sous.get('No'))]=nb_cat
            query={'id':nb_cat,'nom':"%s:%s"%(xml_element.get('Nom'),xml_sous.get('Nom')),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
            Cat.objects.create(**query)
    logger.debug(time.clock())
    logger.debug(u"%s catégories"%nb_cat)
    
    #imputations
    nb_ib = 0
    ib_dic={}
    for xml_element in xml_tree.find('//Detail_des_imputations'):
        nb_ib += 1
        ib_dic[int(xml_element.get('No'))]={0:nb_ib}
        query={'id':nb_ib,'nom':"%s"%(xml_element.get('Nom'),),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
        Ib.objects.create(**query)
        for xml_sous in xml_element:
            nb_ib += 1
            ib_dic[int(xml_element.get('No'))][int(xml_sous.get('No'))]=nb_ib
            query={'id':nb_ib,'nom':"%s:%s"%(xml_element.get('Nom'),xml_sous.get('Nom')),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
            Ib.objects.create(**query)
        logger.debug(nb)
    logger.debug(time.clock())
    logger.debug(u"%s imputations"%nb_ib)

    #gestion des devises:
    nb = 0
    for xml_element in xml_tree.find('//Detail_des_devises'):
        nb += 1
        element = Titre(nom=xml_element.get('Nom'), isin=xml_element.get('IsoCode'), tiers=None, type='DEV',grisbi_id=xml_element.get('No') )
        element.save()
        if fr2decimal(xml_element.get('Change')) != decimal.Decimal('0'):
            element.cours_set.get_or_create(isin=element.isin,date=datefr2datesql(xml_element.get('Date_dernier_change')),defaults={'date':datefr2datesql(xml_element.get('Date_dernier_change')),'valeur':fr2decimal(xml_element.get('Change'))})
        else:
            element.cours_set.get_or_create(isin=element.isin,date=datetime.datetime.today(),defaults={'date':datetime.datetime.today(),'valeur':fr2decimal('1')})
        element.save()
    logger.debug(time.clock())
    logger.debug(u'%s devises'%nb)

    #gestion des banques:
    nb = 0
    for xml_element in xml_tree.find('Banques/Detail_des_banques'):
        nb += 1
        element = Banque(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.cib = xml_element.get('Code')
        element.notes = xml_element.get('Remarques')
        element.save()
    logger.debug(time.clock())
    logger.debug(u'%s banques'%nb)

    #gestion des generalites
    xml_element = xml_tree.find('Generalites')
    if not xml_element.find('Titre').text:
        titre_fichier=""
    else:
        titre_fichier=xml_element.find('Titre').text
    element = Generalite(
        titre=titre_fichier,
        utilise_exercices=bool(int(xml_element.find('Utilise_exercices').text)),
        utilise_ib=bool(int(xml_element.find('Utilise_IB').text)),
        utilise_pc=bool(int(xml_element.find('Utilise_PC').text)),
        devise_generale=Titre.objects.get(type=u'DEV',grisbi_id=int(xml_element.find('Numero_devise_totaux_ib').text)),
        )
    element.save()
    logger.debug(time.clock())
    logger.debug(u'generalites ok')

    #gestion des exercices:
    nb = 0
    for xml_element in xml_tree.find('Exercices/Detail_des_exercices'):
        nb += 1
        element = Exercice(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.date_debut = datefr2datesql(xml_element.get('Date_debut'))
        element.date_fin = datefr2datesql(xml_element.get('Date_fin'))
        element.save()
    logger.debug(time.clock())
    logger.debug(u'%s exercices'%nb)

    #gestion Des rapp
    nb = 0
    for xml_element in xml_tree.find('Rapprochements/Detail_des_rapprochements'):
        nb += 1
        element = Rapp(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.save()
    logger.debug(time.clock())
    logger.debug(u'%s rapprochements'%nb)

    #gestion des comptes
    nb = 0
    nb_tot_moyen = 0
    for xml_element in xml_tree.findall('//Compte'):
        nb += 1
        nb_moyen = 0
        element = Compte(id=(int(xml_element.find('Details/No_de_compte').text)))
        element.nom = xml_element.find('Details/Nom').text
        element.cloture = bool(int(xml_element.find('Details/Compte_cloture').text))
        if xml_element.find('Details/Titulaire').text is None:
            element.titulaire = ''
        else:
            element.titulaire = xml_element.find('Details/Titulaire').text
        element.type = liste_type_compte[int(xml_element.find('Details/Type_de_compte').text)][0]

        if xml_element.find('Details/Devise').text is None:
            element.devise = None
        else:
            element.devise = Titre.objects.get(type=u'DEV',grisbi_id=int(xml_element.find('Details/Devise').text))

        if xml_element.find('Details/Banque') is None or int(xml_element.find('Details/Banque').text) == 0:
            element.banque = None
        else:
            element.banque = Banque.objects.get(id=int(xml_element.find('Details/Banque').text))
        if xml_element.find('Details/Guichet').text is None:
            element.guichet = ''
        else:
            element.guichet = xml_element.find('Details/Guichet').text
        if xml_element.find('Details/No_compte_banque').text is not None:
            element.num_compte = xml_element.find('Details/No_compte_banque').text
        else:
            element.num_compte == ''
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
        tabl_correspondance={}
        #---------------MOYENS---------------------
        for xml_sous in xml_element.find('Detail_de_Types'):
            nb_tot_moyen += 1
            nb_moyen += 1
            moyen,created = Moyen.objects.get_or_create(nom=xml_sous.get('Nom'),defaults={'nom':xml_sous.get('Nom'),
                                     'type':liste_type_moyen[int(xml_sous.get('Signe'))][0],
                                     'affiche_numero':bool(int(xml_sous.get('Affiche_entree'))),
                                     'num_auto':bool(int(xml_sous.get('Numerotation_auto'))),
                                     'num_en_cours':int(xml_sous.get('No_en_cours'))}
            )
            tabl_correspondance[int(xml_sous.get('No'))]=moyen.id
        try:
            element.moyen_credit_defaut_id = tabl_correspondance[int(xml_element.find('Details/Type_defaut_credit').text)]
        except (KeyError, TypeError):
            element.moyen_credit_defaut_id = None
        try:
            element.moyen_debit_defaut_id = tabl_correspondance[int(xml_element.find('Details/Type_defaut_debit').text)]
        except (KeyError, TypeError):
            element.moyen_debit_defaut_id = None
        element.save()
        logger.debug(nb)
    logger.debug(time.clock())
    logger.debug(u'%s comptes'%nb)
    nb_tot_ope=0
    #--------------OPERATIONS-----------------------
    for xml_sous in xml_tree.findall('//Operation'):
        nb_tot_ope += 1
        cpt = Compte.objects.get(id=int(xml_sous.find('../../Details/No_de_compte').text))
        sous = Ope(id=int(xml_sous.get('No')),compte = cpt)
        sous.date = datefr2datesql(xml_sous.get('D'))
        #date de valeur
        sous.date_val = datefr2datesql(xml_sous.get('Db'))
        #montant et gestion des devises
        sous.montant = fr2decimal(xml_sous.get('M'))
        if int(xml_sous.get('De')) != sous.compte.devise.grisbi_id:
            if int(xml_sous.get('Rdc')):
                sous.montant = fr2decimal(xml_sous.get('M')) / fr2decimal(xml_sous.get('Tc')) - fr2decimal(xml_sous.get('Fc'))
                Titre.objects.get(type=u'DEV',grisbi_id=int(xml_sous.get('De'))).cours_set.get_or_create(date=sous.date,defaults={'valeur':fr2decimal(xml_sous.get('Tc'))})
            else:
                sous.montant = fr2decimal(xml_sous.get('M')) * fr2decimal(xml_sous.get('Tc')) - fr2decimal(xml_sous.get('Fc'))
                Titre.objects.get(type=u'DEV',grisbi_id=int(xml_sous.get('De'))).cours_set.get_or_create(date=sous.date,defaults={'valeur':1/fr2decimal(xml_sous.get('Tc'))})
        #numero du moyen de paiment
        sous.num_cheque = xml_sous.get('Ct')
        #statut de pointage
        if int(xml_sous.get('P')) == 1:
            sous.pointe = True
        if int(xml_sous.get('A')) == 1:
            sous.automatique = True
        if  int(xml_sous.get('T')):
            sous.tiers_id = int(xml_sous.get('T'))
        else:
            try:
                sous.tiers = Tiers.objects.get(id=int(xml_sous.get('T')))
            except (Tiers.DoesNotExist, TypeError):
                sous.tiers = None
        if xml_sous.get('C') and (int(xml_sous.get('C'))):
            sous.cat_id = cat_dic[int(xml_sous.get('C'))][int(xml_sous.get('Sc'))]
        else:
            sous.cat = None
        if xml_sous.get('I') and int(xml_sous.get('I')):
            sous.ib_id = ib_dic[int(xml_sous.get('I'))][int(xml_sous.get('Si'))]
        else:
            sous.ib = None
        try:#moyen de paiment
            if int(xml_sous.get('Ty')):
                sous.moyen = Moyen.objects.get(id=int(xml_sous.get('Ty')))
            else:
                sous.moyen = None
        except (Moyen.DoesNotExist, TypeError):
            sous.moyen = None
        try: #gestion des rapprochements
            if int(xml_sous.get('R')):
                sous.rapp = Rapp.objects.get(id=int(xml_sous.get('R')))
                if datetime.datetime.combine(sous.rapp.date, datetime.time()) > datetime.datetime.strptime(sous.date, "%Y-%m-%d"):
                    sous.rapp.date = sous.date
                    sous.rapp.save()
            else:
                sous.rapp = None
        except (Rapp.DoesNotExist, TypeError):
            sous.tapp = None
            #exercices
        try:
            sous.exercice = Exercice.objects.get(id=int(xml_sous.get('E')))
        except (Exercice.DoesNotExist, TypeError):
            sous.exercice = None
        #gestion des virements
        if int(xml_sous.get('Ro')):
            sous.jumelle_id = int(xml_sous.get('Ro'))
        #gestion des ventilations
        #bool(int(xml_sous.get('Ov'))) pas besoin car on regarde avec des requetes sql
        if int(xml_sous.get('Va')):
            sous.mere_id = int(xml_sous.get('Va'))
        sous.notes = xml_sous.get('N')
        sous.piece_comptable = xml_sous.get('Pc')
        sous.save()
        logger.debug(nb_tot_ope)
    logger.debug(time.clock())
    logger.debug(u"%s operations" % nb_tot_ope)
    #gestion des echeances
    nb = 0
    for xml_element in xml_tree.find('Echeances/Detail_des_echeances'):
        nb += 1
        element = Echeance(
            id=int(xml_element.get('No')),
            date=datefr2datesql(xml_element.get('Date')),
            montant=fr2decimal(xml_element.get('Montant'))
        )
        element.compte = Compte.objects.get(id=int(xml_element.get('Compte')))
        try:
            element.tiers = Tiers.objects.get(id=int(xml_element.get('Tiers')))
        except (ObjectDoesNotExist, TypeError):
            element.tiers = None
        try:
            element.devise = Titre.objects.get(type=u'DEV',grisbi_id=int(xml_element.get('Devise')))
        except (ObjectDoesNotExist, TypeError):
            element.devise = None
        element.inscription_automatique=bool(int(xml_element.get('Automatique')))
        try:
            element.moyen = Moyen.objects.get(id=int(xml_element.get('Type')))
        except (ObjectDoesNotExist, TypeError):
            element.moyen = None
        try:
            element.exercice = Exercice.objects.get(id=int(xml_element.get('Exercice')))
        except (ObjectDoesNotExist, TypeError):
            element.moyen = None
        element.notes = xml_element.get('Notes')
        if xml_element.get('Categorie') and int(xml_element.get('Categorie')):
            element.cat_id = cat_dic[int(xml_element.get('Categorie'))][int(xml_element.get('Sous-categorie'))]
        else:
            element.cat= None
        if xml_element.get('Imputation') and int(xml_element.get('Imputation')):
            element.ib_id= ib_dic[int(xml_element.get('Imputation'))][int(xml_element.get('Sous-imputation'))]
        else:
            element.ib= None
        if xml_element.get('Virement_compte') != xml_element.get('Compte'):
            element.compte_virement = Compte.objects.get(id=int(xml_element.get('Virement_compte')))#ici aussi
            try:
                element.moyen_virement = Moyen.objects.get(id=int(xml_element.get('Type_contre_ope')))
            except (Moyen.DoesNotExist, TypeError):
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
        logger.debug(nb)
    logger.debug(u"%s échéances" % nb)
    logger.debug(u'{!s}'.format(time.clock()))
    logger.debug(u'fini')
    if info == '':
        logger.info(u'fichier %s importe',nomfich)
    else:
        logger.info(u'fichier %s importe par %s',(nomfich,info))

if __name__ == "__main__":
    nomfich="%s/test_files/test_original.gsb"%(os.path.dirname(os.path.abspath(__file__)))
    nomfich = os.path.normpath(nomfich)
    import_gsb(nomfich,'script')
    #import_gsb("%s/20040701.gsb"%(os.path.dirname(os.path.abspath(__file__))), 1)
