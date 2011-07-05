# -*- coding: utf-8
from django import forms
from mysite.gsb.models import *
from mysite.gsb import widgets
import datetime
import decimal

class ImportForm(forms.Form):
    nom_du_fichier = forms.FileField()
    version = forms.ChoiceField((
    ('gsb_0_5_0', 'format grisbi version 0.5.x'),
    ))
    replace = forms.ChoiceField((
    ('remplacement', 'remplacement des données par le fichier'),
    ('fusion','fusion des données avec le fichier')
    ))

class BaseForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
from django.core.exceptions import ValidationError
def pointe_et_rapproche(value):
    pass
class OperationForm(BaseForm):
    compte=forms.ModelChoiceField(Compte.objects.all(),empty_label=None)
    cat=forms.ModelChoiceField(Cat.objects.all().order_by('type'),required=False)
    montant=forms.DecimalField(localize=True,initial='0')
    date=forms.DateField(input_formats=('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y','%d%m%y','%d%m%Y'),initial=datetime.date.today)
    pointe=forms.BooleanField(required=False)
    #TODO mettre le moyen de depense par defaut
    mere=forms.ModelChoiceField(Ope.objects.filter(mere__isnull=False).order_by('-date'),required=False)
    class Meta:
        model=Ope
    def clean(self):
        #super(BaseForm,self).clean()
        #verification qu'il n'y ni poitee ni rapprochee
        pointe=self.cleaned_data['pointe']
        rap=self.cleaned_data['rapp']
        if pointe and rap:
            msg=u"cette operation ne peut pas etre a la fois pointée et rapprochée"
            self._errors['pointe']=self.error_class([msg])
            self._errors['rapp']=self.error_class([msg])
            del self.cleaned_data['pointe']
            del self.cleaned_data['rapp']
        return self.cleaned_data

class VirementForm(BaseForm):
    cat=forms.ModelChoiceField(Cat.objects.none())
    class Meta:
        model=Ope

class GeneraliteForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model=Generalite
        fields = ('utilise_exercices','utilise_ib','utilise_pc','affiche_clot')
    def __init__(self, *args, **kwargs):
        super (GeneraliteForm,self).__init__(*args, **kwargs)
