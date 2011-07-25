# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response
import mysite.gsb.forms as gsb_forms
import logging, os, time
from mysite.gsb.models import Generalite
from django.contrib.auth.decorators import login_required

@login_required
def import_file(request):
    import mysite.gsb.import_gsb
    logger = logging.getLogger('gsb.import')
    if request.method == 'POST':
        form = gsb_forms.ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                info = u"%s le %s" % (request.META['REMOTE_ADDR'], time.strftime(u"%Y-%b-%d a %H-%M-%S"))
            except KeyError:
                info = u"%s le %s" % ('0.0.0.0', time.strftime(u"%Y-%b-%d a %H-%M-%S"))
            nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.gsb" % (request.FILES['nom_du_fichier'].name, time.strftime("%Y-%b-%d_%H-%M-%S")))
            destination = open(nomfich, 'wb+')
            for chunk in request.FILES['nom_du_fichier'].chunks():
                destination.write(chunk)
            destination.close()
            logger.debug("enregitrement fichier ok")
            ok = False
            if form.cleaned_data['replace'] == 'remplacement':
                logger.warning(u"remplacement data par fichier %s format %s %s" % (nomfich, form.cleaned_data['version'], info))
                if form.cleaned_data['version'] == 'gsb_0_5_0':
                    mysite.gsb.import_gsb.import_gsb(nomfich, True)
                    ok = True
            else:
                logger.warning("fusion data par fichier %s format %s %s" % (nomfich, form.cleaned_data['version'], info))
                if form.cleaned_data['version'] == 'gsb_0_5_0':
                    mysite.gsb.import_gsb.import_gsb(nomfich, False)
                    ok = True
            if ok:
                return HttpResponseRedirect(reverse('gsb.views.index'))
            else:
                return render_to_response('gsb/import.django.html',
                              {'form': form,
                               'titre':"importation d'un fichier"},
                              context_instance=RequestContext(request))
    else:
        form = gsb_forms.ImportForm()
    return render_to_response('gsb/import.django.html',
                              {'form': form,
                               'titre':"importation d'un fichier"},
                              context_instance=RequestContext(request))

def options_index(request):
    return render_to_response('gsb/options.django.html', context_instance=RequestContext(request))

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
            return HttpResponseRedirect(reverse('gsb.outils.options_index'))
        else:
            return  render_to_response('gsb/outil_generalites.django.html',
            {   'titre':u'modification de certaines options',
                'form':form},
            context_instance=RequestContext(request)
        )
    else:
        form = gsb_forms.GeneraliteForm(instance=Generalite.gen())
        return  render_to_response('gsb/outil_generalites.django.html',
            {   'titre':u'modification de certaines options',
                'form':form},
            context_instance=RequestContext(request)
        )
