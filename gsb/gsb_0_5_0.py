# -*- coding: utf-8 -*-
from mysite.gsb.models import *
from django.http import HttpResponse
from django.db.models import Max
import settings
import sys
try:
    from lxml import etree as et
except:
        from xml.etree import cElementTree as et

class Format:
    def date(s, defaut="0/0/0"):
        if s==None:
            return defaut
        else:
            isinstance(s,datetime.date)
            s=s.strftime('%d/%m/%Y')
            result=[]
            tab=s.split("/")
            for partie in tab:
                if partie[0]=='0':
                    partie=partie[1:]
                result.append(partie)
            return "/".join(result)
    date=staticmethod(date)
    def bool(s,defaut='0'):
        if s==None:
            return defaut
        else:
            isinstance(s, bool)
            return str(int(s))
    bool=staticmethod(bool)
    def float(s):
        s="%10.7f" % s
        return s.replace('.',',').strip()
    float=staticmethod(float)
    def type(liste,s,defaut='0'):
        liste=[str(b[0]) for b in liste]
        try:
            s=str(liste.index(s))
        except ValueError:##on en un ca par defaut
            s = defaut
        return s
    type=staticmethod(type)
    def max(object,defaut='0',champ='id'):
        q=object.aggregate(id=Max(champ))['id']
        if q==None:
            return '0'
        else:
            return str(q-1)
    max=staticmethod(max)

#definitions des listes
liste_type_cat=Cat.typesdep
liste_type_signe=Moyen.typesdep
liste_type_compte=Compte.typescpt
liste_type_pointage=Ope.typespointage

def export(request):
    xml_root = et.Element( "grisbi" )
    #####generalites###
    q=Generalite.objects.all()[0]
    xml_generalites = et.SubElement( xml_root, "Generalites" )
    et.SubElement( xml_generalites, "Version_fichier" ).text = "0.5.0"
    et.SubElement( xml_generalites, "Version_grisbi" ).text = "0.5.9 for Windows (GTK>=2.6.9)"#XXX
    et.SubElement( xml_generalites, "Fichier_ouvert" ).text = "0"
    et.SubElement( xml_generalites, "Backup" ).text="sauvegarde.gsb"#XXX
    et.SubElement( xml_generalites, "Titre" ).text = str(q.titre)#XXX
    et.SubElement( xml_generalites, "Adresse_commune" ).text = ''#XXX
    et.SubElement( xml_generalites, "Adresse_secondaire" ).text = ''#XXX
    et.SubElement( xml_generalites, "Utilise_exercices" ).text = Format.bool(q.utilise_exercices)
    et.SubElement( xml_generalites, "Utilise_IB" ).text = Format.bool(q.utilise_ib)
    et.SubElement( xml_generalites, "Utilise_PC" ).text = Format.bool(q.utilise_pc)
    et.SubElement( xml_generalites, "Utilise_info_BG" ).text = "0"
    et.SubElement( xml_generalites, "Numero_devise_totaux_tiers" ).text = str(q.devise_generale.id-1)
    et.SubElement( xml_generalites, "Numero_devise_totaux_categ" ).text = str(q.devise_generale.id-1)
    et.SubElement( xml_generalites, "Numero_devise_totaux_ib" ).text = str(q.devise_generale.id-1)
    et.SubElement( xml_generalites, "Type_affichage_des_echeances" ).text = "3"
    et.SubElement( xml_generalites, "Affichage_echeances_perso_nb_libre" ).text = "0"
    et.SubElement( xml_generalites, "Type_affichage_perso_echeances" ).text = "0"
    et.SubElement( xml_generalites, "Numero_derniere_operation" ).text = Format.max(Ope.objects)
    et.SubElement( xml_generalites, "Echelle_date_import" ).text = "4"
    et.SubElement( xml_generalites, "Utilise_logo" ).text = "1"#XXX
    et.SubElement( xml_generalites, "Chemin_logo" ).text="g:/Program Files/Grisbi/pixmaps/grisbi-logo.png"#XXX
    et.SubElement( xml_generalites, "Affichage_opes" ).text = "18-1-3-13-5-6-7-4-0-12-0-9-8-0-0-11-15-0-0-0-0-0-0-0-0-0-0-0"
    et.SubElement( xml_generalites, "Rapport_largeur_col" ).text = "10-10-28-3-10-10-10"
    et.SubElement( xml_generalites, "Ligne_aff_une_ligne" ).text = "0"
    et.SubElement( xml_generalites, "Lignes_aff_deux_lignes" ).text = "0-1"
    et.SubElement( xml_generalites, "Lignes_aff_trois_lignes" ).text = "0-1-2"
    #####comptes###
    xml_comptes = et.SubElement( xml_root, "Comptes" )
    xml_generalites=et.SubElement( xml_comptes, "generalites" )
    et.SubElement( xml_generalites, "Ordre_des_comptes" ).text = '-'.join("%s"%(i-1) for i in Compte.objects.all().values_list('id', flat=True))
    et.SubElement( xml_generalites, "Compte_courant" ).text = str(0) # ca n'existe pas dans la bdd
    variable=0
    for co in Compte.objects.all().order_by('id'):
        variable += 1
        if variable > 1:
            continue
        id=co.id-1
        xml_compte = et.SubElement( xml_comptes, "compte" )
        xml_detail = et.SubElement( xml_compte, "Details" )
        et.SubElement( xml_detail, "Nom" ).text = str(co.nom)
        et.SubElement( xml_detail, "Id_compte" )
        et.SubElement( xml_detail, "No_de_compte" ).text = str(id)
        et.SubElement( xml_detail, "Titulaire" ).text = ''# ca n'existe pas dans la bdd
        et.SubElement( xml_detail, "Type_de_compte" ).text = Format.type(liste_type_compte,co.type)
        et.SubElement( xml_detail, "Nb_operations" ).text = str(Ope.objects.filter(compte=co.id).count())
        et.SubElement( xml_detail, "Devise" ).text = str(co.devise.id-1)
        if co.banque==None:
            et.SubElement( xml_detail, "Banque" ).text= str(0)
        else:
            et.SubElement( xml_detail, "Banque" ).text= str(co.banque.id-1)
        if int(co.guichet)==0 or co.guichet==None:
            et.SubElement( xml_detail, "Guichet" ).text = str("")
        else:
            et.SubElement( xml_detail, "Guichet" ).text = str(co.guichet)
        if co.num_compte=='' or co.num_compte==None:
            numero_compte=""
        else:
            numero_compte=co.num_compte
        et.SubElement( xml_detail, "No_compte_banque" ).text = str(numero_compte)
        if co.cle_compte==0 or co.cle_compte==None:
            cle_du_compte=""
        else:
            cle_du_compte=co.cle_compte
        et.SubElement( xml_detail, "Cle_du_compte" ).text = str(cle_du_compte)
        et.SubElement( xml_detail, "Solde_initial" ).text = Format.float(co.solde_init)
        et.SubElement( xml_detail, "Solde_mini_voulu" ).text = Format.float(co.solde_mini_voulu)
        et.SubElement( xml_detail, "Solde_mini_autorise" ).text = Format.float(co.solde_mini_autorise)
        et.SubElement( xml_detail, "Solde_courant" ).text = Format.float(co.solde())
        if co.date_dernier_releve!=None:
            et.SubElement( xml_detail, "Date_dernier_releve" ).text = Format.date(co.date_dernier_releve)
            et.SubElement( xml_detail, "Solde_dernier_releve" ).text = Format.float(co.solde_dernier_releve)
        else:
            et.SubElement( xml_detail, "Date_dernier_releve" )
            et.SubElement( xml_detail, "Solde_dernier_releve" ).text = Format.float(0)
        et.SubElement( xml_detail, "Dernier_no_de_rapprochement" ).text = Format.max(co.rapp_set)
        et.SubElement( xml_detail, "Compte_cloture" ).text = Format.bool(co.cloture)
        et.SubElement( xml_detail, "Affichage_r" ).text = "1" #ca n'existe pas dans la bdd
        et.SubElement( xml_detail, "Nb_lignes_ope" ).text = "2" #ca n'existe pas dans la bdd
        et.SubElement( xml_detail, "Commentaires" ).text = co.notes
        et.SubElement( xml_detail, "Adresse_du_titulaire" ).text='' #TODO mais ca n'existe pas dans la bdd XXX
        et.SubElement( xml_detail, "Nombre_de_types" ).text = str( Moyen.objects.filter(compte=1).count())
        if co.moyen_debit_defaut!=None:
            et.SubElement( xml_detail, "Type_defaut_debit" ).text = str(co.moyen_debit_defaut.grisbi_id)
        else:
            et.SubElement( xml_detail, "Type_defaut_debit" ).text = '0'
        if co.moyen_credit_defaut!=None:
            et.SubElement( xml_detail, "Type_defaut_credit" ).text = str(co.moyen_credit_defaut.grisbi_id)
        else:
            et.SubElement( xml_detail, "Type_defaut_credit" ).text = '0'
        et.SubElement( xml_detail, "Tri_par_type" ).text = '0'#TODO mais ca n'existe pas dans la bdd
        et.SubElement( xml_detail, "Neutres_inclus" ).text = '1'#TODO mais ca n'existe pas dans la bdd
        et.SubElement( xml_detail, "Ordre_du_tri" ).text = '/'.join([str(o.grisbi_id) for o in Moyen.objects.filter(compte=co.id).order_by('id')])
        ##types:
        xml_types = et.SubElement( xml_compte, "Detail_de_Types" )
        for ty in Moyen.objects.filter(compte=co.id).order_by('grisbi_id'):
            xml_element=et.SubElement( xml_types, "Type" )
            xml_element.set('No',str(ty.grisbi_id-1))
            xml_element.set('Nom',ty.nom)
            xml_element.set('Signe',Format.type(liste_type_signe,ty.signe))
            xml_element.set('Affiche_entree',Format.bool(ty.affiche_numero))
            xml_element.set('Numerotation_auto',Format.bool(ty.num_auto))
            xml_element.set('No_en_cours',str(ty.num_en_cours))
        xml_opes = et.SubElement( xml_compte, "Detail_des_operations" )
        #return HttpResponse(et.tostring(xml_root,method="xml",xml_declaration=True,pretty_print=True),mimetype="application/xml")
        ##operations
        for ope in Ope.objects.filter(compte=co.id).order_by('date'):
            xml_element=et.SubElement( xml_opes,'Operation')
            #numero de l'operation
            xml_element.set('No',str(ope.id-1))
            xml_element.set('Id','')#XXX
            #date de l'operation
            xml_element.set('D',Format.date(ope.date))
            #date de valeur
            if ope.date_val==None:
                xml_element.set('Db',"0/0/0")
            else:
                xml_element.set('Db',Format.date(ope.date_val))
            xml_element.set('M',Format.float(ope.montant))
            xml_element.set('De',str(ope.devise.id-1))
            xml_element.set('Rdc','0')#XXX mais pour l'instant ce n'est pas géré par les devises
            change=str(ope.devise.dernier_tx_de_change).replace('.',',')
            if change == '1,0':
                xml_element.set('Tc',Format.float(0))
            else:
                xml_element.set('Tc',Format.float(ope.devise.dernier_tx_de_change))
            xml_element.set('Fc',Format.float(0)) #XXX
            xml_element.set('T',str(ope.tiers.id-1))
            if ope.cat == None:
                xml_element.set('C',str(0))
            else:
                xml_element.set('C',str(ope.cat.id-1))
            if ope.scat == None:
                xml_element.set('Sc',str(0))
            else:
                xml_element.set('Sc',str(ope.scat.grisbi_id-1))
            xml_element.set('Ov',Format.bool(ope.is_mere))
            xml_element.set('N',ope.notes)
            if ope.moyen==None:
                xml_element.set('Ty',str(0))
            else:
                xml_element.set('Ty',str(ope.moyen.grisbi_id))
            xml_element.set('Ct',str(ope.numcheque))
            xml_element.set('P',Format.type(liste_type_pointage,ope.pointe))
            xml_element.set('A',"0")#inutile
            if ope.rapp==None:
                xml_element.set('R',str(0))
            else:
                xml_element.set('R',str(ope.rapp.id-1))
            if ope.exercice==None:
                xml_element.set('E',str(0))
            else:
                xml_element.set('E',str(ope.exercice.id-1))
            if ope.ib == None:
                xml_element.set('I',str(0))
            else:
                xml_element.set('I',str(ope.ib.id-1))
            if ope.sib == None:
                xml_element.set('Si',str(0))
            else:
                xml_element.set('Si',str(ope.sib.grisbi_id))
            xml_element.set('Pc',"")#XXX
            xml_element.set('Ibg',"")#XXX
            if ope.jumelle==None:
                num_jumelle="0"
                num_cpt_jumelle="0"
            else:
                num_cpt_jumelle=str(ope.jumelle.compte.id-1)
                num_jumelle=str(ope.jumelle.id-1)
            xml_element.set('Ro',str(num_jumelle))
            xml_element.set('Rc',str(num_cpt_jumelle))
            if ope.mere==None:
                num_mere="0"
            else:
                num_mere=str(ope.mere.id-1)
            xml_element.set('Va',num_mere)
                #raison pour lesquelles il y a des attributs non modifiables
                #Rdc: mais pour l'instant ce n'est pas géré par les devises
                #Fc: si besoin dans ce cas, ce sera une operation ventilée avec frais de change comme categorie et l'autre categorie
                #A: pas de prise en compte des operations periodiques
    ###Echeances###
    xml_echeances_root = et.SubElement( xml_root, "Echeances" )
    xml_generalite = et.SubElement( xml_echeances_root, "Generalites" )
    et.SubElement( xml_generalite, "Nb_echeances" ).text= str(Echeance.objects.count())
    et.SubElement( xml_generalite, "No_derniere_echeance" ).text=Format.max(Echeance.objects)
    xml_echeances = et.SubElement(xml_echeances_root,'Detail_des_echeances')
    for ech in Echeance.objects.all().order_by('id'):
        xml_element = et.SubElement( xml_echeances, 'Echeance', No = str(ech.id-1))
        xml_element.set('Date', Format.date(ech.date_ech))
        xml_element.set('Compte',str(ech.compte.id-1))
        xml_element.set('Montant',Format.float(ech.montant))
        xml_element.set('Devise',str(ech.devise.id-1))
        if ech.tiers==None:
            xml_element.set('Tiers',"0")
        else:
            xml_element.set('Tiers',str(ech.tiers.id-1))
        if ech.cat==None:
            xml_element.set('Cat',"0")
        else:
            xml_element.set('Cat', str(ech.cat.id-1))
        if ech.compte_virement==None:
            xml_element.set('Virement_compte',"0")
        else:
            xml_element.set('Virement_compte', str(ech.compte_virement.id-1))
        if ech.moyen==None:
            xml_element.set('Type',"0")
        else:
            xml_element.set('Type',str(ech.moyen.id-1))
        if ech.moyen_virement==None:
            xml_element.set('Type_contre_ope',"0")
        else:
            xml_element.set('Type_contre_ope', str(ech.moyen_virement.id-1))
        if ech.exercice==None:
            xml_element.set('Exercice',"-2")
        else:
            xml_element.set('Exercice', str(ech.exercice.id-1))
        xml_element.set('Contenu_du_type',"")#XXX
        if ech.exercice==None:
            xml_element.set('Exercice',"0")
        else:
            xml_element.set('Exercice', str(ech.exercice.id-1))
        if ech.ib==None:
            xml_element.set('Imputation',"0")
        else:
            xml_element.set('Imputation', str(ech.ib.id-1))
        if ech.sib==None:
            xml_element.set('Sous-imputation',"0")
        else:
            xml_element.set('Sous-imputation', str(ech.sib.grisbi_id))
        xml_element.set('Notes',ech.notes)
        xml_element.set('Automatique',Format.bool(ech.inscription_automatique))
        xml_element.set('Notes',str(ech.notes))
        xml_element.set('Periodicite',str(ech.periodicite))#todo gerer ca ne conjonction avec bdd
        xml_element.set('Intervalle_periodicite',str(ech.intervalle))
        xml_element.set('Periodicite_personnalisee',str(ech.periode_perso))
        xml_element.set('date_limite',Format.date(ech.date_limite))
        xml_element.set('date_limite',Format.date(ech.date_limite,defaut=""))
        xml_element.set('Ech_ventilee','0')
        xml_element.set('No_ech_associee','0')
    ###Tiers###
    xml_tiers_root = et.SubElement( xml_root, "Tiers" )
    xml_generalite = et.SubElement( xml_tiers_root, "Generalites" )
    et.SubElement( xml_generalite, "Nb_tiers" ).text=str(Tiers.objects.count())
    et.SubElement( xml_generalite, "No_dernier_tiers" ).text=Format.max(Tiers.objects)
    xml_detail=et.SubElement(xml_tiers_root,'Detail_des_tiers')
    for tier in Tiers.objects.all().order_by('id'):
        xml_sub=et.SubElement( xml_detail , 'Tiers')
        xml_sub.set("No", str(tier.id-1))
        xml_sub.set("Nom",tier.nom)
        if tier.is_titre:##integration des donnees sur les titres afin de garder une consistence
            xml_sub.set("Informations","%s@%s"%(tier.titre_set.all().get().isin,tier.titre_set.all().get().type))
        else:
            xml_sub.set("Informations",tier.notes)
        xml_sub.set("Liaison","0")
    ##categories##
    xml_cat_root = et.SubElement( xml_root, "Categories" )
    xml_generalite = et.SubElement( xml_cat_root, "Generalites" )
    et.SubElement( xml_generalite, "Nb_categories" ).text=str(Cat.objects.count())
    et.SubElement( xml_generalite, "No_derniere_categorie" ).text=Format.max(Cat.objects)
    xml_detail = et.SubElement(xml_cat_root,'Detail_des_categories')
    for c in Cat.objects.all().order_by('id'):
        xml_cate = et.SubElement( xml_detail, 'Categorie')
        xml_cate.set('No',str(c.id-1))
        xml_cate.set('Nom',c.nom)
        xml_cate.set('Type',Format.type(liste_type_cat,c.type))
        xml_cate.set('No_derniere_sous_cagegorie',Format.max(Scat.objects.filter(cat=c.id),defaut='0',champ='grisbi_id'))
        for sc in Scat.objects.filter(cat=c.id):
            if sc != None:
                xml_sub=et.SubElement( xml_cate,'Sous-categorie')
                xml_sub.set('No',str(sc.grisbi_id))
                xml_sub.set('Nom',sc.nom)
    ##imputation
    xml_imp_root = et.SubElement( xml_root, "Imputations" )
    xml_generalite = et.SubElement( xml_imp_root, "Generalites" )
    et.SubElement( xml_generalite, "Nb_imputations" ).text=str(Ib.objects.count())
    et.SubElement( xml_generalite, "No_derniere_imputation" ).text=Format.max(Ib.objects)
    xml_detail = et.SubElement(xml_imp_root,'Detail_des_imputations')
    for c in Ib.objects.all().order_by('id'):
        if c != None:
            xml_ib = et.SubElement( xml_detail, 'Imputation')
            xml_ib.set('No',str(c.id-1))
            xml_ib.set('Nom',c.nom)
            xml_ib.set('Type',Format.type(liste_type_cat,c.type))
            xml_ib.set('No_derniere_sous_imputation',Format.max(Sib.objects.filter(ib=c.id),defaut='0',champ='grisbi_id'))
            for simp in Sib.objects.filter(ib=c.id):
                if simp != None:
                    xml_sub=et.SubElement( xml_ib, 'Sous-imputation')
                    xml_sub.set('No',str(simp.grisbi_id))
                    xml_sub.set('Nom',simp.nom )
    ##devises##
    xml_devises = et.SubElement( xml_root, "Devises" )
    xml_generalite = et.SubElement( xml_devises, "Generalites" )
    et.SubElement( xml_generalite, "Nb_devises" ).text=str(Devise.objects.count())
    et.SubElement( xml_generalite, "No_derniere_devise" ).text= Format.max(Devise.objects)
    xml_detail = et.SubElement(xml_devises,'Detail_des_devises')
    for c in Devise.objects.all().order_by('id'):
        if c != None:
            xml_sub = et.SubElement( xml_detail, 'Devise' )
            xml_sub.set('No',str(c.id-1))
            xml_sub.set('Nom',c.nom)
            xml_sub.set('Code',c.isocode)
            xml_sub.set('IsoCode',c.isocode)
            xml_sub.set('Passage_euro',"0")
            xml_sub.set('Date_dernier_change',Format.date(c.date_dernier_change))
            xml_sub.set('Rapport_entre_devises',"0")
            xml_sub.set('Devise_en_rapport','0')
            xml_sub.set('Change',Format.float(c.dernier_tx_de_change))
            #raison pour lesquelles il y a des attributs non modifiables
            #isocode est par construction egale à code
            #Passage_euro: plus besoin
            #Date_dernier_change TODO
            #Rapport_entre_devises plus besoin
            #Change TODO
    ##BANQUES##
    xml_banques = et.SubElement( xml_root, "Banques" )
    xml_generalite = et.SubElement( xml_banques, "Generalites" )
    et.SubElement( xml_generalite, "Nb_banques" ).text=str(Banque.objects.count())
    et.SubElement( xml_generalite, "No_derniere_banque" ).text=Format.max(Banque.objects)
    xml_detail = et.SubElement( xml_banques,'Detail_des_banques' )
    for c in Banque.objects.all().order_by('id'):
        if c != None:
            xml_sub = et.SubElement( xml_detail, 'Banque')
            xml_sub.set('No',str(c.id-1))
            xml_sub.set('Nom',c.nom)
            xml_sub.set('Code',str(c.cib))
            xml_sub.set('Adresse',"")
            xml_sub.set('Tel',"")
            xml_sub.set('Mail',"")
            xml_sub.set('Web',"")
            xml_sub.set('Nom_correspondant',"")#XXX
            xml_sub.set('Fax_correspondant',"")#XXX
            xml_sub.set('Tel_correspondant',"")#XXX
            xml_sub.set('Mail_correspondant',"")#XXX
            xml_sub.set('Remarques',c.notes)
            #raison pour lesquelles il y a des attributs non modifiables
            #Adresse pas ds BDD
            #Tel,mail, web, Nom_correspondant: pas ds bdd
            #Fax_correspondant: pas ds bdd
            #Tel_correspondant: pas ds bdd
            #Mail_correspondant: pas ds bdd
    ##exercices##
    xml_exo = et.SubElement( xml_root, "Exercices" )
    xml_generalite = et.SubElement( xml_exo, "Generalites" )
    et.SubElement( xml_generalite, "Nb_exercices" ).text==str(Exercice.objects.count())
    et.SubElement( xml_generalite, "No_dernier_exercice" ).text=Format.max(Exercice.objects)
    xml_detail = et.SubElement( xml_exo,'Detail_des_exercices' )
    for c in Exercice.objects.all().order_by('id'):
        if c != None:
            xml_sub = et.SubElement( xml_detail, 'Exercice')
            xml_sub.set('No',str(c.id-1))
            xml_sub.set('Nom',c.nom)
            xml_sub.set('Date_debut',Format.date(c.date_debut))
            xml_sub.set('Date_fin',Format.date(c.date_fin))
            xml_sub.set('Affiche',"1")
    ##rapprochement##TODO
    xml_rapp = et.SubElement( xml_root, "Rapprochements" )
    xml_detail = et.SubElement( xml_rapp,'Detail_des_rapprochements' )
    for c in Rapp.objects.all().order_by('id'):
        if c != None:
            xml_sub = et.SubElement( xml_detail, 'Rapprochement')
            xml_sub.set('No',str(c.id-1))
            xml_sub.set('Nom',c.nom)
    #etatsTODO
    xml_etats = et.SubElement( xml_root, "Etats" )
    generalite = et.SubElement( xml_etats, "Generalites" )
    et.SubElement( xml_generalite, "No_dernier_etat" ).text="0"
    detail = et.SubElement( xml_etats,'Detail_des_etats' )
    #final
    xml=et.tostring(xml_root,method="xml",xml_declaration=True,pretty_print=True)
    avant=['&#232','&#233','&#234','&#244']
    apres=['&#xE8','&#xE9','&#xEA','&#xF4']
    print "test"
    for car in avant:
        xml=xml.replace(car,apres[avant.index(car)])
    #return HttpResponse(et.tostring(xml_root,method="xml",xml_declaration=True,pretty_print=True),mimetype="application/xml")
    return HttpResponse(xml,mimetype="application/xml")
    #h=HttpResponse(xml,mimetype="application/x-grisbi-gsb")
    #h["Cache-Control"] = "no-cache, must-revalidate"
    #h["Content-Disposition"] = "attachment; filename=%s"%(settings.TITRE)
    #return h
