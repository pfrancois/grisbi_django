# -*- coding: utf-8 -*-
from mysite.gsb.models import *
from django.contrib import admin

class Cat_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type')
    list_display_links = ('id',)

class Ib_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type')
    list_display_links = ('id',)


class Compte_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    fieldsets = [
            (None, {'fields': ('nom', 'type', 'devise', 'ouvert')}),
            (u'information sur le compte', {'fields': ('banque', 'guichet', 'num_compte', 'cle_compte'), 'classes': ['collapse']}),
            (u'soldes', {'fields': ('solde_init', 'solde_mini_voulu', 'solde_mini_autorise'), 'classes': ['collapse']}),
            (u'moyens par défaut', {'fields': ('moyen_credit_defaut', 'moyen_debit_defaut'), 'classes': ['collapse']}),
            ]
    list_display = ('nom', 'solde', 'ouvert')


class Ope_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    fieldsets = [
            (None, {'fields': ('compte', 'date', 'montant', 'tiers', 'moyen', 'cat')}),
            (u'informations diverses', {'fields': ('date_val', 'num_cheque', 'notes', 'exercice', 'ib'), 'classes': ['collapse']}),
            (u'pointage', {'fields': ('pointe', 'rapp'), 'classes': ['collapse']}),
            ]
    ordering = ('date',)
    list_display = ('id', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat')
    list_filter = ('compte', 'date', 'pointe', 'rapp')


class cours_admin(admin.ModelAdmin):
    list_display = ('date', 'titre', 'valeur')
    list_editable = ('valeur',)
    list_filter = ('date', 'titre')

class Titre_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    list_display = ('nom', 'isin', 'last_cours')
    list_filter = ('type',)

class moyen_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    fields = ['type', 'nom']

class Histo_ope_titres_admin(admin.ModelAdmin):
    readonly_fields = ('titre', 'compte', 'nombre', 'date')

class Compte_titre_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    list_display = ('nom', 'solde')

class Tiers_admin(admin.ModelAdmin):
    #TODO 2 action pour fusionnner
    list_editable = ('nom', 'notes')
    list_display = ('id', 'nom', 'notes', 'is_titre')
    list_display_links = ('id',)
    list_filter = ('is_titre',)

class ech_admin(admin.ModelAdmin):
    list_display = ('id', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat')
    list_filter = ('compte', 'date')
    list_editable = ('date',)

admin.site.register(Tiers, Tiers_admin)
admin.site.register(Cat, Cat_admin)
admin.site.register(Compte, Compte_admin)
admin.site.register(Ope, Ope_admin)
admin.site.register(Titre, Titre_admin)
admin.site.register(Banque)
admin.site.register(Cours, cours_admin)
admin.site.register(Ib, Ib_admin)
admin.site.register(Exercice)
admin.site.register(Rapp)
admin.site.register(Moyen)
admin.site.register(Echeance, ech_admin)
admin.site.register(Generalite)
admin.site.register(Compte_titre, Compte_titre_admin)
admin.site.register(Titres_detenus)
admin.site.register(Histo_ope_titres, Histo_ope_titres_admin)
