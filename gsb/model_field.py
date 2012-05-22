# -*- coding: utf-8
from django.db import models
from datetime import date
from time import strftime,mktime
from django import forms
import decimal
#definition d'un moneyfield
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
        return "DecimalField"

    def __mul(self, other):
        return decimal.Decimal(self) * decimal.Decimal(other)


class UnixTimestampField(models.DateTimeField):
    """UnixTimestampField: creates a DateTimeField that is represented on the
    database as a TIMESTAMP field rather than the usual DATETIME field.
    """
    description="utilisation des timestamp"
    __metaclass__ = models.SubfieldBase
    def __init__(self, null=False, blank=False, **kwargs):
        super(UnixTimestampField, self).__init__(**kwargs)
        # default for TIMESTAMP is NOT NULL unlike most fields, so we have to
        # cheat a little:
        self.blank, self.isnull = blank, null
        self.null = True # To prevent the framework from shoving in "not null".
        self.editable=False

    def db_type(self):
        typ=['TIMESTAMP']
        # See above!
        if self.isnull:
            typ += ['NULL']
        return ' '.join(typ)

    def to_python(self, value):
        if value == None:
            return None
        elif value=="":
            return date.fromtimestamp(1)
        else:
            value=u"%s"%value
            return date.fromtimestamp(float(value.replace(",",".")))

    def get_db_prep_value(self, value):
        if value==None:
            return None
        return mktime(value.timetuple())

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.DateTimeField}
        defaults.update(kwargs)
        return super(UnixTimestampField, self).formfield(**defaults)
