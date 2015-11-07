# -*- coding: utf-8

from django import forms
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from django.conf import settings
import gsb.utils as utils

input_format_date = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y')


class Dategsbwidget(forms.DateInput):
    """ widget de gestion des dates simple marche sur n95
    """

    # noinspection PyClassHasNoInit
    class Media(object):
        js = ("gsb/js/basiccalendar.js",)
        css = {'all': ('gsb/css/calendar.css',)}

    def __init__(self, attrs=None):  # @UnusedVariable
        super(Dategsbwidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(self._format_value(value))
        cal = '<a href="javascript:editDate(\'%s\');" title="calendrier"><img src="%s" alt="calendrier"/></a>' % (
            final_attrs['id'], settings.STATIC_URL + "gsb/img/calendar.png")
        return mark_safe(
            '<input%s /><span id="date_shct">%s</span><div class="editDate ope_date_ope" id="editDateId"></div>' % (
                flatatt(final_attrs), cal))


class DateFieldgsb(forms.DateField):
    """field qui marche avec le widget au dessus"""

    def __init__(self, input_formats=input_format_date, initial=utils.today, **kwargs):
        super(DateFieldgsb, self).__init__(input_formats=input_formats, initial=initial, widget=Dategsbwidget,
                                           **kwargs)


class Titrewidget(forms.MultiWidget):
    """widget utilise pour la maj des titres"""

    def __init__(self, attrs=None):
        widgets = (Curwidget(attrs=attrs, ),
                   forms.TextInput(attrs=attrs, ))
        super(Titrewidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            chaine = force_text(value).partition('@')
            if chaine[1]:
                return [chaine[2], chaine[0]]
            else:
                return [0, 0]
        else:
            return [0, 0]


class TitreField(forms.MultiValueField):
    """field utilisé pour la maj des titres"""

    def __init__(self, *args, **kwargs):
        fields = (CurField(label='cur'), forms.DecimalField(initial='0', label='nb'))
        super(TitreField, self).__init__(fields, widget=Titrewidget(), *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return "%s@%s" % (data_list[1], data_list[0])
        else:
            return None


class Readonlywidget(forms.Widget):
    text = ''
    is_hidden = False

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type='hidden', name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(value)
        hidden = '<input%s />' % flatatt(final_attrs)
        text = force_text(self.text)
        return mark_safe("<div>%s%s</div>" % (hidden, text))

    # noinspection PyUnusedLocal
    def _has_changed(self, initial, data):  # @UnusedVariable
        return False


class ReadonlyField(forms.FileField):
    widget = Readonlywidget

    def __init__(self, instance=None, attr=None, *args, **kwargs):  # @UnusedVariable
        self.attr = attr
        forms.Field.__init__(self, *args, **kwargs)
        if instance and instance.id:
            self.instance = instance
            self.initial = getattr(instance, self.attr)
            if self.initial:
                self.widget.text = self.initial.__str__()
            else:
                self.widget.text = "aucun"
                self.instance = None
        else:
            self.instance = None

    def clean(self, value, initial=None):
        if initial:
            return initial
        return getattr(self, 'initial', None)


class Curwidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type='text', name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(value)
        hidden = '<input%s />' % flatatt(final_attrs)
        text = force_text("&#8364;")
        return mark_safe("<span>%s%s</span>" % (hidden, text))


class CurField(forms.DecimalField):
    def __init__(self, localize=True, initial='0', widget=Curwidget, *args, **kwargs):
        super(CurField, self).__init__(localize=localize, initial=initial, widget=widget, *args, **kwargs)
