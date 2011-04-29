# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    from mysite import settings

    setup_environ(settings)

from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from mysite.gsb.models import *
import os, codecs, time
import decimal

liste_type_cat = Cat.typesdep
liste_type_signe = Moyen.typesdep
liste_type_compte = Compte.typescpt
liste_type_period = Echeance.typesperiod
liste_type_period_perso = Echeance.typesperiodperso

try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et

class LOG(object):
    def __init__(self, niv_actuel, filename, niv_min_pour_apparaitre_dans_le_fichier=125):
        super(LOG, self).__init__()
        self.niv_actuel = niv_actuel
        self.filename = filename
        self.niv_min_pour_apparaitre_dans_le_fichier = niv_min_pour_apparaitre_dans_le_fichier

    def log(self, s, niv_min_pour_apparaitre=2):
        if type(s) != unicode:
            chaine = unicode(s)
        else:
            chaine = s
        if niv_min_pour_apparaitre >= self.niv_actuel:
            print chaine
        if niv_min_pour_apparaitre >= self.niv_min_pour_apparaitre_dans_le_fichier:
            chaine = u"%s\n" % chaine
            f = codecs.open(self.filename, 'a', 'utf-8')
            f.write(chaine.encode('utf-8'))
            f.close()

    def set(self, niv_actuel):
        self.niv_actuel = niv_actuel


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


def import_gsb(nomfich, niv_log=10):
    log = LOG(niv_log, 'import_gsb.log')
    nomfich = os.path.normpath(nomfich)
    for table in ('generalite', 'ope', 'echeance', 'rapp', 'moyen', 'compte', 'scat', 'cat', 'exercice', 'sib', 'ib', 'banque', 'titre', 'devise', 'tiers', 'cours'):
        connection.cursor().execute("delete from {};".format(table))
        #log.log(u'table {} effacée'.format(table))
    log.log(u"debut du chargement")
    time.clock()
    xml_tree = et.parse(nomfich)
    root = xml_tree.getroot()
    #verification du format
    xml_element = str(xml_tree.find('Generalites/Version_fichier').text)
    if xml_element != '0.5.0':
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
            s = element.notes.partition('@')
            sous = Titre(nom=element.nom[7:])
            if s[1] == '':
                if s[0] == '':
                    sous.isin = "XX{}".format(nb_sous)
                else:
                    sous.isin = s[0]
                sous.type = "XXX"
            else:
                if s[0] == '':
                    sous.isin = "XX{}".format(nb_sous)
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
                    sous.type = liste_type.get(s[2], 'XXX')
            sous.tiers = element
            sous.devise = None
            sous.save()
        log.log(time.clock(), 1)

    log.log(u'{} tiers enregistrés et {} titres'.format(nb, nb_sous))

    #import des categories et des sous categories
    nb = 0
    for xml_element in xml_tree.find('//Detail_des_categories'):
        nb_sous = 0
        nb += 1
        element = Cat(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.type = liste_type_cat[int(xml_element.get('Type'))][0]
        element.save()
        for xml_sous in xml_element:
            nb_sous += 1
            element.scat_set.create(
                nom=xml_sous.get('Nom'),
                grisbi_id=xml_sous.get('No')
            )
        log.log(time.clock(), 1)

    log.log(u"{} catégories".format(nb))

    #imputations
    nb = 0
    for xml_element in xml_tree.find('//Detail_des_imputations'):
        nb_sous = 0
        nb += 1
        element = Ib(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.type = liste_type_cat[int(xml_element.get('Type'))][0]
        element.save()
        for xml_sous in xml_element:
            nb_sous += 1
            element.sib_set.create(
                nom=xml_sous.get('Nom'),
                grisbi_id=xml_sous.get('No')
            )
        log.log(time.clock(), 1)
    log.log(u"{} imputations".format(nb))

    #gestion des devises:
    nb = 0
    for xml_element in xml_tree.find('//Detail_des_devises'):
        nb += 1
        element = Devise(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.isocode = xml_element.get('IsoCode')
        #creation du titre devise
        sous=Titre(nom=element.nom,isin=element.isocode,tiers=None,devise=element,type='DEV',)
        sous.save()
        if fr2decimal(xml_element.get('Change')) != decimal.Decimal('0'):
            element.dernier_tx_de_change = fr2decimal(xml_element.get('Change'))
        else:
            element.dernier_tx_de_change = 1
        if datefr2datesql(xml_element.get('Date_dernier_change')) is not None:
            element.date_dernier_change = datefr2datesql(xml_element.get('Date_dernier_change'))
        #creation du cours
        Cours(isin=sous,valeur=element.dernier_tx_de_change,date=element.date_dernier_change).save()
        element.save()
        log.log(time.clock(), 1)
    log.log(u'{} devises'.format(nb))

    #gestion des banques:
    nb = 0
    for xml_element in xml_tree.find('Banques/Detail_des_banques'):
        nb += 1
        element = Banque(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.cib = xml_element.get('Code')
        element.notes = xml_element.get('Remarques')
        element.save()
        log.log(time.clock(), 1)
    log.log(u'{} banques'.format(nb))

    #gestion des generalites
    xml_element = xml_tree.find('Generalites')
    element = Generalite(
        titre=xml_element.find('Titre').text,
        utilise_exercices=bool(int(xml_element.find('Utilise_exercices').text)),
        utilise_ib=bool(int(xml_element.find('Utilise_IB').text)),
        utilise_pc=bool(int(xml_element.find('Utilise_PC').text)),
        devise_generale=Devise.objects.get(id=int(xml_element.find('Numero_devise_totaux_ib').text)),
        )
    element.save()
    log.log(time.clock(), 1)
    log.log(u'generalites ok')

    #gestion des exercices:
    nb = 0
    for xml_element in xml_tree.find('Exercices/Detail_des_exercices'):
        nb += 1
        element = Exercice(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.date_debut = datefr2datesql(xml_element.get('Date_debut'))
        element.date_fin = datefr2datesql(xml_element.get('Date_fin'))
        element.save()
        log.log(time.clock(), 1)
    log.log(u'{} exercices'.format(nb))

    #gestion Des rapp
    nb = 0
    for xml_element in xml_tree.find('Rapprochements/Detail_des_rapprochements'):
        nb += 1
        element = Rapp(id=xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.save()
        log.log(time.clock(), 1)
    log.log(u'{} rapprochements'.format(nb))

    #gestion des comptes
    nb = 0
    nb_tot_moyen = 0
    nb_tot_ope = 0
    for xml_element in xml_tree.findall('Comptes/Compte'):
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
            element.devise = Devise.objects.get(id=int(xml_element.find('Details/Devise').text))

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
        #---------------MOYENS---------------------
        for xml_sous in xml_element.find('Detail_de_Types'):
            nb_tot_moyen += 1
            nb_moyen += 1
            element.moyen_set.create(nom=xml_sous.get('Nom'),
                                     signe=liste_type_signe[int(xml_sous.get('Signe'))][0],
                                     affiche_numero=bool(int(xml_sous.get('Affiche_entree'))),
                                     num_auto=bool(int(xml_sous.get('Numerotation_auto'))),
                                     num_en_cours=int(xml_sous.get('No_en_cours')),
                                     grisbi_id=int(xml_sous.get('No'))
            )
        try:
            toto = int(xml_element.find('Details/Type_defaut_credit').text)
            element.moyen_credit_defaut = element.moyen_set.get(grisbi_id=toto)
        except (ObjectDoesNotExist, TypeError):
            element.moyen_credit_defaut = None
        try:
            element.moyen_debit_defaut = element.moyen_set.get(
                grisbi_id=int(xml_element.find('Details/Type_defaut_debit').text))
        except (ObjectDoesNotExist, TypeError):
            element.moyen_debit_defaut = None
        element.save()
        log.log(u'ajout du compte "%s" et des %s moyens de paiment ok' % (element.nom, nb_moyen))
        log.log(time.clock(), 1)
    log.log(u'{} comptes'.format(nb))
    #--------------OPERATIONS-----------------------
    for xml_sous in xml_tree.find('//Detail_des_operations'):
        nb_tot_ope += 1
        cpt=Compte.objects.get(id=int(xml_sous.find('../../Details/No_de_compte').text))
        sous, created = element.ope_set.get_or_create(id=int(xml_sous.get('No')), defaults={'compte':cpt })
        if not created and (sous.montant != 0 or sous.date != datetime.date.today() or sous.moyen is not None):
            raise Exception(u'probleme avec les operations')
        #date
        sous.date = datefr2datesql(xml_sous.get('D'))
        #date de valeur
        sous.date_val = datefr2datesql(xml_sous.get('Db'))
        #montant et gestion des devises
        sous.montant = fr2decimal(xml_sous.get('M'))
        if int(xml_sous.get('De')) != sous.compte.devise.id:
            sous.montant = fr2decimal(xml_sous.get('M'))/fr2decimal(xml_sous.get('Tc'))-fr2decimal(xml_sous.get('Fc'))
            Cours(isin=Titre.objects.get(isin=Devise.objects.get(id=int(xml_sous.get('De')))),valeur=fr2decimal(xml_sous.get('Tc')),date=sous.date).save()
        #numero du moyen de paiment
        sous.num_cheque = xml_sous.get('Ct')
        #statut de pointage
        if int(xml_sous.get('P'))==1:
            sous.pointe = True
        if int(xml_sous.get('A')) == 1:
            sous.automatique = True
        try:
            sous.tiers = Tiers.objects.get(id=int(xml_sous.get('T')))
        except (ObjectDoesNotExist, TypeError):
            sous.tiers = None
        try:#cat et scat
            sous.cat = Cat.objects.get(id=int(xml_sous.get('C')))
        except (ObjectDoesNotExist, TypeError):
            sous.cat = None
        else:
            try:
                sous.scat = sous.cat.scat_set.get(grisbi_id=int(xml_sous.get('Sc')))
            except (ObjectDoesNotExist, TypeError):
                sous.scat = None
        try:#ib et sib
            sous.ib = Ib.objects.get(id=int(xml_sous.get('I')))
        except (ObjectDoesNotExist, TypeError):
            sous.ib = None
        else:
            try:
                sous.sib = sous.ib.sib_set.get(grisbi_id=int(xml_sous.get('Si')))
            except (ObjectDoesNotExist, TypeError):
                sous.sib = None
        try:#moyen de paiment
            sous.moyen = sous.compte.moyen_set.get(grisbi_id=int(xml_sous.get('Ty')))
        except (ObjectDoesNotExist, TypeError):
            sous.moyen = None
        try: #gestion des rapprochements
            if int(xml_sous.get('R')):
                sous.rapp = Rapp.objects.get(id=int(xml_sous.get('R')))
                if datetime.datetime.combine(sous.rapp.date, datetime.time()) > datetime.datetime.strptime(sous.date,"%Y-%m-%d"):
                    sous.rapp.date = sous.date
                    sous.rapp.save()
        except (ObjectDoesNotExist, TypeError):
            sous.tapp = None
        #exercices
        try:
            sous.exercice = Exercice.objects.get(id=int(xml_sous.get('E')))
        except (ObjectDoesNotExist, TypeError):
            sous.exercice = None
        #gestion des virements
        try:
            if int(xml_sous.get('Ro')):
                sous.jumelle, created = Ope.objects.get_or_create(id=int(xml_sous.get('Ro')), defaults={'compte': Compte.objects.get(id=int(xml_sous.get('Rc')))})
        except (ObjectDoesNotExist, TypeError):
            sous.jumelle = None
        #gestion des ventilations
        try:
            sous.is_mere = bool(int(xml_sous.get('Ov')))
            if int(xml_sous.get('Va')):
                sous.mere, created = Ope.objects.get_or_create(id=int(xml_sous.get('Va')),defaults={'compte': element})
        except (ObjectDoesNotExist, TypeError):
            sous.mere = None
        sous.notes=xml_sous.get('N')
        sous.piece_comptable=xml_sous.get('Pc')
        sous.save()
    log.log(u"%s operations" % nb_tot_ope)
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
            element.devise = Devise.objects.get(id=int(xml_element.get('Devise')))
        except (ObjectDoesNotExist, TypeError):
            element.devise = None
        try:
            element.devise = Devise.objects.get(id=int(xml_element.get('Devise')))
        except (ObjectDoesNotExist, TypeError):
            element.devise = None
        try:
            element.moyen = Moyen.objects.get(id=int(xml_element.get('Type')))
        except (ObjectDoesNotExist, TypeError):
            element.moyen = None
        try:
            element.exercice = Exercice.objects.get(id=int(xml_element.get('Exercice')))
        except (ObjectDoesNotExist, TypeError):
            element.moyen = None
        element.notes = xml_element.get('Notes')
        try:
            element.cat = Cat.objects.get(id=int(xml_element.get('Categorie')))
            try:
                id = int(xml_element.get('Sous-categorie'))
                element.scat = element.cat.scat_set.get(grisbi_id=id)
            except (ObjectDoesNotExist, TypeError):
                element.scat = None
        except (ObjectDoesNotExist, TypeError):
            element.cat = None
            element.scat = None
        try:
            element.ib = Ib.objects.get(id=int(xml_element.get('Imputation')))
            try:
                element.sib = element.ib.sib_set.get(grisbi_id=int(xml_element.get('Sous-imputation')))
            except (ObjectDoesNotExist, TypeError):
                element.sib = None
        except (ObjectDoesNotExist, TypeError):
            element.ib = None
            element.sib = None
        try:
            if int(xml_element.get('Virement_compte')) and int(xml_element.get('Compte')):
                element.compte_virement = Compte.objects.get(int(xml_element.get('Virement_compte')))
                try:
                    element.moyen_virement = element.compte_virement.moyen_set.get(grisbi_id = int(xml_element.get('Type_contre_ope')))
                except (ObjectDoesNotExist, TypeError):
                    element.moyen_virement = None
            else:
                raise ObjectDoesNotExist
        except (ObjectDoesNotExist, TypeError):
            element.compte_virement = None
            element.moyen_virement = None
        element.save()
    log.log(time.clock(), 1)
    log.log(u'{!s}'.format(time.clock()))
    log.log(u'fini')


if __name__ == "__main__":
    import_gsb("{}/test_files/test_original.gsb".format(os.path.dirname(os.path.abspath(__file__))), 2)
