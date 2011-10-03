# -*- coding: utf-8
from django import forms

from mysite.gsb.models import (Compte, Cat, Moyen, Ope, Virement, Generalite,
    Compte_titre, Titre, Tiers, Ope_titre, Ib, Rapp)
import mysite.gsb.widgets as gsb_field 


#import decimal
error_css_class = 'error'
required_css_class = 'required'

class Baseform(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class

class Basemodelform(forms.ModelForm):
    error_css_class = error_css_class
    required_css_class = required_css_class

class ImportForm(Baseform):
    nom_du_fichier = forms.FileField()
    version = forms.ChoiceField((
    ('gsb_0_5_0', 'format grisbi version 0.5.x'),
    ))
    replace = forms.ChoiceField((
    ('remplacement', 'remplacement des données par le fichier'),
    ('fusion', 'fusion des données avec le fichier')
    ))

class OperationForm(Basemodelform):
    tiers = forms.ModelChoiceField(Tiers.objects.all(), required = False)
    compte = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    cat = forms.ModelChoiceField(Cat.objects.all().order_by('type', 'nom'), empty_label = None)
    ib = forms.ModelChoiceField(Ib.objects.all().order_by('type', 'nom'), required = False)
    montant = gsb_field.CurField()
    notes = forms.CharField(widget = forms.TextInput, required = False)
    date = gsb_field.DateFieldgsb()
    moyen = forms.ModelChoiceField(Moyen.objects.all().order_by('type'), required = False)
    pointe = forms.BooleanField(required = False)
    rapp = forms.ModelChoiceField(Rapp.objects.all(), required = False)
    nouveau_tiers = forms.CharField(required = False)
    class Meta:
        model = Ope
        exclude = ('mere', 'jumelle')
    def clean(self):
        super(OperationForm, self).clean()
        data = self.cleaned_data
        if data['tiers'] is None:
            if not data['nouveau_tiers']:
                self._errors['tiers'] = self.error_class(["si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau dans le champs 'nouveau tiers'", ])
                self._errors['nouveau_tiers'] = self.error_class(["si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau", ])
                del data['nouveau_tiers']
        if data['moyen'].type == u'd' and data['montant'] > 0:
            data['montant'] = -1 * data['montant']
        return data

class VirementForm(Baseform):
    compte_origine = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    moyen_origine = forms.ModelChoiceField(Moyen.objects.all(), required = False)
    compte_destination = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    moyen_destination = forms.ModelChoiceField(Moyen.objects.all(), required = False)
    montant = gsb_field.CurField()
    date = gsb_field.DateFieldgsb()
    notes = forms.CharField(widget = forms.Textarea, required = False)
    pointe = forms.BooleanField(required = False)
    #rapp_origine = forms.CharField(widget=forms.HiddenInput, required=False)
    #rapp_destination = forms.CharField(widget=forms.HiddenInput, required=False)
    piece_comptable_compte_origine = forms.CharField(required = False)
    piece_comptable_compte_destination = forms.CharField(required = False)
    def clean(self):
        super(VirementForm, self).clean()
        data = self.cleaned_data
        if data.get("compte_origine") == data.get("compte_destination"):
            msg = "pas possible de faire un virement vers le meme compte"
            self._errors['compte_origine'] = self.error_class([msg, ])
            self._errors['compte_destination'] = self.error_class([msg, ])
            del data['compte_origine']
            del data['compte_destination']
        return data
    def __init__(self, ope = None, *args, **kwargs):
        self.ope = ope
        if ope:
            vir = Virement(ope)
            super(VirementForm, self).__init__(initial = vir.init_form(), *args, **kwargs)
        else:
            super(VirementForm, self).__init__(*args, **kwargs)
    def save(self):
        if self.ope is None:
            virement_objet = Virement.create(self.cleaned_data['compte_origine'], self.cleaned_data['compte_destination'], self.cleaned_data['montant'], self.cleaned_data['date'], self.cleaned_data['notes'])
        else:
            virement_objet = Virement(self.ope)
        virement_objet.origine.moyen = self.cleaned_data['moyen_origine']
        virement_objet.dest.moyen = self.cleaned_data['moyen_destination']
        virement_objet.pointe = self.cleaned_data['pointe']
        #virement_objet.origine.rapp = Rapp.objects.get(id=self.cleaned_data['rapp_origine'])
        #virement_objet.dest.rapp = Rapp.objects.get(id=self.cleaned_data['rapp_destination'])
        virement_objet.origine.piece_comptable = self.cleaned_data['piece_comptable_compte_origine']
        virement_objet.dest.piece_comptable = self.cleaned_data['piece_comptable_compte_destination']
        virement_objet.save()
        return virement_objet.origine

class Ope_titre_addForm(Baseform):
    date = gsb_field.DateFieldgsb()
    titre = forms.ModelChoiceField(Titre.objects.all(), required = False)
    compte_titre = forms.ModelChoiceField(Compte_titre.objects.all(), empty_label = None)
    compte_espece = forms.ModelChoiceField(Compte.objects.filter(type__in = ('b', 'e', 'p')), required = False)
    nombre = forms.DecimalField(initial = '0')
    cours = gsb_field.CurField(initial = '1')
    #nom_nouveau_titre = forms.CharField(required = False)
    def clean(self):
        super(Ope_titre_addForm, self).clean()
        if not self.cleaned_data['nombre']:
            self._errors['nombre'] = self.error_class([u'le nombre ne peut être nul', ])
            del self.cleaned_data['nombre']
        return self.cleaned_data

class Ope_titre_add_achatForm(Ope_titre_addForm):
    nouveau_titre = forms.CharField(required = False)
    nouvel_isin = forms.CharField(required = False)
    def clean(self):
        super(Ope_titre_add_achatForm, self).clean()
        data = self.cleaned_data
        if not(not(data['titre'] is None) or data['nouveau_titre']):
            self._errors['nouveau_titre'] = self.error_class(["si vous ne choisissez pas un titre, vous devez taper le nom du nouveau", ])
            del data['nouveau_titre']
        return data

class Ope_titre_add_venteForm(Ope_titre_addForm):
    def __init__(self, cpt = None, *args, **kwargs):
        super(Ope_titre_add_venteForm, self).__init__(*args, **kwargs)
        self.fields['titre'].empty_label = None
        self.fields['titre'].required = True
        if cpt and isinstance(cpt, Compte_titre):
            self.fields['titre'].queryset = cpt.liste_titre()
    def clean(self):
        super(Ope_titre_add_venteForm, self).clean()
        data = self.cleaned_data
        if not Ope_titre.nb(titre = data['titre'], compte = data['compte_titre']):
            msg = u"titre pas en portefeuille"
            self._errors['titre'] = self.error_class([msg, ])
            del data['titre']
        return data

class Ope_titreForm(Basemodelform):
    def __init__(self, *args, **kwargs):
        super(Ope_titreForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['titre'] = gsb_field.ReadonlyField(instance, 'titre')
        self.fields['compte'] = gsb_field.ReadonlyField(instance, 'compte')
    nombre = forms.DecimalField(localize = True, initial = '0')
    cours = gsb_field.CurField()
    date = gsb_field.DateFieldgsb()
    class Meta:
        model = Ope_titre

class GeneraliteForm(Basemodelform):
    class Meta:
        model = Generalite
        fields = ('utilise_exercices', 'utilise_ib', 'utilise_pc', 'affiche_clot')
    def __init__(self, *args, **kwargs):
        super (GeneraliteForm, self).__init__(*args, **kwargs)

class MajCoursform(Baseform):
    titre = forms.ModelChoiceField(Titre.objects.all(), empty_label = None)
    date = gsb_field.DateFieldgsb()
    cours = gsb_field.CurField()


class Majtitre(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    date = gsb_field.DateFieldgsb()
    def __init__(self, titres, *args, **kwargs):
        super (Majtitre, self).__init__(*args, **kwargs)
        for titre in titres:
            self.fields[titre.isin] = gsb_field.TitreField(label = titre.nom)
