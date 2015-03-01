# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .. import models
from django.conf import settings  # @Reimport
from lxml import etree as et
# import logging
from .. import utils
from django.views import generic
# definitions des listes
liste_type_cat = models.Cat.typesdep
liste_type_moyen = models.Moyen.typesdep
liste_type_compte = models.Compte.typescpt
from django import http
import time

class Export_xml(generic.View):
    template_name = 'gsb/test.djhtm'
    extension_file = "xml"
    nomfich = "export_xml"
    debug = True
    titre = "export XML"
    format_date="%Y-%m-%d"

    def floattostr(self,s, nb_digit=2):
        """ convertit un float en string 10,7"""
        s1 = "{0:0.{1}f}".format(s, nb_digit)
        return s1.strip()

    def get(self, *args, **kwargs):
        #query=models.Ope.objects.filter(date__gte="2015-01-01").select_related('Compte','Moyen','Rapp','Tiers')
        #query=models.Banque.objects.filter(lastupdate__gte="2010-01-01")
        #query=models.Cat.objects.filter(lastupdate__gte="2010-01-01")
        #query=models.Compte.objects.filter(lastupdate__gte="2010-01-01")
        query=models.Cours.objects.filter(lastupdate__gte="2010-01-01")
        reponse_xml = self.export(query=query)  # comme on a verifier dans le form que c'etait ok
        reponse=http.HttpResponse(reponse_xml, content_type="text/xml")
        if not self.debug:
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse['Pragma'] = "public"
            reponse["Content-Disposition"] = "attachment; filename=%s_%s.%s" % (self.nomfich,
                                                                                time.strftime("%d_%m_%Y_%h_%m_%s", time.localtime()),
                                                                                self.extension_file)
        else:
            return reponse

    def export_header(self,xml_root):
        xml_metadata = et.SubElement(xml_root, "meta")
        et.SubElement(xml_metadata, "Version_fichier").text = "0.1.0"
        et.SubElement(xml_metadata, "Utilise_IB").text = utils.booltostr(settings.UTILISE_IB)
        et.SubElement(xml_metadata, "devise").text = utils.force_unicode(settings.DEVISE_GENERALE)
        et.SubElement(xml_metadata, "date_format").text = self.format_date
        et.SubElement(xml_metadata, "nowutc").text = utils.datetostr(utils.now(),param=self.format_date,defaut="")
        et.SubElement(xml_metadata, "device").text = utils.force_unicode(settings.CODE_DEVICE_POCKET_MONEY)


    def export(self, query):
        xml_root = et.Element("gsb_money")
        self.export_header(xml_root)
        opes=et.SubElement(xml_root, 'operations')
        banques=et.SubElement(xml_root, 'banques')
        cats=et.SubElement(xml_root, 'categories')
        comptes=et.SubElement(xml_root, 'comptes')
        cours=et.SubElement(xml_root, 'cours')
        echeances=et.SubElement(xml_root, 'echeances')
        exercices=et.SubElement(xml_root, 'exercices')
        moyens=et.SubElement(xml_root, 'moyens')
        ibs=et.SubElement(xml_root, 'ibs')
        opes_titre=et.SubElement(xml_root, 'opes_titre')
        rapps=et.SubElement(xml_root, 'rapprochements')
        tiers=et.SubElement(xml_root, 'tiers')
        titres=et.SubElement(xml_root, 'titres')
        for data in query:
            if isinstance(data, models.Ope) :
                opes.append(self.export_ope(data))
            elif isinstance(data,models.Banque):
                banques.append(self.export_banque(data))
            elif isinstance(data,models.Cat):
                cats.append(self.export_cat(data))
            elif isinstance(data,models.Compte):
                comptes.append(self.export_compte(data))
            elif isinstance(data,models.Cours):
                cours.append(self.export_cours(data))
            elif isinstance(data,models.Echeance):
                echeances.append(self.export_ech(data))
            elif isinstance(data,models.Exercice):
                exercices.append(self.export_exercices(data))
            elif isinstance(data,models.Ib):
                ibs.append(self.export_ib(data))
            elif isinstance(data,models.Moyen):
                moyens.append(self.export_moyens(data))
            elif isinstance(data,models.Ope_titre):
                opes_titre.append(self.export_ope_titre(data))
            elif isinstance(data,models.Rapp):
                rapps.append(self.export_rapp(data))
            elif isinstance(data,models.Tiers):
                tiers.append(self.export_tiers(data))
            elif isinstance(data,models.Titre):
                titres.append(self.export_titre(data))
            else:
                raise utils.FormatException('probleme')
        xml = et.tostring(xml_root, method="xml", xml_declaration=True, pretty_print=True)
        avant = ['&#232', '&#233', '&#234', '&#244']
        apres = ['&#xE8', '&#xE9', '&#xEA', '&#xF4']
        for car in avant:
            xml = xml.replace(car, apres[avant.index(car)])
        xml = xml.replace("xml version='1.0' encoding='ASCII'", 'xml version="1.0"')
        xml = xml.replace("  ", '    ')
        return xml

    def export_ope(self,data):
            xml_element=et.Element('operation')
            xml_element.set('pk', utils.force_unicode(data.id))
            xml_element.set('uuid', utils.force_unicode(data.uuid))
            xml_element.set('date_ope', utils.datetostr(data.date,param=self.format_date,defaut=""))
            xml_element.set('date_val', utils.datetostr(data.date_val,param=self.format_date,defaut=""))
            xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
            xml_element.set('date_created', utils.datetostr(data.date_created,param=self.format_date,defaut=""))
            if data.tiers is None:
                xml_element.set('tiers', "")
            else:
                xml_element.set('tiers',utils.force_unicode(data.tiers.nom))
            xml_element.set('montant', self.floattostr(data.montant))
            xml_element.set('compte',utils.force_unicode(data.compte.nom))
            if data.cat is None:
                xml_element.set('cat', "")
            else:
                xml_element.set('cat',utils.force_unicode("%s(%s)"%(data.cat.nom,data.cat.type)))
            if data.notes is None:
                xml_element.text=""
            else:
                 xml_element.text=utils.force_unicode(data.notes)
            if data.moyen is None:
                xml_element.set('moyen', "")
            else:
                xml_element.set('moyen',utils.force_unicode("%s(%s)"%(data.moyen.nom,data.moyen.type)))
            xml_element.text=utils.force_unicode(data.notes)
            xml_element.set('num_cheque',utils.force_unicode(data.num_cheque))
            xml_element.set('p',utils.booltostr(data.pointe))
            if data.rapp is None:
                xml_element.set('r', "0")
                xml_element.set('r_nom', "")
            else:
                xml_element.set('r',"1")
                xml_element.set('r_nom', utils.force_unicode(data.rapp.nom))
            if data.jumelle is None:
                xml_element.set("jumelle_uuid","")
            else:
                xml_element.set("jumelle_uuid",data.jumelle.uuid)
            if data.mere is None:
                xml_element.set("mere_uuid","")
            else:
                xml_element.set("mere_uuid",data.mere.uuid)
            if data.ope_titre_ost is None:
                xml_element.set("ope_titre_ost_uuid","")
            else:
                xml_element.set("ope_titre_ost_uuid",data.ope_titre_ost.uuid)
            if data.ope_titre_pmv is None:
                xml_element.set("ope_titre_pmv_uuid","")
            else:
                xml_element.set("ope_titre_pmv_uuid",data.ope_titre_pmv.uuid)
            xml_element.text=utils.force_unicode(data.notes)
            return xml_element

    def export_banque(self,data):
        xml_element=et.Element('banque')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        xml_element.set('cib',utils.force_unicode(data.cib))
        xml_element.set('nom',utils.force_unicode(data.nom))
        xml_element.text=utils.force_unicode(data.notes)
        return xml_element
    def export_cat(self,data):
        xml_element=et.Element('categorie')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        xml_element.set('nom',utils.force_unicode(data.nom))
        xml_element.set('type',utils.force_unicode(data.type))
        xml_element.set('couleur',utils.force_unicode(data.couleur))
        return xml_element
    def export_compte(self,data):
        xml_element=et.Element('compte')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        xml_element.set('nom',utils.force_unicode(data.nom))
        xml_element.set('titulaire',utils.force_unicode(data.titulaire))
        xml_element.set('type',utils.force_unicode(data.type))
        if data.banque is None:
            xml_element.set('banque','')
        else:
            xml_element.set('banque',utils.force_unicode(data.banque.nom))
        xml_element.set('guichet',utils.force_unicode(data.guichet))
        xml_element.set('num_compte',utils.force_unicode(data.num_compte))
        xml_element.set('cle_compte',utils.force_unicode(data.cle_compte))
        xml_element.set('solde_init',utils.force_unicode(data.solde_init))
        xml_element.set('solde_mini_voulu',self.floattostr(data.solde_mini_voulu))
        xml_element.set('solde_mini_autorise',self.floattostr(data.solde_mini_autorise))
        xml_element.set('ouvert',utils.booltostr(data.ouvert))
        xml_element.set('ouvert',utils.booltostr(data.ouvert))
        if data.moyen_credit_defaut is None:
            xml_element.set('moyen_credit_defaut', "")
        else:
            xml_element.set('moyen_credit_defaut',utils.force_unicode("%s(%s)"%(data.moyen_credit_defaut.nom,data.moyen_credit_defaut.type)))
        if data.moyen_credit_defaut is None:
            xml_element.set('moyen_credit_defaut', "")
        else:
            xml_element.set('moyen_debit_defaut',utils.force_unicode("%s(%s)"%(data.moyen_debit_defaut.nom,data.moyen_debit_defaut.type)))
        xml_element.set('couleur',utils.force_unicode(data.couleur))
        xml_element.text=utils.force_unicode(data.notes)

        return xml_element
    def export_cours(self,data):
        xml_element=et.Element('cours')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        xml_element.set('date', utils.datetostr(data.date,param=self.format_date,defaut=""))
        xml_element.set('valeur', self.floattostr(data.valeur, nb_digit=3))
        xml_element.set('titre', utils.force_unicode(data.titre))
        return xml_element
    def export_ech(self,data):
        xml_element=et.Element('echeance')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element
    def export_exercices(self,data):
        xml_element=et.Element('exercice')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element
    def export_ib(self,data):
        xml_element=et.Element('ib')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element
    def export_moyens(self,data):
        xml_element=et.Element('moyen')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element
    def export_ope_titre(self,data):
        xml_element=et.Element('ope_titre')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element
    def export_rapp(self,data):
        xml_element=et.Element('rapprochment')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element
    def export_tiers(self,data):
        xml_element=et.Element('tiers')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element
    def export_titre(self,data):
        xml_element=et.Element('tiers')
        xml_element.set('pk', utils.force_unicode(data.id))
        xml_element.set('uuid', utils.force_unicode(data.uuid))
        xml_element.set('lastupdate', utils.datetostr(data.lastupdate,param=self.format_date,defaut=""))
        return xml_element