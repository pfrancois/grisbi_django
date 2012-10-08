# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv, cStringIO, codecs


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core import exceptions as django_exceptions
from .models import  Compte,Ope

from django.views.generic.edit import FormView
from gsb import forms as gsb_forms
from django.db import models as models_agg
from django import forms
import time

class Excel_csv(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL
csv.register_dialect("excel_csv", Excel_csv)

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

    def __init__(self, fich, dialect=Excel_csv, encoding="utf-8", **kwds):
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

    def __init__(self, encoding="utf-8",fich=None, dialect=Excel_csv, **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect,  **kwds)
        self.encoder = codecs.getincrementalencoder(encoding)()
        if fich is not None:
            self.stream = fich
        else:
            self.stream = cStringIO.StringIO()
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
        data = self.encoder.encode(data)
        # strip BOM
        #       if self.encoding == "utf-16":
        #           data = data[2:]
        # write to the target stream
        self.stream.write(data)
        # empty queue

        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def getvalue(self,close=True):
        reponse=self.stream.getvalue()
        if close:
            self.close()
        return reponse
    def close(self):
        self.stream.close()

class Exportform_ope(gsb_forms.Baseform):
    collection = forms.ModelMultipleChoiceField(Compte.objects.all(), required=False,label="Comptes")
    date_min = forms.DateField(label='date minimum', widget=forms.DateInput)
    date_max = forms.DateField(label='date maximum', widget=forms.DateInput)
    model_initial=Ope
    model_collec = Compte
    def clean(self):
        if self.model_collec is None:
            raise django_exceptions.ImproperlyConfigured("model_collec non defini")
        super(Exportform_ope, self).clean()
        data = self.cleaned_data
        ensemble = [objet.id for objet in data["collection"]]
        self.query=self.model_initial.objects.filter( date__gte=data['date_min'], date__lte=data['date_max'])
        if ensemble == [] or len(ensemble) == self.model_collec.objects.count():
            pass
        else:
            self.query=self.verif_collec(self.query,ensemble)

        if self.query.count() == 0:#si des operations existent
            raise forms.ValidationError(u"attention pas d'opérations pour la selection demandée",)
        return data
    def verif_collec(self,query,ensemble):
        return query.filter(compte__pk__in=ensemble)



class ExportViewBase(FormView):
    template_name = 'gsb/param_export.djhtm'#nom du template
    model_initial=None#model d'ou on tire les dates initiales
    extension_file=None
    nomfich=None
    def export(self, query):
        """
        fonction principale mais abstraite
        """
        raise django_exceptions.ImproperlyConfigured("attention, il doit y avoir une methode qui extrait effectivement")
    def get_initial(self):
        """gestion des donnees initiales"""
        #prend la date de la premiere operation de l'ensemble des compte
        if self.model_initial is None:
            raise django_exceptions.ImproperlyConfigured("un modele d'ou on tire les dates initiales doit etre defini")
        date_min = self.model_initial.objects.aggregate(element=models_agg.Min('date'))['element']
        #la derniere operation
        date_max = self.model_initial.objects.aggregate(element=models_agg.Max('date'))['element']
        return {'date_min':date_min, 'date_max':date_max}
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """on a besoin pour le method decorator"""
        return super(ExportViewBase, self).dispatch(*args, **kwargs)
    def form_valid(self, form):
        """si le form est valid"""
        reponse = self.export(query=form.query)#comme on a verifier dans le form que c'etait ok
        debug=False#ce debug permet d'afficher les export
        if self.nomfich is None:
            raise django_exceptions.ImproperlyConfigured('nomfich non defini')
        if self.extension_file is None:
            raise django_exceptions.ImproperlyConfigured('extension_file non defini')

        if not debug:
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse["Content-Disposition"] = "attachment; filename=%s_%s.%s" % (self.nomfich,
                                                                         time.strftime("%d_%m_%Y-%H_%M_%S",
                                                                                       time.localtime())
                                                                            ,self.extension_file
                )
        return reponse

    def form_invalid(self, form):
        return self.render_to_response({'form':form, })