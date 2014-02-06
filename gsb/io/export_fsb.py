# -*- coding: utf-8 -*-


# from mysite.gsb.models import Tiers, Titre, Cat, Ope, Banque, Ib, Exercice, Rapp, Moyen, Echeance, Compte, ope_titres, Virement, Cours
#
from django.http import HttpResponse
from django.conf import settings  # @Reimport
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import View
from django.utils.decorators import method_decorator

from sql.pg import sqlite_db


class export_fsb_view(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        """on a besoin pour le method decorator"""
        return super(export_fsb_view, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        engine = settings.DATABASES['default']['ENGINE']
        if engine == 'django.db.backends.sqlite3':
            db = sqlite_db(settings.DATABASES['default']['NAME'])
            return HttpResponse(list(db.dump()), content_type="text/plain")
        else:
            raise NotImplementedError("il faut initialiser")
