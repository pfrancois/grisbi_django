# -*- coding: utf-8
from django import forms
from mysite.gsb.models import Compte, Cat, Moyen, Ope, Virement, Rapp, Generalite 
#from mysite.gsb import widgets
import datetime
#import decimal

class ImportForm(forms.Form):
    nom_du_fichier = forms.FileField()
    version = forms.ChoiceField((
    ('gsb_0_5_0', 'format grisbi version 0.5.x'),
    ))
    replace = forms.ChoiceField((
    ('remplacement', 'remplacement des données par le fichier'),
    ('fusion', 'fusion des données avec le fichier')
    ))

class BaseForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

class OperationForm(BaseForm):
    compte = forms.ModelChoiceField(Compte.objects.all(), empty_label=None)
    cat = forms.ModelChoiceField(Cat.objects.all().order_by('type'), required=False)
    montant = forms.DecimalField(localize=True, initial='0')
    date = forms.DateField(input_formats=('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y'), initial=datetime.date.today)
    #pointe=forms.BooleanField(required=False)
    moyen = forms.ModelChoiceField(Moyen.objects.all(), required=False)
    class Meta:
        model = Ope
        exclude = ('mere', 'jumelle')

class VirementForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'
    compte_origine = forms.ModelChoiceField(Compte.objects.all(), empty_label=None)
    moyen_origine = forms.ModelChoiceField(Moyen.objects.all(), required=False)
    compte_destination = forms.ModelChoiceField(Compte.objects.all(), empty_label=None)
    moyen_destination = forms.ModelChoiceField(Moyen.objects.all(), required=False)
    montant = forms.DecimalField(localize=True, initial='0')
    date = forms.DateField(input_formats=('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y'), initial=datetime.date.today)
    notes = forms.CharField(widget=forms.Textarea, required=False)
    pointe = forms.BooleanField(required=False)
    rapp_origine = forms.CharField(widget=forms.HiddenInput, required=False)
    rapp_destination = forms.CharField(widget=forms.HiddenInput, required=False)
    piece_comptable_compte_origine = forms.CharField(required=False)
    piece_comptable_compte_destination = forms.CharField(required=False)
    def clean(self):
        data = self.cleaned_data
        if data.get("compte_origine") == data.get("compte_destination"):
            msg = "pas possible de faire un virement vers le meme compte"
            self._errors['compte_origine'] = self.error_class([msg])
            self._errors['compte_destination'] = self.error_class([msg])
            del data['compte_origine']
            del data['compte_destination']
        return data
    def save(self):
        v = Virement()
        v.create(self.cleaned_data['compte_origine'], self.cleaned_data['compte_destination'], self.cleaned_data['montant'], self.cleaned_data['date'], self.cleaned_data['notes'])
        v.origine.moyen = self.cleaned_data['moyen_origine']
        v.dest.moyen = self.cleaned_data['moyen_destination']
        v.pointe = self.cleaned_data['pointe']
        v.origine.rapp = Rapp.objects.get(id=self.cleaned_data['rapp_origine'])
        v.dest.rapp = Rapp.objects.get(id=self.cleaned_data['rapp_destination'])
        v.origine.piece_comptable = self.cleaned_data['piece_comptable_compte_origine']
        v.dest.piece_comptable = self.cleaned_data['piece_comptable_compte_destination']
        v.save()
        return v.origine

class GeneraliteForm(BaseForm):
    class Meta:
        model = Generalite
        fields = ('utilise_exercices', 'utilise_ib', 'utilise_pc', 'affiche_clot')
    def __init__(self, *args, **kwargs):
        super (GeneraliteForm, self).__init__(*args, **kwargs)
