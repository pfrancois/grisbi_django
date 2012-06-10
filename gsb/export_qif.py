# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .utils import Format as fmt
import cStringIO


#pour les vues
from django.http import HttpResponse
#pour les vues
#from django.db import models
#from django.contrib import messages
from .views import ExportViewBase
from django.core.exceptions import ObjectDoesNotExist
#django
from .models import Cat, Ope, Ib, Compte

class QifWriter(object):
    """
    A pseudofile which will write rows to file "f", 
    which is encoded in the given encoding.
    """

    def __init__(self, fich, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.stream = fich
        self.encoding = encoding

    def writerow(self, row):
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
        self.writerow("%s%s"%(type_data, row))

    def end_record(self):
        self.writerow("^")

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class Export_qif(ExportViewBase):
    def export(self, q=None):
        #ouverture du fichier
        fich = cStringIO.StringIO()
        qif = QifWriter(fich, encoding='iso-8859-15')
        #recuperation des requete
        if not q:
            export_all = True
            q = Ope.objects.all()
        opes = q.order_by('date').select_related('cat', "compte", "tiers", "ib", 'moyen').exclude(mere__isnull=False)
        comptes = Compte.object.filter(pk__in=set(opes.values_list('compte__id', flat=True)))
        #initialisation
        i = 0
        total = float(opes.count())
        #debut
        #entete du fichier
        qif.writerow("!Account")
        for cpt in comptes:
            qif.w("N", cpt.nom)
            qif.w('D', '')
            if cpt.type == "b":
                qif.w("T", "Bank")
            if cpt.type == "e":
                qif.w("T", "Cash")
            if cpt.type == "t":
                qif.w("T", "Invst")
            if cpt.type == "a":
                qif.w("T", "Oth A")
            if cpt.type == "p":
                qif.w("T", "Oth L")
        if not export_all:
            ope = opes[0]
            type_compte = ope.compte.type
            if type_compte == "b":
                qif.writerow("!Type:Bank")
            if type_compte == "e":
                qif.writerow("!Type:Cash")
            if type_compte == "t":
                qif.writerow("!Type:Invst")
            if type_compte == "a":
                qif.writerow("Type:Oth A")
            if type_compte == "p":
                qif.writerow("!Type:Oth L")
        else:
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
        for ope in opes.iterator():
            i += 1
            if ope.filles_set:
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
            #category and class
            try:
                if not ope.mere:
                    cat_g = fmt.str(ope.cat, "", "nom")
                    if bool(ope.ib):
                        qif.w("L", "/".join([cat_g, fmt.str(ope.ib, "", "nom")]))
                    else:
                        qif.w("L", "%s" % cat_g)
                else:
                    qif.w("L", "%s" % "Splits")
            except ObjectDoesNotExist:
                pass
            #gestion des splits
            #qif.w("S")
            #TODO gestion des virements
            qif.end_record()
        #finalisation
        reponse = HttpResponse(fich.getvalue(), mimetype="text/plain")
        reponse["Cache-Control"] = "no-cache, must-revalidate"
        reponse["Content-Disposition"] = "attachment; filename=export.qif"
        return reponse
