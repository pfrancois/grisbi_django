# -*- coding: utf-8 
from django import forms
from mysite.gsb.models import *

class ImportForm(forms.Form):
    nom_du_fichier = forms.FileField()
    version = forms.ChoiceField((
    ('gsb_0_5_0', 'format grisbi version 0.5.x'),
    ))

class OperationForm(forms.ModelForm):
    class Meta:
        model=Ope