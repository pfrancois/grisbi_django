# -*- coding: utf-8
from __future__ import absolute_import

from django import forms
from django.utils.safestring import mark_safe

from .models import (Compte, Cat, Moyen, Ope, Virement, Titre, Tiers, Ope_titre, Ib, Rapp)
from . import widgets as gsb_field



# import decimal
ERROR_CSS_CLASS = ''
REQUIRED_CSS_CLASS = 'required'


class Baseform(forms.Form):
    # error_css_class = ERROR_CSS_CLASS
    required_css_class = REQUIRED_CSS_CLASS


class Basemodelform(forms.ModelForm):
    # error_css_class = ERROR_CSS_CLASS
    required_css_class = REQUIRED_CSS_CLASS


class OperationForm(Basemodelform):
    tiers = forms.ModelChoiceField(Tiers.objects.all(), required=False)
    compte = forms.ModelChoiceField(Compte.objects.filter(ouvert=True), empty_label=None)
    cat = forms.ModelChoiceField(Cat.objects.all().order_by('type', 'nom'), empty_label=None, required=True)
    ib = forms.ModelChoiceField(Ib.objects.all().order_by('type', 'nom'), required=False)
    montant = gsb_field.CurField()
    notes = forms.CharField(widget=forms.TextInput, required=False)
    date = gsb_field.DateFieldgsb()
    moyen = forms.ModelChoiceField(Moyen.objects.all().order_by('type'), empty_label=None, required=True)
    pointe = forms.BooleanField(required=False)
    rapp = forms.ModelChoiceField(Rapp.objects.all(), required=False)
    nouveau_tiers = forms.CharField(required=False)

    class Meta(object):
        model = Ope
        exclude = ('jumelle', 'mere', 'date_val')  # car sinon c'est un virement

    def __init__(self, *args, **kwargs):
        super(OperationForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['operation_mere'] = gsb_field.ReadonlyField(instance, 'mere', required=False)

    def clean(self):
        data = super(OperationForm, self).clean()
        if data['tiers'] is None:
            if data['nouveau_tiers'] == "":
                self._errors['tiers'] = self.error_class(
                    ["si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau dans le champs 'nouveau tiers'", ])
                self._errors['nouveau_tiers'] = self.error_class(
                    ["si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau", ])
                del data['nouveau_tiers']
        if 'moyen' in data.keys() and data['moyen'].type == u'd' and data['montant'] > 0:
            data['montant'] *= -1
        return data


class VirementForm(Baseform):
    date = gsb_field.DateFieldgsb()
    compte_origine = forms.ModelChoiceField(Compte.objects.filter(ouvert=True), empty_label=None)
    moyen_origine = forms.ModelChoiceField(Moyen.objects.all(), required=False)
    compte_destination = forms.ModelChoiceField(Compte.objects.filter(ouvert=True), empty_label=None)
    moyen_destination = forms.ModelChoiceField(Moyen.objects.all(), required=False)
    montant = gsb_field.CurField()
    notes = forms.CharField(widget=forms.Textarea, required=False)
    pointe = forms.BooleanField(required=False)

    def clean(self):
        super(VirementForm, self).clean()
        data = self.cleaned_data
        if data.get("compte_origine") == data.get("compte_destination"):
            msg = u"pas possible de faire un virement vers le même compte"
            self._errors['compte_origine'] = self.error_class([msg, ])
            self._errors['compte_destination'] = self.error_class([msg, ])
            del data['compte_origine']
            del data['compte_destination']
        return data

    # noinspection PyArgumentList
    def __init__(self, ope=None, *args, **kwargs):
        self.ope = ope
        if ope:
            vir = Virement(ope)
            super(VirementForm, self).__init__(initial=vir.init_form(), *args, **kwargs)
        else:
            super(VirementForm, self).__init__(*args, **kwargs)
        self.fields['rapp_origine'] = gsb_field.ReadonlyField(ope, 'rapp', required=False,
                                                              label=mark_safe(u"rapproché dans <br/> cpt origine"))
        if ope:
            self.fields['rapp_destination'] = gsb_field.ReadonlyField(ope.jumelle, 'rapp', required=False,
                                                                      label=mark_safe(u"rapproché dans <br/> cpt destination"))
        else:
            self.fields['rapp_destination'] = gsb_field.ReadonlyField(ope, 'rapp', required=False,
                                                                      label=mark_safe(u"rapproché dans <br/> cpt destination"))

    def save(self):
        if self.ope is None:
            virement_objet = Virement.create(self.cleaned_data['compte_origine'],
                                             self.cleaned_data['compte_destination'],
                                             self.cleaned_data['montant'],
                                             self.cleaned_data['date'],
                                             self.cleaned_data['notes']
                                            )
        else:
            virement_objet = Virement(self.ope)
        virement_objet.origine.moyen = self.cleaned_data['moyen_origine']
        virement_objet.dest.moyen = self.cleaned_data['moyen_destination']
        virement_objet.pointe = self.cleaned_data['pointe']
        virement_objet.origine.compte = self.cleaned_data['compte_origine']
        virement_objet.dest.compte = self.cleaned_data['compte_destination']
        virement_objet.montant = self.cleaned_data['montant']
        virement_objet.notes = self.cleaned_data['notes']
        virement_objet.date = self.cleaned_data['date']
        # virement_objet.origine.piece_comptable = self.cleaned_data['piece_comptable_compte_origine']
        # virement_objet.dest.piece_comptable = self.cleaned_data['piece_comptable_compte_destination']
        virement_objet.save()
        return virement_objet.origine


class Ope_titre_addForm(Baseform):
    date = gsb_field.DateFieldgsb()
    titre = forms.ModelChoiceField(Titre.objects.all(), required=False)
    compte_titre = forms.ModelChoiceField(Compte.objects.filter(type='t', ouvert=True), empty_label=None, required=True)
    compte_espece = forms.ModelChoiceField(Compte.objects.filter(type__in=('b', 'e', 'p')).filter(ouvert=True), required=False)
    nombre = forms.DecimalField(localize=True, required=True)
    cours = forms.DecimalField(initial='1', required=True, localize=True, min_value=0)
    frais = forms.DecimalField(initial='0', required=False, localize=True)

    class Meta(object):
        widgets = {
            'my_decimal_field': forms.TextInput(attrs={'localization': True}),
        }

    def clean(self):
        super(Ope_titre_addForm, self).clean()
        if 'nombre' in self.cleaned_data and self.cleaned_data['nombre'] == 0:
            self._errors['nombre'] = self.error_class([u'le nombre de titre ne peut être nul', ])
            del self.cleaned_data['nombre']
        if self.cleaned_data['frais'] > 0:
            self.cleaned_data['frais'] *= -1
        return self.cleaned_data


class Ope_titre_dividendeForm(Baseform):
    date = gsb_field.DateFieldgsb(localize=True)
    titre = forms.ModelChoiceField(Titre.objects.all(), required=False)
    compte_titre = forms.ModelChoiceField(Compte.objects.filter(type='t', ouvert=True), empty_label=None, required=True)
    compte_espece = forms.ModelChoiceField(Compte.objects.filter(type__in=('b', 'e', 'p')).filter(ouvert=True), required=False)
    montant = forms.DecimalField(localize=True, initial='0', required=True, min_value=0)

    def __init__(self, cpt=None, *args, **kwargs):
        super(Ope_titre_dividendeForm, self).__init__(*args, **kwargs)
        self.cpt = cpt
        self.fields['titre'].empty_label = None
        self.fields['titre'].required = True
        if cpt and cpt.type == 't':
            self.fields['titre'].queryset = cpt.liste_titre()
        else:
            self.cpt = None


class Ope_titre_add_achatForm(Ope_titre_addForm):
    nouveau_titre = forms.CharField(required=False)
    nouvel_isin = forms.CharField(required=False)

    def clean(self):
        super(Ope_titre_add_achatForm, self).clean()
        data = self.cleaned_data
        # on verifie qu'il y a soit un nouveau titre soit qu'un titre a été tapé
        if data.get('titre', None) is None and data.get('nouveau_titre') == "":
            self._errors['nouveau_titre'] = self.error_class([u"si vous ne choisissez pas un titre, vous devez taper le nom du nouveau", ])
            del data['nouveau_titre']
        if data.get('nouveau_titre', None) == "" and data.get('nouveau_isin', None) != "":
            del data['nouvel_isin']
        return data


class Ope_titre_add_venteForm(Ope_titre_addForm):
    def __init__(self, cpt=None, *args, **kwargs):
        super(Ope_titre_add_venteForm, self).__init__(*args, **kwargs)
        self.fields['titre'].empty_label = None
        self.fields['titre'].required = True
        if cpt and cpt.type == 't':
            self.cpt = cpt
            self.fields['titre'].queryset = cpt.liste_titre()
        else:
            self.cpt = None

    def clean(self):
        super(Ope_titre_add_venteForm, self).clean()
        data = self.cleaned_data
        # on verifie qu'il est portfeuille
        if not data.get('titre', None) is None and data['titre'].nb(compte=data['compte_titre'], datel=data['date']) == 0:
            msg = u"titre pas en portefeuille"
            self._errors['titre'] = self.error_class([msg, ])
            del data['titre']
        if not data.get('titre', None) is None and 0 < data['titre'].nb(compte=data['compte_titre'], datel=data['date']) <= data['nombre']:
            msg = u"titre pas assez en portefeuille pour que l'opération puisse s'effectuer"
            self._errors['titre'] = self.error_class([msg, ])
            del data['titre']
        return data


class Ope_titreForm(Basemodelform):
    fields = ['titre', 'compte', 'nombre', 'date', 'cours']

    def __init__(self, *args, **kwargs):
        super(Ope_titreForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['titre'] = gsb_field.ReadonlyField(instance, 'titre')
        self.fields['compte'] = gsb_field.ReadonlyField(instance, 'compte')

    class Meta(object):
        model = Ope_titre


class MajCoursform(Baseform):
    titre = forms.ModelChoiceField(Titre.objects.all(), empty_label=None)
    date = gsb_field.DateFieldgsb()
    cours = gsb_field.CurField(localize=True)


class Majtitre(Baseform):
    date = gsb_field.DateFieldgsb()
    sociaux = forms.BooleanField(label="prélèvement sociaux ?", required=False, initial=False)

    def __init__(self, titres, *args, **kwargs):
        super(Majtitre, self).__init__(*args, **kwargs)
        for titre in titres:
            self.fields[titre.isin] = gsb_field.TitreField(label=titre.nom)
            self.fields[titre.isin].required = False


class SearchForm(Baseform):
    compte = forms.ModelChoiceField(Compte.objects.all(), required=False)
    date_min = forms.DateField(label='date_min', widget=forms.DateInput, required=False)
    date_max = forms.DateField(label='date_max', widget=forms.DateInput, required=False)


class ajout_ope_bulk_form(Baseform):
    """premier form utilise ajout_ope_titre_bulk"""
    titre = forms.ModelChoiceField(Titre.objects.all())
    cours = gsb_field.CurField()
    nombre = forms.DecimalField(localize=True)
    frais = forms.DecimalField(localize=True, required=False)


class ajout_ope_date_form(Baseform):
    """second form utilise ajout_ope_titre_bulk"""
    date = forms.DateField()
