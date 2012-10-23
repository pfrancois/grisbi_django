# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .models import Tiers, Titre, Cat, Ope, Banque, Cours, Ib, Exercice, Rapp, Moyen, Echeance, Compte_titre, Ope_titre, Compte, Virement
from django.contrib import admin
from django.contrib import messages
from django.db import models
import django.forms as forms
from django.utils.safestring import mark_safe
from django.core import urlresolvers
from django.db import IntegrityError
#from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render
#from django import forms

from django.utils.translation import ugettext_lazy as _
#from django.db.models import Q
#import decimal
from django.contrib.admin import DateFieldListFilter
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
import datetime


##-------------ici les class generiques------
class date_perso_filter(DateFieldListFilter):
    """filtre date perso
    """

    def __init__(self, field, request, params, model, model_admin, field_path):
        super(date_perso_filter, self).__init__(field, request, params, model, model_admin, field_path)
        now = timezone.now()
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)

        self.links = (
            (_('Any date'), {}),
            (_('Past 7 days'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This month'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            ('Les trois derniers mois', {
                self.lookup_kwarg_since: str(today.replace(day=1, month=today.month - 3)),
                self.lookup_kwarg_until: str(today.replace(day=1) - datetime.timedelta(days=1)),
            }),
            (_('This year'), {
                self.lookup_kwarg_since: str(today.replace(month=1, day=1)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            ('L\'an dernier', {
                self.lookup_kwarg_since: str(today.replace(day=1, year=today.year - 1, month=1)),
                self.lookup_kwarg_until: str(today.replace(day=31, month=12, year=today.year - 1)),
            }),
            )


class rapprochement_filter(SimpleListFilter):
    title = "type de rapprochement"
    parameter_name = 'rapp'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('rien', u'ni rapproché ni pointé'),
            ('p', u'pointé uniquement'),
            ('nrapp', u'non-rapproché'),
            ('rapp', u'rapproché uniquement'),
            ('pr', u'pointé ou rapproché')
            )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'p':
            return queryset.filter(pointe=True)
        if self.value() == 'rapp':
            return queryset.filter(rapp__isnull=False)
        if self.value() == 'rien':
            return queryset.filter(rapp__isnull=True, pointe=False)
        if self.value() == 'pr':
            return queryset.exclude(rapp__isnull=True, pointe=False)
        if self.value() == 'nrapp':
            return queryset.exclude(rapp__isnull=False)


def fusion(request, queryset, sens):
    """fonction générique de fusion entre 2 objets"""
    nom_module = queryset[0]._meta.module_name
    if queryset.count() != 2:
        messages.error(request,
                       u"attention, vous devez selectionner 2 %(type)s et uniquement 2, vous en avez selectionné %(n)s" % {
                           'n': queryset.count(),
                           'type': nom_module}
        )
        return
    obj_a = queryset[0]
    obj_b = queryset[1]
    if type(obj_a) != type(obj_b):
        messages.error(request, u"attention vous devez selectionner deux item du meme type")
        return
    try:
        if sens == 'ab':
            message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (
                nom_module,
                obj_a,
                obj_b)
            obj_a.fusionne(obj_b)
        else:
            message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (
                nom_module,
                obj_b,
                obj_a)
            obj_b.fusionne(obj_a)
        messages.success(request, message)
    except Exception as inst:  # TODO mieux gerer
        message = inst.__unicode__()
        messages.error(request, message)


class Modeladmin_perso(admin.ModelAdmin):
    save_on_top = True

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

    def fusionne_a_dans_b(self, request, queryset):
        fusion(request, queryset, 'ab')

    fusionne_a_dans_b.short_description = u"Fusion de 1 dans 2"

    def fusionne_b_dans_a(self, request, queryset):
        fusion(request, queryset, 'ba')

    fusionne_b_dans_a.short_description = u"Fusion de 2 dans 1"

    #from here http://djangosnippets.org/snippets/2531/
    def keepfilter(self, request, result):
    # Look at the referer for a query string '^.*\?.*$'
        ref = request.META.get('HTTP_REFERER', '')
        if ref.find('?') != -1:
            # We've got a query string, set the session value
            request.session['filtered'] = ref
        if request.POST.has_key('_save'):
            try:
                if request.session['filtered'] is not None:
                    result['Location'] = request.session['filtered']
                    request.session['filtered'] = None
            except KeyError:
                pass
        return result

    def add_view(self, request, *args, **kwargs):
        result = super(Modeladmin_perso, self).add_view(request, *args, **kwargs)
        return self.keepfilter(request, result)

    def change_view(self, request, *args, **kwargs):
        """
        save the referer of the page to return to the filtered
        change_list after saving the page
        """
        result = super(Modeladmin_perso, self).change_view(request, *args, **kwargs)
        return self.keepfilter(request, result)

    def delete_view(self, request, object_id, extra_context=None):
        result = super(Modeladmin_perso, self).delete_view(request, object_id, extra_context)
        return self.keepfilter(request, result)


class liste_perso_inline(admin.TabularInline):
    can_delete = False
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput, },
    }
    related = None
    readonly = False

    def __init__(self, parent_model, admin_site):
        if self.readonly:
            self.readonly_fields = self.fields
            self.can_delete = False
        super(liste_perso_inline, self).__init__(parent_model, admin_site)

    def queryset(self, request):
        if self.related is not None:
            args = self.related
            qs = super(liste_perso_inline, self).queryset(request)
            return qs.select_related(*args)
        else:
            return super(liste_perso_inline, self).queryset(request).select_related()


##------------defintiion des classes
class ope_cat_admin(liste_perso_inline):
    model = Ope
    fields = ('date', 'compte', 'montant', 'tiers', 'ib', 'notes')
    readonly = True
    fk_name = 'cat'
    related = ('compte', 'tiers', 'ib')


class Cat_admin(Modeladmin_perso):
    """classe admin pour les categories"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_editable = ('nom', )
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id', )
    list_filter = ('type', )
    radio_fields = {'type': admin.VERTICAL}
    list_select_related = True
    inlines = [ope_cat_admin]

    def queryset(self, request):
        qs = super(Cat_admin, self).queryset(request)
        return qs.select_related('ope')


class Ib_admin(Modeladmin_perso):
    """admin pour les ib"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_editable = ('nom', )
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id', )
    list_filter = ('type', )
    radio_fields = {'type': admin.VERTICAL}


class Compte_admin(Modeladmin_perso):
    """admin pour les comptes normaux"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a',
               'action_supprimer_pointe', 'action_transformer_pointee_rapp',
               'action_ajustement_cb']
    fields = (
        'nom', 'type', 'ouvert', 'banque', 'guichet', 'num_compte', 'cle_compte', 'solde_init', 'solde_mini_voulu',
        'solde_mini_autorise', 'moyen_debit_defaut', 'moyen_credit_defaut')
    list_display = ('nom', 'type', 'ouvert', 'solde', 'solde_rappro', 'date_rappro', 'nb_ope')
    list_filter = ('type', 'banque', 'ouvert')

    def action_supprimer_pointe(self, request, queryset):
        liste_id = queryset.values_list('id', flat=True)
        try:
            Ope.objects.select_related().filter(compte__id__in=liste_id).update(pointe=False)
            messages.success(request, u'suppression des statuts "pointé" dans les comptes %s' % queryset)
        except Exception, err:
            messages.error(request, err)

    action_supprimer_pointe.short_description = u"Supprimer tous les statuts 'pointé' dans les comptes selectionnés"

    class RappForm(forms.Form):
        """form pour la transfo de pointe en rapprochee
        la seule chose demande est la date
        sinon on decide automatiquement du nom
        """
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        rapp_ = forms.ModelChoiceField(Rapp.objects.all(), required=False)
        date = forms.DateField(label="date du rapprochement")

    def action_transformer_pointee_rapp(self, request, queryset):
        form = None
        query_ope = Ope.objects.filter(pointe=True, compte__in=queryset).order_by('-date')
        if 'apply' in request.POST:
            form = self.RappForm(request.POST)
            if form.is_valid():
                rapp = form.cleaned_data['rapp_']
                if not rapp:
                    rapp_date = form.cleaned_data['date'].year
                    last = Rapp.objects.filter(date__year=rapp_date).filter(ope__compte__in=queryset).distinct()
                    if last.exists():
                        last = last.latest('date')
                        rapp_id = int(last.nom[-2:]) + 1
                    else:
                        rapp_id = 1
                    nomrapp = "%s%s%02d" % (queryset[0].nom, rapp_date, rapp_id)
                    rapp = Rapp.objects.create(nom=nomrapp, date=form.cleaned_data['date'])
                count = 0
                for article in query_ope:
                    article.pointe = False
                    article.rapp = rapp
                    count += 1
                    article.save()
                plural = ''
                if count != 1:
                    plural = 's'
                rapp.date = form.cleaned_data['date']
                rapp.save()
                self.message_user(request, u"le compte %s a bien été rapproché (%s opération%s rapprochée%s)" % (
                queryset[0], count, plural, plural))
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.RappForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'admin/add_rapp.djhtm', {'opes': query_ope, 'rapp_form': form, })

    action_transformer_pointee_rapp.short_description = "Rapprocher un compte"


class Compte_titre_admin(Modeladmin_perso):
    """compte titre """
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    fields = Compte_admin.fields  # on prend comme ca les meme champs
    list_display = ('nom', 'solde_titre', 'solde_rappro', 'date_rappro', 'nb_ope')
    list_filter = ('type', 'banque', 'ouvert')


class ope_fille_admin(liste_perso_inline):
    model = Ope
    fields = ('montant', 'cat', 'ib', 'notes')
    fk_name = 'mere'
    related = ('cat', 'ib')


class Ope_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les opes"""
    fields = (
    'compte', ('date', 'date_val'), 'montant', 'tiers', 'moyen', ('cat', 'ib'), ('pointe', 'rapp', 'exercice'),
    ('show_jumelle', 'mere', 'is_mere'), 'oper_titre', 'num_cheque', 'notes')
    readonly_fields = ('show_jumelle', 'show_mere', 'oper_titre', 'is_mere')
    ordering = ('-date', )
    list_display = ('id', 'compte', 'date', 'montant', 'tiers_virement', 'moyen', 'cat', 'rapp', 'pointe')
    list_filter = (
    'compte', ('date', date_perso_filter), rapprochement_filter, 'moyen', 'exercice', 'cat__type', 'cat__nom')
    search_fields = ['tiers__nom']
    list_editable = ('pointe', 'montant')
    actions = ['action_supprimer_pointe', 'fusionne_a_dans_b', 'fusionne_b_dans_a', 'mul']
    #save_on_top = True
    save_as = True
    search_fields = ['tiers__nom']
    ordering = ['date']
    inlines = [ope_fille_admin]
    raw_id_fields = ('mere', )

    def queryset(self, request):
        qs = super(Ope_admin, self).queryset(request)
        return qs.select_related('compte', 'rapp', 'moyen', 'tiers', 'cat')

    def is_mere(self, obj):
        if obj.is_mere:
            return u"opérations filles ci dessous"
        else:
            return u"aucune opération fille"

    def mere_fille(self, obj):
        if obj.is_fille:
            return "fille de %s" % obj.mere_id
        else:
            if obj.is_mere:
                return "mere"
            else:
                return "solitaire"

    def show_jumelle(self, obj):
        """
        retourne le lien pour l'operation lié dans le cadre des virements entre comptes
        """
        if obj.jumelle_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.jumelle.id, ))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.jumelle))
        else:
            return "(aucun-e)"

    show_jumelle.short_description = u"Opération jumelle"

    def show_mere(self, obj):
        if obj.mere_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.mere.id, ))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.mere))
        else:
            return "(aucun-e)"

    show_mere.short_description = "mere"

    def oper_titre(self, obj):
        if obj.ope:
            change_url = urlresolvers.reverse('admin:gsb_ope_titre_change', args=(obj.ope.id, ))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope))
        else:
            return "(aucun-e)"

    oper_titre.short_description = u"compta matiere"

    def mul(self, request, queryset):
        #queryset.update(montant=models.F('montant') * -1)  #ca serait optimal de faire mais because virement pas facile
        for o in queryset:
            if o.jumelle:
                o.montant *= -1
                o.jumelle.montant *= -1
                o.save()
                o.jumelle.save()
            else:
                o.montant *= -1
                o.save()
        return HttpResponseRedirect(request.get_full_path())

    mul.short_description = u"Multiplier le montant des opérations selectionnnés par -1"

    def action_supprimer_pointe(self, request, queryset):
        try:
            queryset.update(pointe=False)
            messages.success(request, u'suppression des statuts "pointé" des opérations selectionnées')
        except Exception, err:
            messages.error(request, unicode(err))

    action_supprimer_pointe.short_description = u'Suppression des statuts "pointé" des opérations selectionnées'

    def delete_view(self, request, object_id, extra_context=None):
        instance = self.get_object(request, admin.util.unquote(object_id))
        #on evite que cela soit une operation rapproche
        error = False
        if instance.rapp:
            messages.error(request, u'ope rapprochee')
            error = True
        if instance.jumelle:
            if instance.jumelle.rapp:
                messages.error(request, u'jumelle rapproche')
                error = True
        if instance.mere:
            if instance.mere.rapp:
                messages.error(request, u'mere rapprochee')
                error = True
        if not error:
            try:
                return super(Ope_admin, self).delete_view(request, object_id, extra_context)
            except IntegrityError, excp:
                messages.error(request, excp)


class Cours_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les  cours des titres """
    list_display = ('date', 'titre', 'valeur')
    list_editable = ('valeur', )
    list_filter = ('date', 'titre')
    ordering = ('-date', )


class Titre_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les titres"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_display = ('nom', 'isin', 'type', 'last_cours')
    fields = ('nom', 'isin', 'type', 'show_tiers')
    readonly_fields = ('tiers', 'show_tiers')
    list_filter = ('type', )
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextInputWidget},
    }

    def show_tiers(self, obj):
        if obj.tiers_id:
            change_url = urlresolvers.reverse('admin:gsb_tiers_change', args=(obj.tiers_id, ))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.tiers))
        else:
            return "(aucun-e)"

    show_tiers.short_description = "tiers"


class Moyen_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les moyens de paiements"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_filter = ('type', )
    fields = ['type', 'nom']

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

    list_display = ('nom', 'type', 'nb_ope')


class ope_tiers_admin(liste_perso_inline):
    model = Ope
    fields = ('date', 'compte', 'montant', 'cat', 'ib', 'notes')
    readonly = True
    fk_name = 'tiers'
    related = ('compte', 'cat', 'ib')


class Tiers_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les tiers"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_editable = ('nom', 'notes')
    list_display = ('id', 'nom', 'notes', 'is_titre', 'nb_ope')
    list_display_links = ('id', )
    list_filter = ('is_titre', )
    search_fields = ['nom']
    inlines = [ope_tiers_admin]
    formfield_overrides = {models.TextField: {'widget': forms.TextInput}, }

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())


class Ech_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les écheances d'operations"""
    list_display = (
    'id', 'valide', 'date', 'compte', 'compte_virement', 'montant', 'tiers', 'cat', 'intervalle', 'periodicite')
    list_filter = ('compte', 'compte_virement', 'date', 'periodicite')
    actions = ['check_ech']

    def check_ech(self, request, queryset):
        Echeance.check(request=request, queryset=queryset)

    check_ech.short_description = u"Verifier si des echeances sont à enregistrer"


class Banque_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les banques"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']


class ope_rapp_admin(liste_perso_inline):
    model = Ope
    fields = ('compte', 'date', 'tiers', 'moyen', 'montant', 'cat', 'notes')
    readonly_fields = ('compte', 'date', 'tiers', 'moyen', 'montant', 'cat', 'notes')
    fk_name = 'rapp'
    related = ('compte', 'tiers', 'moyen', 'cat')


class Rapp_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les rapprochements"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_display = ('nom', 'date')
    inlines = [ope_rapp_admin]


class Exo_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les exercices"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_filter = ('date_debut', 'date_fin')


class Ope_titre_admin(Modeladmin_perso):
    list_display = ('id', 'date', 'compte', 'titre', 'nombre', 'cours', 'invest')
    readonly_fields = ('invest', 'show_ope', "show_ope_pmv")
    list_display_links = ('id', )
    list_filter = ('date', 'compte', 'titre', )
    ordering = ('-date', )

    def show_ope(self, obj):
        change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope.id, ))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope))

    show_ope.short_description = u"opération"

    def show_ope_pmv(self, obj):
        change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope_pmv.id, ))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope_pmv))

    show_ope_pmv.short_description = u"opération relative aux plus ou moins values"

admin.site.register(Tiers, Tiers_admin)
admin.site.register(Cat, Cat_admin)
admin.site.register(Compte, Compte_admin)
admin.site.register(Ope, Ope_admin)
admin.site.register(Titre, Titre_admin)
admin.site.register(Banque, Banque_admin)
admin.site.register(Cours, Cours_admin)
admin.site.register(Ib, Ib_admin)
admin.site.register(Exercice, Exo_admin)
admin.site.register(Rapp, Rapp_admin)
admin.site.register(Moyen, Moyen_admin)
admin.site.register(Echeance, Ech_admin)
admin.site.register(Compte_titre, Compte_titre_admin)
admin.site.register(Ope_titre, Ope_titre_admin)
