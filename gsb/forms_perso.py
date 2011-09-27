# -*- coding: utf-8
from django import forms
from mysite.gsb.models import Compte, Cat, Moyen, Ope, Virement, Generalite, Compte_titre, Cours, Titre, Tiers, Ope_titre, Ib, Rapp
#from mysite.gsb import widgets
from django.conf import settings
import datetime
#import decimal
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from forms import Dategsbwidget, DateFieldgsb, Readonlywidget, ReadonlyField, CurField

input_format_date = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y')
error_css_class = 'error'
required_css_class = 'required'

class majPEE(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    date = DateFieldgsb()
    nombre_A = forms.DecimalField(initial = '0')
    montant_A = CurField()
    nombre_B = forms.DecimalField(initial = '0')
    montant_B = CurField()
    nombre_D = forms.DecimalField(initial = '0')
    montant_D = CurField()
    nombre_E = forms.DecimalField(initial = '0')
    montant_E = CurField()
    def __init__(self, *args, **kwargs):
        super (majPEE, self).__init__(*args, **kwargs)
        self.liste_opcvm = ('A', 'B', 'D', 'E')
    def clean(self):
        super(majPEE, self).clean()
        for l in self.liste_opcvm:
            if self.cleaned_data['nombre_%s' % l] == 0:
                self._errors['nombre_%s' % l] = self.error_class([u'le nombre ne peut être nul', ])
                del self.cleaned_data['nombre_%s' % l]
        return self.cleaned_data
