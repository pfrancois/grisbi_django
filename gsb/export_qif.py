# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .utils import Format as fmt
import cStringIO


#pour les vues
from django.http import HttpResponse
#pour les vues
#from django.db import models
#from django.contrib import messages
from .export_base import ExportViewBase, Exportform_ope, Writer_base
from django.core.exceptions import ObjectDoesNotExist
#django
from .models import Cat, Ib, Compte, Ope

def convert_type2qif(type_a_transformer):
    if type_a_transformer == "b":
        return "Bank"
    if type_a_transformer == "e":
        return "Cash"
    if type_a_transformer == "t":
        return "Invst"
    if type_a_transformer == "a":
        return "Oth A"
    if type_a_transformer == "p":
        return "Oth L"


class QifWriter(Writer_base):
    """
    A pseudofile which will write rows to file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, encoding="utf-8"):
        """ Redirect output to a queue
        """
        self.queue = cStringIO.StringIO()
        self.stream = fich
        self.encoding = encoding

    def writerow(self, row):
        """ecrit une ligne"""
        chaine = unicode(row).encode("utf-8")
        self.queue.write(chaine)
        self.queue.write("\n")
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = data.encode(self.encoding)
        # strip BOM
        #       if self.encoding == "utf-16":
        #           data = data[2:]
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def w(self, type_data, row):
        """ecrit une ligne avec le type"""
        chaine = "%s%s" % (type_data, row)
        self.writerow(chaine)

    def end_record(self):
        """ecrit la fin de l'enregistrement"""
        self.writerow("^")
        self.enregistrement = ""

def cat_export(ope):
    """
    renvoie la categorie au format qif adequat avec la gestion des ib
    @param ope:
    @return:
    """
    if not ope.jumelle:#dans ce cas la c'est une operation normale
        try:
            cat_g = fmt.str(ope.cat, "", "nom")#recupere la cat de l'operation
        except ObjectDoesNotExist:
            cat_g = "inconnu"
        ib = None
        if bool(ope.ib):#gestion de l'ib
            try:
                ib = fmt.str(ope.ib, "", "nom")
            except ObjectDoesNotExist:
                ib = None
        if ib is not None:
            return u"/".join([cat_g, ib]) #s ib on a une cat de la forme cat/ib
        else:
            return u"%s" % cat_g#sinon c'est cat
    else:
        return u"[%s]" % ope.jumelle.compte.nom


class Export_qif(ExportViewBase):
    form_class = Exportform_ope
    model_initial = Ope
    extension_file = "qif"
    nomfich = "export_ope"
    """elle permet d'exporter au format qif"""

    def export(self, query):
        """exportationn effective du fichier qif"""
        #ouverture du fichier
        fich = cStringIO.StringIO()
        qif = QifWriter(fich, encoding='iso-8859-15')
        #recuperation des requete
        opes = query.order_by('compte', 'date').select_related('cat', "compte", "tiers", "ib", 'moyen').exclude(
            mere__isnull=False)
        comptes = Compte.objects.filter(pk__in=set(opes.values_list('compte__id', flat=True)))

        #initialisation
        #nb_ope = 0
        #nb_total = float(opes.count())
        #debut
        #entete du fichier
        qif.writerow("!Option:AutoSwitch")
        qif.writerow("!Account")
        #liste des comptes dont on a les operations
        for cpt in comptes:
            qif.w("N", cpt.nom)
            qif.w('D', '')
            qif.w("T", convert_type2qif(cpt.type))
        qif.writerow("!Clear:AutoSwitch")
        #liste d
        if comptes.count() == Compte.objects.count():
            #extraction categorie
            if Cat.objects.all().exists():
                qif.writerow("!Type:Cat")
                #export des categories
            for cat in Cat.objects.all().order_by('nom').iterator():
                qif.w("N", fmt.str(cat.nom))
                qif.w('D', '')
                if cat.type == 'r':
                    qif.w('I', '')
                if cat.type == 'd':
                    qif.w('E', '')
                qif.end_record()
            if Ib.objects.all().exists():
                qif.writerow("!Type:Class")
                #export des classes
            for ib in Ib.objects.all().order_by('nom').iterator():
                qif.w("N", fmt.str(ib.nom))
                qif.w('D', '')
                qif.end_record()
            #boucle export ope
        cpt = ""
        for ope in opes:
            if ope.compte.nom != cpt:
                qif.writerow("!Account")
                qif.w("N", ope.compte)
                qif.w('D', '')
                qif.w("T", convert_type2qif(ope.compte.type))
                qif.end_record()
                qif.w("!Type:", convert_type2qif(ope.compte.type))
                cpt = ope.compte.nom
            if ope.filles_set.all():
                mere = True
            else:
                mere = False
            if ope.jumelle:
                virement = True
            else:
                virement = True
                #montant
            qif.w("T", fmt.float(ope.montant))
            #tiers
            qif.w("P", fmt.str(ope.tiers, '', "nom"))
            if ope.moyen:
                qif.w('N', ope.moyen.nom)
            else:
                qif.w('N', "")
                #cleared status
            qif.w("M", ope.notes)#TODO verifier si split
            if ope.rapp is None:
                if ope.pointe:
                    cleared_status = "*"
                else:
                    cleared_status = ""
            else:
                cleared_status = "R"
            qif.w("C", cleared_status)
            #category and class et virement inclus dans la fonction
            qif.w("L", "%s" % cat_export(ope))
            #gestion des splits
            if mere:
                for fille in ope.filles_set.all():
                    qif.w("S", "%s" % cat_export(fille))#on cree une nouvelle categorie a au besoin
                    qif.w("E", "%s" % fille.notes)
                    qif.w('$', fille.montant)
            qif.end_record()
            #finalisation
        reponse = HttpResponse(fich.getvalue(), mimetype="text/plain")
        return reponse
