# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings  # @Reimport

# from django.contrib import messages
from django.http import HttpResponse
# from .models import (Tiers, Cat, Ib, Exercice, Moyen, Compte, Titre, Ope_titre, Rapp, Ope)
from . import import_base
from .. import utils

from . import import_csv

def mot(var):
    return var.partition(' ')[0].strip()
def reste(var):
    return var.partition(' ')[2].strip()
def mots(var):
    tour = var.split(' ')
    tour1 = []
    for i in tour:
        if i.strip() != '':
            tour1.append(i.strip())
    return tour1

class csv_sg_reader(import_csv.Csv_unicode_reader):

    @property
    def lib(self):
        return self.row['lib'].strip()
    @property
    def detail(self):
        return self.row['detail'].strip()
    @property
    def det(self):
        tour1 = mots(self.detail)
        retour = None
        try:
            if tour1[1] == "EUROPEEN":
                tour1 = ' '.join(tour1[4:])
                retour = tour1
            if self.moyen == "VIR RECU":
                retour = ' '.join(tour1[3:])
            if retour is None:
                retour = ' '.join(tour1[2:])
        except IndexError:
            retour = ' '.join(tour1[1:])
        return retour.strip()

    @property
    def id(self):
        return None

    @property
    def cat(self):
        return None

    @property
    def automatique(self):
        return False

    @property
    def cpt(self):
        return 'SG'

    @property
    def date(self):
        if self.moyen != "CARTE":
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        else:
            if self.det[:4] == "RETR":
                annee = utils.to_date(self.row['date'], "%d/%m/%Y").year
                if mots(self.det)[2] != "SG":
                    return utils.to_date("%s/%s" % (mots(self.det)[2], annee), "%d/%m/%Y")
                else:
                    return utils.to_date("%s/%s" % (mots(self.det)[3], annee), "%d/%m/%Y")
            else:
                annee = utils.to_date(self.row['date'], "%d/%m/%Y").year
                return utils.to_date("%s/%s" % (mot(self.det), annee), "%d/%m/%Y")

    @property
    def date_val(self):
        if self.moyen == "visa":
            return utils.to_date(self.row['date'].strip(), "%d/%m/%Y")
        else:
            return None

    @property
    def exercice(self):
        return None

    @property
    def ib(self):
        return None

    @property
    def jumelle(self):
        # un retrait
        if self.detail[:19] == u"CARTE X4983 RETRAIT":
            return "caisse"
        if self.det[:14] == "GENERATION VIE":
            return "generation vie"
        if self.det[:16] == "Gr Bque - Banque":
            return "groupama"
        return False

    @property
    def mere(self):
        return None

    @property
    def mt(self):
        return utils.to_decimal(self.row['montant'])

    @property
    def moyen(self):
        m = mots(self.detail)
        if mots(self.detail)[0] == "CARTE":
            if mots(self.detail)[2] != "RETRAIT":
                moyen = "visa"
            else:
                moyen = "virement"
        elif m[0] == "VIR" and m[1] == "RECU":
            moyen = "recette"
        elif m[0] == "CHEQUE":
            moyen = "cheque"
        else:
            moyen = "prelevement"
        return moyen

    @property
    def notes(self):
        return self.detail

    @property
    def num_cheque(self):
        if self.moyen == "CHEQUE":
            return int(self.detail.partition(' ')[2].strip())
        else:
            return None

    @property
    def piece_comptable(self):
        return ''

    @property
    def pointe(self):
        return True

    @property
    def rapp(self):
        return None

    @property
    def tiers(self):
        if self.moyen == "cheque":
            return "inconnu"
        if self.moyen == "virement" and self.mt < 0:
            return "%s=>%s" % (self.cpt, self.jumelle)
        if self.moyen == "virement" and self.mt > 0:
            return "%s=>%s" % (self.jumelle, self.cpt)
        if self.moyen == "visa":
            return " ".join(mots(self.detail)[3:])
        return self.det.lower

    @property
    def monnaie(self):
        return None

    @property
    def ope_titre(self):
        return False

    @property
    def ope_pmv(self):
        return False

    @property
    def ligne(self):
        return 0

    @property
    def has_fille(self):
        return False

class testimport_view(import_base.Import_base):
    # classe du reader
    reader = csv_sg_reader
    # extension du fichier
    extension = ('csv',)
    # nom du type de fichier
    type_f = "csv_version_sg"
    def form_valid(self, form):
        # logger = logging.getLogger('gsb.import')
        self.test = False
        nomfich = form.cleaned_data['nom_du_fichier'].name
        nomfich = nomfich[:-4]
        nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.%s" % (
            nomfich, time.strftime("%Y-%b-%d_%H-%M-%S"), self.extension[0]))
        # commme on peut avoir plusieurs extension on prend par defaut la premiere
        # si le repertoire n'existe pas on le crée
        try:
            destination = open(nomfich, 'wb+')
        except IOError:
            os.makedirs(os.path.join(settings.PROJECT_PATH, 'upload'))
            destination = open(nomfich, 'wb+')
        for chunk in self.request.FILES['nom_du_fichier'].chunks():
            destination.write(chunk)
        destination.close()
        # renomage ok
        # logger.debug(u"enregistrement fichier ok")
        reponse = self.import_file(nomfich)
        os.remove(nomfich)
        return HttpResponse(reponse, mimetype="text/plain")
    def import_file(self, nomfich):
        import inspect
        with open(nomfich, 'rt') as f_non_encode:
            fich = self.reader(f_non_encode, encoding="iso-8859-1", fieldnames=['date', 'lib', 'detail', 'montant', 'devise'])
            data = []
            # on passe trois ligne
            fich.next()
            fich.next()
            fich.next()
            for row in fich:
                r = inspect.getmembers(row)
                raise
                data.append(r)
                # data.append({'initial':[row.lib,row.detail],'date':row.date,'montant':row.mt,'jumelle':row.jumelle, 'moyen':row.moyen,'numcheque':row.num_cheque,'tiers':row.tiers})
            import pprint
            return pprint.pformat(data)
