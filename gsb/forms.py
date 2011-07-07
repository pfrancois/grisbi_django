# -*- coding: utf-8
from django import forms
from mysite.gsb.models import *
from mysite.gsb.shortcuts import *
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

class OperationForm(BaseForm):
    compte=forms.ModelChoiceField(Compte.objects.all(),empty_label=None)
    cat=forms.ModelChoiceField(Cat.objects.all().order_by('type'),required=False)
    montant=forms.DecimalField(localize=True,initial='0')
    date=forms.DateField(input_formats=('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y','%d%m%y','%d%m%Y'),initial=datetime.date.today)
    #pointe=forms.BooleanField(required=False)
    moyen=forms.ModelChoiceField(Moyen.objects.all(),required=False)
    class Meta:
        model=Ope
        exclude=('mere','jumelle')



class VirementForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'
    compte_origine=forms.ModelChoiceField(Compte.objects.all(),empty_label=None)
    moyen_origine=forms.ModelChoiceField(Moyen.objects.all(),required=False)
    compte_destination=forms.ModelChoiceField(Compte.objects.all(),empty_label=None)
    moyen_destination=forms.ModelChoiceField(Moyen.objects.all(),required=False)
    montant=forms.DecimalField(localize=True,initial='0')
    date=forms.DateField(input_formats=('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y','%d%m%y','%d%m%Y'),initial=datetime.date.today)
    note=forms.CharField(widget=forms.Textarea,required=False)
    pointe_origine=forms.BooleanField(required=False)
    rapp_origine=forms.ModelChoiceField(Rapp.objects.all(),required=False)
    pointe_destination=forms.BooleanField(required=False)
    rapp_destination=forms.ModelChoiceField(Rapp.objects.all(),required=False)
    piece_comptable=forms.CharField(required=False)
    def clean(self):
        data=self.cleaned_data
        if data.get("compte_origine") == data.get("compte_origine"):
            msg="pas possible de faire un virement vers le meme compte"
            self._errors['compte_origine']=self.error_class([msg])
            self._errors['compte_destination']=self.error_class([msg])
            del data['compte_origine']
            del data['compte_destination']
        return data
    def save(self):
        v=Virement()
        v.create(self.cleaned_data['compte_origine'],self.cleaned_data['compte_destination'],self.cleaned_data['montant'],self.cleaned_data['date'],self.cleaned_data['notes'])
        v.origine.moyen=self.cleaned_data['moyen_origine']
        v.dest.moyen=self.cleaned_data['moyen_destination']
        v.orgine.pointe=self.cleaned_data['pointe_origine']
        v.dest.pointe=self.cleaned_data['pointe_destination']
        v.orgine.rapp=self.cleaned_data['rapp_origine']
        v.dest.rapp=self.cleaned_data['rapp_destination']
        v.save()
        return v.origine

class GeneraliteForm(BaseForm):
    class Meta:
        model=Generalite
        fields = ('utilise_exercices','utilise_ib','utilise_pc','affiche_clot')
    def __init__(self, *args, **kwargs):
        super (GeneraliteForm,self).__init__(*args, **kwargs)
