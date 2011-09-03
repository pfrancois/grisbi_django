# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os
    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    from mysite import settings
    setup_environ(settings)

#from mysite.gsb.models import Tiers, Titre, Cat, Ope, Banque, Ib, Exercice, Rapp, Moyen, Echeance, Generalite, Compte, Compte_titre, Histo_ope_titres, Virement, Titres_detenus, Cours
# 
from django.http import HttpResponse

#from django.core.exceptions import ObjectDoesNotExist
#import decimal
from django.conf import settings #@Reimport
from datetime import date
from django.contrib.admin.views.decorators import staff_member_required


def _export():
    #output backup
    cmd = settings.MYSQLDUMP_BIN + ' --opt --compact --skip-add-locks -u %s -p%s %s | gzip -c' % (settings.DATABASE_USER, settings.DATABASE_PASSWORD, settings.DATABASE_NAME)
    stdin, stdout = os.popen2(cmd)
    stdin.close()
    return stdout

@staff_member_required
def export_database(request): #@UnusedVariable
    '''
    view pour export en sql 
    '''
    response = HttpResponse(_export(), mimetype = "application/octet-stream")
    response['Content-Disposition'] = 'attachment; filename=%s' % date.today().__str__() + '_db.sql.bz2'
    return response
            
if __name__ == "__main__":
    xml_string = _export()
    fichier = open("%s/export.gz" % (os.path.dirname(os.path.abspath(__file__))), "w")
    fichier.write(xml_string)
    fichier.close()
