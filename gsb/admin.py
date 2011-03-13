# -*- coding: utf-8 -*-
from grisbi.gsb.models import *
from django.contrib import admin

class Scat_Inline(admin.TabularInline):
    model = Scat
    extra = 3

class Cat_admin(admin.ModelAdmin):
    inlines=[Scat_Inline]

class Sib_Inline(admin.TabularInline):
    model = Sib
    extra = 3

class Ib_admin(admin.ModelAdmin):
    inlines=[Sib_Inline]

class Devise_admin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ('nom','isocode')}),
        (u'dernier taux de change', {'fields': ('date_dernier_change','dernier_tx_de_change'), 'classes': ['collapse']}),
    ]

class Compte_admin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ('nom','type','devise','compte_cloture')}),
        (u'information sur le compte', {'fields': ('banque','guichet','num_compte','cle_compte'), 'classes': ['collapse']}),
        (u'soldes', {'fields': ('solde_init','solde_mini_voulu','solde_mini_autorise'), 'classes': ['collapse']})
    ]

class Ope_admin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ('compte','date_ope','montant','devise','tiers','moyen')}),
        (u'catégorie',{'fields':('cat','scat')}),
        (u'imputation bugétaire',{'fields':('ib','sib'), 'classes': ['collapse']}),
        (u'informations diverses', {'fields':('date_val','numcheque','notes','exercice'), 'classes': ['collapse']}),
        (u'pointage',{'fields':('pointe','rapp'), 'classes': ['collapse']}),
        (u'mere et jumelles',{'fields':('mere','jumelle','is_mere'), 'classes': ['collapse']}),
    ]
admin.site.register(Tiers)
admin.site.register(Cat,Cat_admin)
admin.site.register(Compte,Compte_admin)
admin.site.register(Ope,Ope_admin)
admin.site.register(Devise,Devise_admin)
admin.site.register(Titre)
admin.site.register(Cours)
admin.site.register(Banque)
admin.site.register(Ib,Ib_admin)
admin.site.register(Exercice)
admin.site.register(Rapp)
admin.site.register(Echeance)
admin.site.register(Generalite)

