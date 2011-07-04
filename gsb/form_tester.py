# -*- coding: utf-8
from django.contrib.formtools.preview import FormPreview
from mysite.gsb.models import *
from django.http import HttpResponseRedirect
class SomeModelFormPreview(FormPreview):
    def done(self, request, cleaned_data):
        return  HttpResponseRedirect('/')
