# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, time
    sys.path.append(r"c:\django")
    from mysite import settings
    setup_environ(settings)

from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from mysite.gsb.models import *
import os,codecs, time


liste_type_cat = Cat.typesdep
liste_type_signe = Moyen.typesdep
liste_type_compte = Compte.typescpt
liste_type_pointage = Ope.typespointage
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et

class LOG(object):
    def __init__(self, niv_actuel, filename, niv_min_pour_apparaitre_dans_le_fichier = 125):
        super( LOG, self).__init__()
        self.niv_actuel = niv_actuel
        self.filename = filename
        self.niv_min_pour_apparaitre_dans_le_fichier = niv_min_pour_apparaitre_dans_le_fichier
    def log(self, s, niv_min_pour_apparaitre = 2):
        if type(s) != unicode:
            chaine = unicode(s)
        else:
            chaine = s
        if niv_min_pour_apparaitre >= self.niv_actuel:
            print chaine
        if niv_min_pour_apparaitre >= self.niv_min_pour_apparaitre_dans_le_fichier:
            chaine = u"%s\n"%chaine
            f = codecs.open( self.filename, 'a', 'utf-8')
            f.write(chaine.encode('utf-8'))
            f.close()
    def set(self, niv_actuel):
        self.niv_actuel = niv_actuel
def datefr2time(s):
    try:
        t = time.strptime(str(s), "%d/%m/%Y")
        return "{annee}-{mois}-{jour}".format(annee = t[0], mois = t[1], jour = t[2])
    except ValueError :
        return None
def fr2uk(s):
    if s is not None:
        return float(str(s).replace(',' , '.'))
    else:
        return None
class Import_exception(Exception):
    pass
def import_gsb(nomfich, niv_log=10):
    log = LOG(niv_log , 'import_gsb.log')
    nomfich=os.path.normpath(nomfich)
    for table in ('generalite', 'ope', 'echeance', 'rapp', 'moyen', 'compte', 'scat', 'cat', 'exercice', 'sib', 'ib', 'banque', 'titre', 'devise', 'tiers'):
        connection.cursor().execute("delete from {};".format(table))
        #log.log(u'table {} effacée'.format(table))
    log.log(u"debut du chargement")
    t = time.clock()
    xml_tree = et.ElementTree(file = nomfich)
    root = xml_tree.getroot()
    #verification du format
    xml_element=str(xml_tree.find('Generalites/Version_fichier').text)
    if xml_element!='0.5.0':
        raise Import_exception,"le format n'est pas reconnu"
    #import des tiers
    nb = 0
    nb_sous = 0
    for xml_element in xml_tree.find( '//Detail_des_tiers' ):
        nb+= 1
        element = Tiers(id = xml_element.get('No'), nom = xml_element.get('Nom'), notes = xml_element.get('Informations'))
        element.save()
        if element.nom[:6]== "titre_":
            nb_sous+= 1
            element.is_titre = True
            element.save()
            s = element.notes.partition('@')
            sous = Titre(nom = element.nom[7:])
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
            sous.save()
        log.log(time.clock(), 1)

    log.log(u'{} tiers enregistrés et {} titres'.format(nb, nb_sous))

    #import des categories et des sous categories
    nb = 0
    for xml_element in xml_tree.find( '//Detail_des_categories' ):
        nb_sous = 0
        nb+= 1
        element = Cat(id = xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.type = liste_type_cat[int(xml_element.get('Type'))][0]
        element.save()
        for xml_sous in xml_element:
            nb_sous+= 1
            element.scat_set.create(
                nom = xml_sous.get('Nom'),
                grisbi_id = xml_sous.get('No')
                )
        log.log(time.clock(), 1)

    log.log( u"{} catégories".format(nb))

    #imputations
    nb = 0
    for xml_element in xml_tree.find( '//Detail_des_imputations' ):
        nb_sous = 0
        nb+= 1
        element = Ib(id = xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.type = liste_type_cat[int(xml_element.get('Type'))][0]
        element.save()
        for xml_sous in xml_element:
            nb_sous+= 1
            element.sib_set.create(
                nom = xml_sous.get('Nom'),
                grisbi_id = xml_sous.get('No')
                )
        log.log(time.clock(), 1)
    log.log( u"{} imputations".format(nb))

    #gestion des devises:
    nb = 0
    for xml_element in xml_tree.find( '//Detail_des_devises' ):
        nb+= 1
        element = Devise(id = xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.isocode = xml_element.get('IsoCode')
        element.dernier_tx_de_change = fr2uk(xml_element.get('Change'))
        element.save()
        log.log(time.clock(), 1)
    log.log( u'{} devises'.format(nb))

    #gestion des banques:
    nb = 0
    for xml_element in xml_tree.find( 'Banques/Detail_des_banques' ):
        nb+= 1
        element = Banque(id = xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.cib = xml_element.get('Code')
        element.notes = xml_element.get('Remarques')
        element.save()
        log.log(time.clock(), 1)
    log.log( u'{} banques'.format(nb))

    #gestion des generalites
    nb = 0
    xml_element = xml_tree.find( 'Generalites' )
    element = Generalite(
        titre = xml_element.find( 'Titre' ).text,
        utilise_exercices = bool(int(xml_element.find( 'Utilise_exercices' ).text)),
        utilise_ib =  bool(int(xml_element.find( 'Utilise_IB' ).text)),
        utilise_pc =  bool(int(xml_element.find( 'Utilise_PC' ).text)),
        devise_generale = Devise.objects.get(id = int(xml_element.find( 'Numero_devise_totaux_ib' ).text)),
    )
    element.save()
    log.log(time.clock(), 1)
    log.log(u'generalites ok')

    #gestion des exercices:
    nb = 0
    for xml_element in xml_tree.find('Exercices/Detail_des_exercices'):
        nb+= 1
        element = Exercice(id = xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.date_debut = datefr2time(xml_element.get('Date_debut'))
        element.date_fin = datefr2time(xml_element.get('Date_fin'))
        element.save()
        log.log(time.clock(), 1)
    log.log(u'{} exercices'.format(nb))

    #gestion Des rapp
    nb = 0
    for xml_element in xml_tree.find('Rapprochements/Detail_des_rapprochements'):
        nb+= 1
        element = Rapp(id = xml_element.get('No'))
        element.nom = xml_element.get('Nom')
        element.save()
        log.log(time.clock(), 1)
    log.log(u'{} rapprochements'.format(nb))

    #gestion des comptes
    nb = 0
    nb_tot_moyen = 0
    nb_tot_ope = 0
    for xml_element in xml_tree.findall( 'Comptes/Compte' ):
        nb+= 1
        nb_moyen = 0
        nb_ope = 0
        element = Compte(id = (int(xml_element.find( 'Details/No_de_compte' ).text)))
        element.nom  = xml_element.find( 'Details/Nom' ).text
        element.cloture = bool(int(xml_element.find('Details/Compte_cloture').text))
        if xml_element.find( 'Details/Titulaire' ).text is None:
            element.titulaire = ''
        else:
            element.titulaire = xml_element.find( 'Details/Titulaire' ).text
        element.type = liste_type_compte[int(xml_element.find( 'Details/Type_de_compte' ).text)][0]

        if xml_element.find('Details/Devise').text is None:
            element.devise = None
        else:
            element.devise = Devise.objects.get(id = int(xml_element.find('Details/Devise').text))

        if xml_element.find('Details/Banque') is None or int(xml_element.find( 'Details/Banque' ).text) == 0:
            element.banque = None
        else:
            element.banque = Banque.objects.get(id = int(xml_element.find( 'Details/Banque' ).text))
        if xml_element.find( 'Details/Guichet').text is None:
            element.guichet = ''
        else:
            element.guichet = xml_element.find( 'Details/Guichet').text
        if xml_element.find( 'Details/No_compte_banque').text is not None:
            element.num_compte = xml_element.find( 'Details/No_compte_banque').text
        else:
            element.num_compte == ''
        if xml_element.find( 'Details/Cle_du_compte').text is not None:
            element.cle_compte = int(xml_element.find( 'Details/Cle_du_compte').text)
        else:
            element.cle_compte = 0
        element.solde_init = fr2uk(xml_element.find( 'Details/Solde_initial').text)
        element.solde_mini_voulu = fr2uk(xml_element.find( 'Details/Solde_mini_voulu').text)
        element.solde_mini_autorise = fr2uk(xml_element.find( 'Details/Solde_mini_autorise').text)
        element.solde_mini_autorise = fr2uk(xml_element.find( 'Details/Solde_mini_autorise').text)
        if xml_element.find( 'Details/Commentaires').text is not None:
            element.notes = xml_element.find( 'Details/Commentaires').text
        else:
            element.notes = ''
        element.save()
        #---------------MOYENS---------------------
        for xml_sous in xml_element.find('Detail_de_Types'):
            nb_tot_moyen+= 1
            nb_moyen+= 1
            element.moyen_set.create(nom = xml_sous.get('Nom'),
                                     signe = liste_type_signe[int(xml_sous.get('Signe'))][0],
                                     affiche_numero = bool(int(xml_sous.get('Affiche_entree'))),
                                     num_auto = bool(int(xml_sous.get('Numerotation_auto'))),
                                     num_en_cours = int(xml_sous.get('No_en_cours')),
                                     grisbi_id = int(xml_sous.get('No'))
                                     )
        try:
            element.moyen_credit_defaut = element.moyen_set.get(grisbi_id = xml_element.find( 'Details/Type_defaut_credit').text)
        except (ObjectDoesNotExist, TypeError):
            pass
        try:
            element.moyen_debit_defaut = element.moyen_set.get(grisbi_id = xml_element.find( 'Details/Type_defaut_debit').text)
        except (ObjectDoesNotExist, TypeError):
            pass
        element.save()
        log.log(u'ajout du compte "%s" et des %s moyens de paiment ok'%(element.nom,nb_moyen))
        #--------------OPERATIONS-----------------------
        for xml_sous in xml_element.find('Detail_des_operations'):
            nb_ope+=1
            sous, created = element.ope_set.get_or_create(id = int(xml_sous.get('No')), defaults = {'devise':Generalite.objects.get(id = 1).devise_generale, 'compte':element})
            if not created and (sous.montant != 0 or sous.date != datetime.date.today() or sous.moyen is not  None):
                raise Exception(u'probleme avec les operations')
            sous.date = datefr2time(xml_sous.get('D'))
            sous.date_val = datefr2time(xml_sous.get('Db'))
            sous.montant = fr2uk(xml_sous.get('M'))
            sous.num_cheque = xml_sous.get('Ct')
            sous.pointe = liste_type_pointage[int(xml_sous.get('P'))][0]
            sous.ismere = bool(int(xml_sous.get('Va')))
            try:
                sous.devise = Devise.objects.get(id = int(xml_sous.get('De')))
            except (ObjectDoesNotExist, TypeError):
                pass
            sous.save()
            try:
                sous.tiers = Tiers.objects.get(id = int(xml_sous.get('T')))
            except (ObjectDoesNotExist, TypeError):
                pass
            try:
                sous.cat = Cat.objects.get(id = int(xml_sous.get('C')))
            except (ObjectDoesNotExist, TypeError):
                pass
            else:
                try:
                    sous.scat = sous.cat.scat_set.get(grisbi_id = int(xml_sous.get('Sc')))
                except (ObjectDoesNotExist, TypeError):
                    pass
            try:
                sous.ib = Ib.objects.get(id = int(xml_sous.get('I')))
            except (ObjectDoesNotExist, TypeError):
                pass
            else:
                try:
                    sous.sib = sous.ib.sib_set.get(grisbi_id = int(xml_sous.get('Si')))
                except (ObjectDoesNotExist, TypeError):
                    pass
            try:
                sous.moyen = sous.compte.moyen_set.get(grisbi_id = int(xml_sous.get('Ty')))
            except (ObjectDoesNotExist, TypeError):
                pass
            try:
                sous.rapp = Rapp.objects.get(id = int(xml_sous.get('R')))
                if sous.rapp.date > sous.date:
                    sous.rapp.date = sous.date
                    sous.rapp.save()
            except (ObjectDoesNotExist, TypeError):
                pass
            try:
                sous.exercice = Exercice.objects.get(id = int(xml_sous.get('E')))
            except (ObjectDoesNotExist, TypeError):
                pass
            try:
                sous.jumelle, created = Ope.objects.get_or_create(id = int(xml_sous.get('Ro')), defaults = {'devise':Generalite.objects.get(id = 1).devise_generale, 'compte':Compte.objects.get(id = int(xml_sous.get('Rc')))})
            except (ObjectDoesNotExist, TypeError):
                pass
            try:
                sous.mere, created = Ope.objects.get_or_create(id = int(xml_sous.get('Va')), defaults = {'devise':Generalite.objects.get(id = 1).devise_generale, 'compte':element})
            except (ObjectDoesNotExist, TypeError):
                pass
        log.log(u"%s operations"%nb_ope)
        log.log(time.clock(), 1)
    log.log( u'{} comptes'.format(nb))
    #gestion des echeances
    nb = 0
    for xml_element in xml_tree.find('Echeances/Detail_des_echeances'):
        nb+= 1
        element = Echeance(
            id = int(xml_element.get('No')),
            date = datefr2time(xml_element.get('Date')),
            montant = fr2uk(xml_element.get('Montant'))
        )
        try:
            element.compte = Compte.objects.get(id = int(xml_element.get('Compte')))
        except (ObjectDoesNotExist, TypeError):
            pass
        try:
            element.tiers = Tiers.objects.get(id = int(xml_element.get('Tiers')))
        except (ObjectDoesNotExist, TypeError):
            pass
        try:
            element.devise = Devise.objects.get(id = int(xml_element.get('Devise')))
        except (ObjectDoesNotExist, TypeError):
            pass
        try:
            element.cat = Cat.objects.get(id = int(xml_element.get('Categorie')))
        except (ObjectDoesNotExist, TypeError):
            pass
            try:
                element.cat = Cat.objects.get(id = int(xml_sous.get('C')))
            except (ObjectDoesNotExist, TypeError):
                pass
            else:
                try:
                    element.scat = element.cat.scat_set.get(grisbi_id = int(xml_sous.get('categorie')))
                except (ObjectDoesNotExist, TypeError):
                    pass
        try:
            element.ib = Ib.objects.get(id = int(xml_sous.get('Imputation')))
        except (ObjectDoesNotExist, TypeError):
            pass
        else:
            try:
                sous.sib = element.ib.sib_set.get(grisbi_id = int(xml_sous.get('Sous-imputation')))
            except (ObjectDoesNotExist, TypeError):
                pass
        element.save()
        log.log(time.clock(), 1)
    log.log("{} echeances".format(nb))

    log.log(u'{!s}'.format(time.clock()))
    log.log( u'fini')

if __name__ == "__main__":
    import_gsb("{}/fichier_test.gsb".format(os.path.dirname(os.path.abspath(__file__))),10)
