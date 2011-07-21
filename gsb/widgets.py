# -*- coding: utf-8
from django.forms import widgets
class DateInput_perso(widgets.DateInput):
    format = '%d%m%Y'     # '2006-10-25'

    def __init__(self, attrs=None):
        super(DateInput_perso, self).__init__(attrs=attrs, format="%d%m%Y")
