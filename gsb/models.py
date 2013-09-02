# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.db import models
import datetime
import decimal
from django.db import transaction, IntegrityError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.utils.encoding import smart_unicode, force_unicode
import gsb.model_field as models_gsb
from gsb import utils
from django.core.urlresolvers import reverse

__all__ = ['Tiers', 'Titre', 'Cours', 'Banque', 'Cat', 'Ib', 'Exercice', 'Compte', 'Ope_titre', 'Moyen', 'Rapp', 'Echeance', 'Ope', 'Virement', 'has_changed']


class Gsb_exc(Exception):
    pass


class Ex_jumelle_neant(Exception):
    pass


def has_changed(instance, fields):
    if not getattr(instance, "pk", False):
        return False
    if isinstance(fields, basestring):  # si c'est une chaine de caraceteres on le transforme en tupple
        fields = (fields,)
    changed = False
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
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_tiers'
        verbose_name_plural = u'tiers'
        ordering = ['nom']

    def __unicode__(self):
        return u"%s" % self.nom

    @transaction.commit_on_success
    def fusionne(self, new, ok_titre=False):
        """fusionnne tiers vers new tiers
        @param new: tiers
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")

        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        if (self.is_titre or new.is_titre) and not ok_titre:
            raise ValueError(u"un tiers suppport de titre ne peut etre fusionnné directement. vous devez fusionner les titres")
        nb_tiers_change = Echeance.objects.filter(tiers=self).update(tiers=new)
        nb_tiers_change += Ope.objects.filter(tiers=self).update(tiers=new)
        self.delete()
        return nb_tiers_change


class Titre(models.Model):
    """²
    les titres englobe les actifs financiers
    afin de pouvoir faire le lien dans les operations, il y a un ligne vers les tiers
    :model:`gsb.tiers`
    le set_null est mis afin de pouvoir faire du menage dans les titres plus utilise
    sans que cela ne pose trop de problème dans les opérations.
    """
    typestitres = (
        ('ACT', u'action'),
        ('OPC', u'opcvm'),
        ('CSL', u'compte sur livret'),
        ('OBL', u'obligation'),
        ('ZZZ', u'autre'))
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    isin = models.CharField(max_length=12, unique=True, db_index=True)
    type = models.CharField(max_length=3, choices=typestitres, default='ZZZ')
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = u'gsb_titre'
        ordering = ['nom']

    def __unicode__(self):
        return u"%s (%s)" % (self.nom, self.isin)

    def last_cours(self, datel=None):
        """renvoie le dernier cours
        @param datel: la date max du cours ou l'on veut
        @return : decimal"""
        if datel is None:
            datel = utils.today()
        reponse = self.cours_set.filter(date__lte=datel)
        if reponse.exists():
            return reponse.latest('date').valeur
        else:
            return 0

    def last_cours_date(self, rapp=False):
        """renvoie la date du dernier cours
        @return : datetime ou None
        """
        if not rapp:
            return self.cours_set.latest('date').date
        else:
            opes = Ope.objects.filter(tiers=self.tiers).filter(rapp__isnull=False)
            if opes.exists():
                date_rapp = opes.latest('date').rapp.date
                liste = Cours.objects.filter(titre=self).filter(date__lte=date_rapp)
                if liste.exists():
                    return liste.latest('date').date
            else:
                return None

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne ce titre avec le titre new
        @param new: Titre
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        if self.type != new.type:
            raise TypeError(u"pas le même type de titre")
        for cours in self.cours_set.all():
            try:
                if new.cours_set.get(date=cours.date).valeur != cours.valeur:
                    raise Gsb_exc(
                        u"attention les titre %s et %s ne peuvent etre fusionné à cause histo de cours" % (self, new))
            except Cours.DoesNotExist:
                new.cours_set.create(date=cours.date, valeur=cours.valeur)
        nb_change = 0
        nb_change += Ope_titre.objects.filter(titre=self).update(titre=new)
        # on doit aussi reaffecter le tiers associe
        self.tiers.fusionne(new.tiers, ok_titre=True)
        self.delete()
        return nb_change

    def save(self, *args, **kwargs):
        tiers_save = False
        self.alters_data = True
        if not utils.is_onexist(self, "tiers"):
            super(Titre, self).save(*args, **kwargs)
            self.tiers = Tiers.objects.get_or_create(nom='titre_ %s' % self.nom,
                                                     defaults={"nom": 'titre_ %s' % self.nom,
                                                               "is_titre": True,
                                                               "notes": "%s@%s" % (self.isin, self.type)})[0]
            self.tiers.nom = 'titre_ %s' % self.nom
            self.tiers.notes = u"%s@%s" % (self.isin, self.type)
            self.tiers.is_titre = True
            tiers_save = True

        else:
            if has_changed(self, 'nom'):
                if self.tiers.nom != 'titre_ %s' % self.nom:
                    self.tiers.nom = 'titre_ %s' % self.nom
                    tiers_save = True
            if has_changed(self, ('isin', 'type')):
                if self.tiers.notes != u"%s@%s" % (self.isin, self.type):
                    self.tiers.notes = u"%s@%s" % (self.isin, self.type)
                    tiers_save = True
        # comme ca a ete obligatoirement cree au dessus
        if 'force_insert' in kwargs.keys():
            del kwargs['force_insert']
            kwargs['force_update'] = True
        super(Titre, self).save(*args, **kwargs)
        if tiers_save:
            self.tiers.is_titre = True
            self.tiers.save()

    def investi(self, compte=None, datel=None, rapp=None, exclude_id=None):
        """renvoie le montant investi
        @param compte: Compte , si None, renvoie sur  l'ensemble des comptes titres
        @param datel: date, renvoie sur avant la date ou tout si none
        @param rapp: Bool, si true, renvoie uniquement les opération rapprochées
        @param exclude_id: int id de l'ope a exclure.attention c'ets bien ope et non ope_titre
        """
        query = Ope.non_meres().filter(tiers=self.tiers)
        if compte:
            query = query.filter(compte=compte)
        if datel:
            query = query.filter(date__lte=datel)
        if rapp:
            query = query.filter(rapp__isnull=False)
        if exclude_id:
            query = query.exclude(pk=exclude_id.ope.id)
            if exclude_id.ope_pmv is not None:
                query = query.exclude(pk=exclude_id.ope_pmv.id)
        valeur = query.aggregate(invest=models.Sum('montant'))['invest']
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
            query = query.filter(ope__rapp__isnull=False)
        if datel:
            query = query.filter(date__lte=datel)
        if exclude_id:
            query = query.exclude(pk=exclude_id)
        nombre = query.aggregate(nombre=models.Sum('nombre'))['nombre']
        if not nombre:
            return 0
        else:
            return decimal.Decimal(smart_unicode(nombre))

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
        opes = Ope.objects.filter(tiers=self.tiers, date__lte=datel)
        # si on a defini sur seulement un compte
        if compte:
            opes = opes.filter(compte=compte)
        # si on veut juste l'encours des ope rapp
        if rapp:
            opes = opes.filter(rapp__isnull=False)
        if opes.exists():
            if rapp:
                date_cours = opes.latest('date').date
            else:
                date_cours = datel

            # recupere le dernier cours
            cours = self.last_cours(datel=date_cours)
            # renvoie la gestion des param de nb
            nb = self.nb(compte=compte, rapp=rapp, datel=datel)
            return nb * cours
        else:
            return 0  # comme pas d'ope, pas d'encours


class Cours(models.Model):
    """cours des titres"""
    date = models.DateField(default=utils.today)
    valeur = models_gsb.CurField(default=1.000, decimal_places=3)
    titre = models.ForeignKey(Titre)
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_cours'
        verbose_name_plural = u'cours'
        unique_together = ("titre", "date")
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
        return u"le %(date)s, 1 %(titre)s : %(valeur)s %(monnaie)s" % {'titre': self.titre.nom,
                                                                       'date': self.date.strftime('%d/%m/%Y'),
                                                                       'valeur': self.valeur,
                                                                       'monnaie': settings.DEVISE_GENERALE}


class Banque(models.Model):
    """banques"""
    cib = models.CharField(max_length=5, blank=True)
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    notes = models.TextField(blank=True, default='')
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_banque'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne cette banque  avec la banque new
        @param new: banque
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        nb_change = Compte.objects.filter(banque=self).update(banque=new)
        self.delete()
        return nb_change


class Cat(models.Model):
    """categories
    les sous categories n'existent pas en tant que tel, ce sont justes des categories plus longues"""
    typesdep = (
        ('r', u'recette'),
        ('d', u'dépense'),
        ('v', u'virement'))
    nom = models.CharField(max_length=50, unique=True, verbose_name=u"nom de la catégorie", db_index=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d', verbose_name=u"type de la catégorie")
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_cat'
        verbose_name = u"catégorie"
        ordering = ['nom']

    def __unicode__(self):
        return u"%s(%s)" % (self.nom, self.type)

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne cette cat  avec la cat new
        @param new: cat
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        if self.type != new.type:
            raise TypeError(u"pas le même type de catégorie, %s est %s alors que %s est %s" % (
                self.nom, self.type, new.nom, new.type))
        nb_change = Echeance.objects.filter(cat=self).update(cat=new)
        nb_change += Ope.objects.filter(cat=self).update(cat=new)
        self.delete()
        return nb_change


class Ib(models.Model):
    """imputations budgetaires
     c'est juste un deuxieme type de categories ou apparentes"""
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    type = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
        ordering = ['type', 'nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne cette ib avec l'ib new
        @param new: ib
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        if self.type != new.type:
            raise TypeError(u"pas le même type de ib, %s est %s alors que %s est %s" % (
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
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_exercice'
        ordering = ['-date_debut']
        get_latest_by = 'date_debut'

    def __unicode__(self):
        return u"%s au %s" % (self.date_debut.strftime("%d/%m/%Y"), self.date_fin.strftime("%d/%m/%Y"))

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne cet exercice avec l'exercice new
        @param new: exercice
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
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
        ('b', u'bancaire'),
        ('e', u'espece'),
        ('p', u'passif'),
        ('t', u'titre'),
        ('a', u'autre actif'))
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    titulaire = models.CharField(max_length=40, blank=True, default='')
    type = models.CharField(max_length=1, choices=typescpt, default='b')
    banque = models.ForeignKey(Banque, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    guichet = models.CharField(max_length=15, blank=True, default='')
    # il est en charfield comme celui d'en dessous parce qu'on n'est pas sur qu'il n y ait que des chiffres
    num_compte = models.CharField(max_length=20, blank=True, default='')
    cle_compte = models.IntegerField(null=True, blank=True, default=0)
    solde_init = models_gsb.CurField(default=decimal.Decimal('0.00'))
    solde_mini_voulu = models_gsb.CurField(null=True, blank=True)
    solde_mini_autorise = models_gsb.CurField(null=True, blank=True)
    ouvert = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    moyen_credit_defaut = models.ForeignKey('Moyen',
                                             null=True,
                                             blank=True,
                                             on_delete=models.PROTECT,
                                             related_name="compte_moyen_credit_set",
                                             default=None,
                                             limit_choices_to={'type':"r"})
    moyen_debit_defaut = models.ForeignKey('Moyen',
                                             null=True,
                                             blank=True,
                                             on_delete=models.PROTECT,
                                             related_name="compte_moyen_debit_set",
                                             default=None,
                                             limit_choices_to={'type':"d"})
    titre = models.ManyToManyField('Titre', through="Ope_titre")
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_compte'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    def solde(self, datel=None, rapp=False, espece=False, pointe=False):
        """renvoie le solde du compte
            @param datel : date date limite de calcul du solde
            @param rapp : boolean faut il prendre uniquement les opération rapproches
            @param espece : si c'est un compte espece d'un compte titre
        """
        query = Ope.non_meres().filter(compte__id__exact=self.id)
        if rapp:
            query = query.filter(rapp__id__isnull=False)
        if pointe:
            query = query.filter(pointe=True)
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
            solde = solde + self.solde_titre(datel, rapp)
        return solde

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne deux compte, verifie avant que c'est le même type
        @param new: Compte
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        if new.type != self.type:
            raise Gsb_exc(u"attention ce ne sont pas deux compte de même type")
        if not(self.ouvert and new.ouvert):
            raise Gsb_exc(u"attention un des deux comptes est fermé")
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
        return self.solde(rapp=True)

    def solde_pointe(self, espece=False):
        """renvoie le solde du compte pour les operations pointees
        """
        solde = self.solde(espece=espece, pointe=True)
        return solde

    solde_rappro.short_description = u"solde rapproché"

    def date_rappro(self):
        """
        date de rapprochement cad date du rapprochement de la plus recente des ope rapproches
        @return: date or None
        """
        try:
            opes = Ope.objects.filter(compte__id=self.id).filter(rapp__isnull=False).select_related('rapp').latest('date')
            return opes.rapp.date
        except Ope.DoesNotExist:
            return None

    date_rappro.short_description = u"date dernier rapp"

    @transaction.commit_on_success
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
            if decimal.Decimal(force_unicode(frais)):  # des frais bancaires existent
                if not cat_frais:
                    cat_frais = Cat.objects.get(nom=u"Frais bancaires")
                if not tiers_frais:
                    tiers_frais = titre.tiers

                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=tiers_frais,
                                    cat=cat_frais,
                                    notes=u"Frais %s@%s" % (nombre, prix),
                                    moyen=self.moyen_debit(),
                                    automatique=True
                                    )
                # gestion compta matiere (et donc opération sous jacente et cours)
            ope_titre = Ope_titre.objects.create(titre=titre,
                                                 compte=self,
                                                 nombre=decimal.Decimal(force_unicode(nombre)),
                                                 date=date,
                                                 cours=prix)
            # virement
            if virement_de:
                vir = Virement()
                vir.create(compte_origine=virement_de,
                           compte_dest=self,
                           montant=decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)) + frais,
                           date=date)
            return ope_titre
        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def vente(self, titre, nombre, prix=1, date=None, frais=0, virement_vers=None, cat_frais=None, tiers_frais=None):
        """fonction pour vente de titre:
        @param titre
        @param nombre
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
                raise Titre.DoesNotExist(u'titre pas en portefeuille au %s' % date)
                # compta matiere
            ope_titre = Ope_titre.objects.create(titre=titre,
                                                 compte=self,
                                                 nombre=decimal.Decimal(force_unicode(nombre)) * -1,
                                                 date=date,
                                                 cours=prix)
            if decimal.Decimal(force_unicode(frais)):
                if not cat_frais:
                    cat_frais = Cat.objects.get(nom=u"Frais bancaires")
                if not tiers_frais:
                    tiers_frais = titre.tiers
                self.ope_set.create(date=date,
                                    montant=abs(decimal.Decimal(force_unicode(frais))) * -1,
                                    tiers=tiers_frais,
                                    cat=cat_frais,
                                    notes="frais -%s@%s" % (nombre, prix),
                                    moyen=self.moyen_debit(),
                                    automatique=True
                                    )
            if virement_vers:
                vir = Virement()
                vir.create(compte_origine=self,
                           compte_dest=virement_vers,
                           montant=decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)) - frais,
                           date=date)
            return ope_titre
        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def revenu(self, titre, montant=1, date=None, frais=0, virement_vers=None, cat_frais=None, tiers_frais=None):
        """fonction pour ost de titre:"""
        if date is None:
            date = utils.today()
        self.alters_data = True
        if isinstance(titre, Titre):
            # extraction des titres dans portefeuille
            nb_titre_avant = titre.nb(compte=self, datel=date)
            if not nb_titre_avant:
                raise Titre.DoesNotExist(u'titre pas en portefeuille au %s' % date)
                # ajout du revenu proprement dit
            self.ope_set.create(date=date,
                                montant=decimal.Decimal(force_unicode(montant)),
                                tiers=titre.tiers,
                                cat=Cat.objects.get(id=settings.ID_CAT_OST),
                                notes="revenu",
                                moyen=self.moyen_credit(),
                                # on ne prend le moyen par defaut car ce n'est pas une OST
                                automatique=True)
            if decimal.Decimal(force_unicode(frais)):
                if not tiers_frais:
                    tiers_frais = titre.tiers
                if not cat_frais:
                    cat_frais = Cat.objects.get(nom=u"Frais bancaires")
                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=tiers_frais,
                                    cat=cat_frais,
                                    notes="frais revenu",
                                    moyen=self.moyen_debit(),
                                    automatique=True
                )
            if virement_vers:
                vir = Virement()
                vir.create(self, virement_vers, decimal.Decimal(force_unicode(montant)) - frais, date)
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
            return Moyen.objects.get(id=settings.MD_DEBIT)

    def moyen_credit(self):
        if self.moyen_credit_defaut is not None:
            return self.moyen_credit_defaut
        else:
            return Moyen.objects.get(id=settings.MD_CREDIT)


class Ope_titre(models.Model):
    """ope titre en compta matiere"""
    titre = models.ForeignKey(Titre, on_delete=models.CASCADE)
    compte = models.ForeignKey(Compte, verbose_name=u"compte titre", limit_choices_to={'type':'t'})
    nombre = models_gsb.CurField(default=0, decimal_places=5)
    date = models.DateField()
    cours = models_gsb.CurField(default=1, decimal_places=5)
    invest = models_gsb.CurField(default=0, editable=False, decimal_places=2)
    ope = models.OneToOneField('Ope',
                               editable=False,
                               null=True,
                               on_delete=models.CASCADE,
                               related_name="ope")  # null=true car j'ai des operations sans lien
    ope_pmv = models.OneToOneField('Ope',
                                   editable=False,
                                   null=True,
                                   on_delete=models.CASCADE,
                                   related_name="ope_pmv")  # null=true cr tt les operation d'achat sont null
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_ope_titre'
        verbose_name_plural = u'Opérations titres(compta_matiere)'
        verbose_name = u'Opérations titres(compta_matiere)'
        ordering = ['-date']

    def save(self, *args, **kwargs):
        self.cours = decimal.Decimal(self.cours)
        self.nombre = decimal.Decimal(self.nombre)
        # definition des cat avec possibilite
        cat_ost = Cat.objects.get(id=settings.ID_CAT_OST)
        cat_pmv = Cat.objects.get(id=settings.ID_CAT_PMV)
        # gestion de la date
        # self.date = utils.strpdate(self.date)

        # gestion des cours
        # si on chnage la date de l'operation il faut supprimer le cours associe
        if self.ope:
            old_date = self.ope.date
            Cours.objects.get(titre=self.titre, date=old_date).delete()
        Cours.objects.get_or_create(titre=self.titre, date=self.date, defaults={'titre': self.titre, 'date': self.date, 'valeur': self.cours})
        self.invest = decimal.Decimal(force_unicode(self.cours)) * decimal.Decimal(force_unicode(self.nombre))
        if self.nombre >= 0:  # on doit separer because gestion des plues ou moins value
            if self.ope_pmv is not None:
                self.ope_pmv.delete()  # comme achat, il n'y a pas de plus ou moins value exteriosée donc on efface
            if self.ope is None:  # il faut creer l'ope sous jacente
                self.ope = Ope.objects.create(date=self.date,
                                              montant=self.cours * self.nombre * -1,
                                              tiers=self.titre.tiers,
                                              cat=cat_ost,
                                              notes="%s@%s" % (self.nombre, self.cours),
                                              moyen=self.compte.moyen_debit(),
                                              compte=self.compte,
                )

            else:  # la modifier juste
                self.ope.date = self.date
                self.ope.montant = self.cours * self.nombre * -1
                self.ope.tiers = self.titre.tiers
                self.ope.notes = "%s@%s" % (self.nombre, self.cours)
                self.ope.compte = self.compte
                self.ope.save()
        else:  # c'est une vente
            # calcul prealable
            # on met des plus car les chiffres sont negatif
            if self.ope:  # ope existe deja, donc il faut faire attention car les montant inv sont faux
                inv_vrai = self.titre.investi(self.compte, datel=self.date, exclude_id=self)
                nb_vrai = self.titre.nb(self.compte, datel=self.date, exclude_id=self.id)
            else:
                inv_vrai = self.titre.investi(self.compte, datel=self.date)
                nb_vrai = self.titre.nb(self.compte, datel=self.date)
                # chaine car comme on a des decimal
            ost = "{0:.2f}".format((inv_vrai / nb_vrai) * self.nombre)
            ost = decimal.Decimal(ost) * -1
            pmv = abs(self.invest) - abs(ost)
            # on cree les ope
            if not self.ope:
                self.ope = Ope.objects.create(date=self.date,
                                              montant=ost,
                                              tiers=self.titre.tiers,
                                              cat=cat_ost,
                                              notes="%s@%s" % (self.nombre, self.cours),
                                              moyen=self.compte.moyen_credit(),
                                              compte=self.compte,
                )

            else:
                self.ope.date = self.date
                self.ope.montant = ost
                self.ope.tiers = self.titre.tiers
                self.ope.notes = "%s@%s" % (self.nombre, self.cours)
                self.ope.compte = self.compte
                self.ope.moyen = self.compte.moyen_credit()
                self.ope.save()
            if self.ope_pmv is None:
                self.ope_pmv = Ope.objects.create(date=self.date,
                                                  montant=pmv,
                                                  tiers=self.titre.tiers,
                                                  cat=cat_pmv,
                                                  notes="%s@%s" % (self.nombre, self.cours),
                                                  moyen=self.compte.moyen_credit(),
                                                  compte=self.compte,
                )
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
        super(Ope_titre, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.ope is not None:
            if self.ope.rapp is not None:
                raise IntegrityError(u"opération espèce rapprochée")
        if self.ope_pmv is not None:
            if self.ope_pmv.rapp is not None:
                raise IntegrityError(u"opération pmv rapprochée")
        super(Ope_titre, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('ope_titre_detail', kwargs={'pk': str(self.id)})

    def __unicode__(self):
        if self.nombre > 0:
            sens = "achat"
        else:
            sens = "vente"
        chaine = u"(%s) %s de %s %s à %s %s le %s cpt:%s" % (self.id, sens, abs(self.nombre), self.titre, self.cours, settings.DEVISE_GENERALE, self.date.strftime('%d/%m/%Y'), self.compte)
        return chaine


class Moyen(models.Model):
    """moyen de paiements
    commun à l'ensembles des comptes
    actuellement, les comptes ont tous les moyens sans possiblite de faire le tri
    """
    # on le garde pour l'instant car ce n'est pas dans le même ordre que pour les categories
    typesdep = (('v', u'virement'),
                ('d', u'depense'),
                ('r', u'recette'),
                )
    nom = models.CharField(max_length=40, unique=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d')
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_moyen'
        verbose_name = u"moyen de paiment"
        verbose_name_plural = u"moyens de paiment"
        ordering = ['nom']

    def __unicode__(self):
        return u"%s (%s)" % (self.nom, self.type)

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne ce Moyen avec le Moyen new
        @param new: Moyen
        """
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        if self.id == settings.MD_CREDIT or self.id == settings.MD_DEBIT:
            raise ValueError(u"impossible de le fusionner car il est un moyen par défault dans les settings")
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
            raise IntegrityError(u"moyen par defaut")
        super(Moyen, self).delete(*args, **kwargs)


class Rapp(models.Model):
    """rapprochement d'un compte"""
    nom = models.CharField(max_length=40, unique=True, db_index=True)
    date = models.DateField(null=True, blank=True, default=utils.today)
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_rapp'
        verbose_name = u"rapprochement"
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
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

    def fusionne(self, new):
        """fusionnne ce Rapp avec le Rapp new
        @param new: Rapp
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui mème")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        nb_change = Ope.objects.filter(rapp=self).update(rapp=new)
        self.delete()
        return nb_change


class Echeance(models.Model):
    """echeance 'opération future prevue
    soit unique
    soit repete
    """
    typesperiod = (
        ('u', u'unique'),
        ('s', u'semaine'),
        ('m', u'mois'),
        ('a', u'année'),
        ('j', u'jour'),
        )

    date = models.DateField(default=utils.today)
    date_limite = models.DateField(null=True, blank=True, default=None)
    intervalle = models.IntegerField(default=1)
    periodicite = models.CharField(max_length=1, choices=typesperiod, default="u")
    valide = models.BooleanField(default=True)
    compte = models.ForeignKey(Compte)
    montant = models_gsb.CurField()
    tiers = models.ForeignKey(Tiers, on_delete=models.PROTECT)
    cat = models.ForeignKey(Cat, on_delete=models.PROTECT, verbose_name=u"catégorie")
    moyen = models.ForeignKey(Moyen, blank=False, on_delete=models.PROTECT, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name=u"imputation")
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name='echeance_virement_set', default=None)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True, related_name='echeance_moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    notes = models.TextField(blank=True, default='')
    inscription_automatique = models.BooleanField(default=False, help_text=u"inutile")  # tt les echeances sont automatiques
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"echéances"
        ordering = ['date']
        get_latest_by = 'date'

    def __unicode__(self):
        if self.compte_virement:
            return u"(%s) %s=>%s de %s (ech:%s)" % (self.id,
                                                    self.compte,
                                                    self.compte_virement,
                                                    self.montant,
                                                    self.date.strftime('%d/%m/%Y'))
        else:
            return u"(%s) %s à %s de %s (ech:%s)" % (self.id, self.compte, self.tiers, self.montant, self.date.strftime('%d/%m/%Y'))

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
    @transaction.commit_on_success
    def check(request=None, queryset=None, to=None):
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
                    vir = Virement.create(compte_origine=ech.compte,
                                          compte_dest=ech.compte_virement,
                                          montant=ech.montant,
                                          date=ech.date
                    )
                    vir.auto = True
                    vir.exercice = ech.exercice
                    vir.save()
                    if request is not None:
                        messages.info(request, u'virement (%s)%s crée' % (vir.origine.id, vir.origine.tiers))
                else:
                    ope = Ope.objects.create(compte_id=ech.compte_id,
                                             date=ech.date,
                                             montant=ech.montant,
                                             tiers_id=ech.tiers_id,
                                             cat_id=ech.cat_id,
                                             automatique=True,
                                             ib_id=ech.ib_id,
                                             moyen_id=ech.moyen_id,
                                             exercice_id=ech.exercice_id
                    )
                    if request is not None:
                        messages.info(request, u'opération "%s" crée' % ope)
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
            raise ValidationError(u"pas possible de mettre un même compte en virement et compte de base")
        super(Echeance, self).clean()

    def save(self, force_insert=False, force_update=False, using=None):
        self.clean()
        super(Echeance, self).save(force_insert, force_update, using)


class Ope(models.Model):
    """operation"""
    compte = models.ForeignKey(Compte)
    date = models.DateField(default=utils.today)
    date_val = models.DateField(null=True, blank=True, default=None)
    montant = models_gsb.CurField()
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.PROTECT, default=None, verbose_name=u"Catégorie")
    notes = models.TextField(blank=True, default='')
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    num_cheque = models.CharField(max_length=20, blank=True, default='')
    pointe = models.BooleanField(default=False)
    rapp = models.ForeignKey(Rapp, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name=u'Rapprochement')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name=u"projet")
    jumelle = models.OneToOneField('self', null=True, blank=True, related_name='jumelle_set', default=None, editable=False, on_delete=models.CASCADE)
    mere = models.ForeignKey('self', null=True, blank=True, related_name='filles_set', default=None, on_delete=models.PROTECT, verbose_name=u'Mere')
    automatique = models.BooleanField(default=False, help_text=u'si cette opération est crée a cause d\'une echeance')
    piece_comptable = models.CharField(max_length=20, blank=True, default='')
    lastupdate = models_gsb.ModificationDateTimeField()
    uuid = models_gsb.uuidfield(auto=True, add=True)

    class Meta:
        db_table = 'gsb_ope'
        get_latest_by = 'date'
        order_with_respect_to = 'compte'
        verbose_name = u"opération"
        ordering = ['-date']
        permissions = (
            ('can_import', 'peut importer des fichiers'),
            ('can_export', 'peut exporter des fichiers'),
            )

    @staticmethod
    def non_meres():
        """ renvoie uniquement les opération non mere
        """
        return Ope.objects.all().filter(filles_set__isnull=True)

    @staticmethod
    def solde_set(q):
        if not q.exists():
            return 0
        return q.aggregate(total=models.Sum('montant'))['total']

    def __unicode__(self):
        return u"(%s) le %s : %s %s a %s cpt: %s" % (
            self.id,
            self.date.strftime('%d/%m/%Y'),
            self.montant,
            settings.DEVISE_GENERALE,
            self.tiers,
            self.compte
            )

    def get_absolute_url(self):
        return reverse('gsb_ope_detail', kwargs={'pk': str(self.id)})

    def clean(self):
        self.alters_data = True
        self.deja_clean = True
        super(Ope, self).clean()
        # verification qu'il n'y pas pointe et rapprochee
        if self.pointe and self.rapp is not None:
            raise ValidationError(u"cette opération ne peut pas etre à la fois pointée et rapprochée")
        if not self.compte.ouvert:
            raise ValidationError(u"cette opération ne peut pas être modifié car le compte est fermé")
        if self.is_mere:
            if has_changed(self, 'cat'):
                self.cat = Cat.objects.get(nom=u"Opération Ventilée")
            if has_changed(self, 'montant'):
                # ensemble des opefilles
                opes = self.filles_set.all()
                for o in opes.values('id', 'pointe', 'rapp'):
                    if o['pointe'] == True:
                        raise ValidationError(u"impossible de modifier l'opération car au moins une partie est pointée")
                    if o['rapp'] is not None:
                        raise ValidationError(u"impossible de modifier l'opération car au moins une partie est rapprochée")
                if self.pointe:
                    raise ValidationError(u"impossible de modifier l'opération car au moins une partie est pointée")
                if self.rapp is not None:
                    raise ValidationError(u"impossible de modifier l'opération car au moins une partie est rapprochée")

        if self.is_fille:
            if has_changed(self, 'montant'):
                mere = self.mere
                # ensemble des opefilles de la mere
                opes = Ope.objects.filter(mere_id=mere.id)
                for o in opes.values('id', 'pointe', 'rapp'):
                    if o['pointe'] == True:
                        raise ValidationError(u"impossible de modifier l'opération car au moins une partie est pointée")
                    if o['rapp'] is not None:
                        raise ValidationError(u"impossible de modifier l'opération car au moins une partie est rapprochée")
                if self.pointe or mere.pointe:
                    raise ValidationError(u"impossible de modifier l'opération car au moins une partie est pointée")
                if self.rapp is not None or mere.rapp is not None:
                    raise ValidationError(u"impossible de modifier l'opération car au moins une partie est rapprochée")

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
        if self.rapp:
            return False
        if self.compte.ouvert is False:
            return False
        else:
            if self.jumelle:
                if self.jumelle.rapp:
                    return False
            return True

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
        if self.moyen.type == u'd' and self.montant > 0:
            self.montant = self.montant * -1
        super(Ope, self).save(*args, **kwargs)


@receiver(post_save, sender=Ope, weak=False)
def ope_fille(sender, **kwargs):
    if kwargs['raw'] == True:
        return
    self = kwargs['instance']
    if self.is_fille:
        self.mere.save()


@receiver(pre_delete, sender=Ope, weak=False)
def verif_ope_rapp(sender, **kwargs):
    instance = kwargs['instance']
    # on evite que cela soit une opération rapproche
    if instance.rapp:
        raise IntegrityError(u"opération rapprochee")
    if instance.jumelle:
        if instance.jumelle.rapp:
            raise IntegrityError(u"opération jumelle rapprochée")
    if instance.mere:
        if instance.mere.rapp:
            raise IntegrityError(u"opération mere rapprochée")
    if instance.filles_set.count() > 0:
        raise IntegrityError(u"opérations filles existantes %s" % instance.filles_set.all())


class Virement(object):
    """raccourci pour creer un virement entre deux comptes"""

    def __init__(self, ope=None):

        if ope:
            if type(ope) != type(Ope()):
                raise TypeError('pas ope')
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
            tier = Tiers.objects.get_or_create(nom=self.__unicode__(), defaults={'nom': self.__unicode__()})[0]
            self.origine.tiers = tier
            self.dest.tiers = tier
            self.origine.cat = Cat.objects.get(nom="Virement")
            self.dest.cat = self.origine.cat
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
            raise TypeError(u'pas compte')
        if not isinstance(compte_dest, Compte):
            raise TypeError(u'pas compte')
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
            tab = {'compte_origine': self.origine.compte.id,
                   'compte_destination': self.dest.compte.id,
                   'montant': self.montant,
                   'date': self.date,
                   'notes': self.notes,
                   'pointe': self.pointe}
            if self.origine.moyen:
                tab['moyen_origine'] = self.origine.moyen.id
            else:
                tab['moyen_origine'] = Moyen.objects.filter(type='v')[0]
            if self.dest.moyen:
                tab['moyen_destination'] = self.dest.moyen.id
            else:
                tab['moyen_destination'] = Moyen.objects.filter(type='v')[0]
        else:
            raise Gsb_exc(u'attention, on ne peut intialiser un form que si virement est bound')
        return tab

    def __unicode__(self):
        return u"%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)

