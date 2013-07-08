# -*- coding: utf-8
from datetime import date
from time import mktime
import decimal
import os
from django.db import models
from django import forms
import gsb.utils as utils


# definition d'un moneyfield
class CurField(models.DecimalField):
    """
    un champ decimal mais defini pour les monnaies
    """
    description = u"A Monetary value"

    # __metaclass__ = models.SubfieldBase # ca marche pas chez always data
    def __init__(self, verbose_name=None, name=None, max_digits=15, decimal_places=2, default=0.00,
                 **kwargs):
        super(CurField, self).__init__(verbose_name, name, max_digits, decimal_places, default=default, **kwargs)

    def get_internal_type(self):
        return models.DecimalField.__name__

    def __mul__(self, other):
        return decimal.Decimal(self) * decimal.Decimal(other)

class ExtFileField(forms.FileField):
    """
    http://djangosnippets.org/snippets/977/
    Same as forms.FileField, but you can specify a file extension whitelist.

    >>> from django.core.files.uploadedfile import SimpleUploadedFile
    >>>
    >>> t = ExtFileField(ext_whitelist=(".pdf", ".txt"))
    >>>
    >>> t.clean(SimpleUploadedFile('filename.pdf', 'Some File Content'))
    >>> t.clean(SimpleUploadedFile('filename.txt', 'Some File Content'))
    >>>
    >>> t.clean(SimpleUploadedFile('filename.exe', 'Some File Content'))
    Traceback (most recent call last):
    ...
    ValidationError: [u'Not allowed filetype!']
    """

    def __init__(self, *args, **kwargs):
        ext_whitelist = kwargs.pop("ext_whitelist")
        self.ext_whitelist = [i.lower() for i in ext_whitelist]

        super(ExtFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ExtFileField, self).clean(*args, **kwargs)
        if data is None:
            if self.required:
                raise forms.ValidationError("This file is required")
            else:
                return
        else:
            filename = data.name
            ext = os.path.splitext(filename)[1]
            ext = ext.lower()
            if ext not in self.ext_whitelist:
                file_types = ", ".join([i for i in self.ext_whitelist])
                error = "Only allowed file types are: %s" % file_types
                raise forms.ValidationError(error)

class uuidfield(models.CharField):
    """tire de la
    https://github.com/gugu/django-uuid/blob/master/src/django_uuid/fields.py
    """
    def __init__(self, verbose_name=None, name=None, auto=True, add=False, **kwargs):
        kwargs['max_length'] = 36
        self.auto = auto
        self.add = add
        if auto:
            kwargs['blank'] = True
            kwargs['editable'] = kwargs.get('editable', False)
        super(uuidfield, self).__init__(**kwargs)

    def get_internal_type(self):
        return models.CharField.__name__

    def pre_save(self, model_instance, add):
        if self.auto and add:
            value = unicode(utils.uuid())
            setattr(model_instance, self.attname, value)
            return value
        else:
            value = super(uuidfield, self).pre_save(model_instance, add)
            if self.auto and not value:
                value = unicode(utils.uuid())
                setattr(model_instance, self.attname, value)
        return value
