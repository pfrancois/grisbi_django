# -*- coding: utf-8
from django import forms
from mysite.gsb.models import Compte, Cat, Moyen, Ope, Virement, Generalite, Compte_titre, Cours, Titre, Tiers, Ope_titre
#from mysite.gsb import widgets
from django.conf import settings
import datetime
#import decimal
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import flatatt


input_format_date = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y')
error_css_class = 'error'
required_css_class = 'required'

class dateinputgsb(forms.DateInput):
    class Media:
        js = ("js/basiccalendar.js",)
        css = {'all':('css/calendar.css',)}

    def __init__(self, attrs = {}, format = None): #@UnusedVariable
        super(dateinputgsb, self).__init__(attrs = {'class': 'vDateField', 'size': '10'}, format = format)
    def render(self, name, value, attrs = None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type = self.input_type, name = name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))
            
            auj = '<a href="javascript:shct_date(0,\'%s\')" title="aujourd\'hui">AUJ</a>' % final_attrs['id']
            hier = '<a href="javascript:shct_date(-1,\'%s\')" title="hier">HIER</a>' % final_attrs['id']
            cal = '<a href="javascript:editDate(\'%s\');" title="calendrier"><img src="%s" alt="calendrier"/></a>' % (final_attrs['id'], settings.STATIC_URL + "img/calendar.png")
        return mark_safe(u'<input%s /><span>|%s|%s|%s</span><div class="editDate ope_date_ope" id="editDateId"></div>' % (flatatt(final_attrs), hier, auj, cal))

class datefieldgsb(forms.DateField):
    def __init__(self, input_formats = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y'), initial = datetime.date.today, *args, **kwargs):  
        super(datefieldgsb, self).__init__(input_formats = input_formats, initial = initial, widget = dateinputgsb, *args, **kwargs)

    
class ImportForm(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    nom_du_fichier = forms.FileField()
    version = forms.ChoiceField((
    ('gsb_0_5_0', 'format grisbi version 0.5.x'),
    ))
    replace = forms.ChoiceField((
    ('remplacement', 'remplacement des données par le fichier'),
    ('fusion', 'fusion des données avec le fichier')
    ))

class OperationForm(forms.ModelForm):
    error_css_class = error_css_class
    required_css_class = required_css_class
    tiers = forms.ModelChoiceField(Tiers.objects.all(), required = False)
    compte = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    cat = forms.ModelChoiceField(Cat.objects.all().order_by('type', 'nom'), required = False)
    montant = forms.DecimalField(localize = True, initial = '0')
    notes = forms.CharField(widget = forms.TextInput, required = False)
    date = datefieldgsb()
    #pointe=forms.BooleanField(required=False)
    moyen = forms.ModelChoiceField(Moyen.objects.all(), required = False)
    class Meta:
        model = Ope
        exclude = ('mere', 'jumelle')
    def clean(self):
        super(OperationForm, self).clean()        
        if self.cleaned_data['moyen'].type == u'd' and self.cleaned_data['montant'] > 0:
            self.cleaned_data['montant'] = self.cleaned_data['montant']* -1
        return self.cleaned_data

class VirementForm(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    compte_origine = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    moyen_origine = forms.ModelChoiceField(Moyen.objects.all(), required = False)
    compte_destination = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    moyen_destination = forms.ModelChoiceField(Moyen.objects.all(), required = False)
    montant = forms.DecimalField(localize = True, initial = '0')
    date = datefieldgsb()
    notes = forms.CharField(widget = forms.Textarea, required = False)
    pointe = forms.BooleanField(required = False)
    #rapp_origine = forms.CharField(widget=forms.HiddenInput, required=False)#TODO
    #rapp_destination = forms.CharField(widget=forms.HiddenInput, required=False)#TODO
    piece_comptable_compte_origine = forms.CharField(required = False)
    piece_comptable_compte_destination = forms.CharField(required = False)
    def clean(self):
        super(VirementForm, self).clean()
        data = self.cleaned_data
        if data.get("compte_origine") == data.get("compte_destination"):
            msg = "pas possible de faire un virement vers le meme compte"
            self._errors['compte_origine'] = self.error_class([msg])
            self._errors['compte_destination'] = self.error_class([msg])
            del data['compte_origine']
            del data['compte_destination']
        return data
    def __init__(self, ope = None, *args, **kwargs):
        self.ope = ope
        if ope:
            v = Virement(ope)
            super(VirementForm, self).__init__(initial = v.init_form(), *args, **kwargs)
        else:
            super(VirementForm, self).__init__(*args, **kwargs)
    def save(self):
        if self.ope == None:
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

class Ope_titreForm(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    date = datefieldgsb()
    titre = forms.ModelChoiceField(Titre.objects.all())
    compte_titre = forms.ModelChoiceField(Compte_titre.objects.all(), empty_label = None)
    compte_espece = forms.ModelChoiceField(Compte.objects.filter(type__in = ('b', 'e', 'p')), required = False)
    nombre = forms.DecimalField(localize = True, initial = '0')
    cours = forms.DecimalField(localize = True, initial = '0')
    achat = forms.BooleanField(widget = forms.HiddenInput(), initial = True)
    #nom_nouveau_titre=forms.CharField(required=False)
    
class GeneraliteForm(forms.ModelForm):
    error_css_class = error_css_class
    required_css_class = required_css_class
    class Meta:
        model = Generalite
        fields = ('utilise_exercices', 'utilise_ib', 'utilise_pc', 'affiche_clot')
    def __init__(self, *args, **kwargs):
        super (GeneraliteForm, self).__init__(*args, **kwargs)
        
class MajCoursform(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    titre = forms.ModelChoiceField(Titre.objects.all(), empty_label = None)
    date = datefieldgsb()
    cours = forms.DecimalField(min_value = 0, label = "Cours")

