# -*- coding: utf-8
from django.contrib.formtools.preview import FormPreview
from mysite.gsb.models import * #@UnusedWildImport
from django.http import HttpResponseRedirect
class SomeModelFormPreview(FormPreview):
    form_template = "form/form.html"
    preview_template = "form/preview.html"
    def done(self, request, cleaned_data):#@UnusedVariable
        return  HttpResponseRedirect('/')
