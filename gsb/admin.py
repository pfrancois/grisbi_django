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
            (None, {'fields': ('nom', 'type', 'devise', 'cloture')}),
            (u'information sur le compte', {'fields': ('banque', 'guichet', 'num_compte', 'cle_compte'), 'classes': ['collapse']}),
            (u'soldes', {'fields': ('solde_init', 'solde_mini_voulu', 'solde_mini_autorise'), 'classes': ['collapse']}),
            (u'moyens par défaut', {'fields': ('moyen_credit_defaut', 'moyen_debit_defaut'), 'classes': ['collapse']}),
            ]


class Ope_admin(admin.ModelAdmin):
    fieldsets = [
            (None, {'fields': ('compte', 'date', 'montant', 'tiers', 'moyen','cat')}),
            (u'informations diverses', {'fields': ('date_val', 'num_cheque', 'notes', 'exercice','ib'), 'classes': ['collapse']}),
            (u'pointage', {'fields': ('pointe', 'rapp'), 'classes': ['collapse']}),
            (u'mère et jumelles', {'fields': ('jumelle', 'mere'), 'classes': ['collapse']}),
            ]


class cours_admin(admin.ModelAdmin):
    fields = ['isin', 'date', 'valeur']

class moyen_admin(admin.ModelAdmin):
    fields = ['type','nom']

admin.site.register(Tiers)
admin.site.register(Cat)
admin.site.register(Compte, Compte_admin)
admin.site.register(Ope, Ope_admin)
admin.site.register(Titre)
admin.site.register(Cours, cours_admin)
admin.site.register(Banque)
admin.site.register(Ib)
admin.site.register(Exercice)
admin.site.register(Rapp)
admin.site.register(Moyen)
admin.site.register(Echeance)
admin.site.register(Generalite)
