# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings  # @Reimport

from django.contrib import messages

from .. import models
from . import import_base
from .. import utils


class Csv_unicode_reader_ope_base(import_base.property_ope_base, utils.Csv_unicode_reader):
    pass


class Csv_unicode_reader_ope_sans_jumelle_et_ope_mere(Csv_unicode_reader_ope_base):

    @property
    def cat(self):
        if self.jumelle:
            return 'Virement'
        else:
            return utils.to_unicode(self.row['cat'], "Divers:Inconnu")

    @property
    def cpt(self):
        return utils.to_unicode(self.row['cpt'], 'Caisse')

    @property
    def date(self):
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except utils.FormatException:
            raise utils.FormatException("erreur de date '%s' à la ligne %s" % (self.row['date'], self.ligne))

    @property
    def ib(self):
        return utils.to_unicode(self.row['projet'], None)

    @property
    def montant(self):
        return utils.to_decimal(self.row['montant'])

    @property
    def notes(self):
        return self.row['notes']

    @property
    def num_cheque(self):
        return utils.to_unicode(self.row['numchq'], "")

    @property
    def pointe(self):
        return utils.to_bool(self.row['p'])

    @property
    def rapp(self):
        return utils.to_unicode(self.row['r'], '')

    @property
    def tiers(self):
        return utils.to_unicode(self.row['tiers'], "tiers inconnu")

    @property
    def monnaie(self):
        return "EUR"

    @property
    def jumelle(self):
        if self.tiers.count('=>') == 1:
            return True
        return False

    @property
    def moyen(self):
        return utils.to_unicode(self.row['moyen'], None)

    @property
    def ope_titre(self):
        if "@" in self.notes:
            return True
        else:
            return False

    @property
    def ligne(self):
        return self.line_num


class Import_csv_ope_sans_jumelle_et_ope_mere(import_base.Import_base):
    reader = Csv_unicode_reader_ope_sans_jumelle_et_ope_mere
    type_f = "csv_version_totale"
    creation_de_compte = True
    titre = "import csv"
    encoding = "iso-8859-1"
    complexe = False
    extensions = ('.csv', )

    def import_file(self, nomfich):
        """renvoi un tableau complet de l'import"""
        self.init_cache()
        self.erreur = list()
        # les moyens par defaut
        retour = False
        moyen_virement = self.moyens.goc('', {'nom': "Virement", 'type': 'v'})
        try:
            with open(nomfich, 'rt') as f_non_encode:
                fich = self.reader(f_non_encode, encoding=self.encoding)
                #---------------------- boucle
                retour = self.tableau(fich, moyen_virement)
                #------------------fin boucle
        except (import_base.ImportException) as e:
            messages.error(self.request, "attention traitement interrompu parce que %s" % e)
            retour = False
        # gestion des erreurs
        if len(self.erreur) or retour is False:
            for err in self.erreur:
                    messages.warning(self.request, err)
            return False
        # maintenant on sauvegarde les operations
        for ope in self.opes.create_item:
            #print "\nope # %s"%ope
            virement = ope.pop('virement', False)
            ope_titre = ope.pop('ope_titre', False)
            #gestions des cas speciaux
            if virement or ope_titre:
                if virement:
                    # on cree deux operation
                    vir = models.Virement.create(compte_origine=models.Compte.objects.get(id=ope['compte_id']),
                                            compte_dest=models.Compte.objects.get(id=ope['dest_id']),
                                            montant=ope['montant']*-1,  # -1 car la premiere ope est negative alors que le virement est positif
                                            date=ope['date'])
                    # on definit le detail des virement
                    vir.origine.pointe = ope['pointe']
                    vir.notes = ope['notes']
                    if ">P" in ope['notes']:
                        vir.dest.pointe = True
                        vir.notes = ope['notes'].split('>R')[0]
                    #les rapp des jumelle
                    if "rapp" in ope.keys():
                        vir.origine.rapp = models.Rapp.get(id=ope['rapp_id'])
                    if ">R" in ope['notes']:
                        rapp = ope['notes'].split('>R')[1]
                        vir.notes = ope['notes'].split('>R')[0]
                        vir.dest.rapp = models.Rapp.objects.get_or_create(nom=rapp, defaults={'nom': rapp})[0]
                    vir.save()
                    self.opes.nb_created += 1
                if ope_titre:
                    compte = models.Compte.objects.get(id=ope['compte_id'])
                    nombre = utils.to_decimal(ope['notes'].split('@')[0])
                    cours = utils.to_decimal(ope['notes'].split('@')[1])
                    if nombre == 0 and cours == 0:
                        messages.warning(u'attention, fausse opération sur titre ligne %s' % ope['ligne'])
                        ope.pop('ligne')
                        models.Ope.objects.create(**ope)
                        continue
                    if compte.type != 't':
                        compte.type = 't'
                        compte.save()
                    id_titre = self.titres.goc(nom=models.Tiers.objects.get(id=ope['tiers_id']).nom)
                    titre = models.Titre.objects.get(id=id_titre)

                    if nombre > 0:
                        compte.achat(titre=titre, nombre=nombre, prix=cours, date=ope['date'])
                        self.opes.nb_created += 1
                    else:
                        compte.vente(titre=titre, nombre=nombre, prix=cours, date=ope['date'])
                        self.opes.nb_created += 2
            else:
                ope.pop('ligne')
                models.Ope.objects.create(**ope)
        if self.opes.nb_created > 0:
            messages.info(self.request, u"%s opés crées" % (self.opes.nb_created))
        # on gere le nombre de truc annex crée
        for obj in(self.ibs, self.banques, self.cats, self.comptes, self.cours, self.exos, self.moyens, self.tiers, self.titres, self.rapps):
            if obj.nb_created > 0:
                messages.info(self.request, u"%s %s crées" % (obj.nb_created, obj.element._meta.object_name))
        return True

    def tableau(self, fich, moyen_virement):
        # lecture effective du fichier
        verif_format = False
        retour = False
        for row in fich:
            if row.ligne < 1:
                messages.info(self.request, u"Ligne numero %x saute" % row.ligne)
                continue
            if not verif_format:  # on verifie a la premiere ligne
                try:
                    row.id
                    row.automatique
                    row.cat
                    row.cpt
                    row.date
                    if settings.UTILISE_EXERCICES is True:
                        row.exercice
                    row.ib
                    row.ligne
                    row.monnaie        # on gere le nombre de truc annex crée
                    row.moyen
                    row.montant
                    row.notes
                    row.num_cheque
                    row.piece_comptable
                    row.rapp
                    row.tiers
                except KeyError as excp:
                    raise import_base.ImportException(u"il manque la colonne '%s'" % excp.message)
                else:
                    verif_format = True
            ope = dict()
            ope['ligne'] = row.ligne
            # verification pour les lignes
            if row.monnaie != settings.DEVISE_GENERALE:
                self.erreur.append(u"la devise du fichier n'est pas la meme que celui du fichier")
                continue
            # compte
            try:
                ope['compte_id'] = self.comptes.goc(row.cpt)
            except import_base.ImportException:
                self.erreur.append(u"cpt inconnu (%s) à la ligne %s" % (row.cpt, row.ligne))
                continue
            # virement (cat, moyen)
            try:
                ope['cat_id'] = self.cats.goc(row.cat)  # ca marche meme si virement
            except import_base.ImportException:
                self.erreur.append(u"la cat %s est inconnu à la ligne %s" % (row.cat, row.ligne))
                continue
            if row.jumelle:
                virement = True
                origine = row.tiers.split("=>")[0]
                origine = origine.strip()
                dest = row.tiers.split("=>")[1]
                dest = dest.strip()
                if origine and dest:
                    if dest == origine:
                        self.erreur.append('attention, virement impossible entre le meme compte à la ligne' % row.ligne)
                    if self.comptes.goc(dest) != ope['compte_id'] and self.comptes.goc(origine) != ope['compte_id']:
                        self.erreur.append('le compte doit dans le virement' % row.ligne)
                    if self.comptes.goc(dest) == ope['compte_id']:
                        origine, dest = dest, origine
                    ope['dest_id'] = self.comptes.goc(dest)
                    ope['compte_id'] = self.comptes.goc(origine)
                else:
                    self.erreur.append("attention il faut deux bout a un virement ligne %s" % row.ligne)
                    continue
            else:
                virement = False
            try:
                if not row.jumelle:
                    if row.moyen:
                        ope['moyen_id'] = self.moyens.goc(row.moyen, montant=row.montant)
                    else:
                        ope['moyen_id'] = self.moyen_par_defaut.goc(row.cpt, row.montant)
                else:
                    ope['moyen_id'] = moyen_virement
            except import_base.ImportException:
                self.erreur.append(u"le moyen %s est inconnu à la ligne %s" % (row.cat, row.ligne))
                continue
            ope['virement'] = virement
            # tiers
            ope['tiers_id'] = self.tiers.goc(row.tiers)
            # date
            try:
                ope['date'] = row.date
                if ope['date'] is None:
                    ope['date'] = utils.today()
            except utils.FormatException as e:
                self.erreur.append(u"date au mauvais format %s est inconnu à la ligne %s" % (e, row.ligne))
            # auto
            ope['automatique'] = row.automatique
            # date_val
            ope['date_val'] = row.date_val
            # ib
            if settings.UTILISE_IB is True:
                ope['ib_id'] = self.ibs.goc(row.ib)
            else:
                ope['ib_id'] = None
            # montant
            if virement is False:
                ope['montant'] = row.montant
            else:
                ope['montant'] = abs(row.montant) * -1  # comme c'est obligatoirement un compte de depart, c'est du negatif
            ope['notes'] = row.notes
            ope['num_cheque'] = row.num_cheque
            ope['piece_comptable'] = row.piece_comptable
            ope['pointe'] = row.pointe
            if row.rapp != '':
                ope['rapp_id'] = self.rapps.goc(row.rapp, ope['date'])
            else:
                ope['rapp_id'] = None
            if row.ope_titre:
                ope['ope_titre'] = True
            else:
                ope['ope_titre'] = False
            self.opes.create(ope)
        retour = True
        return retour


class Csv_unicode_reader_ope_avec_gestion_id(Csv_unicode_reader_ope_sans_jumelle_et_ope_mere):  # pragma: no cover
    @property
    def id(self):
        if 'id' in self.row:
            return utils.to_id(self.row['id'])

    @property
    def mere(self):
        if 'id_ope_m' in self.row:
            return utils.to_id(self.row['id_ope_m'])

    @property
    def jumelle(self):
        if self.tiers.count('=>') == 1:
            return True
        return False

    @property
    def ope_titre(self):
        if 'ope_titre' in self.row:
            return utils.to_bool(self.row['ope_titre'])

    @property
    def has_fille(self):
        if 'has_fille' in self.row:
            return utils.to_bool(self.row['has_fille'])
        else:
            return False
