# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse

from ..models import (Compte, Ope, Tiers, Cat, Moyen, Echeance, Ib, Banque, Exercice, Rapp, Titre)

# from django.core.exceptions import ObjectDoesNotExist
# import decimal
# import datetime
from django.conf import settings  # @Reimport
#from django.shortcuts import render_to_response
#from django.template import RequestContext


from lxml import etree as et
# import logging
from .. import utils
# definitions des listes
liste_type_cat = Cat.typesdep
liste_type_moyen = Moyen.typesdep
liste_type_compte = Compte.typescpt


def _export(request):
# creation des id pour IB
#####generalites###
    xml_root = et.Element("Grisbi")
    xml_generalites = et.SubElement(xml_root, "Generalites")
    et.SubElement(xml_generalites, "Version_fichier").text = "0.5.0"
    et.SubElement(xml_generalites, "Version_grisbi").text = "0.5.9 for Windows (GTK>=2.6.9)"  # NOT IN BDD
    et.SubElement(xml_generalites, "Fichier_ouvert").text = "0"
    et.SubElement(xml_generalites, "Backup").text = "sauvegarde.gsb"  # NOT IN BDD
    et.SubElement(xml_generalites, "Titre").text = str(settings.TITRE)  # NOT IN BDD
    et.SubElement(xml_generalites, "Adresse_commune").text = ''  # NOT IN BDD
    et.SubElement(xml_generalites, "Adresse_secondaire").text = ''  # NOT IN BDD
    et.SubElement(xml_generalites, "Utilise_exercices").text = utils.booltostr(settings.UTILISE_EXERCICES)
    et.SubElement(xml_generalites, "Utilise_IB").text = utils.booltostr(settings.UTILISE_IB)
    et.SubElement(xml_generalites, "Utilise_PC").text = utils.booltostr(settings.UTILISE_PC)
    et.SubElement(xml_generalites, "Utilise_info_BG").text = "0"  # NOT IN BDD
    et.SubElement(xml_generalites, "Numero_devise_totaux_tiers").text = "1"
    et.SubElement(xml_generalites, "Numero_devise_totaux_categ").text = "1"
    et.SubElement(xml_generalites, "Numero_devise_totaux_ib").text = "1"
    et.SubElement(xml_generalites, "Type_affichage_des_echeances").text = "3"  # NOT IN BDD
    et.SubElement(xml_generalites, "Affichage_echeances_perso_nb_libre").text = "0"  # NOT IN BDD
    et.SubElement(xml_generalites, "Type_affichage_perso_echeances").text = "0"  # NOT IN BDD
    et.SubElement(xml_generalites, "Numero_derniere_operation").text = utils.maxtostr(Ope.objects)
    et.SubElement(xml_generalites, "Echelle_date_import").text = "2"  # NOT IN BDD
    et.SubElement(xml_generalites, "Utilise_logo").text = "1"  # NOT IN BDD
    et.SubElement(xml_generalites, "Chemin_logo").text = "g:/Program Files/Grisbi/pixmaps/grisbi-logo.png"  # NOT IN BDD
    et.SubElement(xml_generalites, "Affichage_opes").text = "18-1-3-13-5-6-7-0-0-12-0-9-8-0-0-0-15-0-0-0-0-0-0-0-0-0-0-0"  # NOT IN BDD
    et.SubElement(xml_generalites, "Rapport_largeur_col").text = "7-9-33-2-10-9-7"  # NOT IN BDD
    et.SubElement(xml_generalites, "Ligne_aff_une_ligne").text = "0"  # NOT IN BDD
    et.SubElement(xml_generalites, "Lignes_aff_deux_lignes").text = "0-1"  # NOT IN BDD
    et.SubElement(xml_generalites, "Lignes_aff_trois_lignes").text = "0-1-2"  # NOT IN BDD

    # requetes pour les comptes
    ordre_du_tri_des_moyens = '/'.join([str(o.id) for o in Moyen.objects.order_by('id')])
    moyens = Moyen.objects.all().order_by('id')

    #####comptes###
    xml_comptes = et.SubElement(xml_root, "Comptes")
    xml_generalites = et.SubElement(xml_comptes, "Generalites")
    et.SubElement(xml_generalites, "Ordre_des_comptes").text = '-'.join(
        ["%s" % i for i in Compte.objects.all().values_list('id', flat=True)])
    et.SubElement(xml_generalites, "Compte_courant").text = str(0)  # NOT IN BDD
    nb_compte = 0
    # --boucle des comptes
    for cpt in Compte.objects.all().order_by('id'):
        nb_compte += 1
        xml_compte = et.SubElement(xml_comptes, "Compte")
        xml_detail = et.SubElement(xml_compte, "Details")
        et.SubElement(xml_detail, "Nom").text = cpt.nom
        et.SubElement(xml_detail, "Id_compte")  # NOT IN BDD
        et.SubElement(xml_detail, "No_de_compte").text = str(cpt.id)
        et.SubElement(xml_detail, "Titulaire").text = ''  # NOT IN BDD
        et.SubElement(xml_detail, "Type_de_compte").text = utils.typetostr(liste_type_compte, cpt.type)
        et.SubElement(xml_detail, "Nb_operations").text = str(Ope.objects.filter(compte=cpt.id).count())
        et.SubElement(xml_detail, "Devise").text = "1"
        if cpt.banque is None:
            et.SubElement(xml_detail, "Banque").text = str(0)
        else:
            et.SubElement(xml_detail, "Banque").text = str(cpt.banque_id)
        et.SubElement(xml_detail, "Guichet").text = str(cpt.guichet)
        numero_compte = cpt.num_compte
        et.SubElement(xml_detail, "No_compte_banque").text = str(numero_compte)
        if cpt.cle_compte == 0 or cpt.cle_compte is None:
            cle_du_compte = ""
        else:
            cle_du_compte = cpt.cle_compte
        et.SubElement(xml_detail, "Cle_du_compte").text = str(cle_du_compte)
        et.SubElement(xml_detail, "Solde_initial").text = utils.floattostr(cpt.solde_init)
        et.SubElement(xml_detail, "Solde_mini_voulu").text = utils.floattostr(cpt.solde_mini_voulu)
        et.SubElement(xml_detail, "Solde_mini_autorise").text = utils.floattostr(cpt.solde_mini_autorise)
        et.SubElement(xml_detail, "Solde_courant").text = utils.floattostr(cpt.solde())
        try:
            rapp = Ope.objects.filter(compte=cpt, rapp__isnull=False).select_related('rapp').latest().rapp
            et.SubElement(xml_detail, "Date_dernier_releve").text = utils.datetostr(rapp.date, gsb=True)
            et.SubElement(xml_detail, "Solde_dernier_releve").text = utils.floattostr(rapp.solde)
            et.SubElement(xml_detail, "Dernier_no_de_rapprochement").text = str(rapp.id)
        except Ope.DoesNotExist:
            et.SubElement(xml_detail, "Date_dernier_releve")
            et.SubElement(xml_detail, "Solde_dernier_releve").text = utils.floattostr(0)
            et.SubElement(xml_detail, "Dernier_no_de_rapprochement").text = str(0)
        et.SubElement(xml_detail, "Compte_cloture").text = utils.booltostr(
            not cpt.ouvert)  # attention, on gere les comptes ouverts et non les comptes clotures
        et.SubElement(xml_detail, "Affichage_r").text = "1"  # NOT IN BDD
        et.SubElement(xml_detail, "Nb_lignes_ope").text = "3"  # NOT IN BDD
        et.SubElement(xml_detail, "Commentaires").text = cpt.notes
        et.SubElement(xml_detail, "Adresse_du_titulaire").text = ''  # NOT IN BDD
        et.SubElement(xml_detail, "Nombre_de_types").text = str(Moyen.objects.count())
        if cpt.moyen_debit_defaut is not None:
            et.SubElement(xml_detail, "Type_defaut_debit").text = str(cpt.moyen_debit_defaut_id)
        else:
            et.SubElement(xml_detail, "Type_defaut_debit").text = '0'
        if cpt.moyen_credit_defaut is not None:
            et.SubElement(xml_detail, "Type_defaut_credit").text = str(cpt.moyen_credit_defaut_id)
        else:
            et.SubElement(xml_detail, "Type_defaut_credit").text = '0'
        et.SubElement(xml_detail, "Tri_par_type").text = '0'  # NOT IN BDD
        et.SubElement(xml_detail, "Neutres_inclus").text = '0'  # NOT IN BDD
        et.SubElement(xml_detail, "Ordre_du_tri").text = ordre_du_tri_des_moyens

        # types ou moyens
        xml_types = et.SubElement(xml_compte, "Detail_de_Types")
        for m_pai in moyens:
            xml_element = et.SubElement(xml_types, "Type")
            xml_element.set('No', str(m_pai.id))
            xml_element.set('Nom', m_pai.nom)
            xml_element.set('Signe', utils.typetostr(liste_type_moyen, m_pai.type))
            xml_element.set('Affiche_entree', "0")  # NOT IN BDD
            xml_element.set('Numerotation_auto', "0")  # NOT IN BDD
            xml_element.set('No_en_cours', "0")  # NOT IN BDD
        xml_opes = et.SubElement(xml_compte, "Detail_des_operations")

        # #operations
        for ope in Ope.objects.filter(compte=cpt.id).order_by('id').select_related('compte', 'jumelle'):
            # raise
            xml_element = et.SubElement(xml_opes, 'Operation')
            # numero de l'operation
            xml_element.set('No', str(ope.id))
            xml_element.set('Id', '')  # NOT IN BDD
            # date de l'operation
            xml_element.set('D', utils.datetostr(ope.date, gsb=True))
            # date de valeur
            if ope.date_val is None:
                xml_element.set('Db', "0/0/0")
            else:
                xml_element.set('Db', utils.datetostr(ope.date_val, gsb=True))
            xml_element.set('M', utils.floattostr(ope.montant))
            xml_element.set('De', str(1))
            xml_element.set('Rdc', '0')  # NOT IN BDD
            xml_element.set('Tc', utils.floattostr(0))  # comme pas de devise pas besoin
            xml_element.set('Fc', utils.floattostr(0))  # NOT IN BDD mais inutile selon moi
            if ope.tiers is not None:
                xml_element.set('T', str(ope.tiers_id))
            else:
                xml_element.set('T', str(0))
            if ope.cat is not None:
                xml_element.set('C', str(ope.cat_id))
            else:
                xml_element.set('C', str(0))
            xml_element.set('Sc', str(0))
            xml_element.set('Ov', utils.booltostr(ope.filles_set.all()))
            xml_element.set('N', ope.notes)
            xml_element.set('Ty', str(ope.moyen_id))
            xml_element.set('Ct', str(ope.num_cheque))
            if ope.pointe:
                xml_element.set('P', str(1))
            else:
                if ope.rapp is None:
                    xml_element.set('P', str(0))
                else:
                    xml_element.set('P', str(2))
            xml_element.set('A', utils.booltostr(ope.automatique))
            if ope.rapp is None:
                xml_element.set('R', str(0))
            else:
                xml_element.set('R', str(ope.rapp_id))
            if ope.exercice is None:
                xml_element.set('E', str(0))
            else:
                xml_element.set('E', str(ope.exercice_id))
            if ope.ib is not None:
                xml_element.set('I', str(ope.ib_id))
            else:
                xml_element.set('I', str(0))
            xml_element.set('Si', str(0))
            xml_element.set('Pc', str(ope.piece_comptable))
            xml_element.set('Ibg', "")  # NOT IN BDD
            if ope.jumelle is None:
                num_jumelle = "0"
                num_cpt_jumelle = "0"
            else:
                num_cpt_jumelle = str(ope.jumelle.compte_id)
                num_jumelle = str(ope.jumelle.id)
            xml_element.set('Ro', str(num_jumelle))
            xml_element.set('Rc', str(num_cpt_jumelle))
            if ope.mere is None:
                xml_element.set('Va', "0")
            else:
                xml_element.set('Va', str(ope.mere_id))
                # raison pour lesquelles il y a des attributs non modifiables
                # Fc: si besoin dans ce cas, ce sera une operation ventilée avec frais de change comme categorie et l'autre categorie
        ###Echeances###
    xml_echeances_root = et.SubElement(xml_root, "Echeances")
    xml_generalite = et.SubElement(xml_echeances_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_echeances").text = str(Echeance.objects.count())
    et.SubElement(xml_generalite, "No_derniere_echeance").text = utils.maxtostr(Echeance.objects)
    xml_echeances = et.SubElement(xml_echeances_root, 'Detail_des_echeances')
    for ech in Echeance.objects.all().order_by('id'):
        xml_element = et.SubElement(xml_echeances, 'Echeance', No=str(ech.id))
        xml_element.set('Date', utils.datetostr(ech.date, gsb=True))
        xml_element.set('Compte', str(ech.compte_id))
        xml_element.set('Montant', utils.floattostr(ech.montant))
        xml_element.set('Devise', str(1))
        xml_element.set('Tiers', str(ech.tiers_id))
        xml_element.set('Categorie', str(ech.cat_id))
        xml_element.set('Sous-categorie', str(0))
        if ech.compte_virement is None:
            xml_element.set('Virement_compte', str(0))
        else:
            xml_element.set('Virement_compte', str(ech.compte_virement_id))
        xml_element.set('Type', str(ech.moyen_id))
        if ech.moyen_virement is None:
            xml_element.set('Type_contre_ope', "0")
        else:
            xml_element.set('Type_contre_ope', str(ech.moyen_virement_id))
        xml_element.set('Contenu_du_type', "")  # NOT IN BDD
        if ech.exercice is None:
            xml_element.set('Exercice', "0")
        else:
            xml_element.set('Exercice', str(ech.exercice_id))
        if ech.ib is None:
            xml_element.set('Imputation', str(0))
        else:
            xml_element.set('Imputation', str(ech.ib_id))
        xml_element.set('Sous-imputation', str(0))
        xml_element.set('Notes', ech.notes)
        xml_element.set('Automatique', utils.booltostr(False))  # not in bdd
        xml_element.set('Notes', str(ech.notes))
        if ech.periodicite is None or ech.periodicite == 'u':
            xml_element.set('Periodicite', str(0))
            xml_element.set('Intervalle_periodicite', '0')
        else:
            if ech.intervalle > 1:  # on cree periodicite perso
                xml_element.set('Intervalle_periodicite', str(ech.intervalle))
                xml_element.set('Periodicite', '4')  # periodicite perso
                if ech.periodicite == 'j':
                    xml_element.set('Intervalle_periodicite', str(ech.intervalle))
                    xml_element.set('Periodicite_personnalisee', '1')
                if ech.periodicite == 's':
                    xml_element.set('Intervalle_periodicite', str(ech.intervalle * 7))
                    xml_element.set('Periodicite_personnalisee', '1')
                if ech.periodicite == 'm':
                    xml_element.set('Intervalle_periodicite', str(ech.intervalle))
                    xml_element.set('Periodicite_personnalisee', '2')
                if ech.periodicite == 'a':
                    xml_element.set('Intervalle_periodicite', str(ech.intervalle))
                    xml_element.set('Periodicite_personnalisee', '3')
            else:
                xml_element.set('Intervalle_periodicite', '1')
                xml_element.set('Periodicite_personnalisee', '0')
                if ech.periodicite == 'j':
                    xml_element.set('Periodicite', str(ech.intervalle))
                if ech.periodicite == 's':  # les semaines n'existent pas
                    xml_element.set('Intervalle_periodicite', str(ech.intervalle * 7))
                    xml_element.set('Periodicite_personnalisee', '1')
                    xml_element.set('Periodicite', '4')
                if ech.periodicite == 'm':
                    xml_element.set('Periodicite', str(ech.intervalle))
                if ech.periodicite == 'a':
                    xml_element.set('Intervalle_periodicite', str(ech.intervalle))
        xml_element.set('Date_limite', utils.datetostr(ech.date_limite, defaut='', gsb=True))
        xml_element.set('Ech_ventilee', '0')
        xml_element.set('No_ech_associee', '0')

    ###Tiers###
    xml_tiers_root = et.SubElement(xml_root, "Tiers")
    xml_generalite = et.SubElement(xml_tiers_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_tiers").text = str(Tiers.objects.count())
    et.SubElement(xml_generalite, "No_dernier_tiers").text = utils.maxtostr(Tiers.objects)
    xml_detail = et.SubElement(xml_tiers_root, 'Detail_des_tiers')
    for tier in Tiers.objects.all().order_by('id'):
        xml_sub = et.SubElement(xml_detail, 'Tiers')
        xml_sub.set("No", str(tier.id))
        xml_sub.set("Nom", tier.nom)
        if tier.is_titre:  # #integration des donnees sur les titres afin de garder une consistence
            try:
                xml_sub.set("Informations", "%s@%s" % (tier.titre.isin, tier.titre.type))
            except Titre.DoesNotExist:
                xml_sub.set("Informations", "%s@%s" % ("00000", "XXX"))
        else:
            xml_sub.set("Informations", tier.notes)
        xml_sub.set("Liaison", "0")

    # #categories##
    xml_cat_root = et.SubElement(xml_root, "Categories")
    xml_generalite = et.SubElement(xml_cat_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_categories").text = str(Cat.objects.count())
    et.SubElement(xml_generalite, "No_derniere_categorie").text = utils.maxtostr(Cat.objects)
    xml_detail = et.SubElement(xml_cat_root, 'Detail_des_categories')

    # creation des id pour cat et sact
    for cat in Cat.objects.all().order_by('id'):
        # list_cats[cat_en_cours.id] = {'cat': {'id': cat_en_cours.id, 'nom': cat_en_cours.nom, 'type': cat_en_cours.type}, 'scat': None}
        xml_cate = et.SubElement(xml_detail, 'Categorie')
        xml_cate.set('No', str(cat.id))
        xml_cate.set('Nom', cat.nom)
        xml_cate.set('Type', utils.typetostr(liste_type_cat, cat.type))
        # on ne gere pas les sous categories
        xml_cate.set('No_derniere_sous_cagegorie', '0')

    # #imputation
    xml_ib_root = et.SubElement(xml_root, "Imputations")
    xml_generalite = et.SubElement(xml_ib_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_imputations").text = str(Ib.objects.count())
    et.SubElement(xml_generalite, "No_derniere_imputation").text = utils.maxtostr(Ib.objects)
    xml_detail = et.SubElement(xml_ib_root, 'Detail_des_imputations')

    for imp in Ib.objects.all().order_by('id'):
        xml_ibe = et.SubElement(xml_detail, 'Imputation')
        xml_ibe.set('No', str(imp.id))
        xml_ibe.set('Nom', imp.nom)
        xml_ibe.set('Type', utils.typetostr(liste_type_cat, imp.type))
        xml_ibe.set('No_derniere_sous_imputation', str(0))

    # #devises##
    xml_devises = et.SubElement(xml_root, "Devises")
    xml_generalite = et.SubElement(xml_devises, "Generalites")
    et.SubElement(xml_generalite, "Nb_devises").text = "1"
    et.SubElement(xml_generalite, "No_derniere_devise").text = '1'
    xml_detail = et.SubElement(xml_devises, 'Detail_des_devises')
    xml_sub = et.SubElement(xml_detail, 'Devise')
    xml_sub.set('No', str(1))
    xml_sub.set('Nom', settings.DEVISE_GENERALE)
    xml_sub.set('Code', settings.DEVISE_GENERALE)
    xml_sub.set('IsoCode', settings.DEVISE_GENERALE)
    xml_sub.set('Passage_euro', "0")  # NOT IN BDD
    xml_sub.set('Date_dernier_change', "")
    xml_sub.set('Rapport_entre_devises', "0")  # NOT IN BDD
    xml_sub.set('Devise_en_rapport', '0')  # NOT IN BDD
    xml_sub.set('Change', utils.floattostr(0))

    # raison pour lesquelles il y a des attributs non modifiables
    # isocode est par construction egale à code
    # Passage_euro: plus besoin
    # Rapport_entre_devises plus besoin

    # #BANQUES##
    xml_banques = et.SubElement(xml_root, "Banques")
    xml_generalite = et.SubElement(xml_banques, "Generalites")
    et.SubElement(xml_generalite, "Nb_banques").text = str(Banque.objects.count())
    et.SubElement(xml_generalite, "No_derniere_banque").text = utils.maxtostr(Banque.objects)
    xml_detail = et.SubElement(xml_banques, 'Detail_des_banques')
    for bq in Banque.objects.all().order_by('id'):
        if bq is not None:
            xml_sub = et.SubElement(xml_detail, 'Banque')
            xml_sub.set('No', str(bq.id))
            xml_sub.set('Nom', bq.nom)
            xml_sub.set('Code', str(bq.cib))
            xml_sub.set('Adresse', "")
            xml_sub.set('Tel', "")
            xml_sub.set('Mail', "")
            xml_sub.set('Web', "")
            xml_sub.set('Nom_correspondant', "")  # NOT IN BDD
            xml_sub.set('Fax_correspondant', "")  # NOT IN BDD
            xml_sub.set('Tel_correspondant', "")  # NOT IN BDD
            xml_sub.set('Mail_correspondant', "")  # NOT IN BDD
            xml_sub.set('Remarques', bq.notes)
            # raison pour lesquelles il y a des attributs non modifiables
            # Adresse pas ds BDD
            # Tel,mail, web, Nom_correspondant: pas ds bdd
            # Fax_correspondant: pas ds bdd
            # Tel_correspondant: pas ds bdd
            # Mail_correspondant: pas ds bdd

    # exercices
    xml_exo = et.SubElement(xml_root, "Exercices")
    xml_generalite = et.SubElement(xml_exo, "Generalites")
    et.SubElement(xml_generalite, "Nb_exercices").text = str(Exercice.objects.count())
    et.SubElement(xml_generalite, "No_dernier_exercice").text = utils.maxtostr(Exercice.objects)
    xml_detail = et.SubElement(xml_exo, 'Detail_des_exercices')
    for exo in Exercice.objects.all().order_by('id'):
        if exo is not None:
            xml_sub = et.SubElement(xml_detail, 'Exercice')
            xml_sub.set('No', str(exo.id))
            xml_sub.set('Nom', exo.nom)
            xml_sub.set('Date_debut', utils.datetostr(exo.date_debut, gsb=True))
            xml_sub.set('Date_fin', utils.datetostr(exo.date_fin, gsb=True))
            xml_sub.set('Affiche', "1")

    # #rapprochement##
    xml_rapp = et.SubElement(xml_root, "Rapprochements")
    xml_detail = et.SubElement(xml_rapp, 'Detail_des_rapprochements')
    for rappro in Rapp.objects.all().order_by('id'):
        if rappro is not None:
            xml_sub = et.SubElement(xml_detail, 'Rapprochement')
            xml_sub.set('No', str(rappro.id))
            xml_sub.set('Nom', rappro.nom)
    xml_etats = et.SubElement(xml_root, "Etats")
    xml_generalite = et.SubElement(xml_etats, "Generalites")
    et.SubElement(xml_generalite, "No_dernier_etat").text = "0"
    et.SubElement(xml_etats, 'Detail_des_etats')

    # final
    xml = et.tostring(xml_root, method="xml", xml_declaration=True, pretty_print=True)
    avant = ['&#232', '&#233', '&#234', '&#244']
    apres = ['&#xE8', '&#xE9', '&#xEA', '&#xF4']
    for car in avant:
        xml = xml.replace(car, apres[avant.index(car)])
    xml = xml.replace("xml version='1.0' encoding='ASCII'", 'xml version="1.0"')
    return xml


@permission_required('gsb_can_export')
def export(request):
    xml_django = _export(request)
    reponse = HttpResponse(xml_django, content_type="text/plain")
    # reponse = HttpResponse(xml_django, content_type="application/x-grisbi-gsb")
    reponse["Cache-Control"] = "no-cache, must-revalidate"
    reponse["Content-Disposition"] = "attachment; filename=%s.gsb" % settings.TITRE
    return reponse
