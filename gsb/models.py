# -*- coding: utf-8 -*-

import datetime
import decimal

from django.db import models
from django.db import transaction, IntegrityError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import signals
from django.dispatch import receiver
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.utils.encoding import smart_text, force_text
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q
import django.utils.timezone as tz

import gsb.model_field as models_gsb
from gsb import utils
from colorful.fields import RGBColorField


class Gsb_exc(utils.utils_Exception):
    pass


class Ex_jumelle_neant(utils.utils_Exception):
    pass


def has_changed(instance, fields):
    if not getattr(instance, "pk", False):
        return False
    if isinstance(fields, str):  # si c'est une chaine de caracteres on le transforme en tupple
        fields = (fields,)
    changed = False
    # noinspection PyProtectedMember
    obj = instance.__class__._default_manager.get(pk=instance.pk)
    for field in fields:
        old_value = getattr(obj, field)
        new_value = getattr(instance, field)
        if hasattr(new_value, "file"):  # pragma: no cover
            # Handle FileFields as special cases, because the uploaded filename could be
            # the same as the filename that's already there even though there may
            # be different file contents.
            from django.core.files.uploadedfile import UploadedFile

            if isinstance(new_value.file, UploadedFile):
                changed = isinstance(new_value.file, UploadedFile)
        if not getattr(instance, field) == old_value:
            changed = not getattr(instance, field) == old_value
    return changed


class Config(models.Model):

    """model generique pour tout ce qui est modifiable"""
    derniere_import_money_journal = models.DateTimeField(default=datetime.datetime(1970, 1, 1, tzinfo=tz.utc))

    class Meta(object):
        db_table = 'gsb_config'

    def __str__(self):
        return "%s" % self.id


class Tiers(models.Model):

    """
    un tiers, c'est a dire une personne ou un titre
    pour les titres, c'est remplis dans le champ note avec TYPE@ISIN
    """

    nom = models.CharField(max_length=40, unique=True, db_index=True)
    notes = models.TextField(blank=True, default='')
    is_titre = models.BooleanField(default=False)
    titre = models.OneToOneField("Titre", null=True, blank=True, editable=False, on_delete=models.CASCADE)
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)
    sort_nom = models.CharField(max_length=40, db_index=True)

    class Meta(object):
        db_table = 'gsb_tiers'
        verbose_name_plural = 'tiers'
        ordering = ['nom']

    def __str__(self):
        return "%s" % self.nom

    @transaction.atomic
    def fusionne(self, new, ok_titre=False):
        """fusionnne tiers vers new tiers
        @param new: tiers
        """
        if new == self:
            raise ValueError("un tiers ne peut être fusionné avec lui même")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        if (self.is_titre or new.is_titre) and not ok_titre:
            raise ValueError(
                "un tiers suppport de titre ne peut etre fusionnné directement. vous devez fusionner les titres")
        nb_tiers_change = Echeance.objects.filter(tiers=self).update(tiers=new)
        nb_tiers_change += Ope.objects.filter(tiers=self).update(tiers=new)
        self.delete()
        return nb_tiers_change

    def save(self, *args, **kwargs):
        self.nom = self.nom.strip()
        self.sort_nom = self.nom.lower()
        super(Tiers, self).save(*args, **kwargs)


class Titre(models.Model):

    """²
    les titres englobe les actifs financiers
    afin de pouvoir faire le lien dans les operations, il y a un ligne vers les tiers
    :model:`gsb.tiers`
    le set_null est mis afin de pouvoir faire du menage dans les titres plus utilise
    sans que cela ne pose trop de problème dans les opérations.
    """
    typestitres = (
        ('ACT', 'action'), ('OPC', 'opcvm'), ('CSL', 'compte sur livret'), ('OBL', 'obligation'), ('ZZZ', 'autre'))
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    isin = models.CharField(max_length=12, unique=True, db_index=True)
    type = models.CharField(max_length=3, choices=typestitres, default='ZZZ')
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_titre'
        ordering = ['nom']

    def __str__(self):
        return "%s (%s)" % (self.nom, self.isin)

    def last_cours(self, datel=None):
        """renvoie le dernier cours
        @param datel: la date max du cours ou l'on veut
        @return : decimal"""
        if datel is None:
            datel = utils.today()
        reponse = self.cours_set.filter(date__lte=datel)
        try:
            return reponse.latest('date').valeur
        except (AttributeError, Cours.DoesNotExist):
            return 0

    def last_cours_date(self, rapp=False):
        """renvoie la date du dernier cours
        @return : datetime ou None
        """
        if not rapp:
            return self.cours_set.latest('date').date
        else:
            opes = Ope.objects.filter(tiers=self.tiers).filter(rapp__isnull=False).exclude(filles_set__isnull=False)
            if opes.exists():
                date_rapp = opes.latest('date').rapp.date
                liste = Cours.objects.filter(titre=self).filter(date__lte=date_rapp)
                if liste.exists():
                    return liste.latest('date').date
            else:
                return None

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne ce titre avec le titre new
        @param new: Titre
        """
        if new == self:
            raise ValueError("un titre ne peut être fusionné avec lui même")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le même type de titre")
        for cours in self.cours_set.all():
            try:
                if new.cours_set.get(date=cours.date).valeur != cours.valeur:
                    raise Gsb_exc(
                        "attention les titre %s et %s ne peuvent etre fusionné à cause histo de cours" % (self, new))
            except Cours.DoesNotExist:
                new.cours_set.create(date=cours.date, valeur=cours.valeur)
        nb_change = 0
        nb_change += Ope_titre.objects.filter(titre=self).update(titre=new)
        # on doit aussi reaffecter le tiers associe
        self.tiers.fusionne(new.tiers, ok_titre=True)
        self.delete()
        return nb_change

    @transaction.atomic
    def save(self, *args, **kwargs):
        tiers_save = False
        self.alters_data = True
        if not utils.is_onexist(self, "tiers"):
            super(Titre, self).save(*args, **kwargs)
            self.tiers = Tiers.objects.get_or_create(nom='titre_ %s' % self.nom,
                                                     defaults={"nom": 'titre_ %s' % self.nom, "is_titre": True,
                                                               "notes": "%s@%s" % (self.isin, self.type)})[0]
            self.tiers.nom = 'titre_ %s' % self.nom
            self.tiers.notes = "%s@%s" % (self.isin, self.type)
            self.tiers.is_titre = True
            tiers_save = True
        else:
            if has_changed(self, 'nom'):
                if self.tiers.nom != 'titre_ %s' % self.nom:
                    self.tiers.nom = 'titre_ %s' % self.nom
                    tiers_save = True
            if has_changed(self, ('isin', 'type')):
                if self.tiers.notes != "%s@%s" % (self.isin, self.type):
                    self.tiers.notes = "%s@%s" % (self.isin, self.type)
                    tiers_save = True
                    # comme ca a ete obligatoirement cree au dessus
        if 'force_insert' in list(kwargs.keys()):
            del kwargs['force_insert']
            kwargs['force_update'] = True
        super(Titre, self).save(*args, **kwargs)
        if tiers_save:
            self.tiers.is_titre = True
            self.tiers.save()

    def investi(self, compte=None, datel=None, rapp=None, exclude=None):
        """renvoie le montant investi
        @param compte: Compte , si None, renvoie sur  l'ensemble des comptes titres
        @param datel: date, renvoie sur avant la date ou tout si none
        @param rapp: Bool, si true, renvoie uniquement les opération rapprochées
        @param exclude: Ope_titre ope titre a exclure.attention c'est bien ope et non ope_titre
        """
        query = Ope.non_meres().filter(tiers__nom="titre_ %s" % self.nom).exclude(cat_id=settings.ID_CAT_PMV)
        if compte:
            query = query.filter(compte=compte)
        if datel:
            query = query.filter(date__lte=datel)
        if rapp:
            query = query.filter(rapp__isnull=False)
        if exclude and utils.is_onexist(exclude, "ope_ost"):
            query = query.exclude(pk=exclude.ope_ost.id)
        valeur = query.aggregate(investi=models.Sum('montant'))['investi']
        if not valeur:
            return decimal.Decimal(0)
        else:
            return valeur * -1

    def nb(self, compte=None, datel=None, rapp=False, exclude_id=None):
        """renvoie le nombre de titre detenus dans un compte C ou dans tous les comptes si pas de compte donnee
                @param datel:date, renvoie sur avant la date ou tout si none
                @param rapp: boolean, renvoie uniquement les op rapp
                @param compte: compte, renvoie uniquement le nombre de titre si dans le compte
                """
        query = Ope_titre.objects.filter(titre=self)
        if compte:
            query = query.filter(compte=compte)
        if rapp:
            query = query.filter(ope_ost__rapp__isnull=False)
        if datel:
            query = query.filter(date__lte=datel)
        if exclude_id:
            query = query.exclude(pk=exclude_id)
        nombre = query.aggregate(nombre=models.Sum('nombre'))['nombre']
        if not nombre:
            return 0
        else:
            return decimal.Decimal(smart_text(nombre))

    def encours(self, compte=None, datel=None, rapp=False):
        """
        renvoie l'encours detenu dans ce titre dans un compte ou dans tous les comptes si pas de compte donné
        @rtype : Decimal
        @param compte: objet compte
        @param datel: chaine au format "aaaa-mm-dd" ou date
        @param rapp: boolean, renvoie les operation rapproches, attention, si rempli, cela renvoie l'encours avec le cours rapproche
        """
        # si pas d'operation existante
        if datel is None:
            datel = utils.today()
            # definition de la population des ope
        nb = self.nb(compte=compte, rapp=rapp, datel=datel)
        if nb > 0:
            if rapp:
                opes = Ope.objects.filter(tiers=self.tiers, date__lte=datel, rapp__isnull=False).exclude(
                    filles_set__isnull=False)
                if compte:
                    opes = opes.filter(compte=compte)
                date_cours = opes.latest('date').date
            else:
                date_cours = datel
                # recupere le dernier cours
            cours = self.last_cours(datel=date_cours)
            return nb * cours
        else:
            return 0  # comme pas d'ope, pas d'encours


class Cours(models.Model):

    """cours des titres"""
    date = models.DateField(default=utils.today, db_index=True)
    valeur = models_gsb.CurField(default=1.000, decimal_places=3)
    titre = models.ForeignKey(Titre, on_delete=models.CASCADE)
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_cours'
        verbose_name_plural = 'cours'
        unique_together = ("titre", "date")
        ordering = ['-date']
        get_latest_by = 'date'

    def __str__(self):
        return "le %(date)s, 1 %(titre)s : %(valeur)s %(monnaie)s" % {'titre': self.titre.nom,
                                                                       'date': self.date.strftime('%d/%m/%Y'),
                                                                       'valeur': self.valeur,
                                                                       'monnaie': settings.DEVISE_GENERALE}


class Banque(models.Model):

    """banques"""
    cib = models.CharField(max_length=5, blank=True, db_index=True)
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    notes = models.TextField(blank=True, default='')
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_banque'
        ordering = ['nom']

    def __str__(self):
        return self.nom

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne cette banque  avec la banque new
        @param new: banque
        """
        if new == self:
            raise ValueError("une banque ne peut être fusionnée avec elle même")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        nb_change = Compte.objects.filter(banque=self).update(banque=new)
        self.delete()
        return nb_change


class Cat(models.Model):

    """categories
    les sous categories n'existent pas en tant que tel, ce sont justes des categories plus longues"""
    typesdep = (('r', 'recette'), ('d', 'dépense'), ('v', 'virement'))
    nom = models.CharField(max_length=50, unique=True, verbose_name="nom de la catégorie", db_index=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d', verbose_name="type de la catégorie")
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)
    couleur = RGBColorField(default="#FFFFFF")

    class Meta(object):
        db_table = 'gsb_cat'
        verbose_name = "catégorie"
        ordering = ['nom']

    def __str__(self):
        return "%s(%s)" % (self.nom, self.type)

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne cette cat  avec la cat new
        @param new: cat
        """
        if new == self:
            raise ValueError("une catégorie ne peut être fusionnée avec elle même")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le même type de catégorie, %s est %s alors que %s est %s" % (
                self.nom, self.type, new.nom, new.type))
        nb_change = Echeance.objects.filter(cat=self).update(cat=new)
        nb_change += Ope.objects.filter(cat=self).update(cat=new)
        self.delete()
        return nb_change

    @property
    def is_editable(self):
        if self.pk in (
                settings.ID_CAT_OST, settings.ID_CAT_VIR, settings.ID_CAT_PMV, settings.ID_CAT_PMV, settings.REV_PLAC,
                settings.ID_CAT_COTISATION):
            return False
        if self.nom in ("Opération Ventilée", "Frais bancaires", "Non affecté", "Avance", "Remboursement"):
            return False
        return True


class Ib(models.Model):

    """imputations budgetaires
     c'est juste un deuxieme type de categories ou apparentes"""
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    type = models.CharField(max_length=1, choices=Cat.typesdep, default='d')
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_ib'
        verbose_name = "imputation budgétaire"
        verbose_name_plural = 'imputations budgétaires'
        ordering = ['type', 'nom']

    def __str__(self):
        return self.nom

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne cette ib avec l'ib new
        @param new: ib
        """
        if new == self:
            raise ValueError("une ib ne peut etre fusionnée avec elle même")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le même type de ib, %s est %s alors que %s est %s" % (
                self.nom, self.type, new.nom, new.type))
        nb_change = Echeance.objects.filter(ib=self).update(ib=new)
        nb_change += Ope.objects.filter(ib=self).update(ib=new)
        self.delete()
        return nb_change


class Exercice(models.Model):

    """listes des exercices des comptes
    attention, il ne faut confondre exercice et rapp. les exercices sont les même pour tous les comptes alors q'un rapp est pour un seul compte
    """
    date_debut = models.DateField(default=utils.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_exercice'
        ordering = ['-date_debut']
        get_latest_by = 'date_debut'

    def __str__(self):
        return "%s au %s" % (self.date_debut.strftime("%d/%m/%Y"), self.date_fin.strftime("%d/%m/%Y"))

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne cet exercice avec l'exercice new
        @param new: exercice
        """
        if new == self:
            raise ValueError("un exercice ne peut etre fusionné avec lui même")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        nb_change = Echeance.objects.filter(exercice=self).update(exercice=new)
        nb_change += Ope.objects.filter(exercice=self).update(exercice=new)
        if self.date_debut != new.date_debut:
            new.date_debut = min(new.date_debut, self.date_debut)
        if self.date_fin != new.date_fin:
            new.date_fin = max(new.date_fin, self.date_fin)
        new.save()
        self.delete()
        return nb_change


class Compte(models.Model):

    """
    comptes (normal)
    """
    typescpt = (
        ('b', 'bancaire'), ('e', 'espece'), ('p', 'passif'), ('t', 'titre'), ('a', 'autre actifs'))
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    titulaire = models.CharField(max_length=40, blank=True, default='')
    type = models.CharField(max_length=1, choices=typescpt, default='b')
    banque = models.ForeignKey(Banque, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    guichet = models.CharField(max_length=15, blank=True, default='')
    # il est en charfield comme celui d'en dessous parce qu'on n'est pas sur qu'il n y ait que des chiffres
    num_compte = models.CharField(max_length=20, blank=True, default='', db_index=True)
    cle_compte = models.IntegerField(null=True, blank=True, default=0)
    solde_init = models_gsb.CurField(default=decimal.Decimal('0.00'))
    solde_mini_voulu = models_gsb.CurField(null=True, blank=True)
    solde_mini_autorise = models_gsb.CurField(null=True, blank=True)
    ouvert = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    moyen_credit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="compte_moyen_credit_set", default=None,
                                            limit_choices_to={'type': "r"})
    moyen_debit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.PROTECT,
                                           related_name="compte_moyen_debit_set", default=None,
                                           limit_choices_to={'type': "d"})
    titre = models.ManyToManyField('Titre', through="Ope_titre")
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)
    couleur = RGBColorField(default="#FFFFFF")

    class Meta(object):
        db_table = 'gsb_compte'
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def solde(self, datel=None, rapp=False, espece=False, pointe_rapp=False):
        """renvoie le solde du compte
            @param datel : date date limite de calcul du solde
            @param rapp : boolean faut il prendre uniquement les opération rapproches
            @param pointe_rapp: boolean
            @param espece : si c'est un compte espece d'un compte titre (fonctionne egalement pour les comptes normaux)
        """
        query = Ope.non_meres().filter(compte__id__exact=self.id)
        if rapp and not pointe_rapp:
            query = query.filter(rapp__id__isnull=False)
        if pointe_rapp:
            query = query.filter(Q(rapp__id__isnull=False) | Q(pointe=True))
        if datel is not None:
            query = query.filter(date__lte=datel)
        req = query.aggregate(total=models.Sum('montant'))['total']
        if req is None:
            req = 0
        if self.solde_init is not None and self.solde_init != 0:
            solde = decimal.Decimal(req) + decimal.Decimal(self.solde_init)
        else:
            solde = decimal.Decimal(req)
        if self.type == 't' and espece is False:
            solde += self.solde_titre(datel, rapp)
        return solde

    def solde_espece(self, datel=None):
        return self.solde(datel=datel, espece=True)

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne deux compte, verifie avant que c'est le même type
        @param new: Compte
        """
        if new == self:
            raise ValueError("un compte ne peut etre fusionné avec lui même")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        if new.type != self.type:
            raise Gsb_exc("attention ce ne sont pas deux compte de même type")
        if not (self.ouvert and new.ouvert):
            raise Gsb_exc("impossible, un des deux comptes est fermé")
        nb_change = Echeance.objects.filter(compte=self).update(compte=new)
        nb_change += Echeance.objects.filter(compte_virement=self).update(compte_virement=new)
        nb_change += Ope.objects.filter(compte=self).update(compte=new)
        if self.type == "t":
            nb_change += Ope_titre.objects.filter(compte=self).update(compte=new)
        self.delete()
        return nb_change

    def get_absolute_url(self):
        return reverse('gsb_cpt_detail', kwargs={'cpt_id': str(self.id)})

    def solde_rappro(self, espece=False):
        return self.solde(rapp=True, espece=espece)

    def solde_pointe_rapp(self, espece=False):
        """renvoie le solde du compte pour les operations pointees
        """
        solde = self.solde(espece=espece, pointe_rapp=True)
        return solde

    solde_rappro.short_description = "solde rapproché"

    def date_rappro(self):
        """
        date de rapprochement cad date du rapprochement de la plus recente des ope rapproches
        @return: date or None
        """
        try:
            opes = Ope.objects.filter(compte__id=self.id).filter(rapp__isnull=False).select_related('rapp').latest(
                'date')
            return opes.rapp.date
        except Ope.DoesNotExist:
            return None

    date_rappro.short_description = "date dernier rapp"

    @transaction.atomic
    def achat(self, titre, nombre, prix=1, date=None, frais=0, virement_de=None, cat_frais=None, tiers_frais=None):
        """fonction pour achat de titre:
        @param titre:object titre
        @param nombre:decimal
        @param prix;decimal
        @param date:date
        @param frais:decimal
        @param virement_de: object compte
        """
        if date is None:
            date = utils.today()
        self.alters_data = True
        if isinstance(titre, Titre):
            if decimal.Decimal(force_text(frais)):  # des frais bancaires existent
                if not cat_frais:
                    cat_frais = Cat.objects.get(nom="Frais bancaires")
                if not tiers_frais:
                    tiers_frais = titre.tiers
                self.ope_set.create(date=date, montant=decimal.Decimal(force_text(frais)) * -1, tiers=tiers_frais,
                                    cat=cat_frais, notes="Frais %s@%s" % (nombre, prix), moyen=self.moyen_debit(),
                                    automatique=True)
                # gestion compta matiere (et donc opération sous jacente et cours)
            ope_titre = Ope_titre.objects.create(titre=titre, compte=self,
                                                 nombre=decimal.Decimal(force_text(nombre)), date=date, cours=prix)
            # virement
            if virement_de:
                vir = Virement()
                vir.create(compte_origine=virement_de, compte_dest=self,
                           montant=decimal.Decimal(force_text(prix)) * decimal.Decimal(force_text(nombre)) + frais,
                           date=date)
            return ope_titre
        else:
            raise TypeError("pas un titre")

    @transaction.atomic
    def vente(self, titre, nombre, prix=1, date=None, frais=0, virement_vers=None, cat_frais=None, tiers_frais=None):
        """fonction pour vente de titre:
        @param titre
        @param nombre positif
        @param prix
        @param date
        @param frais
        @param virement_vers
        """
        if date is None:
            date = utils.today()
        nombre = abs(nombre)
        self.alters_data = True
        if isinstance(titre, Titre):
            # extraction des titres dans portefeuille
            nb_titre_avant = titre.nb(compte=self, datel=date)
            if not nb_titre_avant or nb_titre_avant < nombre:
                raise Titre.DoesNotExist('titre pas en portefeuille au %s' % date)
                # compta matiere
            ope_titre = Ope_titre.objects.create(titre=titre, compte=self,
                                                 nombre=decimal.Decimal(force_text(nombre)) * -1, date=date,
                                                 cours=prix)
            if frais:
                if not cat_frais:
                    cat_frais = Cat.objects.get(nom="Frais bancaires")
                if not tiers_frais:
                    tiers_frais = titre.tiers
                self.ope_set.create(date=date, montant=abs(decimal.Decimal(force_text(frais))) * -1,
                                    tiers=tiers_frais, cat=cat_frais, notes="frais -%s@%s" % (nombre, prix),
                                    moyen=self.moyen_debit(), automatique=True)
            if virement_vers:
                vir = Virement()
                vir.create(compte_origine=self, compte_dest=virement_vers,
                           montant=decimal.Decimal(force_text(prix)) * decimal.Decimal(force_text(nombre)) - frais,
                           date=date)
            return ope_titre
        else:
            raise TypeError("pas un titre")

    @transaction.atomic
    def revenu(self, titre, montant=1, date=None, frais=0, virement_vers=None, cat_frais=None, tiers_frais=None):
        """fonction pour ost de titre:"""
        if date is None:
            date = utils.today()
        self.alters_data = True
        if isinstance(titre, Titre):
            # extraction des titres dans portefeuille
            nb_titre_avant = titre.nb(compte=self, datel=date)
            if not nb_titre_avant:
                raise Titre.DoesNotExist('titre pas en portefeuille au %s' % date)
                # ajout du revenu proprement dit
            self.ope_set.create(date=date, montant=decimal.Decimal(force_text(montant)), tiers=titre.tiers,
                                cat=Cat.objects.get(id=settings.ID_CAT_OST), notes="revenu", moyen=self.moyen_credit(),
                                # on ne prend le moyen par defaut car ce n'est pas une OST
                                automatique=True)
            if frais:
                if not tiers_frais:
                    tiers_frais = titre.tiers
                if not cat_frais:
                    cat_frais = Cat.objects.get(nom="Frais bancaires")
                self.ope_set.create(date=date, montant=decimal.Decimal(force_text(frais)) * -1, tiers=tiers_frais,
                                    cat=cat_frais, notes="frais revenu", moyen=self.moyen_debit(), automatique=True)
            if virement_vers:
                vir = Virement()
                vir.create(self, virement_vers, decimal.Decimal(force_text(montant)) - frais, date)
        else:
            raise TypeError("pas un titre")

    def solde_titre(self, datel=None, rapp=False):
        """
        renvoie le solde titre pour le compte titre
        @type datel: datetime
        @param datel: date, a laquelle on veut ce solde
        @param rapp: boolean, si on ne vuet que les operation rapp
        @return: int
        """
        solde_titre = 0
        # il n'y a pas d'operation
        if datel is not None:
            try:
                datel = min(datel, utils.today())  # @UnusedVariable
            except TypeError:
                datel = utils.strpdate(datel)
                datel = min(datel, utils.today())
        else:
            datel = utils.today()
            # si il n'y a pas d'operations
        try:
            if self.ope_set.latest('date').date > datel:
                return 0
        except Ope.DoesNotExist:
            return 0
        for titre in self.titre.all().distinct():
            solde_titre = solde_titre + titre.encours(compte=self, rapp=rapp, datel=datel)
        return solde_titre

    def liste_titre(self):
        liste = self.titre.all().distinct().values_list("id", flat=True)
        return Titre.objects.filter(id__in=liste)

    def moyen_debit(self):
        if self.moyen_debit_defaut is not None:
            return self.moyen_debit_defaut
        else:
            try:
                return Moyen.objects.get(id=settings.MD_DEBIT)
            except Moyen.DoesNotExist:
                raise Moyen.DoesNotExist()

    def moyen_credit(self):
        if self.moyen_credit_defaut is not None:
            return self.moyen_credit_defaut
        else:
            return Moyen.objects.get(id=settings.MD_CREDIT)

    def ajustement(self, datel, montant_vrai, cat_nom="Ajustements", rapp=False, pointe_rapp=False):
        cat_id = Cat.objects.get_or_create(nom=cat_nom, defaults={"nom": cat_nom, "type": "d"})[0].id
        datel = utils.strpdate(datel)
        montant_theorique = self.solde(espece=True, datel=datel, rapp=rapp, pointe_rapp=pointe_rapp)
        montant_a_corriger = decimal.Decimal(str(montant_vrai)) - montant_theorique
        if montant_a_corriger != 0:
            ope = Ope.objects.create(compte=self, tiers=Tiers.objects.get_or_create(nom="ajustement", defaults={"nom": "ajustement"})[0],
                                     montant=montant_a_corriger, date=datel,
                                     moyen=self.moyen_debit() if montant_a_corriger < 0 else self.moyen_credit(),
                                     automatique=True, notes="ajustement le %s" % utils.today(), cat_id=cat_id)
            return "opération ({}) crée ".format(ope)
        else:
            return "rien à modifier"

    def ajustement_titre(self, datel, titre, nb_vrai, cours):
        datel = utils.strpdate(datel)
        nb_theorique = titre.nb(datel=datel, compte=self)
        nb_a_corriger = nb_theorique - decimal.Decimal(str(nb_vrai))
        if nb_a_corriger > 0:
            ope = self.vente(titre=titre, nombre=nb_a_corriger, prix=cours, date=datel, frais=cours * nb_a_corriger)
        else:
            if nb_a_corriger < 0:
                ope = self.achat(titre=titre, nombre=nb_a_corriger * -1, prix=cours, date=datel)
                self.ope_set.create(date=datel, montant=decimal.Decimal(force_text(cours * nb_a_corriger)) * -1,
                                    tiers=titre.tiers, cat=Cat.objects.get(nom="Frais bancaires"),
                                    notes="Frais %s@%s" % (nb_a_corriger, cours), moyen=self.moyen_credit(),
                                    automatique=True)

            else:
                return "RAS"
        return ope


class Ope_titre(models.Model):

    """ope titre en compta matiere"""

    titre = models.ForeignKey(Titre, on_delete=models.CASCADE)
    compte = models.ForeignKey(Compte, verbose_name="compte titre", limit_choices_to={'type': 't'})
    nombre = models_gsb.CurField(default=0, decimal_places=6)
    date = models.DateField(db_index=True)
    cours = models_gsb.CurField(default=1, decimal_places=6)
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_ope_titre'
        verbose_name_plural = 'Opérations titres(compta_matiere)'
        verbose_name = 'Opération titres(compta_matiere)'
        ordering = ['-date']

    @property
    def rapp(self):
        if utils.is_onexist(self, "ope_ost") and self.ope_ost.rapp is not None:
            return True
        if utils.is_onexist(self, "ope_pmv") and self.ope_pmv.rapp is not None:
            return True
        return False

    @property
    def invest(self):
        return self.nombre * self.cours

    @transaction.atomic
    def save(self, shortcut=False, *args, **kwargs):
        self.cours = decimal.Decimal(self.cours)
        self.nombre = decimal.Decimal(self.nombre)
        # definition des cat avec possibilite
        cat_ost = Cat.objects.get(id=settings.ID_CAT_OST)
        cat_pmv = Cat.objects.get(id=settings.ID_CAT_PMV)
        super(Ope_titre, self).save(*args, **kwargs)
        # gestion des cours
        # si on change la date de l'operation il faut supprimer le cours associe
        if utils.is_onexist(self, "ope_ost"):
            old_date = self.ope_ost.date
            try:
                Cours.objects.get(titre=self.titre, date=old_date).delete()
            except Cours.DoesNotExist:
                pass
        Cours.objects.get_or_create(titre=self.titre, date=self.date,
                                    defaults={'titre': self.titre, 'date': self.date, 'valeur': self.cours})
        if self.nombre >= 0:  # on doit separer because gestion des plues ou moins value
            if utils.is_onexist(self, 'ope_pmv'):
                self.ope_pmv.delete()  # comme achat, il n'y a pas de plus ou moins value exteriosée donc on efface
            if not utils.is_onexist(self, 'ope_ost'):  # il faut creer l'ope sous jacente
                ope_ost = Ope.objects.create(date=self.date, montant=self.cours * self.nombre * -1,
                                             tiers=self.titre.tiers, cat=cat_ost,
                                             notes="%s@%s" % (self.nombre, self.cours), moyen=self.compte.moyen_debit(),
                                             compte=self.compte, ope_titre_ost=self)
                self.ope_ost = ope_ost
            else:  # la modifier juste
                ope_ost = self.ope_ost
                ope_ost.date = self.date
                ope_ost.montant = self.cours * self.nombre * -1
                ope_ost.tiers = self.titre.tiers
                ope_ost.notes = "%s@%s" % (self.nombre, self.cours)
                ope_ost.compte = self.compte
                ope_ost.save()
        else:  # c'est une vente
            # on ne sait pas si l'ope existe donc on exclue
            inv_vrai = self.titre.investi(self.compte, datel=self.date, exclude=self)
            # on exclue par defaut car l'operation existe deja
            nb_vrai = self.titre.nb(self.compte, datel=self.date, exclude_id=self.id)
            # chaine car comme on a des decimal
            ost = decimal.Decimal("{0:.2f}".format((max(inv_vrai, 0) / nb_vrai) * abs(decimal.Decimal(self.nombre))))
            pmv = abs(self.nombre * self.cours) - ost
            # on cree les ope
            if not utils.is_onexist(self, 'ope_ost'):
                Ope.objects.create(date=self.date, montant=ost, tiers=self.titre.tiers, cat=cat_ost,
                                   notes="%s@%s" % (self.nombre, self.cours), moyen=self.compte.moyen_credit(),
                                   compte=self.compte, ope_titre_ost=self)
            else:
                self.ope_ost.date = self.date
                self.ope_ost.montant = ost
                self.ope_ost.tiers = self.titre.tiers
                self.ope_ost.notes = "%s@%s" % (self.nombre, self.cours)
                self.ope_ost.compte = self.compte
                self.ope_ost.moyen = self.compte.moyen_credit()
                self.ope_ost.save()
            if not utils.is_onexist(self, 'ope_pmv'):
                Ope.objects.create(date=self.date, montant=pmv, tiers=self.titre.tiers, cat=cat_pmv,
                                   notes="%s@%s" % (self.nombre, self.cours), moyen=self.compte.moyen_credit(),
                                   compte=self.compte, ope_titre_pmv=self)
            else:
                # on modifie tout
                self.ope_pmv.date = self.date
                self.ope_pmv.montant = pmv
                self.ope_pmv.tiers = self.titre.tiers
                self.ope_pmv.cat = cat_pmv
                self.ope_pmv.notes = "%s@%s" % (self.nombre, self.cours)
                self.ope_pmv.compte = self.compte
                self.ope_pmv.moyen = self.compte.moyen_credit()
                self.ope_pmv.save()
        if shortcut:
            # useful if running total
            for ope_ti in Ope_titre.objects.filter(nombre__lte=0, date__gte=self.date, compte=self.compte).exclude(pk=self.id).order_by('-date'):
                ope_ti.save(shortcut=False)

    def get_absolute_url(self):
        return reverse('ope_titre_detail', kwargs={'pk': str(self.id)})

    def __str__(self):
        if self.nombre > 0:
            sens = "achat"
        else:
            sens = "vente"
        date_ope = utils.strpdate(self.date)
        chaine = "(%s) %s de %s %s à %s %s le %s cpt:%s" % (
            self.id, sens, abs(self.nombre), self.titre, self.cours, settings.DEVISE_GENERALE, date_ope.strftime('%d/%m/%Y'), self.compte)
        return chaine


# noinspection PyUnusedLocal
@receiver(signals.pre_delete, sender=Ope_titre, weak=False)
def verif_opetitre_rapp(sender, **kwargs):
    instance = kwargs['instance']
    # on evite que cela soit une opération rapproche
    if utils.is_onexist(instance, 'ope_ost'):
        if instance.ope_ost.rapp is not None:
            raise IntegrityError("opération espèce rapprochée")
    if utils.is_onexist(instance, 'ope_pmv'):
        if instance.ope_pmv.rapp is not None:
            raise IntegrityError("opération pmv rapprochée")


class Moyen(models.Model):

    """moyen de paiements
    commun à l'ensembles des comptes
    actuellement, les comptes ont tous les moyens sans possiblite de faire le tri
    """
    # on le garde pour l'instant car ce n'est pas dans le même ordre que pour les categories
    typesdep = (('v', 'virement'), ('d', 'depense'), ('r', 'recette'))
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d')
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_moyen'
        verbose_name = "moyen de paiment"
        verbose_name_plural = "moyens de paiment"
        ordering = ['nom']

    def __str__(self):
        return "%s (%s)" % (self.nom, self.type)

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne ce Moyen avec le Moyen new
        @param new: Moyen
        """
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        if new == self:
            raise ValueError("un moyen ne peut etre fusionné avec lui même")
        if self.id == settings.MD_CREDIT or self.id == settings.MD_DEBIT:
            raise ValueError("impossible de le fusionner car il est un moyen par défault dans les settings")
        else:
            self.alters_data = True
            nb_change = Compte.objects.filter(moyen_credit_defaut=self).update(moyen_credit_defaut=new)
            nb_change += Compte.objects.filter(moyen_debit_defaut=self).update(moyen_debit_defaut=new)
            nb_change += Echeance.objects.filter(moyen=self).update(moyen=new)
            nb_change += Echeance.objects.filter(moyen_virement=self).update(moyen_virement=new)
            nb_change += Ope.objects.filter(moyen=self).update(moyen=new)
            self.delete()
        return nb_change

    def delete(self, *args, **kwargs):
        if self.id == settings.MD_CREDIT or self.id == settings.MD_DEBIT:
            raise IntegrityError("moyen par defaut")
        super(Moyen, self).delete(*args, **kwargs)


class Rapp(models.Model):

    """rapprochement d'un compte"""
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    date = models.DateField(null=True, blank=True, default=utils.today)
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_rapp'
        verbose_name = "rapprochement"
        ordering = ['-date']
        get_latest_by = 'date'

    def __str__(self):
        return self.nom

    @property
    def compte(self):  # petit raccourci mais normalement, c'est bon. on prend le compte de la premiere ope
        if self.ope_set.exists():
            return self.ope_set.all()[0].compte.id
        else:
            return None

    @property
    def solde(self):
        req = self.ope_set.filter(mere=None).aggregate(solde=models.Sum('montant'))
        if req['solde'] is None:
            solde = 0
        else:
            solde = req['solde']
        return solde

    @transaction.atomic
    def fusionne(self, new):
        """fusionnne ce Rapp avec le Rapp new
        @param new: Rapp
        """
        if new == self:
            raise ValueError("un objet ne peut etre fusionné sur lui mème")
        self.alters_data = True
        if not isinstance(new, type(self)):
            raise TypeError("pas la même classe d'objet")
        new.date = max(new.date, self.date)
        new.save()
        nb_change = Ope.objects.filter(rapp=self).update(rapp=new)
        self.delete()
        return nb_change


class Echeance(models.Model):

    """echeance 'opération future prevue
    soit unique
    soit repete
    """
    typesperiod = (
        ('u', 'unique'), ('s', 'semaine'), ('m', 'mois'), ('a', 'année'), ('j', 'jour'),
    )

    date = models.DateField(default=utils.today, db_index=True)
    date_limite = models.DateField(null=True, blank=True, default=None, db_index=True)
    intervalle = models.IntegerField(default=1)
    periodicite = models.CharField(max_length=1, choices=typesperiod, default="u")
    valide = models.BooleanField(default=True)
    compte = models.ForeignKey(Compte)
    montant = models_gsb.CurField()
    tiers = models.ForeignKey(Tiers, on_delete=models.PROTECT)
    cat = models.ForeignKey(Cat, on_delete=models.PROTECT, verbose_name="catégorie")
    moyen = models.ForeignKey(Moyen, blank=False, on_delete=models.PROTECT, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name="imputation")
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name='echeance_virement_set', default=None)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True, related_name='echeance_moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    notes = models.TextField(blank=True, default='')
    inscription_automatique = models.BooleanField(default=False, help_text="inutile")  # tt les echeances sont automatiques
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta(object):
        db_table = 'gsb_echeance'
        verbose_name = "échéance"
        verbose_name_plural = "echéances"
        ordering = ['date']
        get_latest_by = 'date'

    def __str__(self):
        if self.compte_virement:
            return "(%s) %s=>%s de %s (ech:%s)" % (
                self.id, self.compte, self.compte_virement, self.montant, self.date.strftime('%d/%m/%Y'))
        else:
            return "(%s) %s à %s de %s (ech:%s)" % (
                self.id, self.compte, self.tiers, self.montant, self.date.strftime('%d/%m/%Y'))

    # noinspection PyTypeChecker
    def calcul_next(self):
        """
        calcul la prochaine date d'echeance
        renvoie None si pas de prochaine date
        """
        if not self.valide:  # si c'est plus en fonction pas besoin de calcul complemnetaire
            return None
        initial = self.date
        if self.periodicite == 'u':
            return None
        finale = None
        if self.periodicite == 'j':
            finale = initial + datetime.timedelta(days=self.intervalle)
        if self.periodicite == 's':
            finale = initial + datetime.timedelta(weeks=self.intervalle)
        if self.periodicite == 'm':
            finale = initial + relativedelta(months=self.intervalle)
        if self.periodicite == 'a':
            finale = initial + relativedelta(years=self.intervalle)
            # on verifie que la date limite n'est pas dépasséee
        if self.date_limite is not None and finale > self.date_limite:
            finale = None
        return finale

    @staticmethod
    @transaction.atomic
    def check_if_necessary(request=None, queryset=None, to=None):
        """
        attention ce n'est pas une vue
        verifie si pas d'écheance a passer et la cree au besoin
        @param queryset: le queryset de definition
        @param request: la requete qui permet d'afficher les messages
        @param to: date finale de checking (a priori, utile seulement pour le test afin d'avoir une date fixe)
        """
        if to is None:
            to = utils.today()
        if queryset is None:
            liste_ech = Echeance.objects.filter(valide=True, date__lte=to)
        else:
            liste_ech = queryset
        for ech in liste_ech:
            while ech.date < to and ech.valide:
                if ech.compte_virement:
                    vir = Virement.create(compte_origine=ech.compte, compte_dest=ech.compte_virement,
                                          montant=ech.montant, date=ech.date)
                    vir.auto = True
                    vir.exercice = ech.exercice
                    vir.save()
                    if request is not None:
                        messages.info(request, 'virement (%s)%s crée' % (vir.origine.id, vir.origine.tiers))
                else:
                    ope = Ope.objects.create(compte_id=ech.compte_id, date=ech.date, montant=ech.montant,
                                             tiers_id=ech.tiers_id, cat_id=ech.cat_id, automatique=True,
                                             ib_id=ech.ib_id, moyen_id=ech.moyen_id, exercice_id=ech.exercice_id)
                    if request is not None:
                        messages.info(request, 'opération "%s" créée' % ope)
                if ech.calcul_next():
                    ech.date = ech.calcul_next()
                else:
                    ech.valide = False
                ech.save()

    def clean(self):
        """
        verifie que l'on ne peut mettre un virement vers lui même
        """
        self.alters_data = True
        if self.compte == self.compte_virement:
            raise ValidationError("pas possible de mettre un même compte en départ et en arrivée")
        super(Echeance, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        super(Echeance, self).save(*args, **kwargs)

    @staticmethod
    def verif(request):
        date_min = Echeance.objects.filter(valide=True).aggregate(models.Min('date'))['date__min']
        if date_min is not None and date_min < utils.today():
            messages.info(request,
                          "attention une ou plusieurs écheances sont arrivées à maturité <a href='%s'> cliquer ici pour les intégrer</A>" % mark_safe(
                              reverse('gestion_echeances')))


class Ope(models.Model):

    """operation"""
    compte = models.ForeignKey(Compte)
    date = models.DateField(default=utils.today, db_index=True)
    date_val = models.DateField(null=True, blank=True, default=None)
    montant = models_gsb.CurField()
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.PROTECT, default=None, verbose_name="Catégorie")
    notes = models.TextField(blank=True, default='')
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    num_cheque = models.CharField(max_length=20, blank=True, default='')
    pointe = models.BooleanField(default=False)
    rapp = models.ForeignKey(Rapp, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name='Rapprochement')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name="projet")
    jumelle = models.OneToOneField('self', null=True, blank=True, related_name='jumelle_set', default=None, editable=False,
                                   on_delete=models.CASCADE)
    mere = models.ForeignKey('self', null=True, blank=True, related_name='filles_set', default=None, on_delete=models.CASCADE,
                             verbose_name='Mere')
    automatique = models.BooleanField(default=False, help_text='si cette opération est crée à cause d\'une écheance')
    piece_comptable = models.CharField(max_length=20, blank=True, default='')
    lastupdate = models_gsb.ModificationDateTimeField()
    date_created = models_gsb.CreationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)
    ope_titre_ost = models.OneToOneField('Ope_titre', editable=False, null=True, on_delete=models.CASCADE,
                                         related_name="ope_ost")  # null=true car j'ai des operations sans lien
    ope_titre_pmv = models.OneToOneField('Ope_titre', editable=False, null=True, on_delete=models.CASCADE,
                                         related_name="ope_pmv")  # null=true cr tt les operation d'achat sont null"""

    class Meta(object):
        db_table = 'gsb_ope'
        get_latest_by = 'date'
        order_with_respect_to = 'compte'
        verbose_name = "opération"
        #ordering = ['-date']

    @staticmethod
    def non_meres():
        """ renvoie uniquement les opération non mere
        """
        return Ope.objects.all().exclude(filles_set__isnull=False)

    @property
    def opetitre(self):
        if self.ope_titre_ost is not None:
            return self.ope_titre_ost
        if self.ope_titre_pmv is not None:
            return self.ope_titre_pmv
        return None

    @staticmethod
    def solde_set(q):
        if not q.exists():
            return 0
        return q.aggregate(total=models.Sum('montant'))['total']

    def __str__(self):
        return "({0}) le {1} : {2:n} {3:s} tiers: {4:s} cpt: {5:s}".format(self.id, self.date.strftime('%d/%m/%Y'),
                                                                           self.montant, settings.DEVISE_GENERALE,
                                                                           self.tiers.nom, self.compte.nom)

    def get_absolute_url(self):
        return reverse('gsb_ope_detail', kwargs={'pk': str(self.id)})

    def clean(self):
        """ verifie que :
        1) une operation n'est pas a a la fois pointe et rapproche
        2) que l'ope n'est pas modifie  (du mois  son montant) si rapproche ou pointe"""
        self.alters_data = True
        self.deja_clean = True
        super(Ope, self).clean()
        self.notes = self.notes.replace("\u2019", "'").replace("\u2018", "'")
        # verification qu'il n'y pas pointe et rapprochee
        if self.pointe and self.rapp is not None:
            raise ValidationError("cette opération ne peut pas etre à la fois pointée et rapprochée")
        if not self.compte.ouvert:
            raise ValidationError("cette opération ne peut pas être modifié car le compte est fermé")
        if self.is_mere:
            self.cat = Cat.objects.get_or_create(nom="Opération Ventilée", defaults={"nom": "Opération Ventilée"})[0]
            if has_changed(self, 'montant'):
                # ensemble des opefilles
                opes = self.filles_set.all()
                for o in opes.values('id', 'pointe', 'rapp'):
                    if o['pointe']:
                        raise ValidationError("impossible de modifier l'opération car au moins une partie est pointée")
                    if o['rapp'] is not None:
                        raise ValidationError(
                            "impossible de modifier l'opération car au moins une partie est rapprochée")
                if self.pointe:
                    raise ValidationError("impossible de modifier l'opération car au moins une partie est pointée")
                if self.rapp is not None:
                    raise ValidationError("impossible de modifier l'opération car au moins une partie est rapprochée")

        if self.is_fille:
            if has_changed(self, 'montant'):
                mere = self.mere
                # ensemble des opefilles de la mere
                opes = Ope.objects.filter(mere_id=mere.id)
                for o in opes.values('id', 'pointe', 'rapp'):
                    if o['pointe']:
                        raise ValidationError("impossible de modifier l'opération car au moins une partie est pointée")
                    if o['rapp'] is not None:
                        raise ValidationError(
                            "impossible de modifier l'opération car au moins une partie est rapprochée")
                if self.pointe or mere.pointe:
                    raise ValidationError("impossible de modifier l'opération car au moins une partie est pointée")
                if self.rapp is not None or mere.rapp is not None:
                    raise ValidationError("impossible de modifier l'opération car au moins une partie est rapprochée")

    @property
    def is_mere(self):
        return self.filles_set.count() > 0  # and self.id > 1  # on rajouter and self.id >1 afin de pouvoir creer une mere

    @property
    def is_fille(self):
        """
        est elle une operation sous ventile
        @return: Boolean
        """
        return self.mere is not None

    @property
    def tot_fille(self):
        return Ope.solde_set(self.filles_set)

    @property
    def pr(self):
        """renvoie true si pointee ou rapprochée"""
        if self.rapp or self.pointe:
            return True
        else:
            return False

    def is_editable(self):
        if self.is_mere:
            return False
        if self.rapp is not None:
            return False
        if self.compte.ouvert is False:
            return False
        if self.jumelle:
            if self.jumelle.rapp:
                return False
        if self.ope_titre_ost is not None or self.ope_titre_pmv is not None:
            return False
        if self.jumelle is not None and (self.jumelle.pointe or self.jumelle.rapp is not None):
            return False
        return True

    @transaction.atomic
    def save(self, *args, **kwargs):
        # lance clean et attrape les erreurs
        try:
            self.clean()
        except ValidationError as e:
            raise IntegrityError("%s" % e)
        if self.is_mere:
            self.montant = self.tot_fille
        if self.moyen is None:
            if self.montant >= 0:
                self.moyen = self.compte.moyen_credit()
            if self.montant < 0:
                self.moyen = self.compte.moyen_debit()
        if self.moyen.type == 'd' and self.montant > 0:
            self.montant *= -1
        super(Ope, self).save(*args, **kwargs)


# noinspection PyUnusedLocal
@receiver(signals.post_save, sender=Ope, weak=False)
def ope_fille(sender, **kwargs):
    if kwargs['raw']:
        return
    self = kwargs['instance']
    if self.is_fille:
        if self.mere.tot_fille != self.mere.montant:
            self.mere.montant = self.mere.tot_fille
            self.mere.save()


# noinspection PyUnusedLocal
@receiver(signals.pre_delete, sender=Ope, weak=False)
def verif_ope_rapp(sender, **kwargs):
    instance = kwargs['instance']
    # on evite que cela soit une opération rapproche
    if instance.rapp:
        raise IntegrityError("opération rapprochée")
    if instance.jumelle:
        if instance.jumelle.rapp:
            raise IntegrityError("opération jumelle rapprochée")
    if instance.mere:
        if instance.mere.rapp:
            raise IntegrityError("opération mère rapprochée")


class Virement(object):

    """raccourci pour creer un virement entre deux comptes"""

    def __init__(self, ope=None):

        if ope:
            if not isinstance(ope, type(Ope())):
                raise TypeError('pas opé')
            if ope.montant <= 0:
                self.origine = ope
                self.dest = self.origine.jumelle
            else:
                self.dest = ope
                self.origine = self.dest.jumelle
            self._init = True
        else:
            self._init = False

    def setdate(self, date):
        self.origine.date = date
        self.dest.date = date

    def getdate(self):
        return self.origine.date

    date = property(getdate, setdate)

    def setdate_val(self, date):
        self.origine.date_val = date
        self.dest.date_val = date

    def getdate_val(self):
        return self.origine.date_val

    date_val = property(getdate_val, setdate_val)

    def setmontant(self, montant):
        self.origine.montant = montant * -1
        self.dest.montant = montant

    def getmontant(self):
        return self.dest.montant

    montant = property(getmontant, setmontant)

    def setnotes(self, notes):
        self.origine.notes = notes
        self.dest.notes = notes

    def getnotes(self):
        return self.origine.notes

    notes = property(getnotes, setnotes)

    def setpointe(self, pointe):
        self.origine.pointe = pointe
        self.dest.pointe = pointe

    def getpointe(self):
        if self.origine.pointe or self.dest.pointe:
            return True
        else:
            return False

    pointe = property(getpointe, setpointe)

    def getauto(self):
        return self.origine.automatique

    def setauto(self, auto):
        self.origine.automatique = auto
        self.dest.automatique = auto

    auto = property(getauto, setauto)

    def getexo(self):
        return self.origine.exercice

    def setexo(self, auto):
        self.origine.exercice = auto
        self.dest.exercice = auto

    exercice = property(getexo, setexo)

    def save(self):
        if self._init:
            tier = Tiers.objects.get_or_create(nom=self.__str__(), defaults={'nom': self.__str__()})[0]
            self.origine.tiers = tier
            self.dest.tiers = tier
            self.origine.cat_id = settings.ID_CAT_VIR
            self.dest.cat_id = settings.ID_CAT_VIR
            self.origine.save()
            self.dest.save()
        else:
            raise Gsb_exc('pas initialise')

    @staticmethod
    def create(compte_origine, compte_dest, montant, date=None, notes=""):
        """
        cree un nouveau virement
        """
        if not isinstance(compte_origine, Compte):
            raise TypeError('pas compte')
        if not isinstance(compte_dest, Compte):
            raise TypeError('pas compte')
        if compte_origine == compte_dest:
            raise TypeError("Attention, le compte de départ ne peut être celui d'arrivée")
        vir = Virement()
        vir.origine = Ope()
        vir.dest = Ope()
        vir.origine.compte = compte_origine
        vir.dest.compte = compte_dest
        vir.montant = montant
        if date:
            vir.date = date
        else:
            vir.date = utils.today()
        vir.notes = notes
        vir._init = True
        moyen = Moyen.objects.filter(type='v')[0]
        vir.dest.moyen = moyen
        vir.origine.moyen = moyen
        vir.save()
        vir.origine.jumelle = vir.dest
        vir.dest.jumelle = vir.origine
        vir.save()
        return vir

    def delete(self):
        self.origine.jumelle = None
        self.dest.jumelle = None
        self.origine.delete()
        self.dest.delete()

    def init_form(self):
        """renvoit les donnnés afin d'intialiser virementform"""
        if self._init:
            tab = {'compte_origine': self.origine.compte.id, 'compte_destination': self.dest.compte.id,
                   'montant': self.montant, 'date': self.date, 'notes': self.notes, 'pointe': self.pointe}
            try:
                tab['moyen_origine'] = self.origine.moyen.id
            except AttributeError:  # pragma: no cover
                tab['moyen_origine'] = Moyen.objects.filter(type='v')[0]
            try:
                tab['moyen_destination'] = self.dest.moyen.id
            except AttributeError:  # pragma: no cover
                tab['moyen_destination'] = Moyen.objects.filter(type='v')[0]
        else:
            raise Gsb_exc('Attention, on ne peut intialiser un form que si le virement est bound')
        return tab

    def __str__(self):
        return "%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)


class Db_log(models.Model):
    date_time_action = models.DateTimeField(auto_now_add=True, null=True)
    datamodel = models.CharField(null=False, max_length=20)
    id_model = models.IntegerField()
    uuid = models.CharField(null=False, max_length=255)
    type_action = models.CharField(null=False, max_length=255)
    memo = models.CharField(max_length=255)
    date_ref = models.DateField(default=datetime.date.today)

    def __str__(self):
        actions = {'I': "insert", 'U': "update", 'D': "delete"}
        date_action = tz.localtime(self.date_time_action)
        return "({obj.id:d}) {action:s} le {obj_date:%Y-%m-%d %H:%M:%S%z} de {obj.datamodel:s} #{obj.id_model:d} memo:'{obj.memo:s}'".format(action=actions[self.type_action], obj=self, obj_date=date_action)
