# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.db import models
import datetime
import decimal
from django.db import transaction, IntegrityError
from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils.encoding import force_unicode
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.db.models import Q
from django.core.exceptions import ImproperlyConfigured
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.utils.encoding import smart_unicode
from .model_field import CurField
from . import utils
import logging
class Gsb_exc(Exception):
    pass


class Ex_jumelle_neant(Exception):
    pass

#import logging

class Tiers(models.Model):
    """
    un tiers, c'est a dire une personne ou un titre
    pour les titres, c'est remplis dans le champ note avec TYPE@ISIN
    """

    nom = models.CharField(max_length=40, unique=True)
    notes = models.TextField(blank=True, default='')
    is_titre = models.BooleanField(default=False)

    class Meta:
        db_table = 'gsb_tiers'
        verbose_name_plural = u'tiers'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne tiers vers new tiers
        @param new: tiers
        """
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        nb_tiers_change = Echeance.objects.filter(tiers=self).update(tiers=new)
        nb_tiers_change += Ope.objects.filter(tiers=self).update(tiers=new)
        self.delete()
        return nb_tiers_change


class Titre(models.Model):
    """
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
        ('ZZZ', u'autre')
        )
    nom = models.CharField(max_length=40, unique=True)
    isin = models.CharField(max_length=12, unique=True)
    tiers = models.OneToOneField(Tiers, null=True, blank=True, editable=False)
    type = models.CharField(max_length=3, choices=typestitres, default='ZZZ')

    class Meta:
        db_table = u'gsb_titre'
        ordering = ['nom']

    def __unicode__(self):
        return u"%s (%s)" % (self.nom, self.isin)

    def last_cours(self, rapp=False):
        """renvoie le dernier cours"""
        date = self.last_cours_date(rapp=rapp)
        if date:
            return self.cours_set.get(date=date).valeur
        else:
            return 0

    def last_cours_date(self, rapp=False):
        """renvoie la date du dernier cours"""
        if not rapp:
            return self.cours_set.latest('date').date
        else:
            opes = Ope.objects.filter(tiers=self.tiers).filter(rapp__isnull=False)
            if opes.exists():
                date_ope = opes.latest('date').date
                date_rapp = opes.latest('date').rapp.date
                liste = Cours.objects.filter(titre=self).filter(date__in=[date_ope, date_rapp])
                if liste.exists():
                    return liste.latest('date').date
                else:
                    return None
            else:
                return None

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne ce titre avec le titre new"""
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
                        u"attention les titre %s et %s ne peuvent etre fusionnés car pas les même histo de cours" % (self, new))
            except Cours.DoesNotExist:
                new.cours_set.create(date=cours.date, valeur=cours.valeur)
        nb_change = 0
        nb_change += Ope_titre.objects.filter(titre=self).update(titre=new)
        #on doit aussi reaffecter le tiers associe
        self.tiers.fusionne(new.tiers)
        self.delete()
        return nb_change

    def save(self, *args, **kwargs):
        self.alters_data = True
        if not self.tiers:
            self.tiers = Tiers.objects.get_or_create(nom='titre_ %s' % self.nom,
                                                     defaults={"nom":'titre_ %s' % self.nom, "is_titre":True,
                                                               "notes":"%s@%s" % (self.isin, self.type)})[0]
        if self.tiers.notes != u"%s@%s" % (self.isin, self.type):
            self.tiers.notes = u"%s@%s" % (self.isin, self.type)
            self.tiers.save()
        super(Titre, self).save(*args, **kwargs)

    def investi(self, compte=None, datel=None, rapp=None, exclude_id=None):
        """renvoie le montant investi
        @param compte: Compte , si None, renvoie sur  l'ensemble des comptes titres
        @param datel: date, renvoie sur avant la date ou tout si none
        @param rapp: Bool, si true, renvoie uniquement les opération rapprochées
        """
        query = Ope.non_meres().filter(tiers=self.tiers).exclude(cat__id=settings.ID_CAT_PMV)
        if compte:
            query = query.filter(compte=compte)
        if datel:
            query = query.filter(date__lte=datel)
        if rapp:
            query = query.filter(rapp__isnull=False)
        if exclude_id:
            query = query.exclude(pk=exclude_id)
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

    def encours(self, compte=None, datel=None, rapp=False, p=False):
        """
        renvoie l'encours detenu dans ce titre dans un compte ou dans tous les comptes si pas de compte donné
        @param compte: objet compte
        @param datel: chaine au format "aaaa-mm-dd" ou date
        @param rapp: boolean, renvoie les operation rapproches, attention, si rempli, cela renvoie l'encours avec le cours rapproche
        @param p: boolean idem que pour rapp mais avec les operations pointee
        """
        if datel and (not self.cours_set.filter(date__lte=datel).exists()):
            return 0
        opes = Ope.objects.filter(tiers=self.tiers)
        if compte:
            opes = opes.filter(compte=compte)
        if rapp:
            #recup de la derniere date
            opes = opes.filter(tiers=self.tiers).filter(rapp__isnull=False)
            if opes.exists():
                liste = []
                if datel:
                    liste.append(utils.strpdate(datel))
                liste.append(self.last_cours_date(rapp=rapp))
                date_r = min(liste)
                if date_r == None:
                    return 0
            else:
                return 0 #comme pas d'ope, pas d'encours
        else:
            if datel:
                date_r = datel
            else:
                date_r = datetime.date.today()
        if opes.exists():
            #recupere la derniere date, attention ce n'est pas necessairement la derniere date d'opération
            cours = self.cours_set.filter(date__lte=date_r).latest().valeur
        else:
            return 0 #comme pas d'ope, pas d'encours
        #renvoie la gestion des param de nb
        nb = self.nb(compte=compte, rapp=rapp, datel=datel)
        return nb * cours


class Cours(models.Model):
    """cours des titres"""
    valeur = CurField(default=1.000, decimal_places=3)
    titre = models.ForeignKey(Titre)
    date = models.DateField(default=datetime.date.today)

    class Meta:
        db_table = 'gsb_cours'
        verbose_name_plural = u'cours'
        unique_together = ("titre", "date")
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
        return u"le %(date)s, 1 %(titre)s : %(valeur)s" % {'titre':self.titre.nom,
                                                           'date':self.date,
                                                           'valeur':self.valeur}


class Banque(models.Model):
    """banques"""
    cib = models.CharField(max_length=5, blank=True)
    nom = models.CharField(max_length=40, unique=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'gsb_banque'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
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
        ('v', u'virement')
        )
    nom = models.CharField(max_length=50, unique=True, verbose_name=u"nom de la catégorie")
    type = models.CharField(max_length=1, choices=typesdep, default='d', verbose_name=u"type de la catégorie")

    class Meta:
        db_table = 'gsb_cat'
        verbose_name = u"catégorie"
        ordering = ['nom']

    def __unicode__(self):
        return "%s(%s)" % (self.nom, self.type)

    @transaction.commit_on_success
    def fusionne(self, new):
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
    nom = models.CharField(max_length=40, unique=True)
    type = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')

    class Meta:
        db_table = 'gsb_ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
        ordering = ['type', 'nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        if self.type != new.type:
            raise TypeError(u"pas le même type de titre")
        nb_change = Echeance.objects.filter(ib=self).update(ib=new)
        nb_change += Ope.objects.filter(ib=self).update(ib=new)
        self.delete()
        return nb_change


class Exercice(models.Model):
    """listes des exercices des comptes
    attention, il ne faut confondre exercice et rapp. les exercices sont les même pour tous les comptes alors q'un rapp est pour un seul compte
    """
    date_debut = models.DateField(default=datetime.date.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = 'gsb_exercice'
        ordering = ['-date_debut']
        get_latest_by = 'date_debut'

    def __unicode__(self):
        return u"%s au %s" % (self.date_debut.strftime("%d/%m/%Y"), self.date_fin.strftime("%d/%m/%Y"))

    @transaction.commit_on_success
    def fusionne(self, new):
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
    attention les comptes de type "t" ne peuvent etre cree directement
    """
    typescpt = (
        ('b', u'bancaire'),
        ('e', u'espece'),
        ('p', u'passif'),
        ('t', u'titre'),
        ('a', u'autre actif')
        )
    nom = models.CharField(max_length=40, unique=True)
    titulaire = models.CharField(max_length=40, blank=True, default='')
    type = models.CharField(max_length=1, choices=typescpt, default='b')
    banque = models.ForeignKey(Banque, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    guichet = models.CharField(max_length=15, blank=True, default='')
    #il est en charfield comme celui d'en dessous parce qu'on n'est pas sur qu'il n y ait que des chiffres
    num_compte = models.CharField(max_length=20, blank=True, default='')
    cle_compte = models.IntegerField(null=True, blank=True, default=0)
    solde_init = CurField(default=decimal.Decimal('0.00'))
    solde_mini_voulu = CurField(null=True, blank=True)
    solde_mini_autorise = CurField(null=True, blank=True)
    ouvert = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    moyen_credit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name="compte_moyen_credit_set", default=None)
    moyen_debit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL,
                                           related_name="compte_moyen_debit_set", default=None)

    class Meta:
        db_table = 'gsb_compte'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    def solde(self, datel=None, rapp=False):
        """renvoie le solde du compte
            @param datel date date limite de calcul du solde
            @param rapp boolean faut il prendre uniquement les opération rapproches
        """
        query = Ope.non_meres().filter(compte__id__exact=self.id)
        if rapp:
            query = query.filter(rapp__isnull=False)
        if datel:
            query = query.filter(date__lte=datel)
        req = query.aggregate(solde=models.Sum('montant'))
        if req['solde'] is None:
            solde = decimal.Decimal(0) + decimal.Decimal(self.solde_init)
        else:
            solde = decimal.Decimal(req['solde']) + decimal.Decimal(self.solde_init)
        return solde

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne deux compte, verifie avant que c'est le même type
        @param new
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
        if self.type == 't':
            nb_change = Compte_titre.objects.get(id=self.id).fusionne(Compte_titre.objects.get(id=new.id))
        else:
            nb_change = Echeance.objects.filter(compte=self).update(compte=new)
            nb_change += Echeance.objects.filter(compte_virement=self).update(compte_virement=new)
            nb_change += Ope.objects.filter(compte=self).update(compte=new)
            self.delete()
        return nb_change

    @models.permalink
    def get_absolute_url(self):
        return 'gsb_cpt_detail', (), {'cpt_id':str(self.id)}

    def save(self, *args, **kwargs):
        """verifie qu'on ne cree pas un compte avec le type 't'"""
        self.alters_data = True
        if self.type == 't' and not isinstance(self, Compte_titre) and not self.id:
            cpt = Compte_titre.objects.create(nom=self.nom, titulaire=self.titulaire, type=self.type,
                                              banque=self.banque,
                                              guichet=self.guichet, num_compte=self.num_compte,
                                              cle_compte=self.cle_compte,
                                              solde_init=self.solde_init, solde_mini_voulu=self.solde_mini_voulu,
                                              solde_mini_autorise=self.solde_mini_autorise, ouvert=self.ouvert,
                                              notes=self.notes, moyen_credit_defaut=self.moyen_credit_defaut,
                                              moyen_debit_defaut=self.moyen_credit_defaut
            )
        else:
            cpt = super(Compte, self).save(*args, **kwargs)
        return cpt

    def solde_rappro(self):
        return self.solde(rapp=True)

    def solde_pointe(self):
        """renvoie le solde du compte pour les operations pointees
              @param datel date date limite de calcul du solde
              @param rapp boolean faut il prendre uniquement les opération rapproches
        """
        query = Ope.non_meres().filter(compte__id__exact=self.id).filter(pointe=True)
        req = query.aggregate(solde=models.Sum('montant'))
        if req['solde'] is None:
            solde = decimal.Decimal(0) + decimal.Decimal(self.solde_init)
        else:
            solde = decimal.Decimal(req['solde']) + decimal.Decimal(self.solde_init)
        return solde


    solde_rappro.short_description = u"solde rapproché"

    def date_rappro(self):
        opes = Ope.objects.filter(compte__id=self.id).filter(rapp__isnull=False)
        if opes.exists():
            o = opes.latest('date')
            date_p = o.rapp.date
            return date_p
        else:
            return None #comme pas de date, pas d'encours

    date_rappro.short_description = u"date dernier rapp"


class Compte_titre(Compte ):
    """
    comptes titres
    compte de classe "t" avec des fonctions en plus. une compta matiere
    """
    titre = models.ManyToManyField('titre', through="Ope_titre")

    class Meta:
        db_table = 'gsb_cpt_titre'
        ordering = ['nom']
        verbose_name_plural = "Comptes Titre"

    #@transaction.commit_on_success
    def achat(self, titre, nombre, prix=1, date=datetime.date.today(), frais=0, virement_de=None, cat_frais=None, tiers_frais=None):
        """fonction pour achat de titre:
        @param titre:object titre
        @param nombre:decimal
        @param prix;decimal
        @param date:date
        @param frais:decimal
        @param virement_de: object compte
        """
        self.alters_data = True
        if isinstance(titre, Titre):
            if decimal.Decimal(force_unicode(frais)):  #des frais bancaires existent
                if not cat_frais:
                    cat_frais = Cat.objects.get_or_create(nom=u"frais bancaires:",
                                                          defaults={'nom':u'frais bancaires:'})[0]
                if not tiers_frais:
                    tiers_frais = titre.tiers
                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=tiers_frais,
                                    cat=cat_frais,
                                    notes=u"frais %s@%s" % (nombre, prix),
                                    moyen=Moyen.objects.get(id=settings.MD_DEBIT),
                                    automatique=True
                )
                #gestion compta matiere (et donc opération sous jacente et cours)
            Ope_titre.objects.create(titre=titre,
                                     compte=self,
                                     nombre=decimal.Decimal(force_unicode(nombre)),
                                     date=date,
                                     cours=prix)
            #virement
            if virement_de:
                vir = Virement()
                vir.create(virement_de, self,
                           decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)) + frais, date)
        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def vente(self, titre, nombre, prix=1, date=datetime.date.today(), frais=0, virement_vers=None, cat_frais=None, tiers_frais=None):
        """fonction pour vente de titre:
        @param titre
        @param nombre
        @param prix
        @param date
        @param frais
        @param virement_vers
        """
        self.alters_data = True
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            nb_titre_avant = titre.nb(compte=self, datel=date)
            if not nb_titre_avant or nb_titre_avant < nombre:
                raise Titre.DoesNotExist(u'titre pas en portefeuille')
                #compta matiere
            Ope_titre.objects.create(titre=titre,
                                     compte=self,
                                     nombre=decimal.Decimal(force_unicode(nombre)) * -1,
                                     date=date,
                                     cours=prix)
            if decimal.Decimal(force_unicode(frais)):
                if not cat_frais:
                    cat_frais = Cat.objects.get_or_create(nom=u"frais bancaires:",
                                                          defaults={'nom':u'frais bancaires:'})[0]
                if not tiers_frais:
                    tiers_frais = titre.tiers
                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=tiers_frais,
                                    cat=cat_frais,
                                    notes="frais -%s@%s" % (nombre, prix),
                                    moyen=Moyen.objects.get(id=settings.MD_DEBIT),
                                    automatique=True
                )
            if virement_vers:
                vir = Virement()
                vir.create(self,
                           virement_vers,
                           decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)) - frais,
                           date)
        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def revenu(self, titre, montant=1, date=datetime.date.today(), frais=0, virement_vers=None, cat_frais=None, tiers_frais=None):
        """fonction pour ost de titre:"""
        self.alters_data = True
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            nb_titre_avant = titre.nb(compte=self, datel=date)
            cat_ost = Cat.objects.get_or_create(id=settings.ID_CAT_OST, defaults={'nom':u'operation sur titre'})[0]
            if not nb_titre_avant:
                raise Titre.DoesNotExist(u'titre pas en portefeuille')
            self.ope_set.create(date=date,
                                montant=decimal.Decimal(force_unicode(montant)),
                                tiers=titre.tiers,
                                cat=cat_ost,
                                notes="revenu",
                                moyen=Moyen.objects.get(id=settings.MD_CREDIT),
                                automatique=True)
            if decimal.Decimal(force_unicode(frais)):
                if not tiers_frais:
                    tiers_frais = titre.tiers
                if not cat_frais:
                    cat_frais = Cat.objects.get_or_create(nom=u"frais bancaires", defaults={'nom':u'frais bancaires'})[0]
                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=tiers_frais,
                                    cat=cat_frais,
                                    notes="frais revenu",
                                    moyen=Moyen.objects.get(id=settings.MD_DEBIT),
                                    automatique=True
                )
            if virement_vers:
                vir = Virement()
                vir.create(self, virement_vers, decimal.Decimal(force_unicode(montant)) - frais, date)
        else:
            raise TypeError("pas un titre")

    def solde(self, datel=None, rapp=False):
        """renvoie le solde"""
        if rapp:
            solde_titre = self.solde_rappro()
        else:
            solde_titre = self.solde_titre(datel)
        solde_espece = self.solde_espece(datel, rapp)

        return solde_espece + solde_titre

    def solde_rappro(self):
        solde_titre = 0
        for titre in self.titre.all().distinct():
            solde_titre = solde_titre + titre.encours(compte=self, rapp=True)
        return solde_titre

    solde_rappro.short_description = u"solde titre rapproché"

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne deux compte_titre"""
        if new == self:
            raise ValueError(u"un objet ne peut etre fusionné sur lui même")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError(u"pas la même classe d'objet")
        nb_change = Echeance.objects.filter(compte=self).update(compte=new)
        nb_change += Ope_titre.objects.filter(compte=self).update(compte=new)
        nb_change += Echeance.objects.filter(compte_virement=self).update(compte_virement=new)
        nb_change += Ope.objects.filter(compte=self).update(compte=new)
        self.delete()
        return nb_change

    @models.permalink
    def get_absolute_url(self):
        return 'gsb_cpt_detail', (), {'cpt_id':str(self.id)}

    def save(self, *args, **kwargs):
        """verifie qu'on a pas changé le type de compte"""
        self.alters_data = True
        if self.type != 't':
            self.type = 't'
        super(Compte_titre, self).save(*args, **kwargs)

    def solde_espece(self, datel=None, rapp=False):
        return super(Compte_titre, self).solde(datel=datel, rapp=rapp)

    def solde_titre(self, datel=None, rapp=False):
        solde_titre = 0
        if rapp:
            return self.solde_rappro()
        for titre in self.titre.all().distinct():
            nb = titre.nb(compte=self, datel=datel)
            cours = titre.last_cours()
            solde_titre = solde_titre + nb * cours

        return solde_titre

    def liste_titre(self, datel=None, rapp=False):
        liste = []
        for i in self.titre.all().distinct():
            if i.nb(compte=self, datel=datel, rapp=rapp):
                liste.append(i.id)
        return Titre.objects.filter(id__in=liste)

class Ope_titre(models.Model):
    """ope titre en compta matiere"""
    titre = models.ForeignKey(Titre)
    compte = models.ForeignKey(Compte_titre, verbose_name=u"compte titre")
    nombre = CurField(default=0, decimal_places=5)
    date = models.DateField()
    cours = CurField(default=1, decimal_places=5)
    invest = CurField(default=0, editable=False, decimal_places=2)
    ope = models.OneToOneField('Ope', editable=False, null=True, on_delete=models.CASCADE)#null=true car j'ai des operations sans lien
    ope_pmv_id = models.IntegerField(editable=False, default=0, null=True)#null=true cr tt les operation d'achat sont null

    class Meta:
        db_table = 'gsb_ope_titre'
        verbose_name_plural = u'Opérations titres(compta_matiere)'
        verbose_name = u'Opérations titres(compta_matiere)'
        ordering = ['-date']


    def get_ope_pmv(self):
        try:
            return Ope.objects.get(id=self.ope_pmv_id)
        except Ope.DoesNotExist:
            return None

    def set_ope_pmv(self, obj):
        raise NotImplementedError('pas possible')

    def del_ope_pmv(self):
        try:
            self.ope_pmv.delete()
        except AttributeError:
            pass
        self.ope_pmv_id = 0

    ope_pmv = property(get_ope_pmv, set_ope_pmv, del_ope_pmv)

    def save(self, *args, **kwargs):
        #definition des cat avec possibilite
        try:
            cat_ost = Cat.objects.get_or_create(id=settings.ID_CAT_OST, defaults={'nom':u'Operation Sur Titre'})[0]
        except IntegrityError:
            raise ImproperlyConfigured(u"attention problème de configuration. l'id pour la cat %s n'existe pas mais il existe deja une categorie 'operation sur titre'"%settings.ID_CAT_OST)
        try:
            cat_pmv = Cat.objects.get_or_create(id=settings.ID_CAT_PMV, defaults={'nom':u'Revenus de placement:Plus-values'})[0]
        except IntegrityError:
            raise ImproperlyConfigured(u"attention problème de configuration. l'id pour la cat %s n'existe pas mais il existe deja une catégorie 'Revenus de placement:Plus-values'"%settings.ID_CAT_OST)
        #gestion des cours
        if self.ope:
            old_date = self.ope.date
            obj = Cours.objects.get(titre=self.titre, date=old_date)
            obj.delete()
        else:
            old_date = self.date
        obj, created = Cours.objects.get_or_create(titre=self.titre, date=old_date, defaults={'valeur':0})
        obj.date = self.date
        obj.valeur = self.cours
        obj.save()

        if self.nombre >= 0:#on doit separer because gestion des plues ou moins value
            del self.ope_pmv #comme achat, il n'y a pas de plus ou moins value exteriosée donc on efface
            self.invest = decimal.Decimal(force_unicode(self.cours)) * decimal.Decimal(force_unicode(self.nombre))
            moyen = self.compte.moyen_debit_defaut
            if not self.ope:#il faut creer l'ope sous jacente
                self.ope = Ope.objects.create(date=self.date,
                                              montant=self.cours * self.nombre * -1,
                                              tiers=self.titre.tiers,
                                              cat=cat_ost,
                                              notes="%s@%s" % (self.nombre, self.cours),
                                              moyen=moyen,
                                              compte=self.compte,
                                              )

            else:#la modifier juste
                self.ope.date = self.date
                self.ope.montant = self.cours * self.nombre * -1
                self.ope.tiers = self.titre.tiers
                self.ope.notes = "%s@%s" % (self.nombre, self.cours)
                self.ope.compte = self.compte
                self.ope.moyen = moyen
                self.ope.save()
        else:#c'est une vente
            #calcul prealable
            #on met des plus car les chiffres sont negatif
            if self.ope:#ope existe deja, donc il faut faire attention car les montant inv sont faux
                inv_vrai = self.titre.investi(self.compte, datel=self.date, exclude_id=self.ope.id)
                nb_vrai = self.titre.nb(self.compte, datel=self.date, exclude_id=self.id)
            else:
                inv_vrai = self.titre.investi(self.compte, datel=self.date)
                nb_vrai = self.titre.nb(self.compte, datel=self.date)
            #chaine car comme on a des decimal
            ost = "{0:.2f}".format(( inv_vrai / nb_vrai ) * self.nombre)
            ost = decimal.Decimal(ost)
            pmv = self.nombre * self.cours - ost
            #on cree les ope
            self.invest = ost
            moyen = self.compte.moyen_credit_defaut

            if not self.ope:
                self.ope = Ope.objects.create(date=self.date,
                                              montant=ost * -1,
                                              tiers=self.titre.tiers,
                                              cat=cat_ost,
                                              notes="%s@%s" % (self.nombre, self.cours),
                                              moyen=moyen,
                                              compte=self.compte,
                                              )
            else:
                self.ope.date = self.date
                self.ope.montant = ost * -1
                self.ope.tiers = self.titre.tiers
                self.ope.notes = "%s@%s" % (self.nombre, self.cours)
                self.ope.compte = self.compte
                self.ope.save()
            if not self.ope_pmv:
                self.ope_pmv_id = Ope.objects.create(date=self.date,
                                                  montant=pmv * -1,
                                                  tiers=self.titre.tiers,
                                                  cat=cat_pmv,
                                                  notes="%s@%s" % (self.nombre, self.cours),
                                                  moyen=moyen,
                                                  compte=self.compte,
                                                  ).id
            else:
                #on modifie tout
                ope_pmv = self.ope_pmv
                ope_pmv.date = self.date
                ope_pmv.montant = pmv*-1
                ope_pmv.tiers = self.titre.tiers
                ope_pmv.cat = cat_pmv
                ope_pmv.notes = "%s@%s" % (self.nombre, self.cours)
                ope_pmv.moyen = moyen
                ope_pmv.compte = self.compte
                ope_pmv.save()
            old_date = self.ope.date

        super(Ope_titre, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            if self.ope:
                if self.ope.rapp:
                    raise IntegrityError(u"opération espece rapprochée")
                if  self.ope.jumelle.rapp:
                    raise IntegrityError(u"opération espece rapprochée")
        except AttributeError as e:
            logger = logging.getLogger('gsb')
            logger.warning("attribute error({0}): {1}".format(e.errno, e.strerror))
        if self.ope_pmv_id:
            del self.ope_pmv
        super(Ope_titre, self).delete(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'ope_titre_detail', (), {'pk':str(self.id)}

    def __unicode__(self):
        return "%s" % self.id

class Moyen(models.Model):
    """moyen de paiements
    commun à l'ensembles des comptes
    actuellement, les comptes ont tous les moyens sans possiblite de faire le tri
    """
    #on le garde pour l'instant car ce n'est pas dans le même ordre que pour les categories
    typesdep = (
        ('v', u'virement'),
        ('d', u'depense'),
        ('r', u'recette'),
        )
    nom = models.CharField(max_length=40, unique=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d')

    class Meta:
        db_table = 'gsb_moyen'
        verbose_name = u"moyen de paiment"
        verbose_name_plural = u"moyens de paiment"
        ordering = ['nom']

    def __unicode__(self):
        return "%s (%s)" % (self.nom, self.type)

    @transaction.commit_on_success
    def fusionne(self, new):
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


class Rapp(models.Model):
    """rapprochement d'un compte"""
    nom = models.CharField(max_length=40, unique=True)
    date = models.DateField(null=True, blank=True, default=datetime.date.today)

    class Meta:
        db_table = 'gsb_rapp'
        verbose_name = u"rapprochement"
        ordering = ['nom']
        get_latest_by = 'date'

    def __unicode__(self):
        return self.nom

    @property
    def compte(self):#petit raccourci mais normalement, c'est bon. on prend le compte de la premiere ope
        if self.ope_set.all():
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

    date = models.DateField(default=datetime.date.today)
    date_limite = models.DateField(null=True, blank=True, default=None)
    intervalle = models.IntegerField(default=1)
    periodicite = models.CharField(max_length=1, choices=typesperiod, default="u")
    valide = models.BooleanField(default=True)
    compte = models.ForeignKey(Compte)
    montant = CurField()
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.PROTECT, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.PROTECT, default=None,
                            verbose_name=u"catégorie")
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.PROTECT, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                           verbose_name=u"imputation")
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name='echeance_virement_set',
                                        default=None)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True, related_name='echeance_moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    notes = models.TextField(blank=True, default='')
    inscription_automatique = models.BooleanField(default=False, help_text=u"attention, ne sert a rien car par defaut les echeances sont automatiques")

    class Meta:
        db_table = 'gsb_echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"echéances"
        ordering = ['date']
        get_latest_by = 'date'

    def __unicode__(self):
        if self.compte_virement:
            return "%s=>%s pour %s" % (self.compte, self.compte_virement, self.montant)
        else:
            return "%s pour %s" % (self.montant, self.tiers)

    def calcul_next(self):
        """
        calcul la prochaine date d'echeance
        renvoie None si pas de prochaine date
        """
        if not self.valide:
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
            #on verifie que la date limite n'est pas dépasséee
        if self.date_limite and finale > self.date_limite:
            finale = None
        return finale

    @staticmethod
    @transaction.commit_on_success
    def check(request=None, queryset=None):
        """
        attention ce n'est pas une vue
        verifie si pas d'écheance a passer et la cree au besoin
        """
        if  not queryset:
            liste_ech = Echeance.objects.filter(valide=True, date__lte=datetime.date.today())
        else:
            liste_ech = queryset
        for ech in liste_ech:
            #TODO ech titre
            while ech.date < datetime.date.today() and ech.valide:
                if ech.compte_virement:
                    vir = Virement.create(compte_origine=ech.compte,
                                          compte_dest=ech.compte_virement,
                                          montant=ech.montant,
                                          date=ech.date
                    )
                    vir.auto = True
                    vir.exercice = ech.exercice
                    vir.save()
                    if request:
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
                    if request:
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
    date = models.DateField(default=datetime.date.today)
    date_val = models.DateField(null=True, blank=True, default=None)
    montant = CurField()
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.PROTECT, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.PROTECT, default=None,
                            verbose_name=u"Catégorie")
    notes = models.TextField(blank=True, default='')
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    num_cheque = models.CharField(max_length=20, blank=True, default='')
    pointe = models.BooleanField(default=False)
    rapp = models.ForeignKey(Rapp, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                             verbose_name=u'Rapprochement')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                           verbose_name=u"projet")
    jumelle = models.OneToOneField('self', null=True, blank=True, related_name='jumelle_set', default=None,
                                   editable=False)
    mere = models.ForeignKey('self', null=True, blank=True, related_name='filles_set', default=None,
                              on_delete=models.PROTECT, verbose_name=u'Mere')
    automatique = models.BooleanField(default=False,
                                      help_text=u'si cette opération est crée a cause d\'une echeance')
    piece_comptable = models.CharField(max_length=20, blank=True, default='')


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
        return Ope.objects.filter(filles_set__isnull=True)

    def __unicode__(self):
        return u"(%s) le %s : %s %s a %s cpt: %s" % (self.id, self.date, self.montant, settings.DEVISE_GENERALE, self.tiers, self.compte)

    @models.permalink
    def get_absolute_url(self):
        return 'gsb_ope_detail', (), {'pk':str(self.id)}

    def clean(self):
        self.alters_data = True
        self.deja_clean = True
        super(Ope, self).clean()
        if not self.compte_id:
            raise ValidationError(u"vous devez mettre un compte")
            #verification qu'il n'y pas pointe et rapprochee
        if self.pointe and self.rapp is not None:
            raise ValidationError(u"cette opération ne peut pas etre à la fois pointée et rapprochée")
        if not self.compte.ouvert:
            raise ValidationError(u"cette opération ne peut pas être modifie car le compte est fermé")
        if self.is_mere:
            if self.montant != self.tot_fille:
                if (self.rapp or self.pointe):
                    raise ValidationError(u"attention cette opération est pointée ou rapproché et on change le montant global")
                else:
                    self.montant = self.tot_fille

    @property
    def is_mere(self):
        return (self.filles_set.count() > 1 and self.id)

    @property
    def is_fille(self):
        return (self.mere != None)

    @property
    def tot_fille(self):
        return self.filles_set.aggregate(total=models.Sum('montant'))['total']

    @property
    def pr(self):
        """renvoie true si pointee ou rapprochée"""
        if self.rapp or self.pointe:
            return True
        else:
            return False

class Virement(object):
    """raccourci pour creer un virement entre deux comptes"""

    def __init__(self, ope=None):
        if ope:
            if type(ope) != type(Ope()):
                raise TypeError('pas ope')
            self.origine = ope
            self.dest = self.origine.jumelle
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
        return self.origine.pointe

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
            nom_tiers = "Virement"
            tier = Tiers.objects.get_or_create(nom=nom_tiers, defaults={'nom':nom_tiers})[0]
            self.origine.tiers = tier
            self.dest.tiers = tier
            self.origine.cat = Cat.objects.get_or_create(nom="Virement", defaults={'nom':u'Virement'})[0]
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
            vir.date = datetime.date.today()
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
            tab = {'compte_origine':self.origine.compte.id,
                   'compte_destination':self.dest.compte.id,
                   'montant':self.montant,
                   'date':self.date,
                   'notes':self.notes,
                   'pointe':self.pointe}
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
        return "%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)

@receiver(pre_delete, sender=Ope)
def verif_ope_rapp(sender, **kwargs):
    instance = kwargs['instance']
    #on evite que cela soit une opération rapproche
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

@receiver(pre_save, sender=Ope)
def verif_ope_save(sender, **kwargs):
    instance = kwargs['instance']
    if instance.is_mere:
        instance.cat = Cat.objects.get_or_create(nom=u"Opération Ventilée", defaults={'type': "d", 'nom': u"Opération Ventilée"})[0]
        if instance.montant != instance.tot_fille:
            if (instance.rapp or instance.pointe):
                raise ValidationError(u"attention cette opération est pointée ou rapproché et on change le montant global")
            else:
                instance.montant = instance.tot_fille
    if not instance.moyen:
        if instance.montant >= 0:
            if instance.compte.moyen_credit_defaut:
                instance.moyen = instance.compte.moyen_credit_defaut
            else:
                moyen = Moyen.objects.get_or_create(id=settings.sMD_CREDIT, defaults={'nom':"moyen_par_defaut_credit", "id": settings.MD_CREDIT})[0]
                instance.moyen = moyen
        if  instance.montant <= 0:
            if instance.compte.moyen_debit_defaut:
                instance.moyen = instance.compte.moyen_debit_defaut
            else:
                moyen = Moyen.objects.get_or_create(id=settings.MD_DEBIT, defaults={'nom':"moyen_par_defaut_debit", "id": settings.MD_DEBIT})[0]
                instance.moyen = moyen
