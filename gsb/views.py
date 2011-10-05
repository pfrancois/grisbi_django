# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from mysite.gsb.models import Generalite, Compte, Ope, Compte_titre, Moyen, Titre, Cours, Tiers, Ope_titre, Cat
import datetime
import mysite.gsb.forms as gsb_forms
from django.db import models
import decimal
#import logging #@UnusedImport
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_unicode

@login_required
def index(request):
    """
    view index
    """
    t = loader.get_template('gsb/index.djhtm')
    if Generalite.gen().affiche_clot:
        bq = Compte.objects.filter(type__in = ('b', 'e', 'p')).select_related()
        pl = Compte_titre.objects.all().select_related()
    else:
        bq = Compte.objects.filter(type__in = ('b', 'e', 'p'), ouvert = True).select_related()
        pl = Compte_titre.objects.filter(ouvert = True).select_related()
    total_bq = Ope.objects.filter(mere__exact = None, compte__type__in = ('b', 'e', 'p')).aggregate(solde = models.Sum('montant'))['solde']
    if total_bq is None:
        total_bq = decimal.Decimal()
    total_pla = decimal.Decimal()
    for p in pl:
        total_pla = total_pla + p.solde
    nb_clos = len(Compte.objects.filter(ouvert = False))
    c = RequestContext(request, {
        'titre': 'liste des comptes',
        'liste_cpt_bq': bq,
        'liste_cpt_pl': pl,
        'total_bq': total_bq,
        'total_pla': total_pla,
        'total': total_bq + total_pla,
        'nb_clos': nb_clos,
        })
    return HttpResponse(t.render(c))

@login_required
def cpt_detail(request, cpt_id):
    """
    view qui affiche la liste des operation de ce compte
    @param request:
    @param cpt_id: id du compte demande
    """
    c = get_object_or_404(Compte.objects.select_related(), pk = cpt_id)
    date_limite = datetime.date.today() - datetime.timedelta(days = settings.NB_JOURS_AFF)
    if c.type in ('t',):
        c = get_object_or_404(Compte_titre.objects.select_related(), pk = cpt_id)
        date_limite = datetime.date.today() - datetime.timedelta(days = settings.NB_JOURS_AFF_TITRE)
        titre = True
    else:
        titre = False
    if not titre:
        q = Ope.non_meres().filter(compte__pk = cpt_id).order_by('-date').filter(date__gte = date_limite).filter(rapp__isnull = True)
        nb_ope_vielles = Ope.non_meres().filter(compte__pk = cpt_id).filter(date__lte = date_limite).filter(rapp__isnull = True).count()
        nb_ope_rapp = Ope.non_meres().filter(compte__pk = cpt_id).filter(rapp__isnull = False).count()
        template = loader.get_template('gsb/cpt_detail.djhtm')
        return HttpResponse(
            template.render(
                RequestContext(
                    request,
                    {
                        'compte': c,
                        'list_ope': q,
                        'nbrapp': nb_ope_rapp,
                        'nbvielles': nb_ope_vielles,
                        'titre': c.nom,
                        'solde': c.solde,
                        'date_limite':date_limite,
                        'nb_j':settings.NB_JOURS_AFF
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
            nb=t.nb(c)
            if abs(nb)>decimal.Decimal('0.01'):
                titres.append({'nom': t.nom, 'type': t.get_type_display(), 'nb':nb, 'invest': invest,
                               'pmv': total - invest, 'total': total, 'id':t.id, 't':t})
        especes = super(Compte_titre, c).solde
        template = loader.get_template('gsb/cpt_placement.djhtm')
        return HttpResponse(
            template.render(
                RequestContext(
                    request,
                    {
                        'compte': c,
                        'titre': c.nom,
                        'solde': c.solde,
                        'titres': titres,
                        'especes': especes,
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
    ope = get_object_or_404(Ope.objects.select_related(), pk = pk)
    #logger = logging.getLogger('gsb')
    if ope.jumelle is not None:
        #------un virement--------------
        if ope.montant > 0:
            ope = ope.jumelle
        if request.method == 'POST':#creation du virement
            form = gsb_forms.VirementForm(data = request.POST, ope = ope)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':ope.jumelle.compte_id}))
        else:
            form = gsb_forms.VirementForm(ope = ope)
        return render(request, 'gsb/vir.djhtm',
                {   'titre_long':u'modification virement interne %s' % ope.id,
                   'titre':u'modification',
                    'form':form,
                    'ope':ope}
                )
    #______ope normale----------
    else:#sinon c'est une operation normale
        if ope.filles_set.all().count() > 0 : #c'est une ope mere
            #TODO message
            HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':ope.compte_id}))
        if request.method == 'POST':
            form = gsb_forms.OperationForm(request.POST, instance = ope)
            if form.is_valid():
                if not form.cleaned_data['tiers']:
                    form.instance.tiers = Tiers.objects.get_or_create(nom = form.cleaned_data['nouveau_tiers'],
                                                     defaults = {'nom':form.cleaned_data['nouveau_tiers'], }
                                                    )[0]
                ope = form.save()
                return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':ope.compte_id}))
        else:
            form = gsb_forms.OperationForm(instance = ope)
        return render(request, 'gsb/ope.djhtm',
                {   'titre_long':u'modification opération %s' % ope.id,
                   'titre':u'modification',
                    'form':form,
                    'ope':ope}
                )

@login_required
def ope_new(request, cpt_id = None):
    """
    creation d'une nouvelle operation
    """
    if cpt_id:
        cpt = get_object_or_404(Compte.objects.select_related(), pk = cpt_id)
    else:
        cpt = None
    #logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.OperationForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['tiers']:
                form.instance.tiers = Tiers.objects.get_or_create(nom = form.cleaned_data['nouveau_tiers'],
                                                 defaults = {'nom':form.cleaned_data['nouveau_tiers'], }
                                                )[0]
            ope = form.save()
            #TODO message
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':ope.compte_id}))
        else:
            #TODO message
            return render(request, 'gsb/ope.djhtm',
            {   'titre':u'création',
                'titre_long':u'création opération',
                'form':form,
                'cpt':cpt}
            )
    else:
        if not cpt_id:
            cpt = get_object_or_404(Compte.objects.select_related(), pk = settings.ID_CPT_M)
        form = gsb_forms.OperationForm(initial = {'compte':cpt, 'moyen':cpt.moyen_debit_defaut})
        return render(request, 'gsb/ope.djhtm',
            {   'titre':u'création',
                'titre_long':u'création opération',
                'form':form,
                'cpt':cpt}
            )

@login_required
def vir_new(request, cpt_id = None):
    if cpt_id:
        cpt = get_object_or_404(Compte.objects.select_related(), pk = cpt_id)
    else:
        cpt = get_object_or_404(Compte.objects.select_related(), pk = settings.ID_CPT_M)
    #logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.VirementForm(data = request.POST)
        if form.is_valid():
            ope = form.save()
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':ope.jumelle.compte_id}))
        else:
            return render(request, 'gsb/vir.djhtm',
            {   'titre_long':u'création virement interne ',
               'titre':u'Création',
                'form':form,
                'cpt_id':cpt_id}
            )
    else:
        form = gsb_forms.VirementForm(initial = {'compte_origine':get_object_or_404(Compte.objects.select_related(), pk = settings.ID_CPT_M), 'moyen_origine':Moyen.objects.filter(type = 'v')[0], 'compte_destination':cpt, 'moyen_destination':Moyen.objects.filter(type = 'v')[0]})
        return render(request, 'gsb/vir.djhtm',
            {   'titre':u'Création',
               'titre_long':u'Création virement interne ',
                'form':form,
                'cpt_id':cpt_id}
            )

@login_required
def ope_delete(request, pk):
    ope = get_object_or_404(Ope.objects.select_related(), pk = pk)
    if request.method == 'POST':
        if ope.jumelle:
            ope.jumelle.delete()
        ope.delete()
    else:
        return HttpResponseRedirect(reverse('mysite.gsb.views.ope_detail', kwargs = {'pk':ope.id}))
    return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':ope.compte_id}))

@login_required
def maj_cours(request, pk):
    titre = get_object_or_404(Titre.objects.select_related(), pk = pk)
    if request.method == 'POST':
        form = gsb_forms.MajCoursform(request.POST)
        if form.is_valid():
            titre = form.cleaned_data['titre']
            date = form.cleaned_data['date']
            if not Cours.objects.filter(titre = titre, date = date).exists():
                titre.cours_set.create(valeur = form.cleaned_data['cours'], date = date)
            else:
                titre.cours_set.get(date = date).valeur = form.cleaned_data['cours']
            cpt_id = Ope_titre.objects.filter(titre = titre).latest('date').compte_id
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':cpt_id}))
    else:
        form = gsb_forms.MajCoursform(initial = {'titre':titre, 'cours':titre.last_cours, 'date':titre.last_cours_date})
    if titre.compte_titre_set.all().distinct().count()==1:
        url="gsb.views.cpt_detail"
        cpt_id=titre.compte_titre_set.all().distinct()[0].id
    else:
        url="gsb.views.index"
        cpt_id=None
    return render(request, "gsb/maj_cours.djhtm", {"titre":u"maj du titre '%s'" % titre.nom , "form": form,"url":url,
                                                   "cpt":cpt_id})

@login_required
def cpt_titre_espece(request, cpt_id, date_limite = False):
    """view qui affiche la liste des operations especes d'un compte titre cpt_id
    si date_limite, utilise la date limite sinon affiche toute les ope espece"""
    c = get_object_or_404(Compte_titre.objects.select_related(), pk = cpt_id)
    if date_limite:
        date_limite = datetime.date.today() - datetime.timedelta(days = settings.NB_JOURS_AFF_TITRE)
        q = Ope.non_meres().filter(compte__pk = cpt_id).order_by('-date').filter(date__gte = date_limite).filter(rapp__isnull = True)
        nbvielles = Ope.non_meres().filter(compte__pk = cpt_id).filter(date__lte = date_limite).filter(rapp__isnull = True).count()
    else:
        date_limite = datetime.datetime.fromtimestamp(0).date()
        nbvielles = 0
        q = Ope.non_meres().filter(compte__pk = cpt_id).order_by('-date')
    template = loader.get_template('gsb/cpt_placement_espece.djhtm')
    return HttpResponse(
        template.render(
            RequestContext(
                request,
                {
                    'compte': c,
                    'list_ope': q,
                    'titre': "%s: Especes" % c.nom,
                    'solde': super(Compte_titre, c).solde,
                    'date_limite':date_limite,
                    'nbrapp': Ope.non_meres().filter(compte__pk = cpt_id).filter(rapp__isnull = False).count(),
                    'nbvielles': nbvielles,
                    'nb_j':settings.NB_JOURS_AFF_TITRE
                }
            )
        )
    )

@login_required
def titre_detail_cpt(request, titre_id, cpt_id, date_limite = True):
    """view qui affiche la liste des operations relative a un titre (titre_id) d'un compte titre (cpt_id)
    si date_limite, utilise la date limite sinon affiche toute les ope """
    titre = get_object_or_404(Titre.objects.select_related(), pk = titre_id)
    cpt = get_object_or_404(Compte_titre.objects.select_related(), pk = cpt_id)
    if date_limite:
        date_limite = datetime.date.today() - datetime.timedelta(days = settings.NB_JOURS_AFF_TITRE)
        q = Ope_titre.objects.filter(compte__pk = cpt_id).order_by('-date').filter(date__gte = date_limite).filter(titre = titre)
        nbvielles = Ope_titre.objects.filter(compte__pk = cpt_id).filter(date__lte = date_limite).count()
    else:
        date_limite = datetime.datetime.fromtimestamp(0).date()
        q = Ope_titre.objects.filter(compte__pk = cpt_id).order_by('-date').filter(titre = titre)
        nbvielles = 0
    template = loader.get_template('gsb/cpt_placement_titre.djhtm')
    return HttpResponse(
        template.render(
            RequestContext(
                request,
                {
                    'compte': cpt,
                    'list_ope': q,
                    'titre': "%s: %s" % (cpt.nom, titre.nom),
                    'solde': titre.investi(cpt),
                    'date_limite':date_limite,
                    'nbrapp': 0,
                    'nbvielles': nbvielles,
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
    ope = get_object_or_404(Ope_titre.objects.select_related(), pk = pk)
    if request.method == 'POST':
        date_initial=ope.date
        form = gsb_forms.Ope_titreForm(request.POST, instance = ope)
        if form.is_valid():
            if ope.ope is None:
                ope.ope=Ope.objects.create(date = form.cleaned_data['date'],
                                                montant = decimal.Decimal(smart_unicode(form.cleaned_data['cours'])) * decimal.Decimal(smart_unicode(form.cleaned_data['nombre'])) * -1,
                                                tiers = ope.titre.tiers,
                                                cat = Cat.objects.get_or_create(nom = u"operation sur titre:", defaults = {'nom':u'operation sur titre:'})[0],
                                                notes = "%s@%s" % (form.cleaned_data['nombre'], form.cleaned_data['cours']),
                                                moyen = None,
                                                automatique = True,
                                                compte = ope.compte,
                                                )
                creation = True
            else :
                creation = False 
            if form.has_changed() and ope.ope.rapp is None:
                #on efface au besoin le cours
                c=Cours.objects.filter(titre=ope.titre,date=date_initial)
                if c.exists():
                    c=c[0]
                    if not Cours.objects.filter(titre=ope.titre,date=form.cleaned_data['date']).exists():
                        c.date=form.cleaned_data['date']
                    c.save()
                if not creation:
                    cours = form.cleaned_data['cours']
                    nb = form.cleaned_data['nombre']
                    ope.ope.date = form.cleaned_data['date']
                    ope.ope.montant = decimal.Decimal(cours) * decimal.Decimal(nb) * -1
                    ope.ope.note = "%s@%s" % (nb, cours)
                    ope.ope.save()
                form.save()

            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':ope.compte_id}))
    else:
        form = gsb_forms.Ope_titreForm(instance = ope)
    if ope.ope is not None:
        rapp = bool(ope.ope.rapp_id)
    else:
        rapp = None
    return render(request, 'gsb/ope_titre_detail.djhtm',
            {   'titre_long':u'opération sur titre %s' % ope.id,
               'titre':u'modification',
                'form':form,
                'ope':ope,
                'rapp': rapp}
            )

@login_required
def ope_titre_delete(request, pk):
    ope = get_object_or_404(Ope_titre.objects.select_related(), pk = pk)
    if request.method == 'POST':
        cpt_id = ope.compte_id
        cours=Cours.objects.filter(date=ope.date,titre=ope.titre)
        if cours.exists():
            cours.delete()
        ope.ope.delete()
        ope.delete()

        return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':cpt_id}))
    else:
        return HttpResponseRedirect(reverse('mysite.gsb.views.ope_titre_detail', kwargs = {'pk':ope.id}))

@login_required
def ope_titre_achat(request, cpt_id):
    cpt = get_object_or_404(Compte_titre.objects.select_related(), pk = cpt_id)
    if request.method == 'POST':
        form = gsb_forms.Ope_titre_add_achatForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['titre']:
                titre = form.cleaned_data['titre']
            else:
                titre = Titre.objects.get_or_create(nom = form.cleaned_data['nouveau_titre'],
                                                     defaults = {'nom':form.cleaned_data['nouveau_titre'],
                                                                 'type':'ZZZ',
                                                                 'isin':form.cleaned_data['nouvel_isin']
                                                                }
                                                    )[0]
            compte = form.cleaned_data['compte_titre']
            if form.cleaned_data['compte_espece']:
                virement = form.cleaned_data['compte_espece']
            else:
                virement = None
            compte.achat(titre = titre,
                         nombre = form.cleaned_data['nombre'],
                         prix = form.cleaned_data['cours'],
                         date = form.cleaned_data['date'],
                         virement_de = virement)
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':cpt.id}))
    else:
        form = gsb_forms.Ope_titre_add_achatForm(initial = {'compte_titre': cpt})
    titre = u' nouvel achat sur %s' % cpt.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
            {   'titre_long':titre,
               'titre':u'modification',
                'form':form,
                'cpt':cpt,
                'sens':'achat'}
            )

@login_required
def ope_titre_vente(request, cpt_id):
    cpte = get_object_or_404(Compte_titre.objects.select_related(), pk = cpt_id)
    if request.method == 'POST':
        form = gsb_forms.Ope_titre_add_venteForm(data=request.POST, cpt = cpte)
        if form.is_valid():
            compte = form.cleaned_data['compte_titre']
            if form.cleaned_data['compte_espece']:
                virement = form.cleaned_data['compte_espece']
            else:
                virement = None
            compte.vente(titre = form.cleaned_data['titre'],
                         nombre = form.cleaned_data['nombre'],
                         prix = form.cleaned_data['cours'],
                         date = form.cleaned_data['date'],
                         virement_vers = virement)
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':cpte.id}))
    else:
        form = gsb_forms.Ope_titre_add_venteForm(initial = {'compte_titre': cpte}, cpt = cpte)
    titre = u' nouvelle vente sur %s' % cpte.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
            {   'titre_long':titre,
               'titre':u'modification',
                'form':form,
                'cpt':cpte,
                'sens':'vente'}
            )

@login_required
def view_maj_cpt_titre(request, cpt_id):
    cpt = Compte_titre.objects.get(id = cpt_id)
    liste_titre = cpt.titre.all().distinct()
    if request.method == 'POST':
        form = gsb_forms.Majtitre(data = request.POST, titres = liste_titre)
        if form.is_valid():
            for titre_en_cours in liste_titre:
                if form.cleaned_data[titre_en_cours.isin] is None:
                    continue
                tab = form.cleaned_data[titre_en_cours.isin].partition('@')
                nb = decimal.Decimal(tab[0])
                cours = decimal.Decimal(tab[2])
                if nb != '0' and nb:
                    if form.cleaned_data['sociaux']:
                        frais=nb*cours*decimal.Decimal(str(settings.TAUX_VERSEMENT))
                        cpt.achat(titre_en_cours, nb, cours, date = form.cleaned_data['date'],frais=frais,
                            cat_frais=Cat.objects.get(id=settings.ID_CAT_COTISATION),)
                    else:
                        cpt.achat(titre_en_cours, nb, cours, date = form.cleaned_data['date'])
                else:
                    if not Cours.objects.filter(date=form.cleaned_data['date'],titre=titre_en_cours).exists() and \
                       cours:
                        Cours.objects.create(date=form.cleaned_data['date'],titre=titre_en_cours,valeur=cours)

            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':cpt_id}))
    else:
        form = gsb_forms.Majtitre(titres = liste_titre)
    return render(request, 'gsb/maj_cpt_titre.djhtm',
                {   'titre_long':u'operations sur le %s' % cpt.nom,
                   'titre':u'ope',
                    'form':form,
                    'titres':liste_titre,
                    'cpt':cpt}
                )
