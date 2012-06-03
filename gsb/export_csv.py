# -*- coding: utf-8 -*-
from __future__ import absolute_import

if __name__ == "__main__":
    import sys, os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.gsb.settings")
    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    from django.core.management import execute_from_command_line


    #from django.conf import settings
    #from mysite.gsb import settings as defaults
    #settings.configure(default_settings=defaults)

    from .models import Compte, Ope
    from .utils import Format, strpdate
else:
    from .models import Compte, Ope
    from .utils import Format, strpdate

import codecs, csv, cStringIO
import logging
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.conf import settings

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, fich, encoding):
        self.reader = codecs.getreader(encoding)(fich)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, dialect=csv.excel, encoding="utf-8", **kwds):
        fich = UTF8Recoder(fich, encoding)
        self.reader = csv.reader(fich, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, **kwds)
        self.stream = fich
        # Force BOM
        #        if encoding=="utf-16":
        #            f.write(codecs.BOM_UTF16)
        self.encoding = encoding

    def writerow(self, row):
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = data.encode(self.encoding)
        # strip BOM
        #       if self.encoding == "utf-16":
        #           data = data[2:]
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class Excel_csv(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\r\n'
    quoting = csv.QUOTE_MINIMAL


def _export():
    """
    fonction principale mais est appelé  par un view
    """
    logger = logging.getLogger('gsb.export')
    csv.register_dialect("excel_csv", Excel_csv)
    fich = cStringIO.StringIO()
    fmt = Format()
    csv_file = UnicodeWriter(fich, encoding='iso-8859-15', dialect=Excel_csv)
    csv_file.writerow(u'ID;Account name;date;montant;P;M;moyen;cat;Tiers;Notes;projet;N chq;id lié;op vent M;num op vent M;mois'.split(';'))
    opes = Ope.objects.all().order_by('date').select_related('cat', "compte", "tiers", "ib").filter(date__gte=strpdate("2009-01-01"))
    i = 0
    total = float(opes.count())
    for ope in opes:
        i += 1
        ligne = [ope.id, ope.compte.nom, fmt.date(ope.date), fmt.float(ope.montant)]
        if ope.rapp is None:
            ligne.append(0)
        else:
            ligne.append(1)
        ligne.append(fmt.bool(ope.pointe))
        ligne.append(fmt.str(ope.moyen, '', 'nom'))
        cat_g = fmt.str(ope.cat, "", "nom").split(":")
        ligne.append("(%s)%s" % (fmt.str(ope.cat, "", "type"), cat_g[0].strip()))
        ligne.append(ope.tiers)
        ligne.append(ope.notes)
        if ope.ib:
            ligne.append(ope.ib.nom)
        else:
            ligne.append('')
        ligne.append(ope.num_cheque)
        ligne.append(fmt.str(ope.jumelle, ''))
        ligne.append(fmt.bool(ope.mere))
        ligne.append(fmt.str(ope.mere, ''))
        ligne.append(ope.date.strftime('%Y_%m'))
        csv_file.writerow(ligne)
        #on affiche que tous les 100 lignes
        if not ( i / 100.0 - int(i / 100)) != 0:
            logger.info("ligne %s %s%%" % (ope.id, i / total * 100))
    return fich


def export(request):
    nb_compte = Compte.objects.count()
    if nb_compte:
        dump = _export().getvalue()
        #h=HttpResponse(xml,mimetype="application/xml")
        reponse = HttpResponse(dump, mimetype="text/csv")
        reponse["Cache-Control"] = "no-cache, must-revalidate"
        reponse["Content-Disposition"] = "attachment; filename=%s.csv" % settings.TITRE
        return reponse
    else:
        return render_to_response('generic.djhtm',
                {'titre':'import csv',
                 'resultats':({'texte':u"attention, il n'y a pas de comptes donc pas de possibilité d'export."},)
            },
                                  context_instance=RequestContext(request)
        )

if __name__ == '__main__':
    chaine = _export()
    f = open('test.csv', "wb")

    f.write(chaine.getvalue())
    #print chaine.getvalue()
