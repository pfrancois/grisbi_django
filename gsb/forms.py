# -*- coding: utf-8
from django import forms
from mysite.gsb.models import *
from mysite.gsb import widgets
class ImportForm(forms.Form):
    nom_du_fichier = forms.FileField()
    version = forms.ChoiceField((
    ('gsb_0_5_0', 'format grisbi version 0.5.x'),
    ))
    replace = forms.ChoiceField((
    ('remplacement', 'remplacement des données par le fichier'),
    ('fusion','fusion des données avec le fichier')
    ))

class OperationForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    cat=forms.ModelChoiceField(Cat.objects.all().order_by('type'),empty_label=None)
    mere=forms.ModelChoiceField(Ope.objects.filter(mere__isnull=False).order_by('-date'))
    class Meta:
        model=Ope
    def __init__(self, *args, **kwargs):
        super (OperationForm,self).__init__(*args, **kwargs)


class GeneraliteForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model=Generalite
        fields = ('utilise_exercices','utilise_ib','utilise_pc','affiche_clot')
    def __init__(self, *args, **kwargs):
        super (GeneraliteForm,self).__init__(*args, **kwargs)
