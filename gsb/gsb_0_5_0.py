# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import permission_required

if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os
    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    from mysite import settings
    setup_environ(settings)

from mysite.gsb.models import *
from django.http import HttpResponse
from django.db.models import Max
#from django.core.exceptions import ObjectDoesNotExist
#import decimal
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et
import logging
class Format:
    def date(s, defaut="0/0/0"):
        if s is None:
            return defaut
        else:
            isinstance(s, datetime.date)
            s = s.strftime('%d/%m/%Y')
            result = []
            tab = s.split("/")
            for partie in tab:#transform 01/01/2010 en 1/1/2010
                if partie[0] == '0':
                    partie = partie[1:]
                result.append(partie)
            return "/".join(result)

    date = staticmethod(date)

    def bool(s, defaut='0'):
        if s is None:
            return defaut
        else:
            if isinstance(s, bool):
                return str(int(s))
            else:
                return str(int(bool(s)))

    bool = staticmethod(bool)

    def float(s):
        s = "%10.7f" % s
        return s.replace('.', ',').strip()

    float = staticmethod(float)

    def type(liste, s, defaut='0'):
        liste = [str(b[0]) for b in liste]
        try:
            s = str(liste.index(s))
        except ValueError:##on en un ca par defaut
            s = defaut
        return s

    type = staticmethod(type)

    def max(object, defaut='0', champ='id'):
        q = object.aggregate(id=Max(champ))['id']
        if q is None:
            return defaut
        else:
            return str(q)

    max = staticmethod(max)


#definitions des listes
liste_type_cat = Cat.typesdep
liste_type_moyen = Moyen.typesdep
liste_type_compte = Compte.typescpt
liste_type_period = Echeance.typesperiod
liste_type_period_perso = Echeance.typesperiodperso

def _export():
    logger=logging.getLogger('gsb.export')
    #creation des id pour cat et sact
    list_cats={}
    nb_cat=0
    for cat_en_cours in Cat.objects.all().order_by('id'):
        try:
            cat_nom,scat_nom=cat_en_cours.nom.split(":")
            if scat_nom:
                list_cats[cat_en_cours.id]={'cat':{'id':cat_en_cours.id,'nom':cat_nom,'type':cat_en_cours.type},'scat':{'id':cat_en_cours.id,'nom':scat_nom}}
            else:
                list_cats[cat_en_cours.id]={'cat':{'id':cat_en_cours.id,'nom':cat_en_cours.nom,'type':cat_en_cours.type},'scat':None}
        except ValueError:
             list_cats[cat_en_cours.id]={'cat':{'id':cat_en_cours.id,'nom':cat_en_cours.nom,'type':cat_en_cours.type},'scat':None}
    #creation des id pour cat et sact
    list_ibs={}
    for ib_en_cours in Ib.objects.all().order_by('id'):
        try:
            ib_nom,sib_nom=ib_en_cours.nom.split(":")
            if sib_nom:
                list_ibs[ib_en_cours.id]={'ib':{'id':ib_en_cours.id,'nom':ib_nom,'type':ib_en_cours.type},'sib':{'id':ib_en_cours.id,'nom':sib_nom}}
            else:
                list_ibs[ib_en_cours.id]={'ib':{'id':ib_en_cours.id,'nom':ib_en_cours.nom,'type':ib_en_cours.type},'sib':None}
        except ValueError:
             list_ibs[ib_en_cours.id]={'ib':{'id':ib_en_cours.id,'nom':ib_en_cours.nom,'type':ib_en_cours.type},'sib':None}
    #####generalites###
    xml_root = et.Element("Grisbi")
    q = Generalite.objects.all()[0]
    xml_generalites = et.SubElement(xml_root, "Generalites")
    et.SubElement(xml_generalites, "Version_fichier").text = "0.5.0"
    et.SubElement(xml_generalites, "Version_grisbi").text = "0.5.9 for Windows (GTK>=2.6.9)"#NOT IN BDD
    et.SubElement(xml_generalites, "Fichier_ouvert").text = "0"
    et.SubElement(xml_generalites, "Backup").text = "sauvegarde.gsb"#NOT IN BDD
    et.SubElement(xml_generalites, "Titre").text = str(q.titre)#NOT IN BDD
    et.SubElement(xml_generalites, "Adresse_commune").text = ''#NOT IN BDD
    et.SubElement(xml_generalites, "Adresse_secondaire").text = ''#NOT IN BDD
    et.SubElement(xml_generalites, "Utilise_exercices").text = Format.bool(q.utilise_exercices)
    et.SubElement(xml_generalites, "Utilise_IB").text = Format.bool(q.utilise_ib)
    et.SubElement(xml_generalites, "Utilise_PC").text = Format.bool(q.utilise_pc)
    et.SubElement(xml_generalites, "Utilise_info_BG").text = "0"#NOT IN BDD
    et.SubElement(xml_generalites, "Numero_devise_totaux_tiers").text = str(q.dev_g().id)
    et.SubElement(xml_generalites, "Numero_devise_totaux_categ").text = str(q.dev_g().id)
    et.SubElement(xml_generalites, "Numero_devise_totaux_ib").text = str(q.dev_g().id)
    et.SubElement(xml_generalites, "Type_affichage_des_echeances").text = "3"#NOT IN BDD
    et.SubElement(xml_generalites, "Affichage_echeances_perso_nb_libre").text = "0"#NOT IN BDD
    et.SubElement(xml_generalites, "Type_affichage_perso_echeances").text = "0"#NOT IN BDD
    et.SubElement(xml_generalites, "Numero_derniere_operation").text = Format.max(Ope.objects)
    et.SubElement(xml_generalites, "Echelle_date_import").text = "2"#NOT IN BDD
    et.SubElement(xml_generalites, "Utilise_logo").text = "1"#NOT IN BDD
    et.SubElement(xml_generalites, "Chemin_logo").text = "g:/Program Files/Grisbi/pixmaps/grisbi-logo.png"#NOT IN BDD
    et.SubElement(xml_generalites,
                  "Affichage_opes").text = "18-1-3-13-5-6-7-0-0-12-0-9-8-0-0-0-15-0-0-0-0-0-0-0-0-0-0-0"#NOT IN BDD
    et.SubElement(xml_generalites, "Rapport_largeur_col").text = "7-9-33-2-10-9-7"#NOT IN BDD
    et.SubElement(xml_generalites, "Ligne_aff_une_ligne").text = "0"#NOT IN BDD
    et.SubElement(xml_generalites, "Lignes_aff_deux_lignes").text = "0-1"#NOT IN BDD
    et.SubElement(xml_generalites, "Lignes_aff_trois_lignes").text = "0-1-2"#NOT IN BDD

    #####comptes###
    xml_comptes = et.SubElement(xml_root, "Comptes")
    xml_generalites = et.SubElement(xml_comptes, "Generalites")
    et.SubElement(xml_generalites, "Ordre_des_comptes").text = '-'.join(["%s" % i for i in Compte.objects.all().values_list('id', flat=True)])
    et.SubElement(xml_generalites, "Compte_courant").text = str(0) #NOT IN BDD
    logger.debug("gen ok")
    variable = 0
    for co in Compte.objects.all().order_by('id'):
        logger.debug('compte %s'%co.id)
        variable += 1
        id = co.id
        xml_compte = et.SubElement(xml_comptes, "Compte")
        xml_detail = et.SubElement(xml_compte, "Details")
        et.SubElement(xml_detail, "Nom").text = str(co.nom)
        et.SubElement(xml_detail, "Id_compte")#NOT IN BDD
        et.SubElement(xml_detail, "No_de_compte").text = str(id)
        et.SubElement(xml_detail, "Titulaire").text = ''#NOT IN BDD
        et.SubElement(xml_detail, "Type_de_compte").text = Format.type(liste_type_compte, co.type)
        et.SubElement(xml_detail, "Nb_operations").text = str(Ope.objects.filter(compte=co.id).count())
        et.SubElement(xml_detail, "Devise").text = str(co.devise_id)
        if co.banque is None:
            et.SubElement(xml_detail, "Banque").text = str(0)
        else:
            et.SubElement(xml_detail, "Banque").text = str(co.banque.id)
        if co.guichet == '' or co.guichet is None:
            et.SubElement(xml_detail, "Guichet").text = str("")
        else:
            et.SubElement(xml_detail, "Guichet").text = str(co.guichet)
        if co.num_compte == '' or co.num_compte is None:
            numero_compte = ""
        else:
            numero_compte = co.num_compte
        et.SubElement(xml_detail, "No_compte_banque").text = str(numero_compte)
        if co.cle_compte == 0 or co.cle_compte is None:
            cle_du_compte = ""
        else:
            cle_du_compte = co.cle_compte
        et.SubElement(xml_detail, "Cle_du_compte").text = str(cle_du_compte)
        et.SubElement(xml_detail, "Solde_initial").text = Format.float(co.solde_init)
        et.SubElement(xml_detail, "Solde_mini_voulu").text = Format.float(co.solde_mini_voulu)
        et.SubElement(xml_detail, "Solde_mini_autorise").text = Format.float(co.solde_mini_autorise)
        et.SubElement(xml_detail, "Solde_courant").text = Format.float(co.solde())
        try:
            et.SubElement(xml_detail, "Date_dernier_releve").text = Format.date(Ope.objects.filter(compte=co,rapp__isnull=False).latest().rapp.date)
            et.SubElement(xml_detail, "Solde_dernier_releve").text = Format.float(Ope.objects.filter(compte=co,rapp__isnull=False).latest().rapp.solde())
            et.SubElement(xml_detail, "Dernier_no_de_rapprochement").text = str(Ope.objects.filter(compte=co,rapp__isnull=False).latest().rapp.id)
        except Ope.DoesNotExist:
            et.SubElement(xml_detail, "Date_dernier_releve")
            et.SubElement(xml_detail, "Solde_dernier_releve").text = Format.float(0)
            et.SubElement(xml_detail, "Dernier_no_de_rapprochement").text = str(0)
        et.SubElement(xml_detail, "Compte_cloture").text = not Format.bool(co.open)#attention, on gere les comptes ouverts et non les comptes clotures
        et.SubElement(xml_detail, "Affichage_r").text = "1" #NOT IN BDD
        et.SubElement(xml_detail, "Nb_lignes_ope").text = "3" #NOT IN BDD
        et.SubElement(xml_detail, "Commentaires").text = co.notes
        et.SubElement(xml_detail, "Adresse_du_titulaire").text = '' #NOT IN BDD
        et.SubElement(xml_detail, "Nombre_de_types").text = str(Moyen.objects.count())
        if co.moyen_debit_defaut is not None:
            et.SubElement(xml_detail, "Type_defaut_debit").text = str(co.moyen_debit_defaut.id)
        else:
            et.SubElement(xml_detail, "Type_defaut_debit").text = '0'
        if co.moyen_credit_defaut is not None:
            et.SubElement(xml_detail, "Type_defaut_credit").text = str(co.moyen_credit_defaut.id)
        else:
            et.SubElement(xml_detail, "Type_defaut_credit").text = '0'
        et.SubElement(xml_detail, "Tri_par_type").text = '0'#NOT IN BDD
        et.SubElement(xml_detail, "Neutres_inclus").text = '0'#NOT IN BDD
        et.SubElement(xml_detail, "Ordre_du_tri").text = '/'.join([str(o.id) for o in Moyen.objects.order_by('id')])
        ##types:
        xml_types = et.SubElement(xml_compte, "Detail_de_Types")
        for ty in Moyen.objects.all().order_by('id'):
            logger.debug('moyen %s'%ty.id)
            xml_element = et.SubElement(xml_types, "Type")
            xml_element.set('No', str(ty.id))
            xml_element.set('Nom', ty.nom)
            xml_element.set('Signe', Format.type(liste_type_moyen, ty.type))
            xml_element.set('Affiche_entree', "0")#NOT IN BDD
            xml_element.set('Numerotation_auto', "0")#NOT IN BDD
            xml_element.set('No_en_cours', "0")#NOT IN BDD
        xml_opes = et.SubElement(xml_compte, "Detail_des_operations")
        ##operations
        for ope in Ope.objects.filter(compte=co.id).order_by('id'):
            logger.debug('ope %s'%ope.id)
            xml_element = et.SubElement(xml_opes, 'Operation')
            #numero de l'operation
            xml_element.set('No', str(ope.id))
            xml_element.set('Id', '')#NOT IN BDD
            #date de l'operation
            xml_element.set('D', Format.date(ope.date))
            #date de valeur
            if ope.date_val is None:
                xml_element.set('Db', "0/0/0")
            else:
                xml_element.set('Db', Format.date(ope.date_val))
            xml_element.set('M', Format.float(ope.montant))
            xml_element.set('De', str(co.devise_id ))
            xml_element.set('Rdc','0') #NOT IN BDD
            if ope.jumelle:
                devise_jumelle=Ope.objects.get(id=ope.id).jumelle.compte.devise
                if co.devise != devise_jumelle and devise_jumelle != Generalite.dev_g():
                    xml_element.set('M', Format.float(ope.montant*devise_jumelle.cours_set.get(date=ope.date).valeur))
                    xml_element.set('De', str(devise_jumelle.id ))
                    xml_element.set('Rdc','1')
                    xml_element.set('Tc', Format.float(devise_jumelle.cours_set.get(date=ope.date).valeur))
                else:
                    xml_element.set('Tc', Format.float(0))
            else:
                xml_element.set('Tc', Format.float(0))
            xml_element.set('Fc', Format.float(0)) #NOT IN BDD mais inutile
            if ope.tiers:
                xml_element.set('T', str(ope.tiers.id ))
            else:
                xml_element.set('T', str(0 ))
            if ope.cat and ope.cat.id!=0:
                xml_element.set('C', str(list_cats[ope.cat.id]['cat']['id']))
                if list_cats[ope.cat.id]['scat']:
                    xml_element.set('Sc', str(list_cats[ope.cat.id]['scat']['id']))
                else:
                    xml_element.set('Sc', str(0))
            else:
                xml_element.set('C', str(0))
                xml_element.set('Sc', str(0))
            xml_element.set('Ov', Format.bool(ope.filles_set.all()))
            xml_element.set('N', ope.notes)
            if ope.moyen is None:
                xml_element.set('Ty', str(0))
            else:
                xml_element.set('Ty', str(ope.moyen.id))
            xml_element.set('Ct', str(ope.num_cheque))
            if ope.pointe:
                xml_element.set('P', str(1))
            else:
                if ope.rapp is None:
                    xml_element.set('P', str(0))
                else:
                    xml_element.set('P', str(2))
            xml_element.set('A', Format.bool(ope.automatique))
            if ope.rapp is None:
                xml_element.set('R', str(0))
            else:
                xml_element.set('R', str(ope.rapp.id ))
            if ope.exercice is None:
                xml_element.set('E', str(0))
            else:
                xml_element.set('E', str(ope.exercice.id ))
            if ope.ib and ope.ib.id:
                xml_element.set('I', str(list_ibs[ope.ib.id]['ib']['id']))
                if list_ibs[ope.ib.id]['sib']:
                    xml_element.set('Si', str(list_ibs[ope.ib.id]['sib']['id']))
                else:
                    xml_element.set('Si', str(0))
            else:
                xml_element.set('I', str(0))
                xml_element.set('Si', str(0))
            xml_element.set('Pc', str(ope.piece_comptable))#NOT IN BDD
            xml_element.set('Ibg', "")#NOT IN BDD
            if ope.jumelle is None:
                num_jumelle = "0"
                num_cpt_jumelle = "0"
            else:
                num_cpt_jumelle = str(ope.jumelle.compte.id )
                num_jumelle = str(ope.jumelle.id )
            xml_element.set('Ro', str(num_jumelle))
            xml_element.set('Rc', str(num_cpt_jumelle))
            if ope.mere is None:
                 xml_element.set('Va',"0")
            else:
                 xml_element.set('Va',str(ope.mere.id ))
            #raison pour lesquelles il y a des attributs non modifiables
            #Fc: si besoin dans ce cas, ce sera une operation ventilée avec frais de change comme categorie et l'autre categorie
###Echeances###

    xml_echeances_root = et.SubElement(xml_root, "Echeances")
    xml_generalite = et.SubElement(xml_echeances_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_echeances").text = str(Echeance.objects.count())
    et.SubElement(xml_generalite, "No_derniere_echeance").text = Format.max(Echeance.objects)
    xml_echeances = et.SubElement(xml_echeances_root, 'Detail_des_echeances')
    for ech in Echeance.objects.all().order_by('id'):
        xml_element = et.SubElement(xml_echeances, 'Echeance', No=str(ech.id ))
        xml_element.set('Date', Format.date(ech.date))
        xml_element.set('Compte', str(ech.compte.id ))
        xml_element.set('Montant', Format.float(ech.montant))
        xml_element.set('Devise', str(ech.devise_id ))
        if ech.tiers is None:
            xml_element.set('Tiers', "0")
        else:
            xml_element.set('Tiers', str(ech.tiers.id ))
        if ech.cat is None:
            xml_element.set('Categorie', str(0))
            xml_element.set('Sous-categorie', str(0))
        else:
            xml_element.set('Categorie', str(list_cats[ech.cat.id]['cat']['id']))
            if list_cats[ech.cat.id]['scat']:
                xml_element.set('Sous-categorie', str(list_cats[ech.cat.id]['scat']['id']))
            else:
                xml_element.set('Sous-categorie', str(0))
        if ech.compte_virement is None:
            xml_element.set('Virement_compte', "0")
        else:
            xml_element.set('Virement_compte', str(ech.compte_virement.id ))
        if ech.moyen is None:
            xml_element.set('Type', "0")
        else:
            xml_element.set('Type', str(ech.moyen.id ))
        if ech.moyen_virement is None:
            xml_element.set('Type_contre_ope', "0")
        else:
            xml_element.set('Type_contre_ope', str(ech.moyen_virement.id ))
        xml_element.set('Contenu_du_type', "")#NOT IN BDD
        if ech.exercice is None:
            xml_element.set('Exercice', "0")
        else:
            xml_element.set('Exercice', str(ech.exercice.id ))
        if ech.ib is None:
            xml_element.set('Imputation', str(0))
            xml_element.set('Sous-imputation', str(0))
        else:
            xml_element.set('Imputation', str(list_ibs[ech.ib.id]['ib']['id']))
            if list_ibs[ech.ib.id]['sib']:
                xml_element.set('Sous-imputation', str(list_ibs[ech.ib.id]['sib'][id]))
            else:
                xml_element.set('Sous-imputation', str(0))
        xml_element.set('Notes', ech.notes)
        xml_element.set('Automatique', Format.bool(ech.inscription_automatique))
        xml_element.set('Notes', str(ech.notes))
        if ech.periodicite is None:
            xml_element.set('Periodicite', str(0))
        else:
            xml_element.set('Periodicite', Format.type(liste_type_period, ech.periodicite))
        xml_element.set('Intervalle_periodicite', str(ech.intervalle))
        xml_element.set('Periodicite_personnalisee', str(Format.type(liste_type_period_perso, ech.periode_perso)))
        xml_element.set('Date_limite', Format.date(ech.date_limite, defaut=''))
        xml_element.set('Ech_ventilee', '0')
        xml_element.set('No_ech_associee', '0')
    ###Tiers###
    xml_tiers_root = et.SubElement(xml_root, "Tiers")
    xml_generalite = et.SubElement(xml_tiers_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_tiers").text = str(Tiers.objects.count())
    et.SubElement(xml_generalite, "No_dernier_tiers").text = Format.max(Tiers.objects)
    xml_detail = et.SubElement(xml_tiers_root, 'Detail_des_tiers')
    for tier in Tiers.objects.all().order_by('id'):
        xml_sub = et.SubElement(xml_detail, 'Tiers')
        xml_sub.set("No", str(tier.id ))
        xml_sub.set("Nom", tier.nom)
        if tier.is_titre:##integration des donnees sur les titres afin de garder une consistence
            xml_sub.set("Informations", "%s@%s" % (tier.titre_set.all().get().isin, tier.titre_set.all().get().type))
        else:
            xml_sub.set("Informations", tier.notes)
        xml_sub.set("Liaison", "0")
    ##categories##
    xml_cat_root = et.SubElement(xml_root, "Categories")
    xml_generalite = et.SubElement(xml_cat_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_categories").text = str(Cat.objects.count())
    et.SubElement(xml_generalite, "No_derniere_categorie").text = Format.max(Cat.objects)
    xml_detail = et.SubElement(xml_cat_root, 'Detail_des_categories')
    old_cat=''
    xml_cate = et.SubElement(xml_detail, 'Categorie')
    for c in list_cats.values():
        if old_cat != c['cat']['nom']:
            if old_cat == '':
                xml_cate.set('No', str(c['cat']['id']))
                xml_cate.set('Nom', c['cat']['nom'])
                xml_cate.set('Type', Format.type(liste_type_cat,c['cat']['type']))
            else:
                xml_cate.set('No_derniere_sous_cagegorie', str(c['cat']['id']-1))
                xml_cate = et.SubElement(xml_detail, 'Categorie')
                xml_cate.set('No', str(c['cat']['id']))
                xml_cate.set('Nom', unicode(c['cat']['nom']))
                xml_cate.set('Type', Format.type(liste_type_cat,c['cat']['type']))
            old_cat=c['cat']['nom']
        if c['scat']:
            xml_sub = et.SubElement(xml_cate, 'Sous-categorie')
            xml_sub.set('No', str(c['cat']['id']))
            xml_sub.set('Nom', unicode(c['scat']['nom']))
    xml_cate.set('No_derniere_sous_cagegorie', str(c['cat']['id']))
    ##imputation
    xml_ib_root = et.SubElement(xml_root, "Imputations")
    xml_generalite = et.SubElement(xml_ib_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_imputations").text = str(Ib.objects.count())
    et.SubElement(xml_generalite, "No_derniere_imputation").text = Format.max(Ib.objects)
    xml_detail = et.SubElement(xml_ib_root, 'Detail_des_imputations')
    old_ib=''
    xml_ibe = et.SubElement(xml_detail, 'Imputation')
    for c in list_ibs.values():
        if old_ib != c['ib']['nom']:# TODO mieux gerer les null
            if old_ib == '':
                xml_ibe.set('No', str(c['ib']['id']))
                xml_ibe.set('Nom', c['ib']['nom'])
                xml_ibe.set('Type', Format.type(liste_type_cat,c['ib']['type']))
            else:
                xml_ibe.set('No_derniere_sous_imputation', str(c['ib']['id']-1))
                xml_ibe = et.SubElement(xml_detail, 'Imputation')
                xml_ibe.set('No', str(c['ib']['id']))
                xml_ibe.set('Nom', unicode(c['ib']['nom']))
                xml_ibe.set('Type', Format.type(liste_type_cat,c['ib']['type']))
            old_ib=c['ib']['nom']
        if c['sib']:
            xml_sub = et.SubElement(xml_ibe, 'Sous-imputation')
            xml_sub.set('No', str(c['ib']['id']))
            xml_sub.set('Nom', unicode(c['sib']['nom']))
    ##devises##
    xml_devises = et.SubElement(xml_root, "Devises")
    xml_generalite = et.SubElement(xml_devises, "Generalites")
    et.SubElement(xml_generalite, "Nb_devises").text = str(Titre.objects.filter(type='DEV').count())
    et.SubElement(xml_generalite, "No_derniere_devise").text = Format.max(Titre.objects.filter(type='DEV'),champ = 'id')
    xml_detail = et.SubElement(xml_devises, 'Detail_des_devises')
    for c in Titre.objects.filter(type='DEV').order_by('id'):
        xml_sub = et.SubElement(xml_detail, 'Devise')
        xml_sub.set('No', str(c.id ))
        xml_sub.set('Nom', c.nom)
        xml_sub.set('Code', c.isin)
        xml_sub.set('IsoCode', c.isin)
        if c == Generalite.dev_g():
            xml_sub.set('Passage_euro', "0")#NOT IN BDD
            xml_sub.set('Date_dernier_change', "")
            xml_sub.set('Rapport_entre_devises', "0")#NOT IN BDD
            xml_sub.set('Devise_en_rapport', '0')#NOT IN BDD
            xml_sub.set('Change', Format.float(0))
        else:
            xml_sub.set('Passage_euro', "0")#NOT IN BDD
            xml_sub.set('Date_dernier_change', Format.date(c.last_cours().date))
            xml_sub.set('Rapport_entre_devises', "1")#NOT IN BDD
            xml_sub.set('Devise_en_rapport', '1')#NOT IN BDD
            xml_sub.set('Change', Format.float(c.last_cours().valeur))

        #raison pour lesquelles il y a des attributs non modifiables
        #isocode est par construction egale à code
        #Passage_euro: plus besoin
        #Rapport_entre_devises plus besoin
    ##BANQUES##
    xml_banques = et.SubElement(xml_root, "Banques")
    xml_generalite = et.SubElement(xml_banques, "Generalites")
    et.SubElement(xml_generalite, "Nb_banques").text = str(Banque.objects.count())
    et.SubElement(xml_generalite, "No_derniere_banque").text = Format.max(Banque.objects)
    xml_detail = et.SubElement(xml_banques, 'Detail_des_banques')
    for c in Banque.objects.all().order_by('id'):
        if c is not None:
            xml_sub = et.SubElement(xml_detail, 'Banque')
            xml_sub.set('No', str(c.id ))
            xml_sub.set('Nom', c.nom)
            xml_sub.set('Code', str(c.cib))
            xml_sub.set('Adresse', "")
            xml_sub.set('Tel', "")
            xml_sub.set('Mail', "")
            xml_sub.set('Web', "")
            xml_sub.set('Nom_correspondant', "")#NOT IN BDD
            xml_sub.set('Fax_correspondant', "")#NOT IN BDD
            xml_sub.set('Tel_correspondant', "")#NOT IN BDD
            xml_sub.set('Mail_correspondant', "")#NOT IN BDD
            xml_sub.set('Remarques', c.notes)
            #raison pour lesquelles il y a des attributs non modifiables
            #Adresse pas ds BDD
            #Tel,mail, web, Nom_correspondant: pas ds bdd
            #Fax_correspondant: pas ds bdd
            #Tel_correspondant: pas ds bdd
            #Mail_correspondant: pas ds bdd
    ##exercices##
    xml_exo = et.SubElement(xml_root, "Exercices")
    xml_generalite = et.SubElement(xml_exo, "Generalites")
    et.SubElement(xml_generalite, "Nb_exercices").text = str(Exercice.objects.count())
    et.SubElement(xml_generalite, "No_dernier_exercice").text = Format.max(Exercice.objects)
    xml_detail = et.SubElement(xml_exo, 'Detail_des_exercices')
    for c in Exercice.objects.all().order_by('id'):
        if c is not None:
            xml_sub = et.SubElement(xml_detail, 'Exercice')
            xml_sub.set('No', str(c.id ))
            xml_sub.set('Nom', c.nom)
            xml_sub.set('Date_debut', Format.date(c.date_debut))
            xml_sub.set('Date_fin', Format.date(c.date_fin))
            xml_sub.set('Affiche', "1")
            ##rapprochement##
    xml_rapp = et.SubElement(xml_root, "Rapprochements")
    xml_detail = et.SubElement(xml_rapp, 'Detail_des_rapprochements')
    for c in Rapp.objects.all().order_by('id'):
        if c is not None:
            xml_sub = et.SubElement(xml_detail, 'Rapprochement')
            xml_sub.set('No', str(c.id ))
            xml_sub.set('Nom', c.nom)
            #etatsTODO
    xml_etats = et.SubElement(xml_root, "Etats")
    xml_generalite = et.SubElement(xml_etats, "Generalites")
    et.SubElement(xml_generalite, "No_dernier_etat").text = "0"
    detail = et.SubElement(xml_etats, 'Detail_des_etats')
    #final
    xml = et.tostring(xml_root, method="xml", xml_declaration=True, pretty_print=True)
    avant = ['&#232', '&#233', '&#234', '&#244']
    apres = ['&#xE8', '&#xE9', '&#xEA', '&#xF4']
    for car in avant:
        xml = xml.replace(car, apres[avant.index(car)])
    xml=xml.replace("xml version='1.0' encoding='ASCII'",'xml version="1.0"')
    return xml

@permission_required('gsb_can_export')
def export(request):
    nb_compte=Compte.objects.count()
    if nb_compte:
        xml=_export()
        #h=HttpResponse(xml,mimetype="application/xml")
        h=HttpResponse(xml,mimetype="application/x-grisbi-gsb")
        h["Cache-Control"] = "no-cache, must-revalidate"
        h["Content-Disposition"] = "attachment; filename=%s"%settings.TITRE
        return h
    else:
            return render_to_response('generic.django.html',
                {
                    'titre':'import gsb',
                    'resultats':({'texte':u"attention, il n'y a pas de comptes donc pas de possibilité d'export."},)
                },
                context_instance=RequestContext(request)
            )

if __name__ == "__main__":
    xml=_export()
    fichier=open("%s/test_files/test.gsb"%(os.path.dirname(os.path.abspath(__file__))),"w")
    fichier.write(xml)
    fichier.close()
