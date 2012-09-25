# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .models import Ope,Cours,Ope_titre
from .utils import Format as fmt
import time
#from .utils import strpdate

import csv, cStringIO, codecs
import logging
from django.http import HttpResponse
#from django.conf import settings
#pour les vues
#from . import forms as gsb_forms
#from django.db import models
#from django.shortcuts import render
#from django.contrib import messages
from .views import ExportViewBase
from django.core.exceptions import ObjectDoesNotExist


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, fich, encoding):
        self.reader = codecs.getreader(encoding)(fich)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, dialect=csv.excel, encoding="utf-8", **kwds):
        fich = UTF8Recoder(fich, encoding)
        self.reader = csv.reader(fich, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, **kwds)
        self.stream = fich
        # Force BOM
        #        if encoding=="utf-16":
        #            f.write(codecs.BOM_UTF16)
        self.encoding = encoding

    def writerow(self, row):
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])
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
        self.queue.truncate()

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class Excel_csv(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\r\n'
    quoting = csv.QUOTE_MINIMAL


class Export_ope_csv(ExportViewBase):
    def export(self, query=None,export_all=None):
        """
        fonction principale
        """
        logger = logging.getLogger('gsb.export')
        csv.register_dialect("excel_csv", Excel_csv)
        fich = cStringIO.StringIO()
        csv_file = UnicodeWriter(fich, encoding='iso-8859-15', dialect=Excel_csv)
        csv_file.writerow(u'id;account name;date;montant;p;m;moyen;cat;tiers;notes;projet;n chq;id jumelle lie;fille;num op vent m;mois'.split(';'))
        if query:
            opes = query.order_by('date').select_related('cat', "compte", "tiers", "ib")
        else:
            opes = Ope.objects.all().order_by('date').select_related('cat', "compte", "tiers", "ib").filter(filles_set__isnull=True)
        i = 0
        total = float(opes.count())
        for ope in opes:
            i += 1
            ligne = [ope.id, ope.compte.nom, fmt.date(ope.date), fmt.float(ope.montant)]
            if ope.rapp is None:
                ligne.append(0)
            else:
                ligne.append(1)
            ligne.append(fmt.bool(ope.pointe))
            try:
                ligne.append(fmt.str(ope.moyen, '', 'nom'))
            except ObjectDoesNotExist:
                ligne.append("")
            try:
                cat_g = fmt.str(ope.cat, "", "nom").split(":")
                if cat_g[0]:
                    ligne.append("(%s)%s" % (fmt.str(ope.cat, "", "type"), cat_g[0].strip()))
                else:
                    ligne.append("")
            except ObjectDoesNotExist:
                ligne.append("")
            ligne.append(fmt.str(ope.tiers, '','nom'))
            ligne.append(ope.notes)
            try:
                ligne.append(fmt.str(ope.ib, '', 'nom'))
            except ObjectDoesNotExist:
                ligne.append("")
            ligne.append(ope.num_cheque)
            ligne.append(fmt.str(ope.jumelle, ''))
            ligne.append(fmt.bool(ope.mere))
            ligne.append(fmt.str(ope.mere, ''))
            ligne.append(ope.date.strftime('%Y_%m'))
            csv_file.writerow(ligne)
            #on affiche que tous les 500 lignes
            if ( (i-1)%500) == 0:
                logger.info("ope %s %s%%" % (ope.id, i / total * 100))
        logger.info('export ope csv')
        reponse = HttpResponse(fich.getvalue(), mimetype="text/plain")
        reponse["Cache-Control"] = "no-cache, must-revalidate"
        reponse["Content-Disposition"] = "attachment; filename=export_ope_%s.csv" % time.strftime("%d_%m_%Y-%H_%M_%S",time.localtime())
        fich.close()
        return reponse

def export_cours(request):
    """
    renvoie l'ensemble des cours.
    @param request:
    @return: object httpreposne se composant du fichier csv
    """
    logger = logging.getLogger('gsb.export')
    csv.register_dialect("excel_csv", Excel_csv)
    fich = cStringIO.StringIO()
    csv_file = UnicodeWriter(fich, encoding='iso-8859-15', dialect=Excel_csv)
    csv_file.writerow(["id","date","nom","value"])
    i=0
    collection=Cours.objects.all().select_related('titre').order_by('date')
    total = float(collection.count())
    for objet in collection:
        i += 1
        ligne=[objet.titre.isin,objet.date,objet.titre.nom,objet.valeur]
        csv_file.writerow(ligne)
        if ( (i-1)%500) == 0:
            logger.info("ope %s %s%%" % (objet.id, i / total * 100))
    reponse = HttpResponse(fich.getvalue(), mimetype="text/plain")
    reponse["Cache-Control"] = "no-cache, must-revalidate"
    reponse["Content-Disposition"] = "attachment; filename=%s.csv" % "cours"
    fich.close()
    return reponse

def export_ope_titres(request):
    """
    renvoie l'ensemble des operations sur titres.
    @param request:
    @return: object httpreposne se composant du fichier csv
    """
    data=[["id","date","compte","titre_id","titre_nom","sens","nombre","value"],]
    collection=Ope_titre.objects.all().select_related('titre',"compte").order_by('date')
    for objet in collection:
        ligne=[objet.id,objet.date,objet.compte.nom,objet.titre.nom,objet.titre.isin]
        if objet.nombre>0:
            ligne.append("achat")
        else:
            ligne.append("vente")
        ligne.append(objet.nombre)
        ligne.append(objet.invest)
        data.append(ligne)
    return export_csv(data,nomfich="ope_titre")

def export_csv(data,nomfich="export",csv=True):
    csv.register_dialect("excel_csv", Excel_csv)
    fich = cStringIO.StringIO()
    csv_file = UnicodeWriter(fich, encoding='iso-8859-15', dialect=Excel_csv)
    for ligne in data:
        csv_file.writerow(ligne)
    reponse = HttpResponse(fich.getvalue(), mimetype="text/plain")
    if csv:
        reponse["Cache-Control"] = "no-cache, must-revalidate"
        reponse["Content-Disposition"] = "attachment; filename=%s.csv" % nomfich
    fich.close()
    return reponse
