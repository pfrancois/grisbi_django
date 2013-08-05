# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv
import cStringIO
import codecs

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..models import Compte, Ope

from django.db import models as models_agg
from django import forms
import time

from ..utils import Excel_csv
from ..views import Myformview as FormView
from .. import forms as gsb_forms
from .. import widgets as gsb_field

from .. import models

class Writer_base(object):
    writer = None
    stream = None
    Encoder = None

    def __init__(self, encoding="utf-8", **kwds):
        self.queue = cStringIO.StringIO()
        self.encoder = codecs.getincrementalencoder(encoding)()
        self.stream = cStringIO.StringIO()
            # Force BOM
        #        if encoding=="utf-16":
        #            f.write(codecs.BOM_UTF16)
        self.encoding = encoding

    def writerow(self, row):
        raise NotImplementedError("il faut initialiser")

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def getvalue(self, close=True):
        reponse = self.stream.getvalue()
        if close:
            self.close()
        return reponse

    def close(self):
        self.stream.close()


class Csv_unicode_writer(Writer_base):

    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fieldnames, fich=None, encoding="utf-8", dialect=Excel_csv, **kwds):
        # Redirect output to a queue
        super(Csv_unicode_writer, self).__init__(encoding)
        self.fieldnames = fieldnames
        self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)

    def writerow(self, row):
        d = dict((k, unicode(s).encode("utf-8")) for (k, s) in row.items())
        self.writer.writerow(d)
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

    def writeheader(self):
            self.writer.writerow(dict((fn, fn) for fn in self.fieldnames))

class Exportform_ope(gsb_forms.Baseform):
    collection = forms.ModelMultipleChoiceField(Compte.objects.all(), required=False, label="Comptes")
    date_min = gsb_field.DateFieldgsb(label='date minimum', localize=True,)
    date_max = gsb_field.DateFieldgsb(label='date maximum', localize=True,)
    model_initial = Ope
    model_collec = Compte

    def clean(self):
        if self.model_collec is None:
            raise NotImplementedError("model_collec non defini")
        super(Exportform_ope, self).clean()
        data = self.cleaned_data
        if not 'collection' in data.keys():
            return data
        ensemble = [objet.id for objet in data["collection"]]  # liste des id des comptes
        date_min = data['date_min']
        date_max = data['date_max']
        self.query = self.model_initial.objects.filter(date__gte=date_min, date__lte=date_max)
        if ensemble == [] or len(ensemble) == models.Compte.objects.count():
            pass
        else:
            self.query = self.verif_collec(self.query, ensemble)
        if self.query.count() == 0:  # si des operations n'existent pas
            raise forms.ValidationError(u"attention pas d'opérations pour la selection demandée")
        return data

    def verif_collec(self, query, ensemble):
        return query.filter(compte__pk__in=ensemble)


class ExportViewBase(FormView):
    template_name = 'gsb/param_export.djhtm'  # nom du template
    model_initial = None  # model d'ou on tire les dates initiales
    extension_file = None
    nomfich = None
    debug = False
    form_class = None
    titre = None

    def export(self, query):  # pylint: disable=W0613
        """
        fonction principale mais abstraite
        """
        raise NotImplementedError("attention, il doit y avoir une methode qui extrait effectivement")

    def get_initial(self):
        """gestion des donnees initiales"""
        # prend la date de la premiere operation de l'ensemble des compte
        date_min = self.model_initial.objects.aggregate(element=models_agg.Min('date'))['element']
        # la derniere operation
        date_max = self.model_initial.objects.aggregate(element=models_agg.Max('date'))['element']
        return {'date_min': date_min, 'date_max': date_max}

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """on a besoin pour le method decorator"""
        if self.nomfich is None:
            raise NotImplementedError('nomfich non defini')
        if self.extension_file is None:
            raise NotImplementedError('extension_file non defini')
        if self.model_initial is None:
            raise NotImplementedError("un modele d'ou on tire les dates initiales doit etre defini")

        return super(ExportViewBase, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """si le form est valid"""
        reponse = self.export(query=form.query)  # comme on a verifier dans le form que c'etait ok

        if not self.debug:
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse['Pragma'] = "public"
            reponse["Content-Disposition"] = "attachment; filename=%s_%s.%s" % (self.nomfich,
                                                                            time.strftime("%d_%m_%Y", time.localtime()),
                                                                            self.extension_file
                                                                            )
        return reponse
