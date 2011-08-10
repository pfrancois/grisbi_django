# -*- coding: utf-8 -*-
from mysite.gsb.models import Tiers, Titre, Cat, Ope, Banque, Cours, Ib, Exercice, Rapp, Moyen, Echeance, Generalite, Compte_titre, Histo_ope_titres, Compte, Titres_detenus
from django.contrib import admin
from django.contrib import messages

def fusion(classe, request, queryset, sens='ab'):
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
    if sens == 'ab':
        message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (nom_module, a, b)
        a.fusionne(b)
    else:
        message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (nom_module, b, a)
        b.fusionne(a)
    classe.message_user(request, message)

class Cat_admin(admin.ModelAdmin):
    """classe admin pour les categories"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion de la première catégorie dans la seconde"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion de la seconde catégorie dans la première"

    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type':admin.VERTICAL}

class Ib_admin(admin.ModelAdmin):
    """admin pour les ib"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion de la première IB dans la seconde"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion de la seconde IB dans la première"

    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type':admin.VERTICAL}


class Compte_admin(admin.ModelAdmin):
    """admin pour les comptes normaux"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier compte dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second compte dans le premier"
    fieldsets = [
            (None, {'fields': ('nom', 'type', 'devise', 'ouvert')}),
            (u'information sur le compte', {'fields': ('banque', 'guichet', 'num_compte', 'cle_compte'), 'classes': ['collapse']}),
            (u'soldes', {'fields': ('solde_init', 'solde_mini_voulu', 'solde_mini_autorise'), 'classes': ['collapse']}),
            (u'moyens par défaut', {'fields': ('moyen_credit_defaut', 'moyen_debit_defaut'), 'classes': ['collapse']}),
            ]
    list_display = ('nom', 'solde', 'type', 'ouvert')
    list_filter = ('type', 'banque', 'ouvert')

class Titre_detenus_inline(admin.TabularInline):
    """inline pour les titres detenus"""
    model = Titres_detenus #@UndefinedVariable
    readonly_fields = ('titre', 'nombre', 'date')
    extra = 1

class Compte_titre_admin(admin.ModelAdmin):
    """compte titre avec inline"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier compte_titre dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du premier compte_titre dans le premier"
    fieldsets = [
            (None, {'fields': ('nom', 'type', 'devise', 'ouvert')}),
            (u'information sur le compte', {'fields': ('banque', 'guichet', 'num_compte', 'cle_compte'), 'classes': ['collapse']}),
            (u'soldes', {'fields': ('solde_init', 'solde_mini_voulu', 'solde_mini_autorise'), 'classes': ['collapse']}),
            (u'moyens par défaut', {'fields': ('moyen_credit_defaut', 'moyen_debit_defaut'), 'classes': ['collapse']}),
            ]
    list_display = ('nom', 'solde')
    list_filter = ('type', 'banque', 'ouvert')
    inlines = (Titre_detenus_inline,)

class Ope_admin(admin.ModelAdmin):
    """classe de gestion de l'amdmin pour les opes"""
    fieldsets = [
            (None, {'fields': ('compte', 'date', 'montant', 'tiers', 'moyen', 'cat')}),
            (u'informations diverses', {'fields': ('date_val', 'num_cheque', 'notes', 'exercice', 'ib'), 'classes': ['collapse']}),
            (u'pointage', {'fields': ('pointe', 'rapp'), 'classes': ['collapse']}),
            ]
    ordering = ('-date',)
    list_display = ('id', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat')
    list_filter = ('compte', 'date', 'pointe', 'rapp')
    search_fields = ['tiers__nom']

class Cours_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les  cours des titres """
    list_display = ('date', 'titre', 'valeur')
    list_editable = ('valeur',)
    list_filter = ('date', 'titre')

class Titre_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les titres"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier titre dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second titre dans le premier"

    list_display = ('nom', 'isin', 'last_cours')
    list_filter = ('type',)
    def has_add_permission(self, request): #@UnusedVariable
        return False

class Moyen_admin(admin.ModelAdmin):
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

class Histo_ope_titres_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour l'historique des operations sur titres (compta matiere)"""
    readonly_fields = ('titre', 'compte', 'nombre', 'date')
    list_filter = ('titre', 'compte', 'date')


class Tiers_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les tiers"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier tiers dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second tiers dans le premier"

    list_editable = ('nom', 'notes')
    list_display = ('id', 'nom', 'notes', 'is_titre')
    list_display_links = ('id',)
    list_filter = ('is_titre',)

class Ech_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les écheances d'operations"""
    list_display = ('id', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat')
    list_filter = ('compte', 'date')
    list_editable = ('date',)

class Banque_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les banques"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion de la première banque dans la seconde"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion de la seconde banque dans la première"

class Rapp_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les rapprochements"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier rapprochement dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second rapprochement dans le premier"

class Exo_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les exercices"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    def fusionne_a_dans_b(self, request, queryset):
        fusion(self, request, queryset, 'ab')
    fusionne_a_dans_b.short_description = u"fusion du premier exercice dans le second"
    def fusionne_b_dans_a(self, request, queryset):
        fusion(self, request, queryset, 'ba')
    fusionne_b_dans_a.short_description = u"fusion du second exercice dans le premier"

    list_filter = ('date_debut', 'date_fin')

class Gen_admin(admin.ModelAdmin):
    """classe de gestion de l'admin pour les preferences"""
    pass

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
admin.site.register(Histo_ope_titres, Histo_ope_titres_admin)
