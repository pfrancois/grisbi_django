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
    """seuls cat cpt date montant obligatoire, mais moyen et tiers sont fortement recommande"""
    champs = None #c'est a dire qu'il prend la premiere ligne
    champ_test = 'cat'

    @property
    def cat(self):
        """obligatoire"""
        if self.jumelle:
            return 'Virement'
        else:
            return utils.to_unicode(self.row['cat'], "Divers:Inconnu")

    @property
    def cpt(self):
        """obligatoire"""
        return utils.to_unicode(self.row['cpt'], 'Caisse')

    @property
    def date(self):
        """obligatoire au format DD/MM/YYYY"""
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except utils.FormatException:
            raise utils.FormatException("erreur de date '%s' à la ligne %s" % (self.row['date'], self.ligne))

    @property
    def ib(self):
        """facultatif"""
        if 'projet' in self.row:
            return utils.to_unicode(self.row['projet'], None)
        else:
            return None

    @property
    def montant(self):
        """obligatoire format anglais"""
        return utils.to_decimal(self.row['montant'])

    @property
    def notes(self):
        """facultatif"""
        if 'notes' in self.row:
            return utils.to_unicode(self.row['notes'], "")
        else:
            return ''

    @property
    def num_cheque(self):
        """facultatif"""
        if 'numchq' in self.row:
            return utils.to_unicode(self.row['numchq'], "")
        else:
            return ""

    @property
    def pointe(self):
        """facultatif"""
        if 'p' in self.row:
            return utils.to_bool(self.row['p'])
        else:
            return False

    @property
    def rapp(self):
        """facultatif"""
        if 'r' in self.row:
            return utils.to_unicode(self.row['r'], None)
        else:
            return ""

    @property
    def tiers(self):
        """facultatif"""
        if 'tiers' in self.row:
            return utils.to_unicode(self.row['tiers'], "tiers inconnu")
        else:
            return "tiers inconnu"

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
        """facultatif"""
        if 'moyen' in self.row:
            return utils.to_unicode(self.row['moyen'], None)
        else:
            return None

    @property
    def ope_titre(self):
        if "@" in self.notes:
            return True
        else:
            return False

    @property
    def ligne(self):
        #on fait -1 pour sauter la premiere ligne
        return self.line_num


class Import_csv_ope_sans_jumelle_et_ope_mere(import_base.Import_base):
    reader = Csv_unicode_reader_ope_sans_jumelle_et_ope_mere
    type_f = "csv_version_totale"
    creation_de_compte = True
    titre = "import csv"
    encoding = "iso-8859-1"
    extensions = ('.csv', )

    def import_file(self, nomfich):
        """renvoi un tableau complet de l'import"""
        self.init_cache()
        self.erreur = list()
        cache_titre = dict()
        # les moyens par defaut
        retour = False
        moyen_virement = self.moyens.goc('', {'nom': "Virement", 'type': 'v'})
        try:
            with open(nomfich, 'r') as f_non_encode:
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
            virement = ope.pop('virement', False)
            ope_titre = ope.pop('ope_titre', False)
            ligne = ope.pop('ligne')
            #gestions des cas speciaux
            if virement or ope_titre:
                if virement:
                    vir = models.Virement.create(compte_origine=models.Compte.objects.get(id=ope['compte_id']),
                        compte_dest=models.Compte.objects.get(id=ope['dest_id']),
                        montant=ope['montant'] * -1,  # -1 car la premiere ope est negative alors que le virement est positif
                        date=ope['date'])
                    # on definit le detail des virement
                    vir.origine.pointe = ope['pointe']
                    vir.notes = ope['notes']
                    #les rapp des jumelle
                    if "rapp" in ope.keys():
                        vir.origine.rapp = models.Rapp.objects.get(id=ope['rapp_id'])
                    if ">R" in ope['notes']:
                        rapp = ope['notes'].split('>R')[1]
                        vir.notes = ope['notes'].split('>R')[0]
                        vir.dest.rapp = models.Rapp.objects.get_or_create(nom=rapp, defaults={'nom': rapp})[0]
                    vir.save()
                    self.opes.nb_created += 1
                    messages.success(self.request, u"virement ope: %s ligne %s" % (vir.origine, ligne))
                    messages.success(self.request, u"virement ope: %s ligne %s" % (vir.dest, ligne))
                if ope_titre:
                    compte = models.Compte.objects.get(id=ope['compte_id'])
                    nombre = utils.to_decimal(ope['notes'].split('@')[0])
                    cours = utils.to_decimal(ope['notes'].split('@')[1])
                    if nombre == 0 and cours == 0:
                        messages.warning(self.request, u'attention, fausse opération sur titre ligne %s' % ligne)
                        continue
                    if compte.type != 't':
                        messages.warning(self.request, u"le compte '%s' n'est pas un compte titre" % compte)
                        continue
                    if ope['titre_id'] not in cache_titre.keys():
                        cache_titre[ope['titre_id']] = models.Titre.objects.get(id=ope['titre_id'])
                    titre = cache_titre[ope['titre_id']]
                    if nombre > 0:
                        ope_gsb = compte.achat(titre=titre, nombre=nombre, prix=cours, date=ope['date'])
                        messages.success(self.request, u"ope_titre: %s ligne %s" % (ope_gsb.ope_ost, ligne))
                    else:
                        ope_gsb = compte.vente(titre=titre, nombre=nombre, prix=cours, date=ope['date'])
                        messages.success(self.request, u"ope_titre: %s ligne %s" % (ope_gsb.ope_ost, ligne))
                        messages.success(self.request, u"ope_titre(pmv): %s ligne %s" % (ope_gsb.ope_pmv, ligne))
            else:
                ope_gsb = models.Ope.objects.create(**ope)
                messages.success(self.request, u"opé créee: %s ligne %s" % (ope_gsb, ligne))
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
            if not row.champ_test in row.row:
                messages.info(self.request, u'ligne %s %s sauté car pas de champ %s' % (row.row, row.line_num, row.champ_test))
                continue
            if not verif_format:  # on verifie a la premiere ligne
                liste_colonnes = ['id', 'automatique', 'cat', 'cpt', 'date', "ib", "ligne", "moyen", "montant", "notes", "num_cheque", "piece_comptable", "rapp", "tiers"]
                if settings.UTILISE_EXERCICES is True:
                    liste_colonnes.append('exercice')
                colonnes_oublies = []
                for attr in liste_colonnes:
                    if not hasattr(row, attr):
                        colonnes_oublies.append(attr)
                print colonnes_oublies, len(colonnes_oublies)
                if len(colonnes_oublies) > 0:
                    raise import_base.ImportException(u"il manque la/les colonne(s) '%s'" % u"','".join(colonnes_oublies))
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
            try:
                ope['cat_id'] = self.cats.goc(row.cat)  # ca marche meme si virement
            except import_base.ImportException:
                self.erreur.append(u"la cat %s est inconnu à la ligne %s" % (row.cat, row.ligne))
                continue
            # date
            try:
                ope['date'] = row.date
                if ope['date'] is None:
                    self.erreur.append(u"date non remplie ligne %s" % row.ligne)
                    raise utils.FormatException
            except utils.FormatException as e:
                self.erreur.append(u"date au mauvais format %s est inconnu à la ligne %s" % (e, row.ligne))
                raise e
            #virement
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
                    # si on est du cote de l'operation receptrice, verification que l'on ne s'est pas trompe dans le tiers
                    if self.comptes.goc(dest) == ope['compte_id'] and row.montant < 0:
                        origine, dest = dest, origine
                        messages.info(self.request, "swap %s=%s" % origine, dest)
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
                        ope['moyen_id'] = self.moyen_par_defaut.goc(row.cpt, montant=row.montant)
                else:
                    ope['moyen_id'] = moyen_virement
            except import_base.ImportException:
                self.erreur.append(u"le moyen %s est inconnu (ou est mal utilisé) à la ligne %s" % (row.cat, row.ligne))
                continue
            ope['virement'] = virement
            # tiers
            ope['tiers_id'] = self.tiers.goc(row.tiers)
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
                if 'titre_ ' in row.tiers:
                    ope['titre_id'] = self.titres.goc(nom=row.tiers.replace('titre_ ', '').strip())
                else:
                    raise import_base.ImportException(u"ce tiers '%s' ne peut etre un titre" % row.tiers)
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
