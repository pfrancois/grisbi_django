# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response
import mysite.gsb.forms as gsb_forms
import logging, os, time

def import_file(request):
    import mysite.gsb.import_gsb
    logger=logging.getLogger('gsb.import')
    if request.method == 'POST':
        form = gsb_forms.ImportForm(request.POST, request.FILES)
        if form.is_valid():#todo gerer l'authentification
            try:
                logger.warning("import d'un fichier par %s le %s"%(request.META['REMOTE_ADDR'],time.strftime("%Y-%b-%d a %H-%M-%S")))
            except KeyError:
                logger.warning("import d'un fichier par %s le %s"%('0.0.0.0',time.strftime("%Y-%b-%d a %H-%M-%S")))
            nomfich=os.path.join(settings.PROJECT_PATH,'upload',"%s-%s.gsb"%(request.FILES['nom_du_fichier'].name,time.strftime("%Y-%b-%d_%H-%M-%S")))
            destination = open(nomfich, 'wb+')
            for chunk in request.FILES['nom_du_fichier'].chunks():
                destination.write(chunk)
            destination.close()
            logger.info("enregitrement fichier ok")
            mysite.gsb.import_gsb.import_gsb(nomfich)
            logger.info("import ok")
            return HttpResponseRedirect(reverse('gsb.views.index'))
    else:
        form = gsb_forms.ImportForm()
    return render_to_response('gsb/import.django.html',
                              {'form': form,
                               'titre':"importation d'un fichier"},
                              context_instance=RequestContext(request))

def options(request):
    return render_to_response('gsb/options.django.html', context_instance=RequestContext(request))