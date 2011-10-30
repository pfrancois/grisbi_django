# -*- coding: utf-8 -*-
from mysite.gsb.models import Tiers, Titre, Cat, Ope, Banque, Cours, Ib, Exercice, Rapp, Moyen, Echeance, Generalite, Compte_titre, Ope_titre, Compte
from django.contrib import admin
from django.contrib import messages
from django.db import models
import django.forms as forms
from django.utils.safestring import mark_safe
from django.core import urlresolvers
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied


def fusion(classe, request, queryset, sens):
    """fonction générique de fusion entre 2 objets"""
    nom_module = queryset[0]._meta.module_name
    if queryset.count() != 2:
        messages.error(request, u"attention, vous devez selectionner 2 %(type)s et uniquement 2, vous en avez selectionné %(n)s" % {'n':queryset.count(), 'type':nom_module})
        return
    a = queryset[0]
    b = queryset[1]
    if type(a) != type(b):
        classe.message_user(request, u"attention vous devez selectionner deux item du meme type")
        return
    try:
        if sens == 'ab':
            message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (nom_module, a, b)
            a.fusionne(b)
        else:
            message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (nom_module, b, a)
            b.fusionne(a)
        classe.message_user(request, message)
    except Exception as inst:#TODO mieux gerer
        message = inst.__unicode__()
        classe.message_user(request, message)

class modeladmin_perso(admin.ModelAdmin):
    save_on_top = True
class Cat_admin(modeladmin_perso):
    """classe admin pour les categories"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion de la première catégorie dans la seconde"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion de la seconde catégorie dans la première"

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type':admin.VERTICAL}

class Ib_admin(modeladmin_perso):
    """admin pour les ib"""
    save_on_top = True
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion de la première IB dans la seconde"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion de la seconde IB dans la première"

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type':admin.VERTICAL}


class Compte_admin(modeladmin_perso):
    """admin pour les comptes normaux"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier compte dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second compte dans le premier"
    fields = ('nom', 'type', 'ouvert', 'banque', 'guichet', 'num_compte', 'cle_compte', 'solde_init', 'solde_mini_voulu',
            'solde_mini_autorise', 'moyen_debit_defaut', 'moyen_credit_defaut')
    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

    list_display = ('nom', 'solde', 'type', 'ouvert', 'nb_ope')
    list_filter = ('type', 'banque', 'ouvert')


class Compte_titre_admin(modeladmin_perso):
    """compte titre avec inline"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier compte_titre dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du premier compte_titre dans le premier"
    fields = Compte_admin.fields#on prend comme ca les meme champs

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())
    list_display = ('nom', 'solde', 'nb_ope')
    list_filter = ('type', 'banque', 'ouvert')

class Ope_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les opes"""
    fields = ('compte', 'date', 'montant', 'tiers', 'moyen', 'cat', 'show_jumelle', 'show_mere', 'oper_titre',
            'notes', 'exercice', 'ib', 'date_val', 'num_cheque', 'pointe', 'rapp')
    readonly_fields = ('show_jumelle', 'show_mere', 'oper_titre')
    ordering = ('-date',)
    list_display = ('id', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat')
    list_filter = ('compte', 'date', 'pointe', 'rapp')
    search_fields = ['tiers__nom']
    def show_jumelle(self, obj):
        if obj.jumelle_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.jumelle.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.jumelle))
        else:
            return "(aucun-e)"
    show_jumelle.short_description = "jumelle"
    def show_mere(self, obj):
        if obj.mere_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.mere.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.mere))
        else:
            return "(aucun-e)"
    show_mere.short_description = "mere"
    def oper_titre(self, obj):
        if obj.ope_titre:
            change_url = urlresolvers.reverse('admin:gsb_ope_titre_change', args=(obj.ope_titre.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope_titre))
        else:
            return "(aucun-e)"
    oper_titre.short_description = u"compta matiere"
    def delete_view(self, request, object_id, extra_context=None):
        instance = self.get_object(request, admin.util.unquote(object_id))
        #on evite que cela soit une operation rapproche
        if instance.rapp:
            raise IntegrityError()
        if instance.jumelle:
            if instance.jumelle.rapp:
                raise IntegrityError
        if instance.mere:
            if instance.mere.rapp:
                raise IntegrityError
        return super(Ope_admin, self).delete_view(request, object_id, extra_context)

class Cours_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les  cours des titres """
    list_display = ('date', 'titre', 'valeur')
    list_editable = ('valeur',)
    list_filter = ('date', 'titre')
    ordering = ('-date',)

class Titre_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les titres"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier titre dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second titre dans le premier"
    list_display = ('nom', 'isin', 'type', 'last_cours')
    fields = ('nom', 'isin', 'type', 'show_tiers')
    readonly_fields = ('tiers', 'show_tiers')
    list_filter = ('type',)
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextInputWidget},
    }
    def show_tiers(self, obj):
        if obj.tiers_id:
            change_url = urlresolvers.reverse('admin:gsb_tiers_change', args=(obj.tiers_id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.tiers))
        else:
            return "(aucun-e)"
    show_tiers.short_description = "tiers"
class Moyen_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les moyens de paiements"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier moyen de paiment dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second moyen dans le premier"
    list_filter = ('type',)
    fields = ['type', 'nom']
    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())
    list_display = ('nom', 'type', 'nb_ope')

class Tiers_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les tiers"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier tiers dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second tiers dans le premier"
    list_editable = ('nom', 'notes')
    list_display = ('id', 'nom', 'notes', 'is_titre', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('is_titre',)
    search_fields = ['nom']
    formfield_overrides = {models.TextField:{'widget':forms.TextInput}, }
    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

class Ech_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les écheances d'operations"""
    list_display = ('id', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat')
    list_filter = ('compte', 'date')

class Banque_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les banques"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion de la première banque dans la seconde"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion de la seconde banque dans la première"

class Rapp_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les rapprochements"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier rapprochement dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second rapprochement dans le premier"

class Exo_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les exercices"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier exercice dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second exercice dans le premier"

    list_filter = ('date_debut', 'date_fin')

class Gen_admin(modeladmin_perso):
    """classe de gestion de l'admin pour les preferences"""
    pass

class Ope_titre_admin(modeladmin_perso):
    list_display = ('id', 'date', 'compte', 'titre', 'nombre', 'cours', 'invest')
    readonly_fields = ('invest', 'show_ope')
    list_display_links = ('id',)
    list_filter = ('date', 'compte', 'titre',)
    ordering = ('-date',)
    def show_ope(self, obj):
        change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope.id,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope))
    show_ope.short_description = "ope"



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
admin.site.register(Generalite, Gen_admin)
admin.site.register(Compte_titre, Compte_titre_admin)
admin.site.register(Ope_titre, Ope_titre_admin)
