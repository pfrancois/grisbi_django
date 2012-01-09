# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .models import Tiers, Titre, Cat, Ope, Banque, Cours, Ib, Exercice, Rapp, Moyen, Echeance, Generalite, Compte_titre, Ope_titre, Compte
from django.contrib import admin
from django.contrib import messages
from django.db import models
import django.forms as forms
from django.utils.safestring import mark_safe
from django.core import urlresolvers
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Q
import decimal

def fusion(request, queryset, sens):
    """fonction générique de fusion entre 2 objets"""
    nom_module = queryset[0]._meta.module_name
    if queryset.count() != 2:
        messages.error(request,
                       u"attention, vous devez selectionner 2 %(type)s et uniquement 2, vous en avez selectionné %(n)s" % {
                           'n':queryset.count(), 'type':nom_module})
        return
    obj_a = queryset[0]
    obj_b = queryset[1]
    if type(obj_a) != type(obj_b):
        messages.error(request, u"attention vous devez selectionner deux item du meme type")
        return
    try:
        if sens == 'ab':
            message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (
                nom_module, obj_a, obj_b)
            obj_a.fusionne(obj_b)
        else:
            message = u"fusion effectuée, dans la type \"%s\", \"%s\" a été fusionnée dans \"%s\"" % (
                nom_module, obj_b, obj_a)
            obj_b.fusionne(obj_a)
        messages.success(request, message)
    except Exception as inst:#TODO mieux gerer
        message = inst.__unicode__()
        messages.error(request, message)


class Modeladmin_perso(admin.ModelAdmin):
    save_on_top = True

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

    def fusionne_a_dans_b(self, request, queryset):
        fusion(request, queryset, 'ab')

    fusionne_a_dans_b.short_description = u"fusion de 1 dans 2"

    def fusionne_b_dans_a(self, request, queryset):
        fusion(request, queryset, 'ba')

    fusionne_b_dans_a.short_description = u"fusion de 2 dans 1"
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


class Cat_admin(Modeladmin_perso):
    """classe admin pour les categories"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type':admin.VERTICAL}


class Ib_admin(Modeladmin_perso):
    """admin pour les ib"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_editable = ('nom',)
    list_display = ('id', 'nom', 'type', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('type',)
    radio_fields = {'type':admin.VERTICAL}


class Compte_admin(Modeladmin_perso):
    """admin pour les comptes normaux"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a', 'action_supprimer_pointe', 'action_transformer_pointee_rapp']
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
            messages.error(request, err.strerror)

    action_supprimer_pointe.short_description = u"supprimer tous les statuts 'pointé' dans les comptes selectionnés"

    class RappForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        #rapp_f = forms.CharField(label=u'nom du rapprochement à creer', help_text=u"sous la forme compteAAAAMM")
        rapp_f = forms.ModelChoiceField(Rapp.objects.all(), required=False)
        date = forms.DateField()

    def action_transformer_pointee_rapp(self, request, queryset):
        if queryset.count() > 1:
            messages.error(request, u"attention, vous ne pouvez choisir qu'un seul compte")
            return HttpResponseRedirect(request.get_full_path())
        compte = queryset[0]
        form = None
        query_ope = compte.ope_set.filter(pointe=True).order_by('-date')
        if 'apply' in request.POST:
            form = self.RappForm(request.POST)
            if form.is_valid():
                rapp = form.cleaned_data['rapp_f']
                if not rapp:
                    rapp_date = form.cleaned_data['date'].year
                    last = Rapp.objects.filter(date__year=rapp_date).filter(ope__compte=compte).distinct()
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
                self.message_user(request, u"le compte %s a bien été rapproché (%s opération%s rapprochée%s)" % (queryset[0], count, plural, plural))
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.RappForm(initial={'_selected_action':request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'admin/add_rapp.djhtm', {'opes':query_ope, 'rapp_form':form, })

    action_transformer_pointee_rapp.short_description = "rapprocher un compte"


class Compte_titre_admin(Modeladmin_perso):
    """compte titre """
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    fields = Compte_admin.fields#on prend comme ca les meme champs
    list_display = ('nom', 'solde_titre', 'solde_rappro', 'date_rappro', 'nb_ope')
    list_filter = ('type', 'banque', 'ouvert')


class Ope_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les opes"""
    fields = ('compte', 'date', 'montant', 'tiers', 'moyen', 'cat', 'pointe','show_jumelle', 'show_mere', 'oper_titre',
              'notes', 'exercice', 'ib', 'date_val', 'num_cheque',  'rapp')
    readonly_fields = ('show_jumelle', 'show_mere', 'oper_titre', 'show_pmv')
    ordering = ('-date',)
    list_display = ('id', 'compte', 'date', 'montant', 'tiers', 'moyen', 'cat', 'rapp', 'pointe')
    list_filter = ('compte', 'date', 'moyen', 'pointe', 'rapp', 'exercice', 'cat__type')
    search_fields = ['tiers__nom']
    list_editable = ('pointe','montant')
    actions = ['action_supprimer_pointe','fusionne_a_dans_b', 'fusionne_b_dans_a', 'mul']
    #save_on_top = True
    save_as=True
    search_fields=['tiers__nom']
    ordering=['date']

    def show_jumelle(self, obj):
        """
        retourne le lien pour l'operation lié dans le cadre des virements entre comptes
        """
        if obj.jumelle_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.jumelle.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.jumelle))
        else:
            return "(aucun-e)"

    show_jumelle.short_description = "operation"

    def show_pmv(self, obj):
        """
        retourne le lien pour l'operation lié dans le cadre des plus ou moins values
        """

        if obj.ope_pmv_id:
            change_url = urlresolvers.reverse('admin:gsb_ope_change', args=(obj.ope_pmv.id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.ope_pmv))
        else:
            return "(aucun-e)"

    show_jumelle.short_description = "operation"

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

    def mul(self, request, queryset):
        #queryset.update(montant=models.F('montant') * -1)  #ca serait optimal de faire mais because virement pas facile
        for o in queryset:
            if o.jumelle:
                o.montant = o.montant * -1
                o.jumelle.montant = o.jumelle.montant * -1
                o.save()
                o.jumelle.save()
            else:
                o.montant = o.montant * -1
                o.save()
        return HttpResponseRedirect(request.get_full_path())

    mul.short_description = u"multiplier le montant des opérations selectionnnés par -1"

    def action_supprimer_pointe(self, request, queryset):
        #liste_id = queryset.values_list('id', flat=True)
        try:
            queryset.update(pointe=False)
            messages.success(request, u'suppression des statuts "pointé" des opérations selectionnées' )
        except Exception, err:
            messages.error(request, unicode(err))

    action_supprimer_pointe.short_description =  u'_suppression des statuts "pointé" des opérations selectionnées'

    def delete_view(self, request, object_id, extra_context=None):
        instance = self.get_object(request, admin.util.unquote(object_id))
        #on evite que cela soit une operation rapproche
        error = False
        if instance.rapp:
            messages.error(request, u'instance rapprochee')
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
            except IntegrityError, e:
                messages.error(request, e.strerror)


class Cours_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les  cours des titres """
    list_display = ('date', 'titre', 'valeur')
    list_editable = ('valeur',)
    list_filter = ('date', 'titre')
    ordering = ('-date',)


class Titre_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les titres"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_display = ('nom', 'isin', 'type', 'last_cours')
    fields = ('nom', 'isin', 'type', 'show_tiers')
    readonly_fields = ('tiers', 'show_tiers')
    list_filter = ('type',)
    formfield_overrides = {
        models.TextField:{'widget':admin.widgets.AdminTextInputWidget},
        }

    def show_tiers(self, obj):
        if obj.tiers_id:
            change_url = urlresolvers.reverse('admin:gsb_tiers_change', args=(obj.tiers_id,))
            return mark_safe('<a href="%s">%s</a>' % (change_url, obj.tiers))
        else:
            return "(aucun-e)"

    show_tiers.short_description = "tiers"


class Moyen_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les moyens de paiements"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_filter = ('type',)
    fields = ['type', 'nom']

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())

    list_display = ('nom', 'type', 'nb_ope')


class Tiers_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les tiers"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_editable = ('nom', 'notes')
    list_display = ('id', 'nom', 'notes', 'is_titre', 'nb_ope')
    list_display_links = ('id',)
    list_filter = ('is_titre',)
    search_fields = ['nom']
    formfield_overrides = {models.TextField:{'widget':forms.TextInput}, }

    def nb_ope(self, obj):
        return '%s' % (obj.ope_set.count())


class Ech_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les écheances d'operations"""
    list_display = ('id', 'valide', 'date', 'compte', 'compte_virement', 'montant', 'tiers', 'cat', 'intervalle', 'periodicite')
    list_filter = ('compte', 'compte_virement', 'date', 'periodicite')
    actions = ['check_ech']

    def check_ech(self, request, queryset):
        Echeance.check(request=request, queryset=queryset)
    check_ech.short_description =u"verifier si des echeances sont à enregistrer"

class Banque_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les banques"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']


class Rapp_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les rapprochements"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_display = ('nom', 'date')


class Exo_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les exercices"""
    actions = ['fusionne_a_dans_b', 'fusionne_b_dans_a']
    list_filter = ('date_debut', 'date_fin')


class Gen_admin(Modeladmin_perso):
    """classe de gestion de l'admin pour les preferences"""
    pass


class Ope_titre_admin(Modeladmin_perso):
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
