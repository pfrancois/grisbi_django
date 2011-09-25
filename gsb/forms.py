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


input_format_date = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y')
error_css_class = 'error'
required_css_class = 'required'

class Dategsbwidget(forms.DateInput):
    class Media:
        js = ("js/basiccalendar.js",)
        css = {'all':('css/calendar.css',)}

    def __init__(self, attrs = None): #@UnusedVariable
        super(Dategsbwidget, self).__init__(attrs)
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

class DateFieldgsb(forms.DateField):
    def __init__(self, input_formats = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y'), initial = datetime.date.today, *args, **kwargs):
        super(DateFieldgsb, self).__init__(input_formats = input_formats, initial = initial, widget = Dategsbwidget, *args, **kwargs)
class Readonlywidget(forms.Widget):
    text = ''
    is_hidden = False

    def render(self, name, value, attrs = None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type = 'hidden', name = name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(value)
        hidden = u'<input%s />' % flatatt(final_attrs)
        text = force_unicode(self.text)
        return mark_safe("<div>%s%s</div>" % (hidden, text))
    def _has_changed(self, initial, data):
        return False

class ReadonlyField(forms.FileField):
    widget = Readonlywidget
    def __init__(self, model = None, *args, **kwargs): #@UnusedVariable
        self.model = model
        forms.Field.__init__(self, *args, **kwargs)
    def clean(self, value, initial):
        if self.instance and self.instance.id:
            return getattr(self.instance, self.model)

    def set_text(self, instance):
        if instance and instance.id:
            self.instance = instance
            t = getattr(instance, self.model)
            self.widget.text = t.__unicode__()

class Curwidget(forms.TextInput):
    def render(self, name, value, attrs = None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type = 'text', name = name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(value)
        hidden = u'<input%s />' % flatatt(final_attrs)
        text = force_unicode("&#8364;")
        return mark_safe("<div>%s%s</div>" % (hidden, text))

class CurField(forms.DecimalField):
    def __init__(self, localize = True, initial = '0', widget = Curwidget, *args, **kwargs):
        super(CurField, self).__init__(localize = localize, initial = initial, widget = widget, *args, **kwargs)

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
    cat = forms.ModelChoiceField(Cat.objects.all().order_by('type', 'nom'), empty_label = None)
    ib = forms.ModelChoiceField(Ib.objects.all().order_by('type', 'nom'), required = False)
    montant = CurField()
    notes = forms.CharField(widget = forms.TextInput, required = False)
    date = DateFieldgsb()
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
        if data['tiers'] == None:
            if not data['nouveau_tiers']:
                self._errors['nouveau_tiers'] = self.error_class(["si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau", ])
                del data['nouveau_tiers']                    
        if data['moyen'].type == u'd' and data['montant'] > 0:
            data['montant'] = data['montant']* -1
        return data

class VirementForm(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    compte_origine = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    moyen_origine = forms.ModelChoiceField(Moyen.objects.all(), required = False)
    compte_destination = forms.ModelChoiceField(Compte.objects.all(), empty_label = None)
    moyen_destination = forms.ModelChoiceField(Moyen.objects.all(), required = False)
    montant = CurField()
    date = DateFieldgsb()
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
            self._errors['compte_origine'] = self.error_class([msg, ])
            self._errors['compte_destination'] = self.error_class([msg, ])
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

class Ope_titre_addForm(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    date = DateFieldgsb()
    titre = forms.ModelChoiceField(Titre.objects.all(), required = False)
    compte_titre = forms.ModelChoiceField(Compte_titre.objects.all(), empty_label = None)
    compte_espece = forms.ModelChoiceField(Compte.objects.filter(type__in = ('b', 'e', 'p')), required = False)
    nombre = forms.DecimalField(initial = '0')
    cours = CurField(initial = '1')
    #nom_nouveau_titre = forms.CharField(required = False)
    def clean(self):
        super(Ope_titre_addForm, self).clean()
        if self.cleaned_data['nombre'] == 0:
            self._errors['nombre'] = self.error_class([u'le nombre ne peut être nul', ])
            del self.cleaned_data['nombre']
        return self.cleaned_data
class Ope_titre_add_achatForm(Ope_titre_addForm):
    nouveau_titre = forms.CharField(required = False)
    nouvel_isin = forms.CharField(required = False)
    def clean(self):
        super(Ope_titre_add_achatForm, self).clean()
        data = self.cleaned_data
        if data['titre'] == None:
            if not data['nouveau_titre']:
                self._errors['nouveau_titre'] = self.error_class(["si vous ne choisissez pas un titre, vous devez taper le nom du nouveau", ])
                del data['nouveau_titre']                    
        return data
    
class Ope_titre_add_venteForm(Ope_titre_addForm):
    def __init__(self, *args, **kwargs):
        super(Ope_titre_add_venteForm, self).__init__()
        self.fields['titre'].empty_label = None
        self.fields['titre'].required = True
    def clean(self):
        super(Ope_titre_add_venteForm, self).clean()
        data = self.cleaned_data
        if not Ope_titre.nb(titre = data['titre'], compte = data['compte_titre']):
            msg = u"titre pas en portefeuille"
            self._errors['titre'] = self.error_class([msg, ])
            del data['titre']
        return data

class Ope_titreForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(Ope_titreForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['titre'].set_text(instance)
        self.fields['compte'].set_text(instance)

    titre = ReadonlyField('titre')
    compte = ReadonlyField('compte')
    nombre = forms.DecimalField(localize = True, initial = '0')
    cours = CurField(initial = '0')
    date = DateFieldgsb()
    error_css_class = error_css_class
    required_css_class = required_css_class
    class Meta:
        model = Ope_titre

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
    date = DateFieldgsb()
    cours = CurField(initial = '0')

