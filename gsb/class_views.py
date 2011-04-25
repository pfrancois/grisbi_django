# -*- coding: utf-8 -*-
# Create your views here.
from django.db import models
from django.template import RequestContext, loader
from mysite.gsb.models import *
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db import models
import datetime
import settings
from django.shortcuts import render_to_response, get_list_or_404,get_object_or_404
#view generiques
from django.views.generic import TemplateView, DetailView

class ope_view(DetailView):
    queryset = Ope.objects.all()
    
    def get_object(self):
        object = super(DetailView, self).get_object()
