# -*- coding: utf-8 -*-
# Create your views here.
from __future__ import absolute_import
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from .models import Generalite, Compte, Ope, Compte_titre, Moyen, Titre, Cours, Tiers, Ope_titre, Cat
import datetime
from . import forms as gsb_forms
from django.db import models
import decimal
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_unicode
from django.contrib import messages
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from django.core import exceptions as django_exceptions
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator

def has_changed(instance, field):
    if not instance.pk:
        return False
    old_value = getattr(instance.__class__._default_manager.get(pk=instance.pk), field)
    new_value = getattr(instance, field)
    if hasattr(new_value, "file"):
        # Handle FileFields as special cases, because the uploaded filename could be
        # the same as the filename that's already there even though there may
        # be different file contents.
        from django.core.files.uploadedfile import UploadedFile
        return isinstance(new_value.file, UploadedFile)

    return not getattr(instance, field) == old_value

@login_required
def index(request):
    """
    view index
    """
    t = loader.get_template('gsb/index.djhtm')
    if Generalite.gen().affiche_clot:
        bq = Compte.objects.filter(type__in=('b', 'e', 'p'))
        pl = Compte_titre.objects.all()
    else:
        bq = Compte.objects.filter(type__in=('b', 'e', 'p'), ouvert=True)
        pl = Compte_titre.objects.filter(ouvert=True)
        #calcul du solde des bq
    total_bq = Ope.objects.filter(mere__exact=None,
                                  compte__type__in=('b', 'e', 'p')).aggregate(solde=models.Sum('montant'))['solde']
    if total_bq is None:
        total_bq = decimal.Decimal()
        #calcul du solde des pla
    total_pla = decimal.Decimal()
    id_pla = Compte_titre.objects.all().values_list("id", flat=True)
    solde_espece = Ope.objects.filter(compte__id__in=list(id_pla), mere__exact=None).aggregate(solde=models.Sum('montant'))
    if solde_espece['solde']:
        total_pla += solde_espece['solde']
    for p in pl:
        total_pla += p.solde_titre()
    nb_clos = Compte.objects.filter(ouvert=False).count()
    c = RequestContext(request, {
        'titre':'liste des comptes',
        'liste_cpt_bq':bq,
        'liste_cpt_pl':pl,
        'total_bq':total_bq,
        'total_pla':total_pla,
        'total':total_bq + total_pla,
        'nb_clos':nb_clos,
        })
    return HttpResponse(t.render(c))

@login_required
def cpt_detail(request, cpt_id, all=False, rapp=False):
    """
    view qui affiche la liste des operation de ce compte
    @param request:
    @param cpt_id: id du compte demande
    @param rapp: si true, affiche l'ensemble des operations
    """
    c = get_object_or_404(Compte, pk=cpt_id)
    if c.type in ('t',):
        titre = True
    else:
        titre = False
    if not titre:
        date_rappro = c.date_rappro()
        solde_rappro = c.solde(rapp=True)
        date_limite = datetime.date.today() - datetime.timedelta(days=settings.NB_JOURS_AFF)
        q = Ope.non_meres().filter(compte__pk=cpt_id).order_by('-date')
        if all:
            nb_ope_vieilles = 0
            nb_ope_rapp = 0
            solde = c.solde()
        else:
            if rapp:
                nb_ope_vieilles = 0
                nb_ope_rapp = 0
                solde = c.solde(rapp=True)
                q = q.exclude(rapp__isnull=True)
            else:
                nb_ope_vieilles = Ope.non_meres().filter(compte__pk=cpt_id).filter(date__lte=date_limite).filter(rapp__isnull=True).count()
                nb_ope_rapp = q.filter(rapp__isnull=False).filter(date__gte=date_limite).count()
                q = q.filter(rapp__isnull=True).filter(date__gte=date_limite)
                solde = c.solde()
                #gestion du tri
        try:
            sort = request.GET.get('sort')
        except (ValueError, TypeError):
            sort = ''
        if sort:
            sort = unicode(sort)
            q = q.order_by(sort)
            sort_get = u"&sort=%s" % sort
        else:
            q = q.order_by('-date')
            sort_get = None
        q = q.select_related('tiers', 'cat', 'rapp')
        #gestion pagination
        paginator = Paginator(q, 50)
        try:
            page = int(request.GET.get('page'))
        except (ValueError, TypeError):
            page = 1
        try:
            opes = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            opes = paginator.page(1)
        except (EmptyPage, InvalidPage):
            opes = paginator.page(paginator.num_pages)
        template = loader.get_template('gsb/cpt_detail.djhtm')
        return HttpResponse(
            template.render(
                RequestContext(
                    request,
                        {
                        'compte':c,
                        'list_ope':opes,
                        'nbrapp':nb_ope_rapp,
                        'nbvieilles':nb_ope_vieilles,
                        'titre':c.nom,
                        'solde':solde,
                        'date_limite':date_limite,
                        'nb_j':settings.NB_JOURS_AFF,
                        "sort":sort_get,
                        "date_r":date_rappro,
                        "solde_r":solde_rappro
                    }
                )
            )
        )
    else:
        compte = get_object_or_404(Compte_titre, pk=cpt_id)
        #recupere la liste des titres qui sont utilise dans ce compte
        titre_sans_sum = compte.titre.all().distinct()
        titres = []
        for t in titre_sans_sum:
            invest = t.investi(compte)
            total = t.encours(compte)
            nb = t.nb(compte)
            if abs(nb) > decimal.Decimal('0.01'):
                titres.append({'nom':t.nom, 'type':t.get_type_display(), 'nb':nb, 'invest':invest,
                               'pmv':total - invest, 'total':total, 'id':t.id, 't':t, 'rapp':t.encours(rapp=True, compte=compte)})
        template = loader.get_template('gsb/cpt_placement.djhtm')
        return HttpResponse(
            template.render(
                RequestContext(
                    request,
                        {
                        'compte':compte,
                        'titre':compte.nom,
                        'solde':compte.solde(),
                        'titres':titres,
                        'especes':compte.solde_espece(),
                        'especes_rapp':compte.solde_espece(rapp=True),
                        'solde_rapp':compte.solde(rapp=True),
                        'solde_titre_rapp':compte.solde_titre(rapp=True),
                        }
                )
            )
        )


@login_required
def ope_detail(request, pk):
    """
    view, une seule operation
    @param request:
    @param pk: id de l'ope
    """
    ope = get_object_or_404(Ope.objects.select_related(), pk=pk)
    #logger = logging.getLogger('gsb')
    if ope.jumelle is not None:
        #------un virement--------------
        if ope.montant > 0:
            ope = ope.jumelle
        if request.method == 'POST':#creation du virement
            form = gsb_forms.VirementForm(data=request.POST, ope=ope)
            if form.is_valid():
                if not ope.rapp and not ope.jumelle.rapp:
                    form.save()
                    messages.success(request, 'modification du virement effectue')
                    return HttpResponseRedirect(ope.jumelle.compte.get_absolute_url())
                else:
                    if ope.rapp:
                        compte = ope.compte
                    else:
                        compte = ope.jumelle.compte
                    messages.error(request, u"impossible de modifier car le virement coté %s est rapprochée" % compte)
        else:
            form = gsb_forms.VirementForm(ope=ope)
        return render(request, 'gsb/vir.djhtm',
                {'titre_long':u'modification virement interne %s' % ope.id,
                 'titre':u'modification',
                 'form':form,
                 'ope':ope}
        )
    #--------ope normale----------
    else:#sinon c'est une operation normale
        if ope.filles_set.all().count() > 0: #c'est une ope mere
            messages.error(request, u"attention cette operation n'est pas éditable car c'est une ope mere.")
            HttpResponseRedirect(ope.compte.get_absolute_url())
        if request.method == 'POST':
            form = gsb_forms.OperationForm(request.POST, instance=ope)
            if form.is_valid():
                if not form.cleaned_data['tiers']:
                    form.instance.tiers = Tiers.objects.get_or_create(nom=form.cleaned_data['nouveau_tiers'],
                                                                      defaults={'nom':form.cleaned_data['nouveau_tiers']
                                                                          , }
                    )[0]
                    messages.info(request, u"tiers '%s' créé" % form.instance.tiers.nom)
                if not ope.rapp:
                    messages.success(request, u"opération modifiée")
                    ope = form.save()
                else:
                    #verification que les données essentielles ne sont pas modifiés
                    if (has_changed(ope,'montant') or  has_changed(ope,'compte') or has_changed(ope,'pointe') or has_changed(ope,'jumelle') or has_changed(ope,'mere')):
                        messages.error(request, u"impossible de modifier l'opération car elle est rapprochée")
                    else:
                        messages.success(request, u"opération modifiée")
                        ope = form.save()
                return HttpResponseRedirect(ope.compte.get_absolute_url())
        else:
            form = gsb_forms.OperationForm(instance=ope)
        return render(request, 'gsb/ope.djhtm',
                {'titre_long':u'modification opération %s' % ope.id,
                 'titre':u'modification',
                 'form':form,
                 'ope':ope}
        )


@login_required
def ope_new(request, cpt_id=None):
    """
    creation d'une nouvelle operation
    """
    if cpt_id:
        cpt = get_object_or_404(Compte.objects.select_related(), pk=cpt_id)
    else:
        cpt = None
        #logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.OperationForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['tiers']:
                form.instance.tiers = Tiers.objects.get_or_create(nom=form.cleaned_data['nouveau_tiers'],
                                                                  defaults={'nom':form.cleaned_data['nouveau_tiers'], }
                )[0]
                messages.info(request, u"tiers '%s' créé" % form.instance.tiers.nom)
            ope = form.save()

            messages.success(request, u"Opération '%s' crée" % ope)
            return HttpResponseRedirect(ope.compte.get_absolute_url())
        else:
            #TODO message
            return render(request, 'gsb/ope.djhtm',
                    {'titre':u'création',
                     'titre_long':u'création opération',
                     'form':form,
                     'cpt':cpt}
            )
    else:
        if not cpt_id:
            try:
                cpt = Compte.objects.get(Compte.objects.select_related(), pk=settings.ID_CPT_M)
            except Compte.DoesNotExists:
                messages.error(request, u"pas de compte par defaut")
                return HttpResponseRedirect(reverse('gsb.views.index'))
        form = gsb_forms.OperationForm(initial={'compte':cpt, 'moyen':cpt.moyen_debit_defaut})
        return render(request, 'gsb/ope.djhtm',
                {'titre':u'création',
                 'titre_long':u'création opération',
                 'form':form,
                 'cpt':cpt}
        )


@login_required
def vir_new(request, cpt_id=None):
    if cpt_id:
        cpt = get_object_or_404(Compte.objects.select_related(), pk=cpt_id)
    else:
        cpt = get_object_or_404(Compte.objects.select_related(), pk=settings.ID_CPT_M)
        #logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.VirementForm(data=request.POST)
        if form.is_valid():
            ope = form.save()
            messages.success(request, u"virement crée %s" % ope.jumelle.tiers)
            return HttpResponseRedirect(ope.jumelle.compte.get_absolute_url())
        else:
            return render(request, 'gsb/vir.djhtm',
                    {'titre_long':u'création virement interne ',
                     'titre':u'Création',
                     'form':form,
                     'cpt':cpt}
            )
    else:
        form = gsb_forms.VirementForm(
            initial={'compte_origine':get_object_or_404(Compte.objects.select_related(), pk=settings.ID_CPT_M),
                     'moyen_origine':Moyen.objects.filter(type='v')[0], 'compte_destination':cpt,
                     'moyen_destination':Moyen.objects.filter(type='v')[0]})
        return render(request, 'gsb/vir.djhtm',
                {'titre':u'Création',
                 'titre_long':u'Création virement interne ',
                 'form':form,
                 'cpt':cpt}
        )


@login_required
def ope_delete(request, pk):
    ope = get_object_or_404(Ope.objects.select_related(), pk=pk)
    if request.method == 'POST':
        if ope.rapp:
            messages.error(request, u"impossible d'effacer une opération rapprochée")
            return HttpResponseRedirect(ope.get_absolute_url())
        else:
            if ope.jumelle:
                if ope.jumelle.rapp:
                    messages.error(request, u"impossible d'effacer une opération rapprochée")
                    return HttpResponseRedirect(ope.get_absolute_url())
                else:
                    ope.jumelle.delete()
                    ope.delete()
                    messages.success(request, u"virement effacé")
            else:
                ope.delete()
                messages.success(request, u"opération effacé")
    else:
        return HttpResponseRedirect(ope.get_absolute_url())
        #si pas de formulaire, c'est que c'est une tentative d'intrusion
    return HttpResponseRedirect(ope.compte.get_absolute_url())


@login_required
def maj_cours(request, pk):
    titre = get_object_or_404(Titre.objects.select_related(), pk=pk)
    if request.method == 'POST':
        form = gsb_forms.MajCoursform(request.POST)
        if form.is_valid():
            titre = form.cleaned_data['titre']
            date = form.cleaned_data['date']
            if not Cours.objects.filter(titre=titre, date=date).exists():
                messages.info(request, u"cours crée")
                titre.cours_set.create(valeur=form.cleaned_data['cours'], date=date)
            else:
                titre.cours_set.get(date=date).valeur = form.cleaned_data['cours']
            compte = Ope_titre.objects.filter(titre=titre).latest('date').compte
            return HttpResponseRedirect(compte.get_absolute_url())
    else:
        form = gsb_forms.MajCoursform(initial={'titre':titre, 'cours':titre.last_cours, 'date':titre.last_cours_date})
        #petit bidoullage afin recuperer le compte d'origine
    if titre.compte_titre_set.all().distinct().count() == 1:
        url = titre.compte_titre_set.all().distinct()[0].get_absolute_url()
    else:
        url = reverse("gsb.views.index")
    return render(request, "gsb/maj_cours.djhtm", {"titre":u"maj du titre '%s'" % titre.nom, "form":form, "url":url})


@login_required
def cpt_titre_espece(request, cpt_id, all=False, rapp=False):
    """view qui affiche la liste des operations especes d'un compte titre cpt_id
    si date_limite, utilise la date limite sinon affiche toute les ope espece
    @param rapp"""
    compte = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    q = Ope.non_meres().filter(compte__pk=cpt_id).order_by('-date')
    date_rappro = compte.date_rappro()
    solde_rappro = compte.solde_espece(rapp=True)
    if all:
        q = q
    else:
        if rapp:
            q = q.filter(rapp__isnull=False)
        else:
            q = q.filter(rapp__isnull=True)
    q = q.select_related('tiers', 'tiers__titre', 'cat', 'rapp')
    paginator = Paginator(q, 50)
    try:
        page = int(request.GET.get('page'))
    except (ValueError, TypeError):
        page = 1
    try:
        opes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        opes = paginator.page(1)
    except (EmptyPage, InvalidPage):
        opes = paginator.page(paginator.num_pages)
    template = loader.get_template('gsb/cpt_placement_espece.djhtm')
    return HttpResponse(
        template.render(
            RequestContext(
                request,
                    {
                    'compte':compte,
                    'list_ope':opes,
                    'titre':"%s: Especes" % compte.nom,
                    'solde':compte.solde_espece(),
                    'nbrapp':Ope.non_meres().filter(compte__pk=cpt_id).filter(rapp__isnull=False).count(),
                    "date_r":date_rappro,
                    "solde_r":solde_rappro,
                    }
            )
        )
    )


@login_required
def titre_detail_cpt(request, cpt_id, titre_id, all=False, rapp=False):
    """view qui affiche la liste des operations relative a un titre (titre_id) d'un compte titre (cpt_id)
    si rapp affiche uniquement les rapp
    si all affiche toute les ope
    sinon affiche uniquement les non rapp"""
    titre = get_object_or_404(Titre.objects.select_related(), pk=titre_id)
    compte = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    request.session['titre'] = titre_id

    date_rappro = compte.date_rappro()
    solde_rappro = titre.encours(compte=compte, rapp=True)
    q = Ope_titre.objects.filter(compte__pk=cpt_id).order_by('-date').filter(titre=titre)
    if all:
        pass
    else:
        #on prend comme reference les ope especes
        if rapp:
            q = q.filter(ope__rapp__isnull=False)
        else:
            q = q.filter(ope__rapp__isnull=True)
    paginator = Paginator(q, 50)
    try:
        page = int(request.GET.get('page'))
    except (ValueError, TypeError):
        page = 1
    try:
        opes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        opes = paginator.page(1)
    except (EmptyPage, InvalidPage):
        opes = paginator.page(paginator.num_pages)
    template = loader.get_template('gsb/cpt_placement_titre.djhtm')
    return HttpResponse(
        template.render(
            RequestContext(
                request,
                    {
                    'compte':compte,
                    'titre_id':titre.id,
                    'list_ope':opes,
                    'titre':"%s: %s" % (compte.nom, titre.nom),
                    'encours':titre.encours(compte),
                    't':titre,
                    'nb_titre':titre.nb(compte),
                    'nb_r':titre.nb(compte, rapp=True),
                    'date_rappro':date_rappro,
                    'solde_rappro':solde_rappro,
                    'investi_r':titre.investi(compte, rapp=True),
                    'pmv':titre.encours(compte) - titre.investi(compte)
                }
            )
        )
    )


@login_required
def ope_titre_detail(request, pk):
    """
    view, une seule operation mais pour les comptes titres
    @param request:
    @param pk: id de l'ope
    """
    ope = get_object_or_404(Ope_titre.objects.select_related(), pk=pk)
    if request.method == 'POST':
        #date_initial = ope.date#inutile
        form = gsb_forms.Ope_titreForm(request.POST, instance=ope)
        if form.is_valid():
            if ope.ope.rapp is None:
                try:
                    form.save()
                    messages.info(request, u"opération modifiée")
                except django_exceptions.ImproperlyConfigured as e:
                    messages.error(request, e.unicode())
            else:
                messages.error(request, u"opération impossible a modifier, elle est rapprochée")
            return HttpResponseRedirect( reverse('gsb_cpt_titre_detail',
                                                 kwargs={'cpt_id':ope.compte.id,
                                                         'titre_id':ope.titre.id}
                                                 )
                                        )
    else:
        form = gsb_forms.Ope_titreForm(instance=ope)
    if ope.ope is not None:
        rapp = bool(ope.ope.rapp_id)
    else:
        rapp = False
    return render(request, 'gsb/ope_titre_detail.djhtm',
            {'titre_long':u'opération sur titre %s' % ope.id,
             'titre':u'modification',
             'form':form,
             'ope':ope,
             'rapp':rapp}
    )


@login_required
def ope_titre_delete(request, pk):
    ope = get_object_or_404(Ope_titre.objects.select_related(), pk=pk)
    if request.method == 'POST':
        if ope.ope and ope.ope.rapp:
            messages.error(request, u"impossible d'effacer une operation rapprochée")
            return HttpResponseRedirect(ope.get_absolute_url())
        compte_id = ope.compte.id
        titre_id = ope.titre.id
        #gestion des cours inutiles
        cours = Cours.objects.filter(date=ope.date, titre=ope.titre)
        if cours.exists():
            s = u'%s' % cours
            cours.delete()
            messages.success(request, u'cours effacé: %s' % s)
        if ope.ope:
            ope.ope.delete()
        s = u'%s' % ope.id
        ope.delete()
        messages.success(request, u'ope effacé id %s' % s)
        return HttpResponseRedirect( reverse('gsb_cpt_titre_detail',
                                             kwargs={'cpt_id':compte_id,
                                                     'titre_id':titre_id}
                                             )
                                    )
    else:
        return HttpResponseRedirect(ope.get_absolute_url())


@login_required
def ope_titre_achat(request, cpt_id):
    compte = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    try:
        titre_id = request.session['titre']
        titre = Titre.objects.get(id=titre_id)
    except Titre.DoesNotExist:#on est dans le cas où l'on viens d'une page avec un titre qui n'existe pas
        messages.error(request, u"attention le titre demandé intialement n'existe pas")
        titre_id = None
    except AttributeError:#on est dans le cas où l'on viens d'une page sans titre defini
        titre_id = None

    if request.method == 'POST':
        form = gsb_forms.Ope_titre_add_achatForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['titre']:
                titre = form.cleaned_data['titre']
            else:
                titre = Titre.objects.get_or_create(nom=form.cleaned_data['nouveau_titre'],
                                                    defaults={'nom':form.cleaned_data['nouveau_titre'],
                                                              'type':'ZZZ',
                                                              'isin':form.cleaned_data['nouvel_isin']
                                                    }
                )[0]
                messages.info(request, u"nouveau titre crée: %s" % titre)
            compte = form.cleaned_data['compte_titre']
            if form.cleaned_data['compte_espece']:
                virement = form.cleaned_data['compte_espece']
            else:
                virement = None
            compte.achat(titre=titre,
                     nombre=form.cleaned_data['nombre'],
                     prix=form.cleaned_data['cours'],
                     date=form.cleaned_data['date'],
                     virement_de=virement,
                     frais=form.cleaned_data['frais'])
            messages.info(request, u"nouvel achat de %s %s @ %s le %s" % (form.cleaned_data['nombre'],
                                                                      form.cleaned_data['titre'],
                                                                      form.cleaned_data['cours'],
                                                                      form.cleaned_data['date']))
            return HttpResponseRedirect(compte.get_absolute_url())
    else:
        if titre_id:
            form = gsb_forms.Ope_titre_add_achatForm(initial={'compte_titre':compte, 'titre':titre})
        else:
            form = gsb_forms.Ope_titre_add_achatForm(initial={'compte_titre':compte})
    titre = u' nouvel achat sur %s' % compte.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
            {'titre_long':titre,
             'titre':u'modification',
             'form':form,
             'cpt':compte,
             'sens':'achat'}
    )


@login_required
def ope_titre_vente(request, cpt_id):
    compte = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    try:
        titre_id = request.session['titre']
        titre = Titre.objects.get(id=titre_id)
    except Titre.DoesNotExist:#on est dans le cas où l'on viens d'une page avec un titre qui n'existe pas
        messages.error(request, u"attention le titre demandé intialement n'existe pas")
        titre_id = None
    except KeyError:#on est dans le cas où l'on viens d'une page sans titre defini
        titre_id = None

    if compte.titre.all().distinct().count() < 1:
        messages.error(request, 'attention, ce compte ne possède aucun titre. donc vous ne pouvez pas vendre')
        return HttpResponseRedirect(compte.get_absolute_url())

    if request.method == 'POST':
        form = gsb_forms.Ope_titre_add_venteForm(data=request.POST, cpt=compte)
        if form.is_valid():
            compte = form.cleaned_data['compte_titre']
            if form.cleaned_data['compte_espece']:
                virement = form.cleaned_data['compte_espece']
            else:
                virement = None
            compte.vente(titre=form.cleaned_data['titre'],
                     nombre=form.cleaned_data['nombre'],
                     prix=form.cleaned_data['cours'],
                     date=form.cleaned_data['date'],
                     virement_vers=virement)
            messages.info(request, u"nouvel vente de %s %s @ %s le %s" % (form.cleaned_data['nombre'],
                                                                      form.cleaned_data['titre'],
                                                                      form.cleaned_data['cours'],
                                                                      form.cleaned_data['date']))
            return HttpResponseRedirect(compte.get_absolute_url())
    else:
        if titre_id:
            form = gsb_forms.Ope_titre_add_venteForm(initial={'compte_titre':compte, 'titre':titre}, cpt=compte)
        else:
            form = gsb_forms.Ope_titre_add_venteForm(initial={'compte_titre':compte}, cpt=compte)
    titre = u' nouvelle vente sur %s' % compte.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
            {'titre_long':titre,
             'titre':u'modification',
             'form':form,
             'cpt':compte,
             'sens':'vente'}
    )


@login_required
def view_maj_cpt_titre(request, cpt_id):
    """mise a jour global d'un portefeuille"""
    cpt = Compte_titre.objects.get(id=cpt_id)
    liste_titre_original = cpt.titre.all().distinct()
    liste_titre = []
    if liste_titre_original.count() < 1:
        messages.error(request, u'attention, ce compte ne possède aucun titre. donc vous ne pouvez mettre a jour')
        return HttpResponseRedirect(cpt.get_absolute_url())
    for l in liste_titre_original:
        liste_titre.append(l)
    if request.method == 'POST':
        form = gsb_forms.Majtitre(data=request.POST, titres=liste_titre)
        if form.is_valid():
            for titre_en_cours in liste_titre:
                if form.cleaned_data[titre_en_cours.isin] is None:
                    continue
                tab = form.cleaned_data[titre_en_cours.isin].partition('@')
                nb = decimal.Decimal(tab[0])
                cours = decimal.Decimal(tab[2])
                if nb != '0' and nb:
                    if form.cleaned_data['sociaux']:
                        frais = nb * cours * decimal.Decimal(str(settings.TAUX_VERSEMENT))
                        cpt.achat(titre_en_cours, nb, cours, date=form.cleaned_data['date'], frais=frais,
                                  cat_frais=Cat.objects.get(id=settings.ID_CAT_COTISATION), )
                    else:
                        cpt.achat(titre_en_cours, nb, cours, date=form.cleaned_data['date'])
                else:
                    if not Cours.objects.filter(date=form.cleaned_data['date'], titre=titre_en_cours).exists() and\
                       cours:
                        Cours.objects.create(date=form.cleaned_data['date'], titre=titre_en_cours, valeur=cours)

            return HttpResponseRedirect(cpt.get_absolute_url())
    else:
        form = gsb_forms.Majtitre(titres=liste_titre)
    return render(request, 'gsb/maj_cpt_titre.djhtm',
            {'titre_long':u'operations sur le %s' % cpt.nom,
             'titre':u'ope',
             'form':form,
             'titres':liste_titre,
             'compte':cpt}
    )


@login_required
def search_opes(request):
    if request.method == 'POST':
        form = gsb_forms.SearchField(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            compte = data['compte']
            q = Ope.objects.filter(compte=compte, date__gte=data['date_min'], date__lte=data['date_max'])
            sort = request.GET.get('sort')
            if sort:
                sort = unicode(sort)
                q = q.order_by(sort)
                sort_get = u"&sort=%s" % sort
            else:
                sort_get = ""
                q = q.order_by('-date')
            q = q.select_related('tiers', 'cat', 'rapp', 'moyen', 'jumelle', 'ope_titre')[:100]
            return render(request, 'templates_perso/search.djhtm', {'form':form,
                                                                    'list_ope':q,
                                                                    'titre':u'recherche des %s premières opérations du compte %s' % (q.count(), compte.nom),
                                                                    "sort":sort_get,
                                                                    'date_max':data['date_max'],
                                                                    'solde':compte.solde(datel=data['date_max'])})
        else:
            date_max = Ope.objects.aggregate(element=models.Max('date'))['element']
    else:
        date_min = Ope.objects.aggregate(element=models.Min('date'))['element']
        date_max = Ope.objects.aggregate(element=models.Max('date'))['element']
        form = gsb_forms.SearchField(initial={'date_min':date_min, 'date_max':date_max})

    return render(request, 'templates_perso/search.djhtm', {'form':form,
                                                            'list_ope':None,
                                                            'titre':'recherche',
                                                            "sort":"",
                                                            'date_max':date_max,
                                                            'solde':None})

class ExportViewBase(FormView):
    template_name = 'gsb/param_export.djhtm'
    form_class = gsb_forms.Exportform
    def export(self, query=None,export_all=False):
        """
        fonction principale mais abstraite
        """
        django_exceptions.ImproperlyConfigured("attention, il doit y avoir une methode qui extrait effectivement")
    def get_initial(self):
        """gestion des donnees initiales"""
        #prend la date de la premiere operation de l'ensemble des compte
        date_min = Ope.objects.aggregate(element=models.Min('date'))['element']
        #la derniere operation
        date_max = Ope.objects.aggregate(element=models.Max('date'))['element']
        return {'date_min':date_min, 'date_max':date_max}
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """on a besoin pour le method decorator"""
        return super(ExportViewBase, self).dispatch(*args, **kwargs)
    def form_valid(self, form):
        """si le form est valid"""
        data = form.cleaned_data
        comptes = [cpt.id for cpt in data['compte']]
        if comptes == [] or len(comptes) == Compte.objects.all().count():
            #en fonction des dates demandes
            query = Ope.objects.filter( date__gte=data['date_min'], date__lte=data['date_max'])
            export_total = True
        else:
            #o rajoute un compte
            query = Ope.objects.filter(compte__pk__in=comptes, date__gte=data['date_min'], date__lte=data['date_max'])
            export_total = False
        if query.count() > 0:#si des operations existent
            reponse = self.export(query=query, export_all=export_total)
            return reponse
        else:
            messages.error(self.request, u"attention pas d'opérations pour la selection demandée")
            return self.render_to_response({'form':form, })
