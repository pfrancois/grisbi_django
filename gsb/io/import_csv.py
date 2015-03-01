# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings  # @Reimport

from django.contrib import messages

from .. import models
from . import import_base
from .. import utils
from django.db import transaction

class Csv_unicode_reader_ope_base(import_base.Property_ope_base, utils.Csv_unicode_reader):
    pass


class Csv_unicode_reader_ope_sans_jumelle_et_ope_mere(Csv_unicode_reader_ope_base):
    champs = None  # c'est a dire qu'il prend la premiere ligne
    champ_test = 'cat'

    @property
    def cat(self):
        """obligatoire, c'est le nom de la cat"""
        if self.jumelle:
            return 'Virement'
        else:
            return utils.to_unicode(self.row['cat'], "Divers:Inconnu")

    @property
    def cpt(self):
        """obligatoire, nom du compte"""
        return utils.to_unicode(self.row['cpt'], 'Caisse')

    @property
    def date(self):
        """obligatoire au format DD/MM/YYYY"""
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except utils.FormatException:
            raise utils.FormatException(u"erreur de date '%s' à la ligne %s" % (self.row['date'], self.ligne))
    @property
    def date_val(self):
        """facultatif au format DD/MM/YYYY"""
        try:
            return utils.to_date(self.row['date_val'], "%d/%m/%Y")
        except utils.FormatException:
            raise utils.FormatException(u"erreur de date '%s' à la ligne %s" % (self.row['date'], self.ligne))
        except KeyError:
            return None
    @property
    def ib(self):
        """obligatoire"""
        return utils.to_unicode(self.row['ib'], None)

    @property
    def montant(self):
        """obligatoire , marche avec point ou vrigules"""
        return utils.to_decimal(self.row['montant'])

    @property
    def notes(self):
        """obligatoires becaus virement et autres ope titres"""
        return utils.to_unicode(self.row['notes'], "")

    @property
    def num_cheque(self):
        """obligatoire"""
        return utils.to_unicode(self.row['num_cheque'], "")

    @property
    def p(self):
        """obligatoire"""
        return utils.to_bool(self.row['p'])

    @property
    def r(self):
        """oligatoire"""
        return utils.to_unicode(self.row['r'], None)

    @property
    def tiers(self):
        """obligatoire"""
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
        """obligatoire"""
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
     
    @property
    def jambe_gauche(self):
        #permet d'eliminer les jambes gauches des virements
        if self.jumelle and self.montant > 0:
            return True
        return False


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
        with transaction.atomic():
            self.erreur = list()
            cache_titre = dict()
            # les moyens par defaut
            moyen_virement = self.moyens.goc(nom=None, obj={'nom': "Virement", 'type': 'v'})
            with open(nomfich, 'r') as f_non_encode:
                fich = self.reader(f_non_encode, encoding=self.encoding)
                #---------------------- boucle
                retour = self.tableau(fich, moyen_virement)
                #------------------fin boucle
            # gestion des erreurs
            if retour is False:
                for err in self.erreur:
                    messages.warning(self.request, err)
                return False
                # maintenant on sauvegarde les operations
            for ope in self.opes.created_items:
                virement = ope.pop('virement', False)
                ope_titre = ope.pop('ope_titre', False)
                ligne = ope.pop('ligne')
                # gestions des cas speciaux
                if virement or ope_titre:
                    if virement:
                        vir = models.Virement.create(compte_origine=models.Compte.objects.get(id=ope['compte_id']),
                                                     compte_dest=models.Compte.objects.get(id=ope['dest_id']),
                                                     montant=ope['montant'] * -1,
                                                     # -1 car la premiere ope est negative alors que le virement est positif
                                                     date=ope['date'])
                        vir.notes = ope['notes']
                        # on definit le detail des virement
                        vir.origine.pointe = ope['pointe']
                        if ">P" in ope['notes']:#rapp cote dest
                            vir.notes = ope['notes'].split('>P')[0]
                            vir.dest.pointe = True
                        # les rapp des jumelles
                        if "rapp_id" in ope.keys() and ope['rapp_id'] is not None:#rapp cote origine
                            vir.origine.rapp = models.Rapp.objects.get(id=ope['rapp_id'])
                        if ">R" in ope['notes']:#rapp cote dest
                            rapp = ope['notes'].split('>R')[1]
                            vir.notes = ope['notes'].split('>R')[0]
                            vir.dest.rapp = models.Rapp.objects.get_or_create(nom=rapp, defaults={'nom': rapp})[0]
                        vir.date_val=ope['date_val']
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
                        if ope['titre_id'] not in cache_titre.keys():
                            cache_titre[ope['titre_id']] = models.Titre.objects.get(id=ope['titre_id'])
                        titre = cache_titre[ope['titre_id']]
                        if nombre > 0:
                            ope_gsb = compte.achat(titre=titre, nombre=nombre, prix=cours, date=ope['date'])
                            messages.success(self.request, u"ope_titre: %s ligne %s" % (ope_gsb.ope_ost, ligne))
                        else:
                            try:
                                ope_gsb = compte.vente(titre=titre, nombre=nombre, prix=cours, date=ope['date'])
                                messages.success(self.request, u"ope_titre: %s ligne %s" % (ope_gsb.ope_ost, ligne))
                                messages.success(self.request, u"ope_titre(pmv): %s ligne %s" % (ope_gsb.ope_pmv, ligne))
                            except models.Titre.DoesNotExist:
                                messages.error(self.request, "impossible de vendre car pas de titre en portefeuille ligne %s" % ligne)
                else:
                    ope_gsb = models.Ope.objects.create(**ope)
                    messages.success(self.request, u"opé créee: %s ligne %s" % (ope_gsb, ligne))
                # on gere le nombre de truc annex crée
            for obj in (self.ibs, self.banques, self.cats, self.comptes, self.cours, self.exos, self.moyens, self.tiers, self.titres, self.rapps):
                if obj.nb_created > 0:
                    # noinspection PyProtectedMember
                    messages.info(self.request, u"%s %s crées" % (obj.nb_created, obj.element._meta.object_name))
        return True

    def tableau(self, fich, moyen_virement):
        # lecture effective du fichier
        verif_format = False
        for row in fich:
            if not verif_format:  # on verifie a la premiere ligne
                liste_colonnes = ['id', 'cpt', 'date', "montant", 'r', 'p', "moyen", 'cat', "tiers", "notes", "ib", "num_cheque"]
                if settings.UTILISE_EXERCICES is True:
                    liste_colonnes.append('exercice')
                colonnes_oublies = []
                for attr in liste_colonnes:
                    try:
                        if getattr(row, attr, "colonne inexistante") == "colonne inexistante":
                            colonnes_oublies.append(attr)
                    except (import_base.ImportException, utils.FormatException):
                        pass
                    except KeyError:
                        colonnes_oublies.append(attr)
                if len(colonnes_oublies) > 0:
                    self.erreur.append(u"il manque la/les colonne(s) '%s'" % u"','".join(colonnes_oublies))
                    return False
                else:
                    verif_format = True
            if row.jambe_gauche:
                continue
            ope = dict()
            ope['ligne'] = row.ligne
            # verification pour les lignes
            if row.monnaie != settings.DEVISE_GENERALE: # pragma: no cover
                self.erreur.append(u"la devise du fichier n'est pas la même que celui de la base")
                continue
            # compte
            nb_created_avant = self.comptes.nb_created
            ope['compte_id'] = self.comptes.goc(row.cpt)
            if self.comptes.nb_created != nb_created_avant:  # il y a eu une creation
                if row.ope_titre:
                    cpt = models.Compte.objects.get(id=ope['compte_id'])
                    if cpt.type != 't':
                        cpt.type = 't'
                        cpt.save()
            #cat
            ope['cat_id'] = self.cats.goc(row.cat)  # ca marche meme si virement
            # date
            try:
                ope['date'] = row.date
            except utils.FormatException as e:
                self.erreur.append(u"%s" % e)
                continue
            try:
                ope['date_val'] = row.date_val
            except utils.FormatException as e:
                self.erreur.append(u"%s" % e)
                continue
            # virement
            if row.jumelle:
                ope['virement'] = True
                origine = row.tiers.split("=>")[0]
                origine = origine.strip()
                dest = row.tiers.split("=>")[1]
                dest = dest.strip()
                if origine and dest:
                    if dest == origine:
                        self.erreur.append(u'attention, virement impossible entre le même compte à la ligne %s' % row.ligne)
                        continue
                    if self.comptes.goc(dest) != ope['compte_id'] and self.comptes.goc(origine) != ope['compte_id']:
                        self.erreur.append(u"le compte designé doit être un des deux comptes 'tiers' ligne %s"  % row.ligne)
                        continue
                    ope['dest_id'] = self.comptes.goc(dest)
                    ope['compte_id'] = self.comptes.goc(origine)
                else:
                    self.erreur.append(u"attention il faut deux bouts à un virement ligne %s" % row.ligne)
                    continue
            else:
                ope['virement'] = False
            if not row.jumelle:
                if row.moyen:
                    ope['moyen_id'] = self.moyens.goc(row.moyen, montant=row.montant)
                else:
                    ope['moyen_id'] = self.moyen_par_defaut.goc(row.cpt, montant=row.montant)
            else:
                ope['moyen_id'] = moyen_virement
            # tiers
            ope['tiers_id'] = self.tiers.goc(row.tiers)
            # auto
            ope['automatique'] = row.automatique
            # ib
            if settings.UTILISE_IB is True:
                ope['ib_id'] = self.ibs.goc(row.ib)
            else:
                ope['ib_id'] = None
            # montant
            if ope['virement'] is False:
                ope['montant'] = row.montant
            else:
                ope['montant'] = abs(row.montant) * -1  # comme c'est obligatoirement un compte de depart, c'est du negatif
            ope['notes'] = row.notes
            ope['num_cheque'] = row.num_cheque
            ope['pointe'] = row.p
            ope['rapp_id'] = self.rapps.goc(row.r, ope['date'])
            if row.ope_titre:
                ope['ope_titre'] = True
                if 'titre_ ' in row.tiers:
                    ope['titre_id'] = self.titres.goc(nom=row.tiers.replace('titre_ ', '').strip())
                else:
                    self.erreur.append(u"Ce tiers '%s' ne peut être un titre à la ligne %s" % (row.tiers, row.line_num))
                    continue
            else:
                ope['ope_titre'] = False
            self.opes.created_items.append(ope)
        if len(self.erreur) == 0:
            return True
        else:
            return False
