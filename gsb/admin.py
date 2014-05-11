# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib import admin
from django.contrib import messages
from django.db import models
import django.forms as forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings  # @Reimport
from django.utils.translation import ugettext_lazy as _

from .models import Tiers, Titre, Cat, Ope, Banque, Cours, Ib, Exercice, Rapp, Moyen, Echeance, Ope_titre, Compte, Config

#from django.db.models import Q
# import decimal
from django.contrib.admin import DateFieldListFilter
from django.contrib.admin import SimpleListFilter

from django.forms.models import BaseInlineFormSet
import gsb.utils as utils
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db import transaction
from collections import OrderedDict
from . import model_field


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
                self.lookup_kwarg_until: str(today.replace(day=15)), # fin du mois precedent car pour la sg c'est jusqu'au 6
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
    # Parameter for the filter that will be used in the URL query.
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


class ouinonfilter(SimpleListFilter):
    title = None
    # Parameter for the filter that will be used in the URL query.
    parameter_name = None

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('1', u'oui'),
            ('0', u'non')
        )


class mere_et_standalone_filter(ouinonfilter):
    title = "elimination des filles"
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'elimfille'

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(mere__isnull=True)
        else:
            return queryset


class sauf_visa_filter(ouinonfilter):
    title = "tous les moyens sauf visa"
    parameter_name = 'visa'

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == '1':
            return queryset.exclude(moyen_id=24)
        if self.value() == '0':
            return queryset.filter(moyen_id=24)


class verifmere_filter(ouinonfilter):
    title = "fille oui mere non ou inverse"
    parameter_name = 'merep'

    def queryset(self, request, queryset):
        if self.value() == '1':
            messages.info(request, "attention sur l'ensemble de la base")
            merep = Ope.objects.filter(filles_set__pointe=True).filter(pointe=False).distinct().values_list('id', flat=True)
            fillep = Ope.objects.filter(mere__isnull=False).filter(pointe=False).filter(mere__pointe=True).values_list('id', flat=True)
            listep = list(merep) + list(fillep)
            return Ope.objects.filter(id__in=listep)
        else:
            return queryset


class Modeladmin_perso(admin.ModelAdmin):
    save_on_top = True
    id_ope = None
    table_annexe = None
    change_list = False
    list_select_related = True

    def get_queryset(self, request):
    #    raise
    # compte le nombre d'ope
        if 'nb_opes' in self.list_display and self.change_list:
            if (self.id_ope is None) or (self.table_annexe is None):
                raise ImproperlyConfigured
            else:
                return super(Modeladmin_perso, self).queryset(request).extra(select={
                    'nb_opes': 'select count(*) from gsb_ope'
                                'WHERE (gsb_ope.%s = %s.id '
                                        'AND NOT (gsb_ope.id IN (SELECT mere_id FROM gsb_ope '
                                        'WHERE (id IS NOT NULL AND mere_id IS NOT NULL))))' % (
                        self.id_ope, self.table_annexe), }, )
        else:
            return super(Modeladmin_perso, self).queryset(request)

    def nb_opes(self, inst):
        return inst.nb_opes

    nb_opes.admin_order_field = 'nb_opes'

    def fusionne(self, request, queryset):
        """fonction générique de fusion entre 2 objets"""
        # noinspection PyProtectedMember
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

    def changelist_view(self, request, extra_context=None):
        self.change_list = True
        return super(Modeladmin_perso, self).changelist_view(request, extra_context)


class formsetreadonly(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(formsetreadonly, self).__init__(*args, **kwargs)
        self.can_delete = False


class ope_inline_admin(admin.TabularInline):
    model = Ope
    fields = ('lien', 'date', 'compte', 'montant', 'cat', 'tiers', 'ib', 'notes')
    readonly_fields = fields
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput, },
    }
    related = ('compte', 'cat', 'ib')
    readonly = True
    orderby = ('-date',)
    formset = formsetreadonly

    def queryset(self, request):
        qs = super(ope_inline_admin, self).queryset(request)
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

    def has_add_permission(self, request):
        if self.readonly:
            return False
        return True

    def lien(self, obj):
        if obj.id:
            obj.has_absolute_url = False
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.id,))
            return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.id))
        else:
            return "(aucun-e)"

    lien.short_description = u"ID"

# ------------definition des classes


class ope_cat(ope_inline_admin):
    fk_name = 'cat'


class Cat_admin(Modeladmin_perso):
    """classe admin pour les categories"""
    actions = ['fusionne', ]
    list_editable = ('nom', 'couleur')
    list_display = ('id', 'nom', 'type', 'nb_opes', 'couleur')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type': admin.HORIZONTAL}
    inlines = [ope_cat]
    id_ope = "cat_id"
    table_annexe = "gsb_cat"

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if obj.id in (settings.ID_CAT_OST, settings.ID_CAT_VIR, settings.ID_CAT_PMV, settings.REV_PLAC, settings.ID_CAT_COTISATION):
            return False
        if obj.nom in (u"Frais bancaires", u"Opération Ventilée"):
            return False
        return True


class ope_ib(ope_inline_admin):
    fk_name = 'ib'


class Ib_admin(Modeladmin_perso):
    """admin pour les ib"""
    actions = ['fusionne', ]
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type', 'nb_opes')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type': admin.VERTICAL}
    inlines = [ope_ib]
    id_ope = "ib_id"
    table_annexe = "gsb_ib"


class Compte_admin(Modeladmin_perso):
    """admin pour les comptes normaux"""
    actions = ['fusionne', 'action_supprimer_pointe', 'action_transformer_pointee_rapp']
    fields = ('nom', ('type', 'ouvert'), 'banque', ('guichet', 'num_compte', 'cle_compte'), ('solde_init', 'solde_mini_voulu',
                                                                                             'solde_mini_autorise'),
              ('moyen_debit_defaut', 'moyen_credit_defaut', 'couleur'))
    list_display = ('id', 'nom', 'type', 'ouvert', 'solde_espece', 'solde_rappro', 'date_rappro', 'nb_ope', 'couleur')
    list_filter = ('type', 'banque', 'ouvert')
    list_editable = ('couleur',)
    radio_fields = {'type': admin.HORIZONTAL,
                    'moyen_debit_defaut': admin.VERTICAL,
                    'moyen_credit_defaut': admin.VERTICAL}

    def nb_ope(self, obj):
        return '%s(%s non rapp)' % (obj.ope_set.exclude(filles_set__isnull=False).count(),
                                    obj.ope_set.exclude(filles_set__isnull=False).filter(rapp__isnull=True).count())

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
                with transaction.atomic():
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

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
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


class ope_ope(ope_inline_admin):
    fk_name = 'mere'


class Ope_changelist_Form(forms.ModelForm):
    class Meta(object):
        model = Ope

    date = forms.DateField(widget=forms.TextInput(attrs={'size': '10'}))


class Ope_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les opes"""
    fields = (
        'compte', ('date', 'date_val'), 'montant', 'tiers', 'moyen', ('cat', 'ib'), ('pointe', 'rapp', 'exercice'),
        ('show_jumelle', 'mere', 'is_mere'), 'oper_titre', 'num_cheque', 'notes')
    readonly_fields = ('show_jumelle', 'show_mere', 'oper_titre', 'is_mere')
    list_display = ('id', 'pointe', 'compte', 'tiers', 'date', 'montant', 'cat', "moyen", 'num_cheque', 'rapp', "mere")
    list_filter = (
        'compte', ('date', Date_perso_filter), Rapprochement_filter, sauf_visa_filter, mere_et_standalone_filter, verifmere_filter,
        'moyen__type', 'cat__type', 'cat__nom')
    search_fields = ['tiers__nom']
    list_editable = ('montant', 'pointe', 'date')
    actions = ['action_supprimer_pointe', 'fusionne_a_dans_b', 'fusionne_b_dans_a', 'mul', 'cree_operation_mere', 'defilliser']
    save_on_top = True
    save_as = True
    ordering = ['-date', 'id']
    #inlines = [ope_ope]
    raw_id_fields = ('mere',)
    date_hierarchy = 'date'
    formfield_overrides = {
        model_field.CurField: {'widget': forms.TextInput(attrs={'size': '8'})},
    }

    def get_changelist_form(self, request, **kwargs):
        return Ope_changelist_Form

    def queryset(self, request):
        qs = super(Ope_admin, self).queryset(request)
        return qs.select_related('compte', 'rapp', 'moyen', 'tiers', 'cat', 'mere')

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
            return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.jumelle))
        else:
            return "(aucun-e)"

    show_jumelle.short_description = u"Opération jumelle"

    def show_mere(self, obj):
        if obj.mere_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.mere.id,))
            return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.mere))
        else:
            return "(aucun-e)"

    show_mere.short_description = "mere"

    def oper_titre(self, obj):
        if obj.ope_titre_ost:
            change_url = urlresolvers.reverse('admin:gsb_ope_titre_change', args=(obj.ope_titre_ost.id,))
            return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.ope_titre_ost))
        else:
            if obj.ope_titre_pmv:
                change_url = urlresolvers.reverse('admin:gsb_ope_titre_change', args=(obj.ope_titre_pmv.id,))
                return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.ope_titre_pmv))
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

    @transaction.atomic
    def cree_operation_mere(self, request, queryset):
        # on verifie que les operations ont la meme date et ne sont pas deja des operations filles ni des operations mere.
        montant = 0
        mere = None
        for ope in queryset:
            montant = ope.montant + montant
            if ope.mere is not None:
                if mere is None:
                    mere = ope.mere
                else:
                    messages.error(request, u"les opé ont plusieurs mère")
                    return
            if ope.is_mere:
                messages.error(request, u"l'ope %s est déja une ope mère" % ope.id)
                return
            if ope.rapp:
                messages.error(request, u"l'ope %s est déja rapprochée" % ope.id)
                return
        date_ope = list(OrderedDict.fromkeys(queryset.order_by('id').values_list('date', flat=True)))
        if len(date_ope) > 1:
            messages.error(request, "toutes les opérations doivent avoir la meme date")
            return
        else:
            date_ope = date_ope[0]
        tiers_id = list(OrderedDict.fromkeys(queryset.order_by('id').values_list('tiers', flat=True)))[0]
        compte_id = list(OrderedDict.fromkeys(queryset.order_by('id').values_list('compte', flat=True)))[0]
        # ok c'est bon on peut commencer a creer
        if mere is None:
            mere = Ope.objects.create(date=date_ope,
                                      montant=montant,
                                      tiers_id=tiers_id,
                                      cat=Cat.objects.get(nom=u"Opération Ventilée"),
                                      moyen_id=settings.MD_CREDIT if montant > 0 else settings.MD_DEBIT,
                                      compte_id=compte_id
            )
            messages.success(request, u"ope mere crée '%s' " % mere)
        else:
            messages.info(request, u"on va utiliser cette operation mere '%s' " % mere)
        for ope in queryset:
            ope.mere = mere
            ope.save()
            messages.success(request, u"ope '%s' mise à jour" % ope)

    cree_operation_mere.short_description = u"cree une opération mère pour les opérations selectionnées"

    @transaction.atomic
    def defilliser(self, request, queryset):
        if queryset.count() > 1:
            if queryset[0].is_fille:
                if len(list(OrderedDict.fromkeys(queryset.order_by('id').values_list('mere', flat=True)))) > 1:
                    messages.error(request, u"les opé ont plusieurs mère")
                    return
                for ope in queryset:
                    if ope.rapp:
                        messages.error(request, u"l'ope %s est déja rapprochée" % ope.id)
                        return
                    ope.mere = None
                    ope.save()
                    messages.success(request, u"ope '%s' mise à jour" % ope)
            else:
                messages.error(request, u"vous ne pouvez selectionnner que plusieurs filles")
                return
        else:
            ope = queryset[0]
            if ope.is_mere:
                for o in ope.filles_set.all():
                    o.mere = None
                    o.save()
                    messages.success(request, u"ope '%s' mise à jour" % o)
                ope.delete()
                messages.success(request, u"ope mere effacee")

            else:
                messages.error(request, u"si vous en selectionner une seul, vous ne pouvez selection qu'une mere")
                return

    defilliser.short_description = u"rompt la relation entre les filles selectionné et la mère"


class Cours_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les  cours des titres """
    list_display = ('date', 'titre', 'valeur')
    list_editable = ('valeur',)
    list_filter = ('date', 'titre')
    fields = ('date', 'titre', 'valeur')
    ordering = ('-date',)
    date_hierarchy = 'date'


class Titre_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les titres"""
    actions = ['fusionne']
    list_display = ('id', 'nom', 'isin', 'type', 'last_cours')
    fields = ('nom', 'isin', 'type', 'show_tiers')
    readonly_fields = ('tiers', 'show_tiers')
    list_filter = ('type',)

    def show_tiers(self, obj):
        if obj.tiers:
            change_url = urlresolvers.reverse('admin:gsb_tiers_change', args=(obj.tiers.id,))
            return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.tiers))
        else:
            return "(aucun-e)"

    show_tiers.short_description = "tiers"


class Moyen_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les moyens de paiements"""
    actions = ['fusionne']
    list_filter = ('type',)
    fields = ['nom', 'type']
    list_display = ('nom', 'type', 'nb_opes')
    radio_fields = {'type': admin.HORIZONTAL}
    id_ope = "moyen_id"
    table_annexe = "gsb_moyen"


class ope_tiers(ope_inline_admin):
    fk_name = 'tiers'


class Tiers_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les tiers"""
    actions = ['fusionne']
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'notes', 'is_titre', 'nb_opes')
    list_display_links = ('id',)
    list_filter = ('is_titre', ('lastupdate', Date_perso_filter),)
    search_fields = ['nom']
    inlines = [ope_tiers]
    formfield_overrides = {models.TextField: {'widget': forms.TextInput}, }
    id_ope = "tiers_id"
    table_annexe = "gsb_tiers"

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
    fields = ('date', 'date_limite', ('intervalle', 'periodicite'), 'valide', 'compte', ('montant', 'tiers'), ('cat', 'moyen', 'ib'),
              ('compte_virement', 'moyen_virement'), 'exercice', 'notes')
    actions = ['check_ech']
    radio_fields = {'periodicite': admin.HORIZONTAL}

    def check_ech(self, request, queryset):
        Echeance.check(request=request, queryset=queryset)

    check_ech.short_description = u"Verifier si des echeances sont à enregistrer"


class Banque_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les banques"""
    actions = ['fusionne']


class ope_rapp(ope_inline_admin):
    fk_name = 'rapp'


class Rapp_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les rapprochements"""
    actions = ['fusionne']
    list_display = ('nom', 'date')
    inlines = [ope_rapp]


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
    date_hierarchy = 'date'

    def show_ope(self, obj):
        change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope_ost.id,))
        return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.ope_ost))

    show_ope.short_description = u"opération"

    def show_ope_pmv(self, obj):
        change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope_pmv.id,))
        return format_html('<a href="%s">%s</a>' % (mark_safe(change_url), obj.ope_pmv))

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


class Config_admin(Modeladmin_perso):
    list_display = ('derniere_import_money_journal',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


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
admin.site.register(Config, Config_admin)
