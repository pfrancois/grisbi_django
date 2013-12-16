# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .models import Tiers, Titre, Cat, Ope, Banque, Cours, Ib, Exercice, Rapp, Moyen, Echeance, Ope_titre, Compte
from django.contrib import admin
from django.contrib import messages
from django.db import models
import django.forms as forms
from django.utils.safestring import mark_safe
from django.core import urlresolvers
# from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings  # @Reimport

from django.utils.translation import ugettext_lazy as _
# from django.db.models import Q
# import decimal
from django.contrib.admin import DateFieldListFilter
from django.contrib.admin import SimpleListFilter

from django.forms.models import BaseInlineFormSet
import gsb.utils as utils
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db import transaction


#-------------ici les classes generiques------
class Date_perso_filter(DateFieldListFilter):

    """filtre date perso
    """

    def __init__(self, field, request, params, model, model_admin, field_path):
        super(Date_perso_filter, self).__init__(field, request, params, model, model_admin, field_path)
        today = utils.today()
        tomorrow = today + timedelta(days=1)
        troismois = today + relativedelta(months=-3, day=1)
        self.links = (
            (_('Any date'), {}),
            (_('Today'), {
                self.lookup_kwarg_since: str(today - timedelta(days=1)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Past 7 days'), {
                self.lookup_kwarg_since: str(today - timedelta(days=7)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This month'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            ('Les trois derniers mois', {
                self.lookup_kwarg_since: str(troismois),
                self.lookup_kwarg_until: str(today.replace(day=7)),  # fin du mois precedent car pour la sg c'est jusqu'au 6
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


class Rapprochement_filter(SimpleListFilter):
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
            return queryset.filter(rapp__isnull=True)


class Modeladmin_perso(admin.ModelAdmin):
    save_on_top = True

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.exclude(filles_set__isnull=False).count())

    def fusionne(self, request, queryset):
        """fonction générique de fusion entre 2 objets"""
        nom_module = queryset[0]._meta.module_name
        if queryset.count() < 2:
            messages.error(request,
                           u"attention, vous devez selectionner au moins 2 %(type)s , vous en avez selectionné %(n)s" % {
                               'n': queryset.count(),
                               'type': nom_module}
                           )
            return
        obj_a = queryset[0]
        for obj_b in queryset:
            if obj_a == obj_b:  # on saute le premier
                continue
            try:
                with transaction.atomic():
                    message = u"fusion effectuée, pour le type \"%s\", \"%s\" a été fusionné dans \"%s\"" % (
                        nom_module,
                        obj_b,
                        obj_a)
                    obj_b.fusionne(obj_a)
                    messages.success(request, message)
            except Exception as inst:
                message = inst.__unicode__()
                messages.error(request, message)

    fusionne.short_description = u"Fusion dans la première selectionnée"


class formsetligne_limit(BaseInlineFormSet):

    def get_queryset(self):
        sup = super(formsetligne_limit, self).get_queryset()
        return sup[:10]


class liste_perso_inline(admin.TabularInline):
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput, },
    }
    related = None
    readonly = True
    orderby = None
    formset = formsetligne_limit

    # afin de pouvoir avoir des inline readonly
    def __init__(self, parent_model, admin_site):
        if self.readonly:
            self.readonly_fields = self.fields
            self.can_delete = False
        super(liste_perso_inline, self).__init__(parent_model, admin_site)

    def queryset(self, request):
        qs = super(liste_perso_inline, self).queryset(request)
        # on related pour les inlines
        if self.related is not None:
            args = self.related
            qs = qs.select_related(*args)
    # gestion du orderby
        if self.orderby is not None:
            args = self.orderby
            qs = qs.order_by(*args)
        return qs
    # afin de pouvoir avoir des inline readonly

    def has_add_permission(self, request, obj=None):
        if self.readonly:
            return False
        return True


# ------------definitiion des classes
class ope_cat_admin(liste_perso_inline):
    model = Ope
    fields = ('date', 'compte', 'montant', 'tiers', 'ib', 'notes')
    fk_name = 'cat'
    related = ('compte', 'tiers', 'ib')
    orderby = ('-date',)
    max_num = 10


class Cat_admin(Modeladmin_perso):

    """classe admin pour les categories"""
    actions = ['fusionne', ]
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type': admin.HORIZONTAL}
    list_select_related = True
    inlines = [ope_cat_admin]

    def queryset(self, request):
        qs = super(Cat_admin, self).queryset(request)
        return qs.select_related('ope')

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if obj.id in (settings.ID_CAT_OST, settings.ID_CAT_VIR, settings.ID_CAT_PMV, settings.REV_PLAC, settings.ID_CAT_COTISATION):
            return False
        if obj.nom in (u"Frais bancaires", u"Opération Ventilée"):
            return False
        return True


class ope_ib_admin(liste_perso_inline):
    model = Ope
    fields = ('date', 'compte', 'montant', 'tiers', 'cat', 'notes')
    fk_name = 'ib'
    related = ('compte', 'tiers', 'cat')
    orderby = ('-date',)
    readonly = False
    formset = BaseInlineFormSet


class Ib_admin(Modeladmin_perso):

    """admin pour les ib"""
    actions = ['fusionne', ]
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type': admin.VERTICAL}
    inlines = [ope_ib_admin]


class Compte_admin(Modeladmin_perso):

    """admin pour les comptes normaux"""
    actions = ['fusionne', 'action_supprimer_pointe', 'action_transformer_pointee_rapp']
    fields = ('nom', ('type', 'ouvert'), 'banque', ('guichet', 'num_compte', 'cle_compte'), ('solde_init', 'solde_mini_voulu',
              'solde_mini_autorise'), ('moyen_debit_defaut', 'moyen_credit_defaut'))
    list_display = ('id', 'nom', 'type', 'ouvert', 'solde', 'solde_rappro', 'date_rappro', 'nb_ope')
    list_filter = ('type', 'banque', 'ouvert')
    radio_fields = {'type': admin.HORIZONTAL,
                    'moyen_debit_defaut': admin.VERTICAL,
                    'moyen_credit_defaut': admin.VERTICAL}

    def nb_ope(self, obj):
        return '%s(%s non rapp)' % (obj.ope_set.exclude(filles_set__isnull=False).count(), obj.ope_set.exclude(filles_set__isnull=False).filter(rapp__isnull=True).count())

    def action_supprimer_pointe(self, request, queryset):
        liste_id = queryset.values_list('id', flat=True)
        try:
            Ope.objects.select_related().filter(compte__id__in=liste_id).update(pointe=False)
            messages.success(request, u'suppression des statuts "pointé" dans les comptes %s' % queryset)
        except Exception as err:
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
        if query_ope.filter(cat__nom="Non affecté").exists():
            self.message_user(request, u"attention, au moins une operation n'est pas encore affectée")
            return HttpResponseRedirect(request.get_full_path())
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
                    nomrapp = "%s%s_%02d" % (queryset[0].nom, rapp_date, rapp_id)
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'moyen_debit_defaut':
            kwargs['queryset'] = Moyen.objects.filter(type='d')
        else:
            if db_field.name == 'moyen_credit_defaut':
                kwargs['queryset'] = Moyen.objects.filter(type='r')
        return super(Compte_admin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if not obj.ouvert:
            return False
        return True


class ope_fille_admin(liste_perso_inline):
    model = Ope
    fields = ('montant', 'cat', 'ib', 'notes')
    fk_name = 'mere'
    related = ('cat', 'ib')
    orderby = ('ib',)
    readonly = True

from django.forms import TextInput
from . import model_field


class Ope_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les opes"""
    fields = (
        'compte', ('date', 'date_val'), 'montant', 'tiers', 'moyen', ('cat', 'ib'), ('pointe', 'rapp', 'exercice'),
        ('show_jumelle', 'mere', 'is_mere'), 'oper_titre', 'num_cheque', 'notes')
    readonly_fields = ('show_jumelle', 'show_mere', 'oper_titre', 'is_mere')
    list_display = ('id', 'pointe', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat', 'num_cheque', 'rapp')
    list_filter = ('compte', ('date', Date_perso_filter), Rapprochement_filter, 'moyen', 'exercice', 'cat__type', 'cat__nom')
    search_fields = ['tiers__nom']
    list_editable = ('montant', 'pointe')
    actions = ['action_supprimer_pointe', 'fusionne_a_dans_b', 'fusionne_b_dans_a', 'mul']
    save_on_top = True
    save_as = True
    ordering = ['-date']
    inlines = [ope_fille_admin]
    raw_id_fields = ('mere',)
    formfield_overrides = {
        model_field.CurField: {'widget': TextInput(attrs={'size': '8'})},
        #    models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

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
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.jumelle.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.jumelle))
        else:
            return "(aucun-e)"

    show_jumelle.short_description = u"Opération jumelle"

    def show_mere(self, obj):
        if obj.mere_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.mere.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.mere))
        else:
            return "(aucun-e)"

    show_mere.short_description = "mere"

    def oper_titre(self, obj):
        if obj.ope_titre_ost:
            change_url = urlresolvers.reverse('admin:gsb_ope_titre_change', args=(obj.ope_titre_ost.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope_titre_ost))
        else:
            if obj.ope_titre_pmv:
                change_url = urlresolvers.reverse('admin:gsb_ope_titre_change', args=(obj.ope_titre_pmv.id,))
                return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope_titre_pmv))
            else:
                return "(aucun-e)"

    oper_titre.short_description = u"compta matiere"

    def mul(self, request, queryset):
        # queryset.update(montant=models.F('montant') * -1)  #ca serait optimal de faire mais because virement pas facile
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

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if not obj.compte.ouvert:
            return False
        if obj.is_mere:
            opes = obj.filles_set.all()
            for o in opes.values('id', 'pointe', 'rapp'):
                if o['pointe'] or o['rapp'] is not None:
                    return False
            if obj.pointe or obj.rapp is not None:
                return False
        if obj.ope_titre_ost is not None or obj.ope_titre_pmv is not None:
            return False
        if obj.jumelle is not None and (obj.jumelle.pointe or obj.jumelle.rapp is not None):
            return False
        if obj.rapp is not None:
            return False
        return True


class Cours_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les  cours des titres """
    list_display = ('date', 'titre', 'valeur')
    list_editable = ('valeur',)
    list_filter = ('date', 'titre')
    fields = ('date', 'titre', 'valeur')
    ordering = ('-date',)


class Titre_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les titres"""
    actions = ['fusionne']
    list_display = ('nom', 'isin', 'type', 'last_cours')
    fields = ('nom', 'isin', 'type', 'show_tiers')
    readonly_fields = ('tiers', 'show_tiers')
    list_filter = ('type',)
    formfield_overrides = {models.TextField: {'widget': admin.widgets.AdminTextInputWidget}, }

    def show_tiers(self, obj):
        if obj.tiers:
            change_url = urlresolvers.reverse('admin:gsb_tiers_change', args=(obj.tiers.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.tiers))
        else:
            return "(aucun-e)"

    show_tiers.short_description = "tiers"


class Moyen_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les moyens de paiements"""
    actions = ['fusionne']
    list_filter = ('type',)
    fields = ['nom', 'type']
    list_display = ('nom', 'type', 'nb_ope')
    radio_fields = {'type': admin.HORIZONTAL}


class ope_tiers_admin(liste_perso_inline):
    model = Ope
    fields = ('date', 'compte', 'montant', 'cat', 'ib', 'notes')
    readonly = True
    fk_name = 'tiers'
    orderby = ('-date',)
    related = ('compte', 'cat', 'ib')


class Tiers_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les tiers"""
    actions = ['fusionne']
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'notes', 'is_titre', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('is_titre', ('lastupdate', Date_perso_filter),)
    search_fields = ['nom']
    inlines = [ope_tiers_admin]
    formfield_overrides = {models.TextField: {'widget': forms.TextInput}, }

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if obj.is_titre is True:
            return False
        return True


class Ech_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les écheances d'operations"""
    list_display = ('id', 'valide', 'date', 'compte', 'compte_virement', 'montant', 'tiers', 'cat', 'intervalle', 'periodicite')
    list_filter = ('compte', 'compte_virement', 'date', 'periodicite')
    fields = ('date', 'date_limite', ('intervalle', 'periodicite'), 'valide', 'compte', ('montant', 'tiers'), ('cat', 'moyen', 'ib'), ('compte_virement', 'moyen_virement'), 'exercice', 'notes')
    actions = ['check_ech']
    radio_fields = {'periodicite': admin.HORIZONTAL}

    def check_ech(self, request, queryset):
        Echeance.check(request=request, queryset=queryset)

    check_ech.short_description = u"Verifier si des echeances sont à enregistrer"


class Banque_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les banques"""
    actions = ['fusionne']


class ope_rapp_admin(liste_perso_inline):
    model = Ope
    fields = ('compte', 'date', 'tiers', 'moyen', 'montant', 'cat', 'notes')
    readonly_fields = ('compte', 'date', 'tiers', 'moyen', 'montant', 'cat', 'notes')
    fk_name = 'rapp'
    related = ('compte', 'tiers', 'moyen', 'cat')
    orderby = ('-date',)
    formset = BaseInlineFormSet


class Rapp_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les rapprochements"""
    actions = ['fusionne']
    list_display = ('nom', 'date')
    inlines = [ope_rapp_admin]


class Exo_admin(Modeladmin_perso):

    """classe de gestion de l'admin pour les exercices"""
    actions = ['fusionne']
    list_filter = ('date_debut', 'date_fin')


class Ope_titre_admin(Modeladmin_perso):
    list_display = ('id', 'date', 'compte', 'titre', 'nombre', 'cours', 'invest')
    readonly_fields = ('invest', 'show_ope', "show_ope_pmv")
    list_display_links = ('id',)
    list_filter = ('date', 'compte', 'titre',)
    ordering = ('-date',)

    def show_ope(self, obj):
        change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope_ost.id,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope_ost))

    show_ope.short_description = u"opération"

    def show_ope_pmv(self, obj):
        change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope_pmv.id,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope_pmv))

    show_ope_pmv.short_description = u"opération relative aux plus ou moins values"

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if utils.is_onexist(obj, "ope_ost") and obj.ope_ost.rapp is not None:
            return False
        if utils.is_onexist(obj, "ope_ost") and obj.ope_ost.pointe is True:
            return False
        if utils.is_onexist(obj, "ope_pmv") and obj.ope_pmv.rapp is not None:
            return False
        if utils.is_onexist(obj, "ope_pmv") and obj.ope_pmv.pointe is True:
            return False
        return True


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
admin.site.register(Ope_titre, Ope_titre_admin)
