# -*- coding: utf-8 -*-
from mysite.gsb.models import *
from django.contrib import admin

class Cat_admin(admin.TabularInline):
    model = Cat
    extra = 3


class Ib_admin(admin.TabularInline):
    model = Ib
    extra = 3


class Compte_admin(admin.ModelAdmin):
    fieldsets = [
            (None, {'fields': ('nom', 'type', 'devise', 'ouvert')}),
            (u'information sur le compte', {'fields': ('banque', 'guichet', 'num_compte', 'cle_compte'), 'classes': ['collapse']}),
            (u'soldes', {'fields': ('solde_init', 'solde_mini_voulu', 'solde_mini_autorise'), 'classes': ['collapse']}),
            (u'moyens par défaut', {'fields': ('moyen_credit_defaut', 'moyen_debit_defaut'), 'classes': ['collapse']}),
            ]
    list_display=('nom','solde','ouvert')

class Ope_admin(admin.ModelAdmin):
    fieldsets = [
            (None, {'fields': ('compte', 'date', 'montant', 'tiers', 'moyen','cat')}),
            (u'informations diverses', {'fields': ('date_val', 'num_cheque', 'notes', 'exercice','ib'), 'classes': ['collapse']}),
            (u'pointage', {'fields': ('pointe', 'rapp'), 'classes': ['collapse']}),
            (u'mère et jumelles', {'fields': ('jumelle', 'mere'), 'classes': ['collapse']}),
            ]
    date_hierarchy = 'date'
    ordering =('date',)

class cours_admin(admin.TabularInline):
    model= Cours
    fields = ['isin', 'date', 'valeur']
    date_hierarchy = 'date'

class Titre_admin(admin.ModelAdmin):
    inlines = [cours_admin,]
    list_display=('nom',)

class moyen_admin(admin.ModelAdmin):
    fields = ['type','nom']

class Histo_ope_titres_admin(admin.ModelAdmin):
    readonly_fields=('titre','compte','nombre','date')

class Compte_titre_admin(admin.ModelAdmin):
    list_display=('nom','solde')

admin.site.register(Tiers)
admin.site.register(Cat)
admin.site.register(Compte, Compte_admin)
admin.site.register(Ope, Ope_admin)
admin.site.register(Titre, Titre_admin)
admin.site.register(Banque)
admin.site.register(Ib)
admin.site.register(Exercice)
admin.site.register(Rapp)
admin.site.register(Moyen)
admin.site.register(Echeance)
admin.site.register(Generalite)
admin.site.register(Compte_titre,Compte_titre_admin)
admin.site.register(Titres_detenus)
admin.site.register(Histo_ope_titres,Histo_ope_titres_admin)
