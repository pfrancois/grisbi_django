# -*- coding: utf-8 -*-
# Create your views here.
from __future__ import absolute_import
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response
from . import forms as gsb_forms
import logging, os, time
from .models import Generalite, Echeance
from django.contrib.auth.decorators import login_required
from .import_gsb import import_gsb_050
from django.contrib import messages
import os

@login_required
def import_file(request):
    logger = logging.getLogger('gsb.import')
    nomfich = ""
    etape_nb = 1
    liste_import = {"gsb_0_5_0":gsb_forms.ImportForm2_gsb_0_5_0,
                    "qif":gsb_forms.ImportForm2_qif}
    if request.method == 'POST':
        if request.session.get('import_etape_nb', '1') == 1:
            form = gsb_forms.ImportForm1(request.POST, request.FILES)
            if form.is_valid():
                nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.gsb" % (
                    request.FILES['nom_du_fichier'].name, time.strftime("%Y-%b-%d_%H-%M-%S")))
                destination = open(nomfich, 'wb+')
                for chunk in request.FILES['nom_du_fichier'].chunks():
                    destination.write(chunk)
                destination.close()
                #renomage ok
                logger.debug("enregistrement fichier ok")
                request.session['nomfich'] = nomfich
                request.session['import_type'] = form.cleaned_data['type_f']
                try:
                    form = liste_import[form.cleaned_data['type_f']]()
                    etape_nb = 2
                except KeyError:
                    messages.error(request, message="type d'import inconnu")
        else:
            try:
                form = liste_import[request.session['import_type']](request.POST)
                if form.is_valid():
                    # on recupere les info pour le nom
                    try:
                        info = u"%s le %s" % (request.META['REMOTE_ADDR'], time.strftime(u"%A %d %B %Y a %Hh%Mm%Ss tz:%z"))
                    except KeyError:
                        info = u"%s le %s" % ('0.0.0.0', time.strftime(u"%A %d %B %Y a %Hh%Mm%Ss tz:%z"))
                        #-----------------------gestion des imports
                    try:
                        nomfich = request.session['nomfich']
                        #on essaye d'ouvrir le fichier
                        destination = open(nomfich, 'r')
                        #si on peut
                        destination.close()
                        if request.session['import_type'] == 'qif':
                            if nomfich[-3:] == "qif":
                                import_qif(nomfich, compte=form.cleaned_data['compte'])
                            else:
                                raise ValueError("pas le bon format")
                        elif request.session['import_type'] == 'gsb_0_5_0':
                            if nomfich[-3:] == "gsb":
                                if form.cleaned_data['replace'] == 'remplacement':
                                    logger.warning(
                                        u"remplacement data par fichier %s format %s %s" % (nomfich, request.session['import_type'], info))
                                    import_gsb_050(nomfich=nomfich, efface_table=True)
                                else:
                                    logger.warning(
                                        u"fusion data par fichier %s format %s %s" % (nomfich, request.session['import_type'], info))
                                    import_gsb_050(nomfich=nomfich, efface_table=False)
                            else:
                                raise ValueError("pas le bon format")
                        else:
                            raise NotImplementedError(u' %s pas implementé' % request.session['import_type'])
                    except Exception as exp:
                        logger.warning(u"probleme d'importation à cause de %s(%s) " % (type(exp), exp))
                        messages.error(request, u"erreur dans l'import du fichier %s" % nomfich)
                    else:
                        messages.success(request, u"import du fichier %s ok" % nomfich)
                        return HttpResponseRedirect(reverse('gsb.views.index'))
            except KeyError:
                messages.error(request, message="type d'import inconnu")
    else:
        form = gsb_forms.ImportForm1()
        etape_nb = 1
    request.session['import_etape_nb'] = etape_nb
    param = {'form':form,
             'titre':u"importation d'un fichier: étape %s" % etape_nb,
             'etape_nb':etape_nb}
    return render_to_response('gsb/import.djhtm',
                              param,
                              context_instance=RequestContext(request))


def options_index(request):
    return render_to_response('gsb/options.djhtm', context_instance=RequestContext(request))


@login_required
def modif_gen(request):
    logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.GeneraliteForm(request.POST, request.FILES)
        if form.is_valid():
            g = Generalite.gen()
            logger.info('modification de gen')
            g.utilise_exercices = form.cleaned_data['utilise_exercices']
            g.utilise_ib = form.cleaned_data['utilise_ib']
            g.utilise_pc = form.cleaned_data['utilise_pc']
            g.affiche_clot = form.cleaned_data['affiche_clot']
            g.save()
            return HttpResponseRedirect(reverse('mysite.gsb.outils.options_index'))
        else:
            return  render_to_response('gsb/outil_generalites.djhtm',
                    {'titre':u'modification de certaines options',
                     'form':form},
                                       context_instance=RequestContext(request)
            )
    else:
        form = gsb_forms.GeneraliteForm(instance=Generalite.gen())
        return  render_to_response('gsb/outil_generalites.djhtm',
                {'titre':u'modification de certaines options',
                 'form':form},
                                   context_instance=RequestContext(request)
        )


@login_required
def gestion_echeances(request):
    Echeance.check(request)
    return render_to_response('gsb/options.djhtm', {'titre':u'integration des échéances échues', }, context_instance=RequestContext(request))
