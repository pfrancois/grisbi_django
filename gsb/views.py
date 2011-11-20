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
                                  compte__type__in=('b', 'e', 'p')).aggregate(solde=models.Sum('montant'))[
    'solde']
    if total_bq is None:
        total_bq = decimal.Decimal()
    #calcul du solde des pla
    total_pla = decimal.Decimal()
    id_pla = Compte_titre.objects.all().values_list("id",flat=True)
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
    try:
        date_rappro=Ope.objects.filter(compte__pk=cpt_id).latest('rapp__date').date
    except Ope.DoesNotExist:
        date_rappro=None
    solde_rappro=c.solde(rapp=True)
    date_limite = datetime.date.today() - datetime.timedelta(days=settings.NB_JOURS_AFF)
    if c.type in ('t',):
        #on prend les ope_titres
        c = get_object_or_404(Compte_titre, pk=cpt_id)
        date_limite = datetime.date.today() - datetime.timedelta(days=settings.NB_JOURS_AFF_TITRE)
        titre = True
    else:
        titre = False
    if not titre:
        q = Ope.non_meres().filter(compte__pk=cpt_id).order_by('-date')
        if all:
            nb_ope_vielles = 0
            nb_ope_rapp = 0
            solde = c.solde()
        else:
            if rapp:
                nb_ope_vielles = 0
                nb_ope_rapp = 0
                solde = c.solde(rapp=True)
                q = q.exclude(rapp__isnull=True)
            else:
                nb_ope_vielles = Ope.non_meres().filter(compte__pk=cpt_id).filter(date__lte=date_limite).filter(rapp__isnull=True).count()
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
            print "'", sort, "'"
            q = q.order_by(sort)
            sort_get = u"&sort=%s"%sort
        else:
            q = q.order_by('-date')
            sort_get = None
        q = q.select_related('tiers', 'cat','rapp')
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
                        'nbvielles':nb_ope_vielles,
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
        #recupere la liste des titres qui sont utilise dans ce compte
        titre_sans_sum = c.titre.all().distinct()
        titres = []
        for t in titre_sans_sum:
            invest = t.investi(c)
            total = t.encours(c)
            nb = t.nb(c)
            if abs(nb) > decimal.Decimal('0.01'):
                titres.append({'nom':t.nom, 'type':t.get_type_display(), 'nb':nb, 'invest':invest,
                               'pmv':total - invest, 'total':total, 'id':t.id, 't':t})
        especes = super(Compte_titre, c).solde()
        template = loader.get_template('gsb/cpt_placement.djhtm')
        return HttpResponse(
            template.render(
                RequestContext(
                    request,
                        {
                        'compte':c,
                        'titre':c.nom,
                        'solde':c.solde(),
                        'titres':titres,
                        'especes':especes,
                        'date_limite':date_limite,
                        'nb_j':settings.NB_JOURS_AFF_TITRE
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
                else:
                    if ope.rapp:
                        compte = ope.compte
                    else:
                        compte = ope.jumelle.compte
                    messages.error(request, u"impossible de modifier car le virement coté %s est rapprochée" % compte)
                return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',
                                                    kwargs={'cpt_id':ope.jumelle.compte_id}))
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
            HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
        if request.method == 'POST':
            form = gsb_forms.OperationForm(request.POST, instance=ope)
            if form.is_valid():
                if not form.cleaned_data['tiers']:
                    form.instance.tiers = Tiers.objects.get_or_create(nom=form.cleaned_data['nouveau_tiers'],
                                                                      defaults={'nom':form.cleaned_data['nouveau_tiers']
                                                                          , }
                    )[0]
                    messages.info(request, u"tiers '%s' créé"%form.instance.tiers.nom)
                if not ope.rapp:
                    messages.success(request, u"opération modifiée")
                    ope = form.save()
                else:
                    messages.error(request, u"impossible de modifier l'opération car elle est rapprochée")
                return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
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
                messages.info(request, u"tiers '%s' créé"%form.instance.tiers.nom)
            ope = form.save()

            messages.success(request, u"Opération '%s' crée"%ope)
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
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
                cpt = get_object(Compte.objects.select_related(), pk=settings.ID_CPT_M)
            except Compte.DoesNotExists:
                messages.error(request, u"pas de compte par defaut")
                return HttpResponseRedirect(reverse('mysite.gsb.views.index'))
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
            messages.success(request, u"virement crée %s"%ope.jumelle.tiers)
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.jumelle.compte_id}))
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
            return HttpResponseRedirect(reverse('mysite.gsb.views.ope_detail', kwargs={'pk':ope.id}))
        else:
            if ope.jumelle:
                if ope.jumelle.rapp:
                    messages.error(request, u"impossible d'effacer une opération rapprochée")
                    return HttpResponseRedirect(reverse('mysite.gsb.views.ope_detail', kwargs={'pk':ope.id}))
                else:
                    ope.jumelle.delete()
                    ope.delete()
                    messages.success(request, u"virement effacé")
            else:
                ope.delete()
                messages.success(request, u"opération effacé")
    else:
        return HttpResponseRedirect(reverse('mysite.gsb.views.ope_detail', kwargs={'pk':ope.id}))
    #si pas de formulaire, c'est que c'est une tentative d'intrusion
    return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))


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
            cpt_id = Ope_titre.objects.filter(titre=titre).latest('date').compte_id
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':cpt_id}))
    else:
        form = gsb_forms.MajCoursform(initial={'titre':titre, 'cours':titre.last_cours, 'date':titre.last_cours_date})
    #petit bidoullage afin recuperer le compte d'origine
    if titre.compte_titre_set.all().distinct().count() == 1:
        url = "gsb.views.cpt_detail"
        cpt_id = titre.compte_titre_set.all().distinct()[0].id
    else:
        url = "gsb.views.index"
        cpt_id = None
    return render(request, "gsb/maj_cours.djhtm", {"titre":u"maj du titre '%s'" % titre.nom, "form":form, "url":url,
                                                   "cpt":cpt_id})


@login_required
def cpt_titre_espece(request, cpt_id, date_limite=False):
    """view qui affiche la liste des operations especes d'un compte titre cpt_id
    si date_limite, utilise la date limite sinon affiche toute les ope espece"""
    c = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    if date_limite:
        q = Ope.non_meres().filter(compte__pk=cpt_id).order_by('-date').filter(date__gte=date_limite).filter(
            rapp__isnull=True)
        nbvielles = Ope.non_meres().filter(compte__pk=cpt_id).filter(date__lte=date_limite).filter(
            rapp__isnull=True).count()
    else:
        date_limite = datetime.datetime.fromtimestamp(0).date()
        nbvielles = 0
        q = Ope.non_meres().filter(compte__pk=cpt_id).order_by('-date').select_related('tiers','tiers__titre','cat')
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
                    'compte':c,
                    'list_ope':opes,
                    'titre':"%s: Especes" % c.nom,
                    'solde':c.solde_espece(),
                    'date_limite':date_limite,
                    'nbrapp':Ope.non_meres().filter(compte__pk=cpt_id).filter(rapp__isnull=False).count(),
                    'nbvielles':nbvielles,
                    'nb_j':settings.NB_JOURS_AFF_TITRE
                }
            )
        )
    )


@login_required
def titre_detail_cpt(request, titre_id, cpt_id, date_limite=True):
    """view qui affiche la liste des operations relative a un titre (titre_id) d'un compte titre (cpt_id)
    si date_limite, utilise la date limite sinon affiche toute les ope """
    titre = get_object_or_404(Titre.objects.select_related(), pk=titre_id)
    cpt = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    if date_limite:
        date_limite = datetime.date.today() - datetime.timedelta(days=settings.NB_JOURS_AFF_TITRE)
        q = Ope_titre.objects.filter(compte__pk=cpt_id).order_by('-date').filter(date__gte=date_limite).filter(
            titre=titre)
        nbvielles = Ope_titre.objects.filter(compte__pk=cpt_id).filter(date__lte=date_limite).count()
    else:
        date_limite = datetime.datetime.fromtimestamp(0).date()
        q = Ope_titre.objects.filter(compte__pk=cpt_id).order_by('-date').filter(titre=titre)
        nbvielles = 0
    template = loader.get_template('gsb/cpt_placement_titre.djhtm')
    return HttpResponse(
        template.render(
            RequestContext(
                request,
                    {
                    'compte':cpt,
                    'list_ope':q,
                    'titre':"%s: %s" % (cpt.nom, titre.nom),
                    'solde':titre.investi(cpt),
                    'date_limite':date_limite,
                    'nbrapp':0,
                    'nbvielles':nbvielles,
                    'tit':titre,
                    'nb_titre':titre.nb(cpt),
                    'nb_j':settings.NB_JOURS_AFF_TITRE
                    #                    'nb_titre':titre.nb()
                }
            )
        )
    )


@login_required
def ope_titre_detail(request, pk):
    """
    view, une seule operation
    @param request:
    @param pk: id de l'ope
    """
    ope = get_object_or_404(Ope_titre.objects.select_related(), pk=pk)
    if request.method == 'POST':
        date_initial = ope.date
        form = gsb_forms.Ope_titreForm(request.POST, instance=ope)
        if form.is_valid():
            if ope.ope is None:
                ope.ope = Ope.objects.create(date=form.cleaned_data['date'],
                                             montant=decimal.Decimal(
                                                 smart_unicode(form.cleaned_data['cours'])) * decimal.Decimal(
                                                 smart_unicode(form.cleaned_data['nombre'])) * -1,
                                             tiers=ope.titre.tiers,
                                             cat=Cat.objects.get_or_create(id=settings.ID_CAT_OST,
                                                                           defaults={'nom':u'operation sur titre:'})[0],
                                             notes="%s@%s" % (form.cleaned_data['nombre'], form.cleaned_data['cours']),
                                             moyen=None,
                                             automatique=True,
                                             compte=ope.compte
                )
                creation = True
            else:
                creation = False
            if form.has_changed() and ope.ope.rapp is None:
                #on efface au besoin le cours
                c = Cours.objects.filter(titre=ope.titre, date=date_initial)
                if c.exists():
                    c = c[0]
                    if not Cours.objects.filter(titre=ope.titre, date=form.cleaned_data['date']).exists():
                        c.date = form.cleaned_data['date']
                    c.save()
                    messages.info(request, u'cours crée')
                if not creation:
                    cours = form.cleaned_data['cours']
                    nb = form.cleaned_data['nombre']
                    ope.ope.date = form.cleaned_data['date']
                    ope.ope.montant = decimal.Decimal(cours) * decimal.Decimal(nb) * -1
                    ope.ope.note = "%s@%s" % (nb, cours)
                    ope.ope.save()
                    message = u"opération modifié"
                else:
                    message = u"opération crée"
                form.save()
                messages.success(request, u"%s %s"%(message, ope))
            else:
                messages.error(request, u"opération impossible a modifier, elle est rapprochée")
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
    else:
        form = gsb_forms.Ope_titreForm(instance=ope)
    if ope.ope is not None:
        rapp = bool(ope.ope.rapp_id)
    else:
        rapp = None
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
            return HttpResponseRedirect(reverse('mysite.gsb.views.ope_titre_detail', kwargs={'pk':ope.id}))
        cpt_id = ope.compte_id
        cours = Cours.objects.filter(date=ope.date, titre=ope.titre)
        if cours.exists():
            s = u'%s' % cours
            cours.delete()
            messages.success(request, u'cours effacé:%s'%s)
        if ope.ope:
            ope.ope.delete()
        s = u'%s' % ope
        ope.delete()
        messages.success(request, u'ope effacé:%s'%s)
        return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':cpt_id}))
    else:
        return HttpResponseRedirect(reverse('mysite.gsb.views.ope_titre_detail', kwargs={'pk':ope.id}))


@login_required
def ope_titre_achat(request, cpt_id):
    cpt = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
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
                messages.info(request, u"nouveau titre crée: %s"%titre)
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
            messages.info(request, u"nouvel achat de %s %s @ %s le %s"%(form.cleaned_data['nombre'],
                                                                        form.cleaned_data['titre'],
                                                                        form.cleaned_data['cours'],
                                                                        form.cleaned_data['titre']))

            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':cpt.id}))
    else:
        form = gsb_forms.Ope_titre_add_achatForm(initial={'compte_titre':cpt})
    titre = u' nouvel achat sur %s' % cpt.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
            {'titre_long':titre,
             'titre':u'modification',
             'form':form,
             'cpt':cpt,
             'sens':'achat'}
    )


@login_required
def ope_titre_vente(request, cpt_id):
    cpte = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    if request.method == 'POST':
        form = gsb_forms.Ope_titre_add_venteForm(data=request.POST, cpt=cpte)
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
            messages.info(request, u"nouvel vente de %s %s @ %s le %s"%(form.cleaned_data['nombre'],
                                                                        form.cleaned_data['titre'],
                                                                        form.cleaned_data['cours'],
                                                                        form.cleaned_data['titre']))
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':cpte.id}))
    else:
        form = gsb_forms.Ope_titre_add_venteForm(initial={'compte_titre':cpte}, cpt=cpte)
    titre = u' nouvelle vente sur %s' % cpte.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
            {'titre_long':titre,
             'titre':u'modification',
             'form':form,
             'cpt':cpte,
             'sens':'vente'}
    )


@login_required
def view_maj_cpt_titre(request, cpt_id):
    cpt = Compte_titre.objects.get(id=cpt_id)
    liste_titre_original = cpt.titre.all().distinct()
    liste_titre = []
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

            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':cpt_id}))
    else:
        form = gsb_forms.Majtitre(titres=liste_titre)
    return render(request, 'gsb/maj_cpt_titre.djhtm',
            {'titre_long':u'operations sur le %s' % cpt.nom,
             'titre':u'ope',
             'form':form,
             'titres':liste_titre,
             'cpt':cpt}
    )
