# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import permission_required

if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os
    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    from mysite import settings
    setup_environ(settings)

from mysite.gsb.models import Tiers, Titre, Cat, Ope, Banque, Ib, Exercice, Rapp, Moyen, Echeance, Generalite, Compte, Compte_titre, Histo_ope_titres, Virement, Titres_detenus, Cours
# 
from django.http import HttpResponse

#from django.core.exceptions import ObjectDoesNotExist
#import decimal
from django.conf import settings #@Reimport
from django.shortcuts import render_to_response
from django.template import RequestContext
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et
import logging
import mysite.gsb.utils
def _export():
    '''tout la plomberie'''
    dev = settings.UTIDEV
    fmt = mysite.gsb.utils.Format()
    logger = logging.getLogger('gsb.export')
    #####generalites###
    xml_root = et.Element("Grisbi")
    gene = Generalite.objects.all()[0]
    xml_generalites = et.SubElement(xml_root, "Generalites")
    et.SubElement(xml_generalites, "Version_fichier").text = "FSB_0_1"
    et.SubElement(xml_generalites, "Fichier_ouvert").text = "0"
    et.SubElement(xml_generalites, "Titre").text = str(gene.titre)
    et.SubElement(xml_generalites, "Utilise_exercices").text = fmt.bool(gene.utilise_exercices)
    et.SubElement(xml_generalites, "Utilise_IB").text = fmt.bool(gene.utilise_ib)
    et.SubElement(xml_generalites, "Utilise_PC").text = fmt.bool(gene.utilise_pc)
    if dev:
        et.SubElement(xml_generalites, "utilise_devise").text = fmt.bool(True)
        et.SubElement(xml_generalites, "Numero_devise_totaux").text = str(gene.dev_g().id)
    else:
        et.SubElement(xml_generalites, "utilise_dev").text = fmt.bool(False)
        et.SubElement(xml_generalites, "Numero_devise_totaux").text = "1"
    et.SubElement(xml_generalites, "Numero_derniere_operation").text = fmt.max(Ope.objects)
    et.SubElement(xml_generalites, 'Affiche_operation_clos').text = fmt.bool(gene.affiche_clot)
    #####comptes### (sans les operations)
    xml_comptes = et.SubElement(xml_root, "Comptes")
    xml_generalites = et.SubElement(xml_comptes, "Generalites")
    et.SubElement(xml_generalites, "Ordre_des_comptes").text = '-'.join(["%s" % i for i in Compte.objects.all().values_list('id', flat = True)])
    logger.debug("gen ok")
    for cpt in Compte.objects.all().order_by('id'):
        logger.debug('compte %s' % cpt.id)
        xml_compte = et.SubElement(xml_comptes, "Compte")
        xml_detail = et.SubElement(xml_compte, "Details")
        et.SubElement(xml_detail, "Nom").text = str(cpt.nom)
        et.SubElement(xml_detail, "No_de_compte").text = str(cpt.id)
        et.SubElement(xml_detail, "Type_de_compte").text = str(cpt.type)
        et.SubElement(xml_detail, "Nb_operations").text = str(Ope.objects.filter(compte = cpt.id).count())
        if dev:
            et.SubElement(xml_detail, "Devise").text = str(cpt.devise_id)
        else:
            et.SubElement(xml_detail, "Devise").text = str(1)
        et.SubElement(xml_detail, "Banque").text = str(fmt.str(cpt.banque))
        if cpt.guichet == '' or cpt.guichet is None:
            et.SubElement(xml_detail, "Guichet").text = str("")
        else:
            et.SubElement(xml_detail, "Guichet").text = str(cpt.guichet)
        if cpt.num_compte == '' or cpt.num_compte is None:
            numero_compte = ""
        else:
            numero_compte = cpt.num_compte
        et.SubElement(xml_detail, "No_compte_banque").text = str(numero_compte)
        if cpt.cle_compte == 0 or cpt.cle_compte is None:
            cle_du_compte = ""
        else:
            cle_du_compte = cpt.cle_compte
        et.SubElement(xml_detail, "Cle_du_compte").text = str(cle_du_compte)
        et.SubElement(xml_detail, "Solde_initial").text = fmt.float(cpt.solde_init)
        et.SubElement(xml_detail, "Solde_mini_voulu").text = fmt.float(cpt.solde_mini_voulu)
        et.SubElement(xml_detail, "Solde_mini_autorise").text = fmt.float(cpt.solde_mini_autorise)
        et.SubElement(xml_detail, "Solde_courant").text = fmt.float(cpt.solde())
        try:
            et.SubElement(xml_detail, "Date_dernier_releve").text = fmt.date(Ope.objects.filter(compte = cpt, rapp__isnull = False).latest().rapp.date)
            et.SubElement(xml_detail, "Solde_dernier_releve").text = fmt.float(Ope.objects.filter(compte = cpt, rapp__isnull = False).latest().rapp.solde())
            et.SubElement(xml_detail, "Dernier_no_de_rapprochement").text = str(Ope.objects.filter(compte = cpt, rapp__isnull = False).latest().rapp.id)
        except Ope.DoesNotExist:
            et.SubElement(xml_detail, "Date_dernier_releve")
            et.SubElement(xml_detail, "Solde_dernier_releve").text = fmt.float(0)
            et.SubElement(xml_detail, "Dernier_no_de_rapprochement").text = str(0)
        et.SubElement(xml_detail, "Compte_cloture").text = not fmt.bool(cpt.open)#attention, on gere les comptes ouverts et non les comptes clotures
        et.SubElement(xml_detail, "Commentaires").text = cpt.notes
        et.SubElement(xml_detail, "Nombre_de_types").text = str(Moyen.objects.count())
        et.SubElement(xml_detail, "Type_defaut_debit").text = fmt.str(cpt.moyen_debit_defaut)
        et.SubElement(xml_detail, "Type_defaut_credit").text = fmt.str(cpt.moyen_credit_defaut)
    ##types##
    xml_types = et.SubElement(xml_root, "Detail_de_Types")
    for mdp in Moyen.objects.all().order_by('id'):
        logger.debug('moyen %s' % mdp.id)
        xml_element = et.SubElement(xml_types, "Type")
        xml_element.set('No', str(mdp.id))
        xml_element.set('Nom', mdp.nom)
        xml_element.set('Signe', str(mdp.type))
        xml_element.set('Affiche_entree', "0")#NOT IN BDD mais TODO affiche entree
        xml_element.set('Numerotation_auto', "0")#NOT IN BDD mais TODO num auto
        xml_element.set('No_en_cours', "0")#NOT IN BDD mais TODO num en cour
    ##operations
    xml_opes = et.SubElement(xml_root, "Detail_des_operations")
    for ope in Ope.objects.all().order_by('id'):
        logger.debug('ope %s' % ope.id)
        xml_element = et.SubElement(xml_opes, 'Operation')
        #numero de l'operation
        xml_element.set('No', str(ope.id))
        #compte
        xml_element.set('Compte', str(ope.compte_id))
        #date de l'operation
        xml_element.set('D', fmt.date(ope.date))
        #date de valeur
        if ope.date_val is None:
            xml_element.set('Db', "0/0/0")
        else:
            xml_element.set('Db', fmt.date(ope.date_val))
        xml_element.set('M', fmt.float(ope.montant))
        if ope.jumelle:
            if settings.UTIDEV:
                devise_jumelle = Ope.objects.get(id = ope.id).jumelle.compte.devise
                if ope.compte.devise != devise_jumelle and devise_jumelle != Generalite.dev_g():
                    xml_element.set('M', fmt.float(ope.montant * devise_jumelle.cours_set.get(date = ope.date).valeur))
                    xml_element.set('Dev_jumelle', str(devise_jumelle.id))
                    xml_element.set('Tc', fmt.float(devise_jumelle.cours_set.get(date = ope.date).valeur))
                else:
                    xml_element.set('Tc', fmt.float(0))
                    xml_element.set('Dev_jumelle', str(devise_jumelle))
            else:
                xml_element.set('Tc', fmt.float(0))
                xml_element.set('Dev_jumelle', str(1))
        if ope.tiers:
            xml_element.set('T', str(ope.tiers.id))
        else:
            xml_element.set('T', str(0))
        if ope.cat:
            xml_element.set('C', str(ope.cat.id))
        else:
            xml_element.set('C', str(0))
        xml_element.set('Ov', fmt.bool(ope.filles_set.all()))
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
        xml_element.set('A', fmt.bool(ope.automatique))
        if ope.rapp is None:
            xml_element.set('R', str(0))
        else:
            xml_element.set('R', str(ope.rapp.id))
        if ope.exercice is None:
            xml_element.set('E', str(0))
        else:
            xml_element.set('E', str(ope.exercice.id))
        if ope.cat:
            xml_element.set('Ib', str(ope.cat.id))
        else:
            xml_element.set('Ib', str(0))
        xml_element.set('Pc', str(ope.piece_comptable))
        if ope.jumelle is None:
            num_jumelle = "0"
            num_cpt_jumelle = "0"
        else:
            num_cpt_jumelle = str(ope.jumelle.compte.id)
            num_jumelle = str(ope.jumelle.id)
        xml_element.set('Ro', str(num_jumelle))
        xml_element.set('Rc', str(num_cpt_jumelle))
        if ope.mere is None:
            xml_element.set('Va', "0")
        else:
            xml_element.set('Va', str(ope.mere.id))
        #raison pour lesquelles il y a des attributs non modifiables
        #Fc: si besoin dans ce cas, ce sera une operation ventilée avec frais de change comme categorie et l'autre categorie
###Echeances###

    xml_echeances_root = et.SubElement(xml_root, "Echeances")
    xml_generalite = et.SubElement(xml_echeances_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_echeances").text = str(Echeance.objects.count())
    et.SubElement(xml_generalite, "No_derniere_echeance").text = fmt.max(Echeance.objects)
    xml_echeances = et.SubElement(xml_echeances_root, 'Detail_des_echeances')
    for ech in Echeance.objects.all().order_by('id'):
        xml_element = et.SubElement(xml_echeances, 'Echeance', No = str(ech.id))
        xml_element.set('Date', fmt.date(ech.date))
        xml_element.set('Compte', str(ech.compte.id))
        xml_element.set('Montant', fmt.float(ech.montant))
        xml_element.set('Devise', str(ech.devise_id))
        if ech.tiers is None:
            xml_element.set('Tiers', "0")
        else:
            xml_element.set('Tiers', str(ech.tiers.id))
        if ech.cat is None:
            xml_element.set('Categorie', str(0))
        else:
            xml_element.set('Categorie', str(ech.cat.id))
        if ech.compte_virement is None:
            xml_element.set('Virement_compte', "0")
        else:
            xml_element.set('Virement_compte', str(ech.compte_virement.id))
        if ech.moyen is None:
            xml_element.set('Type', "0")
        else:
            xml_element.set('Type', str(ech.moyen.id))
        if ech.moyen_virement is None:
            xml_element.set('Type_contre_ope', "0")
        else:
            xml_element.set('Type_contre_ope', str(ech.moyen_virement.id))
        xml_element.set('Contenu_du_type', "")#NOT IN BDD
        if ech.exercice is None:
            xml_element.set('Exercice', "0")
        else:
            xml_element.set('Exercice', str(ech.exercice.id))
        if ech.ib is None:
            xml_element.set('Imputation', str(0))
        else:
            xml_element.set('Imputation', str(ech.ib.id))
        xml_element.set('Notes', ech.notes)
        xml_element.set('Automatique', fmt.bool(ech.inscription_automatique))
        xml_element.set('Notes', str(ech.notes))
        if ech.periodicite is None:
            xml_element.set('Periodicite', str(0))
        else:
            xml_element.set('Periodicite',str(ech.periodicite))
        xml_element.set('Intervalle_periodicite', str(ech.intervalle))
        xml_element.set('Periodicite_personnalisee', str(ech.periode_perso))
        xml_element.set('Date_limite', fmt.date(ech.date_limite, defaut = ''))
        xml_element.set('Ech_ventilee', '0')
        xml_element.set('No_ech_associee', '0')
    ###Tiers###
    xml_tiers_root = et.SubElement(xml_root, "Tiers")
    xml_generalite = et.SubElement(xml_tiers_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_tiers").text = str(Tiers.objects.count())
    et.SubElement(xml_generalite, "No_dernier_tiers").text = fmt.max(Tiers.objects)
    xml_detail = et.SubElement(xml_tiers_root, 'Detail_des_tiers')
    for tier in Tiers.objects.all().order_by('id'):
        xml_sub = et.SubElement(xml_detail, 'Tiers')
        xml_sub.set("No", str(tier.id))
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
    et.SubElement(xml_generalite, "No_derniere_categorie").text = fmt.max(Cat.objects)
    xml_detail = et.SubElement(xml_cat_root, 'Detail_des_categories')
    for cat in Cat.objects.all():
        xml_cate = et.SubElement(xml_detail, 'Categorie')
        xml_cate.set('No', str(cat.id))
        xml_cate.set('Nom', cat.nom)
        xml_cate.set('Type', cat.type)
    ##imputation
    xml_ib_root = et.SubElement(xml_root, "Imputations")
    xml_generalite = et.SubElement(xml_ib_root, "Generalites")
    et.SubElement(xml_generalite, "Nb_imputations").text = str(Ib.objects.count())
    et.SubElement(xml_generalite, "No_derniere_imputation").text = fmt.max(Ib.objects)
    xml_detail = et.SubElement(xml_ib_root, 'Detail_des_imputations')
    for imp in Ib.objects.all():
        xml_cate = et.SubElement(xml_detail, 'Imputation')
        xml_cate.set('No', str(imp.id))
        xml_cate.set('Nom', imp.nom)
        xml_cate.set('Type', imp.type)
    ##devises##
    xml_devises = et.SubElement(xml_root, "Devises")
    xml_generalite = et.SubElement(xml_devises, "Generalites")
    if settings.UTIDEV:
        et.SubElement(xml_generalite, "Nb_devises").text = str(Titre.objects.filter(type = 'DEV').count())
        et.SubElement(xml_generalite, "No_derniere_devise").text = fmt.max(Titre.objects.filter(type = 'DEV'), champ = 'id')
        xml_detail = et.SubElement(xml_devises, 'Detail_des_devises')
        for devise in Titre.objects.filter(type = 'DEV').order_by('id'):
            xml_sub = et.SubElement(xml_detail, 'Devise')
            xml_sub.set('No', str(devise.id))
            xml_sub.set('Nom', devise.nom)
            xml_sub.set('IsoCode', devise.isin)
            if devise == Generalite.dev_g():
                xml_sub.set('Date_dernier_change', "")
                xml_sub.set('Change', fmt.float(0))
            else:
                xml_sub.set('Date_dernier_change', fmt.date(devise.last_cours_date))
                xml_sub.set('Change', fmt.float(devise.last_cours))
    else:
        et.SubElement(xml_generalite, "Nb_devises").text = "1"
        et.SubElement(xml_generalite, "No_derniere_devise").text = '1'
        xml_detail = et.SubElement(xml_devises, 'Detail_des_devises')
        xml_sub = et.SubElement(xml_detail, 'Devise')
        xml_sub.set('No', str(0))
        xml_sub.set('Nom', settings.DEVISE_GENERALE)
        xml_sub.set('IsoCode', settings.DEVISE_GENERALE)
        xml_sub.set('Date_dernier_change', "")
        xml_sub.set('Rapport_entre_devises', "0")#NOT IN BDD
        xml_sub.set('Devise_en_rapport', '0')#NOT IN BDD
        xml_sub.set('Change', fmt.float(0))


    ##BANQUES##
    xml_banques = et.SubElement(xml_root, "Banques")
    xml_generalite = et.SubElement(xml_banques, "Generalites")
    et.SubElement(xml_generalite, "Nb_banques").text = str(Banque.objects.count())
    et.SubElement(xml_generalite, "No_derniere_banque").text = fmt.max(Banque.objects)
    xml_detail = et.SubElement(xml_banques, 'Detail_des_banques')
    for bank in Banque.objects.all().order_by('id'):
        if bank is not None:
            xml_sub = et.SubElement(xml_detail, 'Banque')
            xml_sub.set('No', str(bank.id))
            xml_sub.set('Nom', bank.nom)
            xml_sub.set('Code', str(bank.cib))
    ##exercices##
    xml_exo = et.SubElement(xml_root, "Exercices")
    xml_generalite = et.SubElement(xml_exo, "Generalites")
    et.SubElement(xml_generalite, "Nb_exercices").text = str(Exercice.objects.count())
    et.SubElement(xml_generalite, "No_dernier_exercice").text = fmt.max(Exercice.objects)
    xml_detail = et.SubElement(xml_exo, 'Detail_des_exercices')
    for exo in Exercice.objects.all().order_by('id'):
        if exo is not None:
            xml_sub = et.SubElement(xml_detail, 'Exercice')
            xml_sub.set('No', str(exo.id))
            xml_sub.set('Nom', exo.nom)
            xml_sub.set('Date_debut', fmt.date(exo.date_debut))
            xml_sub.set('Date_fin', fmt.date(exo.date_fin))
    ##rapprochement##
    xml_rapp = et.SubElement(xml_root, "Rapprochements")
    xml_detail = et.SubElement(xml_rapp, 'Detail_des_rapprochements')
    for rapp in Rapp.objects.all().order_by('id'):
        if rapp is not None:
            xml_sub = et.SubElement(xml_detail, 'Rapprochement')
            xml_sub.set('No', str(rapp.id))
            xml_sub.set('Nom', rapp.nom)

    #final
    xml = et.tostring(xml_root, method = "xml", xml_declaration = True, pretty_print = True)
    avant = ['&#232', '&#233', '&#234', '&#244']
    apres = ['&#xE8', '&#xE9', '&#xEA', '&#xF4']
    for car in avant:
        xml = xml.replace(car, apres[avant.index(car)])
    xml = xml.replace("xml version='1.0' encoding='ASCII'", 'xml version="1.0"')
    return xml

@permission_required('gsb_can_export')
def export_fsb(request):
    nb_compte = Compte.objects.count()
    if nb_compte:
        xml_django = _export()
        #h=HttpResponse(xml,mimetype="application/xml")
        reponse = HttpResponse(xml_django, mimetype="application/x-grisbi-fsb")
        reponse["Cache-Control"] = "no-cache, must-revalidate"
        reponse["Content-Disposition"] = "attachment; filename=%s" % settings.TITRE
        return reponse
    else:
        return render_to_response('generic.django.html',
            {
                'titre':'import fsb',
                'resultats':({'texte':u"attention, il n'y a pas de comptes donc pas de possibilité d'export."},)
            },
            context_instance=RequestContext(request)
        )

if __name__ == "__main__":
    xml_string = _export()
    fichier = open("%s/test_files/test.gsb" % (os.path.dirname(os.path.abspath(__file__))), "w")
    fichier.write(xml_string)
    fichier.close()
