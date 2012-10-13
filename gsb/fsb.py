# -*- coding: utf-8 -*-


#from mysite.gsb.models import Tiers, Titre, Cat, Ope, Banque, Ib, Exercice, Rapp, Moyen, Echeance, Compte, Compte_titre, ope_titres, Virement, Cours
#
from django.http import HttpResponse

from django.core.exceptions import ObjectDoesNotExist
import decimal
from django.conf import settings #@Reimport
from datetime import date
from django.contrib.admin.views.decorators import staff_member_required
import os
import gsb.utils as utils

def _export():
    #output backup
    cmd = settings.MYSQLDUMP_BIN + ' --opt --compact --skip-add-locks -u %s -p%s %s | gzip -c' % (
        settings.DATABASE_USER, settings.DATABASE_PASSWORD, settings.DATABASE_NAME)
    stdin, stdout = os.popen2(cmd)
    stdin.close()
    return stdout


@staff_member_required
def export_database(request): #@UnusedVariable
    """
    view pour export en sql
    """
    response = HttpResponse(_export(), mimetype="application/octet-stream")
    response['Content-Disposition'] = 'attachment; filename=%s' % utils.today().__str__() + '_db.sql.bz2'
    return response

if __name__ == "__main__":
    xml_string = _export()
    fichier = open("%s/export.gz" % (os.path.dirname(os.path.abspath(__file__))), "w")
    fichier.write(xml_string)
    fichier.close()
