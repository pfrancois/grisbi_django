# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .utils import Format as fmt
from .utils import strpdate,UTF8Recoder
import codecs, cStringIO


#pour les vues
from django.http import HttpResponse
#pour les vues
from . import forms as gsb_forms
from django.db import models
from django.shortcuts import render
from django.contrib import messages
from .views import ExportViewBase
from django.core.exceptions import ObjectDoesNotExist
#django
from .models import Cat

class qifWriter(object):
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
        chaine=unicode(row).encode("utf-8")
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
    def w(self,type,row):
        self.writerow("%s%s"%(type,row))
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class Export_qif(ExportViewBase):
    def export(self, q):
        #ouverture du fichier
        fich = cStringIO.StringIO()
        qif = qifWriter(fich, encoding='iso-8859-15')
        #recuperation de la requete
        if q:
            opes=q.order_by('date').select_related('cat', "compte", "tiers", "ib")
            #TODO gerer les split à mon avis faut juste garder les mere et sans mere
        else:
             opes = Ope.objects.all().order_by('date').select_related('cat', "compte", "tiers", "ib").filter(date__gte=strpdate("2009-01-01"))
             #TODO idem au dessus
        #initialisation
        i = 0
        total = float(opes.count())
        #debut
        #entete du fichier
        qif.writerow("!Type:Bank")
        #pour les operations "normales" cad non achat de titre
        for ope in opes:
            i += 1
            #TODO determiner si split par une variable
            #date
            qif.w("D",fmt.date(ope.date))
            #montant
            qif.w("T",fmt.float(ope.montant))
            #tiers
            qif.w("P",fmt.str(ope.tiers,'',"nom"))
            #cleared status
            qif.w("M",ope.notes)#TODO verifier si split
            if ope.rapp is None:
                if ope.pointe:
                    cleared_status="c"
                else:
                    cleared_status=""
            else:
                cleared_status="R"
            qif.w("C",cleared_status)
            #category and class
            try:
                if not ope.mere:
                    cat_g = fmt.str(ope.cat, "", "nom")
                    if bool(ope.ib):
                        qif.w("L","/".join([cat_g,fmt.str(ope.ib,"","nom")]))
                    else:
                        qif.w("L","%s" % cat_g)
                else:
                    qif.w("L","%s/%s" % ("Splits"))
            except ObjectDoesNotExist:
                pass
            #gestion des splits
            #qif.w("S")
            #TODO gestion des virements
            qif.w('^',"")
        #finalisation
        reponse = HttpResponse(fich.getvalue(), mimetype="text/plain")
        reponse["Cache-Control"] = "no-cache, must-revalidate"
        reponse["Content-Disposition"] = "attachment; filename=export.qif"
        return reponse
