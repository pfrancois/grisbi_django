# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from mysite.gsb.models import *
import mysite.gsb.forms as gsb_forms
import mysite.gsb.import_gsb as import_gsb
import logging

def import_file(request):
    import mysite.gsb.import_gsb
    logger=logging.getLogger('gsb.import')
    if request.method == 'POST':
        form = gsb_forms.ImportForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info('debut import')
            logger.info('debut import')
            mysite.gsb.import_gsb.import_gsb(request.FILES['nom_du_fichier'])
            logger.info('fin import')
            return HttpResponseRedirect(reverse('gsb.views.index'))
    else:
        form = gsb_forms.ImportForm()
    return render_to_response('gsb/import.django.html',
                              {'form': form,
                               'titre':"importation d'un fichier"},
                              context_instance=RequestContext(request))

def options(request):
    return render_to_response('gsb/options.django.html', context_instance=RequestContext(request))
