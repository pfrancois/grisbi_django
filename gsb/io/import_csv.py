# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings  # @Reimport

from django.contrib import messages

from .. import models
from . import import_base
from .. import utils
from django.db.models import Max
from django.db import IntegrityError 

class Csv_unicode_reader_ope_base(import_base.property_ope_base, utils.Csv_unicode_reader):
    pass

class Csv_unicode_reader_ope(Csv_unicode_reader_ope_base):
    @property
    def id(self):
        return utils.to_id(self.row['id'])

    @property
    def cat(self):
        if self.jumelle:
            return 'Virement'
        else:
            return utils.to_unicode(self.row['cat'], "Divers:Inconnu")

    @property
    def cpt(self):
        cpt = utils.to_unicode(self.row['cpt'])
        if cpt is None:
            return "Caisse"
        else:
            return cpt

    @property
    def date(self):
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except utils.FormatException:
            raise utils.FormatException ("%s" % self.row['date'])

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
        return utils.to_bool(self.row['r'])

    @property
    def tiers(self):
        return utils.to_unicode(self.row['tiers'], "tiers inconnu")

    @property
    def monnaie(self):
        return "EUR"

    @property
    def mere(self):
        return utils.to_id(self.row['id_ope_m'])

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
        return utils.to_bool(self.row['ope_titre'])

    @property
    def ope_pmv(self):
        return utils.to_bool(self.row['ope_pmv'])

    @property
    def has_fille(self):
        return utils.to_bool(self.row['has_fille'])

    @property
    def ligne(self):
        return self.line_num


class Import_csv_ope(import_base.Import_base):
    reader = Csv_unicode_reader_ope
    extension = ("csv",)
    type_f = "csv_version_totale"
    creation_de_compte = True
    titre = "import csv"

    def init_cache(self):
        self.moyens = Moyen_cache(self.request)
        self.cats = Cat_cache(self.request)
        self.ibs = IB_cache(self.request)
        self.comptes = Compte_cache(self.request)
        self.banques = Banque_cache(self.request)
        self.cours = Cours_cache(self.request)
        self.exos = Exercice_cache(self.request)
        self.tiers = Tiers_cache(self.request)
        self.opes = Ope_cache(self.request)
        self.titres = Titre_cache(self.request)

    def import_file(self, nomfich):
        """renvoi un tableau complet de l'import"""
        self.init_cache()
        self.erreur = list()

        # les moyens par defaut
        created = models.Moyen.objects.get_or_create(id=settings.MD_DEBIT, defaults={"id": settings.MD_DEBIT, "nom": 'DEBIT', "type": "d"})[1]
        if created:  messages.info(self.request, "ajout moyen debit par defaut")
        created = models.Moyen.objects.get_or_create(id=settings.MD_CREDIT, defaults={"id": settings.MD_CREDIT, "nom": 'CREDIT', "type": "r"})[1]
        if created: messages.info(self.request, "ajout moyen credit par defaut")
        moyen_virement, created = models.Moyen.objects.get_or_create(nom='Virement', type="v", defaults={"nom":'Virement', "type":"v"})
        if created: messages.info(self.request, "ajout moyen virement par defaut")
        # les cat
        created = models.Moyen.objects.get_or_create(id=settings.ID_CAT_OST, defaults={"id": settings.ID_CAT_OST, "nom": 'Operation sur titre', "type": "d"})[1]
        if created: messages.info(self.request, "ajout cat OST")
        created = models.Moyen.objects.get_or_create(id=settings.ID_CAT_PMV, defaults={"id": settings.ID_CAT_PMV, "nom": 'Revenus de placement:Plus-values', "type": "r"})[1]
        if created: messages.info(self.request, "ajout cat PMV")
        retour=False
        try:
            with open(nomfich, 'rt') as f_non_encode:
                fich = self.reader(f_non_encode, encoding="iso-8859-1")
                retour=self.tableau(fich,moyen_virement)
        except (utils.FormatException, import_base.ImportException) as e:
            messages.error(self.request, "attention traitement interrompu parce que %s" % e)
            retour = False
        # gestion des erreurs
        if len(self.erreur) or retour == False:
            for err in self.erreur:
                    messages.warning(self.request, err)
            return False
        # on gere le nombre de truc annex crée
        for obj in(self.ibs, self.banques, self.cats, self.comptes, self.cours, self.exos, self.moyens, self.tiers, self.titres):
            if obj.nb_created > 0:
                messages.info(self.request, u"%s %s crées" % (obj.nb_created, obj.element._meta.object_name))
        # maintenant on sauvegarde les operations
        for ope in self.opes.create_item:
            ligne = ope.pop('ligne')
            ope.pop('mere_id')  # on efface ca comme pour l'instant je gere pas
            if ope.get('has_fille', True):
                messages.warning(self.request, u"opé ligne %s efface car ope mere " % ligne)
                continue
            ope.pop('has_fille', False)
            virement = ope.pop('virement', False)
            if virement:
                # on cree deux operation
                ope_origine = models.Ope.objects.create(**ope)
                dest = ope.pop('dest_id')
                ope['compte'] = dest
                ope['montant'] = ope['montant'] * -1
                ope.pop('ib_id', None)
                ope_dest = models.Ope.objects.create(**ope)
                ope_origine.jumelle = ope_dest
                ope_origine.save()
                ope_dest.jumelle = ope_origine
                ope_dest.save()
            else:
                models.Ope.objects.create(**ope)
        if self.opes.nb_created > 0:
            messages.info(self.request, u"%s opés crées" % (self.opes.nb_created))

        return True 
    
    def tableau(self,fich,moyen_virement):
        # lecture effective du fichier
        verif_format = False
        for row in fich:
            try:
                if row.date:
                    pass
            except utils.FormatException:
                self.erreur.append(u"Ligne numero %x saute" % row.ligne)
                continue
            if not verif_format:  # on verifie a la premiere ligne
                try:
                    row.id
                    row.automatique
                    row.cat
                    row.cpt
                    row.date
                    if settings.UTILISE_EXERCICES == True:
                        row.exercice
                    row.has_fille
                    row.ib
                    row.ligne
                    row.mere
                    row.monnaie
                    row.moyen
                    row.montant
                    row.notes
                    row.num_cheque
                    row.ope_pmv
                    # row.ope_titre
                    # row.piece_comptable
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
            if "=>" in row.tiers:
                virement = True
                ope['cat_id'] = self.cats.goc('Virement')
                ope['moyen_id'] = moyen_virement
                origine = row.tiers.split("=>")[0]
                origine = origine.strip()
                dest = row.tiers.split("=>")[2]
                dest = dest.strip()
                ope['dest_id'] = self.comptes.goc(dest)
                if origine  and dest:
                    if self.comptes.goc(origine) != ope['compte']:
                        if self.comptes.goc(dest) != ope['compte']:
                            self.erreur.append(u"attention cette operation n'a pas la bonne origine, elle dit partir de %s alors qu'elle part de %s" % (origine, row.compte))
                        else:
                            self.erreur.append(u"attention cette operation n'a pas orientée corectement, il faut remplir le compte de depart et non le compte d'arrivee" % (dest, row.compte))
                        continue
                else:
                    self.erreur.append("attention il faut deux bout a un virement ligne %s" % row.ligne)
                    continue
            else:
                virement = False
                try:
                    ope['cat_id'] = self.cats.goc(row.cat)
                except import_base.ImportException:
                    self.erreur.append(u"la cat %s est inconnu à la ligne %s" % (row.cat, row.ligne))
                    continue
                try:
                    if row.moyen:
                        ope['moyen_id'] = self.moyens.goc(row.moyen)
                    else:
                        if row.montant > 0:
                            ope['moyen_id'] = settings.MD_CREDIT
                        else:
                            ope['moyen_id'] = settings.MD_DEBIT
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
            if settings.UTILISE_IB == True:
                ope['ib_id'] = self.ibs.goc(row.ib)
            else:
                ope['ib_id'] = None
            # jumelle et mere
            ope['mere_id'] = row.mere
            ope['has_fille'] = row.has_fille
            # montant
            ope['montant'] = row.montant
            ope['notes'] = row.notes
            ope['num_cheque'] = row.num_cheque
            ope['piece_comptable'] = row.piece_comptable
            ope['pointe'] = row.pointe
            self.opes.create(ope)
        retour=True
        return retour


class Table(object):
    """Moyen avec cache"""
    element = None
    readonly = False
    def __init__(self, request):
        self.id = dict()
        self.create_item = list()
        self.request = request
        if self.element is None:
            raise NotImplementedError("table de l'element non choisi")
        else:
            self.last_id_db = self.element.objects.aggregate(id_max=Max('id'))['id_max']
        self.nb_created=0

    def goc(self, nom, obj=None):
        if nom == "" or nom is None:
            return None
        try:
            pk = self.id[nom]
        except KeyError:
            try:
                if obj is None:
                    arguments = {"nom": nom}
                else:
                    arguments = obj
                pk = self.element.objects.get(**arguments).id
                self.id[nom] = pk
            except self.element.DoesNotExist:
                if not self.readonly:  # on cree donc l'operation
                    argument_def = self.arg_def(nom, obj)
                    try:
                        created = self.element.objects.create(**argument_def)
                        self.nb_created += 1
                    except IntegrityError as e:
                        raise import_base.ImportException("%s" % e)
                    pk = created.pk
                    self.id[nom] = pk 
                    self.create_item.append(created)
                    messages.info(self.request, u'création du %s "%s"' % (self.element._meta.object_name, created))
                else:
                    raise import_base.ImportException("%s non defini alors que c'est read only" % self.element.__class__.__name__)
        return pk
    
    def arg_def(self, nom, obj):
        raise NotImplementedError("methode arg_def non defini")

    

class Cat_cache(Table):
    element = models.Cat
    readonly = True


class Moyen_cache(Table):
    element = models.Moyen
    readonly = True

class IB_cache(Table):
    element = models.Ib
    def arg_def(self, nom, obj):
        if obj is None:
            return {"nom":nom, "type":'d'}

class Compte_cache(Table):
    element = models.Compte
    readonly = True

class Banque_cache(Table):
    element = models.Banque
    readonly = True

class Cours_cache(Table):
    element = models.Cours
    def goc(self, date, titre, montant):
        try:
            titre_id = self.id[titre]
            pk = titre_id[date]
        except KeyError:
            try:
                el = self.element.objects.get(date=date, titre_id=titre)
                pk = el.id
                if el.montant != montant:
                    raise import_base.ImportException(u'difference de montant %s et %s pour le titre %s à la date %s' % (el.montant, montant, el.titre.nom, date))
            except self.element.DoesNotExist:
                self.create_item.append({'titre': titre, 'date': date, "montant": montant})
                pk = self.create_item.index({'titre': titre, 'date': date, "montant": montant}) + self.last_id
            finally:
                if self.id.get(titre) is not None:
                    self.id[titre][date] = pk
                else:
                    self.id[titre] = titre
                    self.id[titre][date] = pk
                pk = self.id[titre][date]
        finally:
            return pk

class Exercice_cache(Table):
    element = models.Exercice
    readonly = True  # a finir

class Tiers_cache(Table):
    element = models.Tiers
    def arg_def(self, nom, obj):
        if obj is None:
            return {"nom":nom}

class Titre_cache(Table):
    element = models.Titre
    def goc(self, pk, obj):
        self.element.objects.create(id=pk, isin="XX00000%s" % pk, type="XXX")
        messages.info(self.request, 'creation du titre "%s"' % obj)

class Ope_cache(Table):
    element = models.Ope
    def goc(self, nom):
        raise NotImplementedError("methode goc non defini")
    def create(self, ope):
        self.create_item.append(ope)
        self.nb_created += 1
