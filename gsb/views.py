# -*- coding: utf-8 -*-
# Create your views here.
from __future__ import absolute_import
from django.template import RequestContext, loader
from django import http
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from .models import Compte, Ope, Moyen, Titre, Cours, Tiers, Ope_titre, Cat, Rapp
from .import forms as gsb_forms
from django.db import models
import decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from django.core import exceptions as django_exceptions
from django.views import generic
from django.utils.decorators import method_decorator
import datetime


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


class Mytemplateview(generic.TemplateView):
    template_name = 'gsb/options.djhtm'
    titre = None

    def get_context_data(self, **kwargs):
        return {
            'titre': self.titre
        }

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """on a besoin pour le method decorator"""
        return super(Mytemplateview, self).dispatch(*args, **kwargs)


class Myformview(generic.FormView):
    form_class = None
    template_name = None

    def form_valid(self, form):
        """
        This is what's called when the form is valid.
        """
        return super(Myformview, self).form_valid(form)

    def form_invalid(self, form):
        """
        This is what's called when the form is invalid.
        """
        return self.render_to_response(self.get_context_data(form=form))

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """on a besoin pour le method decorator"""
        return super(Myformview, self).dispatch(*args, **kwargs)


class Myredirectview(generic.RedirectView):
    call = None

    def post(self, request, *args, **kwargs):
        pass

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(Myredirectview, self).get(self, request, *args, **kwargs)


class Index_view(Mytemplateview):
    template_name = 'gsb/index.djhtm'

    def get(self, request, *args, **kwargs):
        if settings.AFFICHE_CLOT:
            self.bq = Compte.objects.filter(type__in=('b', 'e', 'p')).select_related('ope')
            self.pl = Compte.objects.exclude(type__in=('b', 'e', 'p')).select_related('ope', 'tiers')
        else:
            self.bq = Compte.objects.filter(type__in=('b', 'e', 'p'), ouvert=True).select_related('ope')
            self.pl = Compte.objects.filter(type='t', ouvert=True).select_related('ope', 'tiers')
            # calcul du solde des bq
        self.bqe = []
        self.total_bq = decimal.Decimal('0')
        soldes=self.bq.select_related('ope').filter(ope__filles_set__isnull=True).annotate(solde=models.Sum('ope__montant'))
        for p in soldes:
            cpt = {'solde':p.solde,
                 'nom':p.nom,
                 'url':p.get_absolute_url(),
                 'ouvert':p.ouvert}
            self.total_bq += cpt['solde']
            self.bqe.append(cpt)
        # calcul du solde des pla
        self.total_pla = decimal.Decimal('0')
        self.pla = []
        for p in self.pl:
            cpt = {'solde':p.solde(),
                 'nom':p.nom,
                 'url':p.get_absolute_url(),
                 'ouvert':p.ouvert}
            self.pla.append(cpt)
            if cpt['solde'] is not None:
                self.total_pla += cpt['solde']
        self.nb_clos = Compte.objects.filter(ouvert=False).count()
        return super(Index_view, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return  {
            'titre': 'liste des comptes',
            'liste_cpt_bq': self.bqe,
            'liste_cpt_pl': self.pla,
            'total_bq': self.total_bq,
            'total_pla': self.total_pla,
            'total': self.total_bq + self.total_pla,
            'nb_clos': self.nb_clos,
        }


class Cpt_detail_view(Mytemplateview):
    template_name = 'gsb/cpt_detail.djhtm'
    cpt_titre_espece = False
    rapp = False
    all = False
    nb_ope_par_pages = 100

    def get(self, request, cpt_id):
        """
        view qui affiche la liste des operation de ce compte
        @param request:
        @param cpt_id: id du compte demande
        """
        try:
            compte = Compte.objects.get(pk=cpt_id)
        except Compte.DoesNotExist:
            raise http.Http404('pas de compte correspondant.')
        self.type = "nrapp"
        if self.all:
            self.type = "all"
        if self.rapp:
            self.type = "rapp"

        if compte.type not in ('t',) or self.cpt_titre_espece == True:
            if self.cpt_titre_espece:
                self.template_name = 'gsb/cpt_placement_espece.djhtm'
            #sinon on prend le nom du template par defaut
            self.espece = True

            q = Ope.non_meres().filter(compte=compte).order_by('-date')
            if self.rapp:
                q = q.filter(rapp__isnull=False)
            else:
                if not self.all:
                    q = q.filter(rapp__isnull=True)
            if self.all:
                nb_ope_rapp = 0
            else:
                nb_ope_rapp = 0
                if self.all:
                    nb_ope_rapp = 0
                if self.rapp:
                    nb_ope_rapp = 0
                if not self.all and not self.rapp:
                    nb_ope_rapp = Ope.objects.filter(compte=compte, rapp__isnull=False).count()
            try:
                sort = request.GET.get('sort')  # il y a un sort dans le get
            except (ValueError, TypeError):  # non donc on regarde dans l'historique
                sort = False
                if request.session.key('sort', False):
                    sort = request.session.key('sort', False)
            if sort:
                sort = unicode(sort)
                q = q.order_by(sort)
            else:
                q = q.order_by('-date')
            sort_t = {}
            if sort == "date":
                sort_t['date'] = "-date"
            else:
                sort_t['date'] = "date"
            if sort == "tiers":
                sort_t['tiers'] = "-tiers"
            else:
                sort_t['tiers'] = "tiers"
            if sort == "cat":
                sort_t['cat'] = "-cat"
            else:
                sort_t['cat'] = "cat"
            if sort == "montant":
                sort_t['montant'] = "-montant"
            else:
                sort_t['montant'] = "montant"
            sort_t['actuel'] = "?sort=%s" % sort
            if not self.all:
                q=q.filter(date__year=datetime.date.today().year)
            opes = q.select_related('tiers', 'cat', 'rapp')
            context = self.get_context_data(compte, opes, nb_ope_rapp, sort_t)
            
        else:
            self.espece = False
            self.template_name = 'gsb/cpt_placement.djhtm'
            # recupere la liste des titres qui sont utilise dans ce compte
            compte_titre = get_object_or_404(Compte, pk=cpt_id)
            if compte_titre.type != 't':
                return http.HttpResponseRedirect(reverse("index"))
            titre_sans_sum = compte_titre.titre.all().distinct()
            titres = []
            for t in titre_sans_sum:
                invest = t.investi(compte_titre)
                total = t.encours(compte_titre)
                nb = t.nb(compte_titre)
                if abs(nb) > decimal.Decimal('0.01'):
                    titres.append(
                        {'nom': t.nom,
                         'type': t.get_type_display(),
                         'nb': nb,
                         'invest': invest,
                         'pmv': total - invest,
                         'total': total,
                         'id': t.id,
                         't': t,
                         'rapp': t.encours(rapp=True, compte=compte_titre)
                        })
            context = self.get_context_data(compte_titre, titres)

        return self.render_to_response(context)

    def cpt_espece_pagination(self, request, q):
        # gestion pagination
        paginator = Paginator(q, self.nb_ope_par_pages)
        try:
            page = int(request.GET.get('page'))
            return paginator.page(page)
        except (ValueError, TypeError, PageNotAnInteger):
            return paginator.page(1)
        except (EmptyPage, InvalidPage):
            return paginator.page(paginator.num_pages)

    def get_context_data(self, *kwargs):
        type_long = {
            "nrapp": u"Opérations non rapprochées",
            "rapp": u"Opérations rapprochées",
            "all": u"Ensemble des opérations"
        }
        c = kwargs[0]
        solde_espece=c.solde(espece=True)
        solde_r_esp=c.solde(rapp=True, espece=True)
        solde_p=c.solde_pointe(espece=True)
        if self.espece:

            context = {'compte': c,
                       'list_ope': kwargs[1],
                       'nbrapp': kwargs[2],
                       'titre': c.nom,
                       'solde': solde_espece,
                       "date_r": c.date_rappro(),
                       "solde_r": solde_r_esp,
                       "solde_p": solde_p,
                       "solde_pr": solde_r_esp + solde_p,
                       "sort_tab": kwargs[3],
                       "type": self.type,
                       "titre_long": "%s (%s)" % (c.nom, type_long[self.type]),
            }
        else:
            solde_r=c.solde(rapp=True)
            context = {
                'compte': c,
                'titre': c.nom,
                'solde': c.solde(),
                'titres': kwargs[1],
                'especes': solde_espece,
                'especes_rapp': solde_r_esp,
                'solde_rapp': solde_r,
                'solde_titre_rapp': solde_r-solde_r_esp,
            }
        
        return context


@login_required
def ope_detail(request, pk):
    """
    view, une seule operation
    @param request: la requette hhtp
    @param pk: id de l'ope
    """
    ope = get_object_or_404(Ope.objects.select_related(), pk=pk)
    # logger = logging.getLogger('gsb')
    if ope.jumelle is not None:
        #------un virement--------------
        if ope.montant > 0:
            ope = ope.jumelle
        if request.method == 'POST':  # creation du virement
            form = gsb_forms.VirementForm(data=request.POST, ope=ope)
            if form.is_valid():
                if not ope.rapp and not ope.jumelle.rapp:
                    form.save()
                    messages.success(request, 'modification du virement effectue')
                    return http.HttpResponseRedirect(ope.compte.get_absolute_url())
                else:
                    if ope.rapp:
                        compte = ope.compte
                    else:
                        compte = ope.jumelle.compte
                    messages.error(request, u"impossible de modifier car le virement coté %s est rapprochée" % compte)
        else:
            form = gsb_forms.VirementForm(ope=ope)
        return render(request, 'gsb/vir.djhtm',
                      {'titre_long': u'modification virement interne %s' % ope.id,
                       'titre': u'modification',
                       'form': form,
                       'ope': ope}
        )
    #--------ope normale----------
    else:  # sinon c'est une operation normale
        if request.method == 'POST':
            if ope.filles_set.all().count() > 0:  # c'est une ope mere
                messages.error(request, u"attention cette operation n'est pas éditable car c'est une ope mere.")
                http.HttpResponseRedirect(ope.compte.get_absolute_url())
            form = gsb_forms.OperationForm(request.POST, instance=ope)
            if form.is_valid():
                if not form.cleaned_data['tiers']:
                    form.instance.tiers = Tiers.objects.get_or_create(nom=form.cleaned_data['nouveau_tiers'],
                                                                      defaults={
                                                                      'nom': form.cleaned_data['nouveau_tiers']
                                                                          , }
                    )[0]
                    messages.info(request, u"tiers '%s' créé" % form.instance.tiers.nom)
                if not ope.rapp:
                    messages.success(request, u"opération modifiée")
                    ope = form.save()
                else:
                    # verification que les données essentielles ne sont pas modifiés
                    if has_changed(ope, 'montant') or  has_changed(ope, 'compte') or has_changed(ope,
                                                                                                 'pointe') or has_changed(
                        ope, 'jumelle') or has_changed(ope, 'mere'):
                        messages.error(request, u"impossible de modifier l'opération car elle est rapprochée")
                    else:
                        messages.success(request, u"opération modifiée")
                        ope = form.save()
                return http.HttpResponseRedirect(ope.compte.get_absolute_url())
        else:
            form = gsb_forms.OperationForm(instance=ope)
        return render(request, 'gsb/ope.djhtm',
                      {'titre_long': u'modification opération %s' % ope.id,
                       'titre': u'modification',
                       'form': form,
                       'ope': ope}
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
        # logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.OperationForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['tiers']:
                form.instance.tiers = Tiers.objects.get_or_create(nom=form.cleaned_data['nouveau_tiers'],
                                                                  defaults={'nom': form.cleaned_data['nouveau_tiers'], }
                )[0]
                messages.info(request, u"tiers '%s' créé" % form.instance.tiers.nom)
            ope = form.save()

            messages.success(request, u"Opération '%s' crée" % ope)
            # retour vers
            return http.HttpResponseRedirect(ope.compte.get_absolute_url())
        else:
            # TODO message
            return render(request, 'gsb/ope.djhtm',
                          {'titre': u'création',
                           'titre_long': u'création opération',
                           'form': form,
                           'cpt': cpt}
            )
    else:
        if not cpt_id:
            try:
                cpt = Compte.objects.filter(pk=settings.ID_CPT_M).select_related()[0]
            except Compte.DoesNotExist:
                messages.error(request, u"pas de compte par defaut")
                return http.HttpResponseRedirect(reverse('gsb.views.index'))
        form = gsb_forms.OperationForm(initial={'compte': cpt, 'moyen': cpt.moyen_debit_defaut})
        return render(request, 'gsb/ope.djhtm',
                      {'titre': u'création',
                       'titre_long': u'création opération',
                       'form': form,
                       'cpt': cpt}
        )


@login_required
def vir_new(request, cpt_id=None):
    cpt_par_def = Compte.objects.filter(id=settings.ID_CPT_M)
    if cpt_par_def.exists():
        cpt_origine = cpt_par_def[0]
    else:
        cpt_origine = Compte.objects.get(id=1)
    if cpt_id:
        cpt = get_object_or_404(Compte.objects.select_related(), pk=cpt_id)
    else:
        cpt = cpt_origine
        # logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.VirementForm(data=request.POST)
        if form.is_valid():
            ope = form.save()
            messages.success(request, u"virement crée %s=>%s de %s le %s" % (
            ope.compte, ope.jumelle.compte, ope.jumelle.montant, ope.date))
            return http.HttpResponseRedirect(ope.compte.get_absolute_url())
        else:
            return render(request, 'gsb/vir.djhtm',
                          {'titre_long': u'création virement interne ',
                           'titre': u'Création',
                           'form': form,
                           'cpt': cpt}
            )
    else:
        form = gsb_forms.VirementForm(
            initial={'compte_origine': cpt_origine,
                     'moyen_origine': Moyen.objects.filter(type='v')[0],
                     'compte_destination': cpt,
                     'moyen_destination': Moyen.objects.filter(type='v')[0]
            }
        )
        return render(request, 'gsb/vir.djhtm',
                      {'titre': u'Création',
                       'titre_long': u'Création virement interne ',
                       'form': form,
                       'cpt': cpt}
        )


@login_required
def ope_delete(request, pk):
    ope = get_object_or_404(Ope.objects.select_related(), pk=pk)
    if request.method == 'POST':
        if ope.rapp:
            messages.error(request, u"impossible d'effacer une opération rapprochée")
            return http.HttpResponseRedirect(ope.get_absolute_url())
        else:
            if ope.jumelle:
                if ope.jumelle.rapp:
                    messages.error(request, u"impossible d'effacer une opération rapprochée")
                    return http.HttpResponseRedirect(ope.get_absolute_url())
                else:
                    ope.jumelle.delete()
                    ope.delete()
                    messages.success(request, u"virement effacé")
            else:
                ope.delete()
                messages.success(request, u"opération effacé")
    else:
        return http.HttpResponseRedirect(ope.get_absolute_url())
        # si pas de formulaire, c'est que c'est une tentative d'intrusion
    return http.HttpResponseRedirect(ope.compte.get_absolute_url())


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
            return http.HttpResponseRedirect(compte.get_absolute_url())
    else:
        form = gsb_forms.MajCoursform(
            initial={'titre': titre, 'cours': titre.last_cours(), 'date': titre.last_cours_date()})
        # petit bidoullage afin recuperer le compte d'origine
    if titre.compte_set.all().distinct().count() == 1:
        url = titre.compte_set.all().distinct()[0].get_absolute_url()
    else:
        url = reverse("gsb.views.index")
    return render(request, "gsb/maj_cours.djhtm", {"titre": u"maj du titre '%s'" % titre.nom, "form": form, "url": url})


@login_required
def titre_detail_cpt(request, cpt_id, titre_id, all=False, rapp=False): 
    """view qui affiche la liste des operations relative a un titre (titre_id) d'un compte titre (cpt_id)
    si rapp affiche uniquement les rapp
    si all affiche toute les ope
    sinon affiche uniquement les non rapp"""
    titre = get_object_or_404(Titre.objects.select_related(), pk=titre_id)
    compte = get_object_or_404(Compte.objects.select_related(), pk=cpt_id)
    request.session['titre'] = titre_id

    date_rappro = compte.date_rappro()
    solde_rappro = titre.encours(compte=compte, rapp=True)
    q = Ope_titre.objects.filter(compte__pk=cpt_id).order_by('-date').filter(titre=titre)
    if all:
        pass
    else:
        # on prend comme reference les ope especes
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
    return http.HttpResponse(
        template.render(
            RequestContext(
                request,
                {
                    'compte': compte,
                    'titre_id': titre.id,
                    'list_ope': opes,
                    'titre': "%s: %s" % (compte.nom, titre.nom),
                    'encours': titre.encours(compte),
                    't': titre,
                    'nb_titre': titre.nb(compte),
                    'nb_r': titre.nb(compte, rapp=True),
                    'date_rappro': date_rappro,
                    'solde_rappro': solde_rappro,
                    'investi_r': titre.investi(compte, rapp=True),
                    'pmv': titre.encours(compte) - titre.investi(compte)
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
        # date_initial = ope.date#inutile
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
            return http.HttpResponseRedirect(reverse('gsb_cpt_titre_detail',
                                                     kwargs={'cpt_id': ope.compte.id,
                                                             'titre_id': ope.titre.id}
            )
            )
    else:
        form = gsb_forms.Ope_titreForm(instance=ope)
    if ope.ope is not None:
        rapp = bool(ope.ope.rapp_id)
    else:
        rapp = False
    return render(request, 'gsb/ope_titre_detail.djhtm',
                  {'titre_long': u'opération sur titre %s' % ope.id,
                   'titre': u'modification',
                   'form': form,
                   'ope': ope,
                   'rapp': rapp}
    )


@login_required
def ope_titre_delete(request, pk):
    ope = get_object_or_404(Ope_titre.objects.select_related(), pk=pk)
    if request.method == 'POST':
        if ope.ope and ope.ope.rapp:
            messages.error(request, u"impossible d'effacer une operation rapprochée")
            return http.HttpResponseRedirect(ope.get_absolute_url())
        compte_id = ope.compte.id
        titre_id = ope.titre.id
        # gestion des cours inutiles
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
        return http.HttpResponseRedirect(reverse('gsb_cpt_titre_detail',
                                                 kwargs={'cpt_id': compte_id,
                                                         'titre_id': titre_id}
        )
        )
    else:
        return http.HttpResponseRedirect(ope.get_absolute_url())


@login_required
def ope_titre_achat(request, cpt_id):
    compte = get_object_or_404(Compte.objects.select_related(), pk=cpt_id)
    if compte.type != 't':
        messages.error(request, "ce n'est pas un compte titre")
        return http.HttpResponseRedirect(reverse("index"))
    try:
        titre_id = request.session['titre']
        titre = Titre.objects.get(id=titre_id)
    except Titre.DoesNotExist:  # on est dans le cas où l'on viens d'une page avec un titre qui n'existe pas
        messages.error(request, u"attention le titre demandé initialement n'existe pas")
        titre_id = None
        titre = None
    except KeyError:  # on est dans le cas où l'on viens d'une page sans titre defini
        titre_id = None
        titre = None

    if request.method == 'POST':
        form = gsb_forms.Ope_titre_add_achatForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['titre']:
                titre = form.cleaned_data['titre']
            else:
                titre = Titre.objects.get_or_create(nom=form.cleaned_data['nouveau_titre'],
                                                    defaults={'nom': form.cleaned_data['nouveau_titre'],
                                                              'type': 'ZZZ',
                                                              'isin': form.cleaned_data['nouvel_isin']
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
            return http.HttpResponseRedirect(compte.get_absolute_url())
    else:
        if titre_id:
            form = gsb_forms.Ope_titre_add_achatForm(initial={'compte_titre': compte, 'titre': titre})
        else:
            form = gsb_forms.Ope_titre_add_achatForm(initial={'compte_titre': compte})
    titre = u' nouvel achat sur %s' % compte.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
                  {'titre_long': titre,
                   'titre': u'modification',
                   'form': form,
                   'cpt': compte,
                   'sens': 'achat'}
    )


@login_required
def ope_titre_vente(request, cpt_id):
    compte = get_object_or_404(Compte.objects.select_related(), pk=cpt_id)
    if compte.type != 't':
        messages.error(request, "ce n'est pas un compte titre")
        return http.HttpResponseRedirect(reverse("index"))

    try:
        titre_id = request.session['titre']
        titre = Titre.objects.get(id=titre_id)
    except Titre.DoesNotExist:  # on est dans le cas où l'on viens d'une page avec un titre qui n'existe pas
        messages.error(request, u"attention le titre demandé intialement n'existe pas")
        titre_id = None
        titre = None
    except AttributeError:  # on est dans le cas où l'on viens d'une page sans titre defini
        titre_id = None
        titre = None

    if compte.titre.all().distinct().count() < 1:
        messages.error(request, 'attention, ce compte ne possède aucun titre. donc vous ne pouvez pas vendre')
        return http.HttpResponseRedirect(compte.get_absolute_url())

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
            return http.HttpResponseRedirect(compte.get_absolute_url())
    else:
        if titre_id:
            form = gsb_forms.Ope_titre_add_venteForm(initial={'compte_titre': compte, 'titre': titre}, cpt=compte)
        else:
            form = gsb_forms.Ope_titre_add_venteForm(initial={'compte_titre': compte}, cpt=compte)
    titre = u' nouvelle vente sur %s' % compte.nom
    return render(request, 'gsb/ope_titre_create.djhtm',
                  {'titre_long': titre,
                   'titre': u'modification',
                   'form': form,
                   'cpt': compte,
                   'sens': 'vente'}
    )


@login_required
def view_maj_cpt_titre(request, cpt_id):
    """mise a jour global d'un portefeuille"""
    cpt = Compte.objects.get(id=cpt_id)
    if cpt.type != 't':
        messages.error(request, "ce n'est pas un compte titre")
        return http.HttpResponseRedirect(reverse("index"))

    liste_titre_original = cpt.titre.all().distinct()
    liste_titre = []
    if liste_titre_original.count() < 1:
        messages.error(request, u'attention, ce compte ne possède aucun titre. donc vous ne pouvez mettre a jour')
        return http.HttpResponseRedirect(cpt.get_absolute_url())
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
                                  cat_frais=Cat.objects.get(id=settings.ID_CAT_COTISATION),)
                    else:
                        cpt.achat(titre_en_cours, nb, cours, date=form.cleaned_data['date'])
                else:
                    if not Cours.objects.filter(date=form.cleaned_data['date'], titre=titre_en_cours).exists() and \
                       cours:
                        Cours.objects.create(date=form.cleaned_data['date'], titre=titre_en_cours, valeur=cours)

            return http.HttpResponseRedirect(cpt.get_absolute_url())
    else:
        form = gsb_forms.Majtitre(titres=liste_titre)
    return render(request, 'gsb/maj_cpt_titre.djhtm',
                  {'titre_long': u'operations sur le %s' % cpt.nom,
                   'titre': u'ope',
                   'form': form,
                   'titres': liste_titre,
                   'compte': cpt}
    )


@login_required
def search_opes(request):
    if request.method == 'POST':
        form = gsb_forms.SearchForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            compte = data['compte']
            if compte:
                q = Ope.objects.filter(compte=compte, date__gte=data['date_min'], date__lte=data['date_max'])
            else:
                q = Ope.objects.filter(date__gte=data['date_min'], date__lte=data['date_max'])
            sort = request.GET.get('sort')
            if sort:
                sort = unicode(sort)
                q = q.order_by(sort)
                sort_get = u"&sort=%s" % sort
            else:
                sort_get = ""
                q = q.order_by('-date')
            q = q.select_related('tiers', 'cat', 'rapp', 'moyen', 'jumelle', 'ope')[:100]
            if compte:
                titre = u'recherche des %s premières opérations du compte %s' % (q.count(), compte.nom)
            else:
                titre = u'recherche des %s premières opérations' % q.count()
            if compte:
                solde = compte.solde(datel=data['date_max'])
            else:
                solde = 0

            return render(request, 'templates_perso/search.djhtm', {'form': form,
                                                                    'list_ope': q,
                                                                    'titre': titre,
                                                                    "sort": sort_get,
                                                                    'date_max': data['date_max'],
                                                                    'solde': solde})
        else:
            date_max = Ope.objects.aggregate(element=models.Max('date'))['element']
    else:
        date_min = Ope.objects.aggregate(element=models.Min('date'))['element']
        date_max = Ope.objects.aggregate(element=models.Max('date'))['element']
        form = gsb_forms.SearchForm(initial={'date_min': date_min, 'date_max': date_max})

    return render(request, 'templates_perso/search.djhtm', {'form': form,
                                                            'list_ope': None,
                                                            'titre': 'recherche',
                                                            "sort": "",
                                                            'date_max': date_max,
                                                            'solde': None})


def perso(request):
    resultat = []
    for r in Rapp.objects.filter(nom__startswith="Sg"):
        solde_visa = r.ope_set.filter(compte__nom="Visa").aggregate(total=models.Sum('montant'))['total']
        if solde_visa:
            resultat.append(r.nom)
            resultat.append(solde_visa)
            # r.save()
    return render(request, 'generic.djhtm',
                  {'resultats': resultat,
                   'titre_long': "traitement personalise",
                   'titre': "perso",
                  }
    )
