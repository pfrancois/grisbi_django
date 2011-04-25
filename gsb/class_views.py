# -*- coding: utf-8 -*-
# Create your views here.
from mysite.gsb.models import *
#view generiques
from django.views.generic import  DetailView

class ope_view(DetailView):
    queryset = Ope.objects.all()

    def get_object(self):
        object = super(DetailView, self).get_object()
