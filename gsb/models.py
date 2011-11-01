# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.db import models
import datetime
import decimal
from django.db import transaction, IntegrityError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_unicode
from django.db.models.signals import pre_delete
from django.dispatch import receiver

class Gsb_exc(Exception):
    pass


class Ex_jumelle_neant(Exception):
    pass

#import logging
#definition d'un moneyfield
class CurField(models.DecimalField):
    """
    un champ decimal mais defini pour les monnaies
    """
    description = "A Monetary value"
    # __metaclass__ = models.SubfieldBase # ca marche pas chez always data
    def __init__(self, verbose_name=None, name=None, max_digits=15, decimal_places=3, default=0.000,
                 **kwargs):
        super(CurField, self).__init__(verbose_name, name, max_digits, decimal_places, default=default, **kwargs)

    def get_internal_type(self):
        return "DecimalField"

    def __mul(self, other):
        return decimal.Decimal(self) * decimal.Decimal(other)


class Tiers(models.Model):
    """
    un tiers, c'est a dire une personne ou un titre
    pour les titres, c'est remplis dans le champ note avec TYPE@ISIN
    """

    nom = models.CharField(max_length=40, unique=True)
    notes = models.TextField(blank=True, default='')
    is_titre = models.BooleanField(default=False)

    class Meta:
        db_table = 'tiers'
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
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_tiers_change = Echeance.objects.filter(tiers=self).update(tiers=new)
        nb_tiers_change += Ope.objects.filter(tiers=self).update(tiers=new)
        self.delete()
        return nb_tiers_change


class Titre(models.Model):
    """
    les titres englobe les actifs financiers
    afin de pouvoir faire le lien dans les operation, il y a un ligne vers les tiers
    :model:`gsb.tiers`
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
    tiers = models.OneToOneField(Tiers, null=True, blank=True, editable=False, on_delete=models.SET_NULL)
    type = models.CharField(max_length=3, choices=typestitres, default='ZZZ')

    class Meta:
        db_table = u'titre'
        ordering = ['nom']

    def __unicode__(self):
        return "%s (%s)" % (self.nom, self.isin)

    @property
    def last_cours(self):
        """renvoie le dernier cours"""
        return self.cours_set.latest().valeur

    @property
    def last_cours_date(self):
        """renvoie la date du dernier cours"""
        return self.cours_set.latest().date

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne ce titre avec le titre new"""
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le meme type de titre")
        for cours in self.cours_set.all():
            try:
                if new.cours_set.get(date=cours.date).valeur != cours.valeur:
                    raise Gsb_exc(
                        'attention les titre %s et %s ne peuvent etre fusionne car pas les meme histo de cours' % (
                            self, new))
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
        if self.tiers.notes != "%s@%s" % (self.isin, self.type):
            self.tiers.notes = "%s@%s" % (self.isin, self.type)
            self.tiers.save()
        super(Titre, self).save(*args, **kwargs)

    def investi(self, compte=None, datel=None, rapp=False):
        """renvoie le montant investi
        @param compte: Compte , si None, renvoie sur  l'ensemble des comptes titres
        @param datel:date, renvoie sur avant la date ou tout si none
        @param rapp: boolean, renvoie uniquement les op rapp
        """
        query = Ope.objects.filter(tiers=self.tiers)
        if compte:
            query = query.filter(compte=compte)
        if rapp:
            query = query.filter(rapp__isnull=False)
        if datel:
            query = query.filter(date__lte=datel)
        valeur = query.aggregate(invest=models.Sum('montant'))['invest']
        if not valeur:
            return 0
        else:
            return valeur * -1

    def nb(self, compte=None, datel=None, rapp=False):
        """renvoie le nombre de titre detenus dans un compte C ou dans tous les comptes si pas de compte donnee
                @param datel:date, renvoie sur avant la date ou tout si none
                @param rapp: boolean, renvoie uniquement les op rapp
                """
        query = Ope_titre.objects.filter(titre=self)
        if compte:
            query = query.filter(compte=compte)
        if rapp:
            query = query.filter(ope__rapp__isnull=False)
        if datel:
            query = query.filter(date__lte=datel)
        nombre = query.aggregate(nombre=models.Sum('nombre'))['nombre']
        if not nombre:
            return 0
        else:
            return nombre

    def encours(self, compte=None):
        """renvoie l'encours detenu dans ce titre dans un compte ou dans tous les comptes si pas de compte donné"""
        if compte:
            return self.nb(compte) * self.last_cours
        else:
            return self.nb() * self.last_cours


class Cours(models.Model):
    """cours des titres"""
    valeur = CurField(default=1.000)
    titre = models.ForeignKey(Titre)
    date = models.DateField(default=datetime.date.today)

    class Meta:
        db_table = 'cours'
        verbose_name_plural = u'cours'
        unique_together = ("titre", "date")
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
        return u"le %(date)s, 1 %(titre)s : %(valeur)s" % {'titre':self.titre.nom, 'date':self.date,
                                                           'valeur':self.valeur}


class Banque(models.Model):
    """banques"""
    cib = models.CharField(max_length=5, blank=True)
    nom = models.CharField(max_length=40, unique=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'banque'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
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
    nom = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d', verbose_name="type de la catégorie")

    class Meta:
        db_table = 'cat'
        verbose_name = u"catégorie"
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
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
        db_table = 'ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
        ordering = ['type', 'nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le meme type de titre")
        nb_change = Echeance.objects.filter(ib=self).update(ib=new)
        nb_change += Ope.objects.filter(ib=self).update(ib=new)
        self.delete()
        return nb_change


class Exercice(models.Model):
    """listes des exercices des comptes
    attention, il ne faut confondre exercice et rapp. les exercices sont les meme pour tous les comptes alors q'un rapp est pour un seul compte
    """
    date_debut = models.DateField(default=datetime.date.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = 'exercice'
        ordering = ['-date_debut']
        get_latest_by = 'date_debut'

    def __unicode__(self):
        return u"%s au %s" % (self.date_debut.strftime("%d/%m/%Y"), self.date_fin.strftime("%d/%m/%Y"))

    @transaction.commit_on_success
    def fusionne(self, new):
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_change = Echeance.objects.filter(exercice=self).update(exercice=new)
        nb_change += Ope.objects.filter(exercice=self).update(exercice=new)
        if self.date_debut != new.date_debut:
            new.date_debut = min(new.date_debut, self.date_debut)
        if self.date_fin != new.date_fin:
            new.date_fin = max(new.date_fin, self.date_fin)
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
        ('t', u'titre')
        )
    nom = models.CharField(max_length=40, unique=True)
    titulaire = models.CharField(max_length=40, blank=True, default='')
    type = models.CharField(max_length=1, choices=typescpt, default='b')
    banque = models.ForeignKey(Banque, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    guichet = models.CharField(max_length=15, blank=True,
                               default='')#il est en charfield comme celui d'en dessous parce qu'on n'est pas sur qu'il n y ait que des chiffres
    num_compte = models.CharField(max_length=20, blank=True, default='')
    cle_compte = models.IntegerField(null=True, blank=True, default=0)
    solde_init = CurField(default=decimal.Decimal('0.00'))
    solde_mini_voulu = CurField(null=True, blank=True)
    solde_mini_autorise = CurField(null=True, blank=True)
    ouvert = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    moyen_credit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name="moyen_credit_set", default=None)
    moyen_debit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL,
                                           related_name="moyen_debit_set", default=None)

    class Meta:
        db_table = 'compte'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    def solde(self, datel=None, rapp=False):
        """renvoie le solde du compte
            @param datel date date limite de calcul du solde
            @param rapp boolean faut il prendre uniquement les operation rapproches
        """
        query = Ope.objects.filter(compte__id__exact=self.id, mere__exact=None)
        if rapp:
            query = query.filter(rapp__isnull=True)
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
        """fusionnne deux compte, verifie avant que c'est le meme type
        @param new
        """
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        if new.type != self.type:
            raise Gsb_exc("attention ce ne sont pas deux compte de meme type")
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
        return 'mysite.gsb.views.cpt_detail', (), {'cpt_id':str(self.id)}

    def save(self, *args, **kwargs):
        """verifie qu'on ne cree pas un compte avec le type 't'"""
        self.alters_data = True
        if self.type == 't' and not isinstance(self, Compte_titre):
            c=Compte_titre.objects.create(nom=self.nom, titulaire=self.titulaire, type=self.type,
                                        banque=self.banque,
                                        guichet=self.guichet, num_compte=self.num_compte,
                                        cle_compte=self.cle_compte,
                                        solde_init=self.solde_init, solde_mini_voulu=self.solde_mini_voulu,
                                        solde_mini_autorise=self.solde_mini_autorise, ouvert=self.ouvert,
                                        notes=self.notes, moyen_credit_defaut=self.moyen_credit_defaut,
                                        moyen_debit_defaut=self.moyen_credit_defaut
            )
        else:
            c=super(Compte, self).save(*args, **kwargs)
        return c


class Compte_titre(Compte):
    """
    comptes titres
    compte de classe "t" avec des fonctions en plus. une compta matiere
    """
    titre = models.ManyToManyField('titre', through="Ope_titre")

    class Meta:
        db_table = 'cpt_titre'
        ordering = ['nom']
        verbose_name_plural = "Comptes Titre"

        #@transaction.commit_on_success

    def achat(self, titre, nombre, prix=1,
              date=datetime.date.today(), frais=0, virement_de=None,
              cat_frais=None, tiers_frais=None):
        """fonction pour achat de titre:
        @param titre
        @param nombre
        @param prix
        @param date
        @param frais
        @param virement_de
        """
        self.alters_data = True
        if frais:
            if not cat_frais:
                cat_frais = Cat.objects.get_or_create(nom=u"frais bancaires:",
                                                      defaults={'nom':u'frais bancaires:'})[0]
            if not tiers_frais:
                tiers_frais = titre.tiers
        if isinstance(titre, Titre):
            if decimal.Decimal(force_unicode(frais)):
                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=tiers_frais,
                                    cat=cat_frais,
                                    notes="frais %s@%s" % (nombre, prix),
                                    moyen=Moyen.objects.get(id=settings.MD_DEBIT),
                                    automatique=True
                )
                #gestion compta matiere (et donc operation sous jacente et cours)
            Ope_titre.objects.create(titre=titre,
                                     compte=self,
                                     nombre=decimal.Decimal(force_unicode(nombre)),
                                     date=date,
                                     cours=prix)
            #virement
            if virement_de:
                vir = Virement()
                vir.create(virement_de, self,
                           decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)), date)
        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def vente(self, titre, nombre, prix=1,
              date=datetime.date.today(), frais=0, virement_vers=None,
              cat_frais=None, titre_frais=None):
        """fonction pour vente de titre:
        @param titre
        @param nombre
        @param prix
        @param date
        @param frais
        @param virement_vers
        """
        self.alters_data = True
        if not cat_frais:
            cat_frais = Cat.objects.get_or_create(nom=u"frais bancaires:",
                                                  defaults={'nom':u'frais bancaires:'})[0]
        if not titre_frais:
            titre_frais = titre.tiers
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            nb_titre_avant = titre.nb(compte=self)
            if not nb_titre_avant:
                raise Titre.DoesNotExist('titre pas en portefeuille')
                #compta matiere
            Ope_titre.objects.create(titre=titre,
                                     compte=self,
                                     nombre=decimal.Decimal(force_unicode(nombre)) * -1,
                                     date=date,
                                     cours=prix)
            if decimal.Decimal(force_unicode(frais)):
                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=titre_frais,
                                    cat=cat_frais,
                                    notes="frais %s@%s" % (nombre, prix),
                                    moyen=Moyen.objects.get(id=settings.MD_DEBIT),
                                    automatique=True
                )
            if virement_vers:
                vir = Virement()
                vir.create(self,
                           virement_vers,
                           decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)),
                           date)
        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def revenu(self, titre, montant=1,
               date=datetime.date.today(), frais=0, virement_vers=None,
               cat_frais=None, titre_frais=None):
        """fonction pour ost de titre:"""
        self.alters_data = True
        if not cat_frais:
            cat_frais = Cat.objects.get_or_create(nom=u"frais bancaires:", defaults={'nom':u'frais bancaires:'})[0]
        if not titre_frais:
            titre_frais = titre.tiers
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            if not titre.nb(compte=self):
                raise Titre.DoesNotExist('titre pas en portefeuille')
            if decimal.Decimal(force_unicode(frais)):
                self.ope_set.create(date=date,
                                    montant=decimal.Decimal(force_unicode(frais)) * -1,
                                    tiers=titre_frais,
                                    cat=cat_frais,
                                    notes="frais revenu",
                                    moyen=Moyen.objects.get(id=settings.MD_DEBIT),
                                    automatique=True
                )
            if virement_vers:
                vir = Virement()
                vir.create(self, virement_vers, decimal.Decimal(force_unicode(montant)), date)
        else:
            raise TypeError("pas un titre")

    def solde(self, datel=None, rapp=False):
        """renvoie le solde"""
        solde_espece = self.solde_espece(datel, rapp)
        solde_titre = 0
        for titre in self.titre.all().distinct():
            solde_titre = solde_titre + titre.encours(self)
        return solde_espece + solde_titre

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne deux compte_titre"""
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_change = Echeance.objects.filter(compte=self).update(compte=new)
        nb_change += Ope_titre.objects.filter(compte=self).update(compte=new)
        nb_change += Echeance.objects.filter(compte_virement=self).update(compte_virement=new)
        nb_change += Ope.objects.filter(compte=self).update(compte=new)
        self.delete()
        return nb_change

    @models.permalink
    def get_absolute_url(self):
        return 'cpt_detail', (), {'pk':str(self.id)}

    def save(self, *args, **kwargs):
        """verifie qu'on a pas changé le type de compte"""
        self.alters_data = True
        if self.type != 't':
            self.type = 't'
        super(Compte_titre, self).save(*args, **kwargs)

    def solde_espece(self, datel=None, rapp=False):
        return super(Compte_titre, self).solde(datel, rapp)

    def solde_titre(self):
        solde_titre = 0
        for titre in self.titre.all().distinct():
            solde_titre = solde_titre + titre.encours(self)
        return solde_titre

    def liste_titre(self):
        return self.titre.all().distinct()


class Ope_titre(models.Model):
    """ope titre en compta matiere"""
    titre = models.ForeignKey(Titre)
    compte = models.ForeignKey(Compte_titre, verbose_name=u"compte titre")
    nombre = CurField(default=0, decimal_places=5)
    date = models.DateField()
    cours = CurField(default=1, decimal_places=5)
    invest = CurField(default=0, editable=False, decimal_places=5)
    ope = models.OneToOneField('Ope', editable=False, null=True)#null=true car j'ai des operations sans lien

    class Meta:
        db_table = 'ope_titre'
        verbose_name_plural = u'Opérations titres(compta_matiere)'
        verbose_name = u'Opérations titres(compta_matiere)'
        ordering = ['-date']

    def save(self, *args, **kwargs):
        self.invest = decimal.Decimal(force_unicode(self.cours)) * decimal.Decimal(force_unicode(self.nombre))
        #        super(Ope_titre, self).save(*args, **kwargs)
        if not self.ope:
            #gestion des cours
            cat_ost = Cat.objects.get_or_create(id=settings.ID_CAT_OST, defaults={'nom':u'operation sur titre :'})[
                      0]
            if self.cours * self.nombre < 0:#vente
                moyen = self.compte.moyen_credit_defaut
            else:#achat
                moyen = self.compte.moyen_credit_defaut
            self.ope = Ope.objects.create(date=self.date,
                                          montant=self.cours * self.nombre * -1,
                                          tiers=self.titre.tiers,
                                          cat=cat_ost,
                                          notes="%s@%s" % (self.nombre, self.cours),
                                          moyen=moyen,
                                          compte=self.compte,
                                          )
            self.titre.cours_set.get_or_create(date=self.date, defaults={'date':self.date, 'valeur':self.cours})
        else:
            self.ope.date = self.date
            self.ope.montant = self.cours * self.nombre * -1
            self.ope.tiers = self.titre.tiers
            self.ope.notes = "%s@%s" % (self.nombre, self.cours)
            self.ope.compte = self.compte
            self.ope.save()
        super(Ope_titre, self).save(*args, **kwargs)

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
    #on le garde pour l'instant car ce n'est pas dans le meme ordre que pour les categories
    typesdep = (
        ('v', u'virement'),
        ('d', u'depense'),
        ('r', u'recette'),
        )
    nom = models.CharField(max_length=40, unique=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d')

    class Meta:
        db_table = 'moyen'
        verbose_name = u"moyen de paiment"
        verbose_name_plural = u"moyens de paiment"
        ordering = ['nom']

    def __unicode__(self):
        return "%s (%s)" % (self.nom, self.type)

    @transaction.commit_on_success
    def fusionne(self, new):
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        if not (self.id == settings.MD_CREDIT or self.id == settings.MD_DEBIT):
            self.alters_data = True
            if type(new) != type(self):
                raise TypeError("pas la meme classe d'objet")
            nb_change = Compte.objects.filter(moyen_credit_defaut=self).update(moyen_credit_defaut=new)
            nb_change += Compte.objects.filter(moyen_debit_defaut=self).update(moyen_debit_defaut=new)
            nb_change += Echeance.objects.filter(moyen=self).update(moyen=new)
            nb_change += Echeance.objects.filter(moyen_virement=self).update(moyen_virement=new)
            nb_change += Ope.objects.filter(moyen=self).update(moyen=new)
            self.delete()
        else:
            nb_change = 0
        return nb_change


class Rapp(models.Model):
    """rapprochement d'un compte"""
    nom = models.CharField(max_length=40, unique=True)
    date = models.DateField(null=True, blank=True, default=datetime.date.today)

    class Meta:
        db_table = 'rapp'
        verbose_name = u"rapprochement"
        ordering = ['-nom']
        get_latest_by = 'date'

    def __unicode__(self):
        return self.nom

    @property
    def compte(self):#petit raccourci mais normalement, c'est bon. on prend le compte de la premiere ope
        if self.ope_set.all():
            return self.ope_set.all()[0].compte.id
        else:
            return None

    def solde(self):
        req = self.ope_set.aggregate(solde=models.Sum('montant'))
        if req['solde'] is None:
            solde = 0
        else:
            solde = req['solde']
        return solde

    def fusionne(self, new):
        if new == self:
            raise ValueError("un objet ne peut etre fusionne sur lui meme")
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_change = Ope.objects.filter(rapp=self).update(rapp=new)
        self.delete()
        return nb_change


class Echeance(models.Model):
    """echeance 'operation future prevue
    soit unique
    soit repete
    """
    typesperiod = (
        ('u', u'unique'),
        ('h', u'hebdomadaire'),
        ('m', u'mensuel'),
        ('a', u'annuel'),
        ('p', u'personalisé'),
        )
    typesperiodperso = (
        ('j', u'jour'),
        ('m', u'mois'),
        ('a', u'année'),
        ('na', 'non applicable')
        )

    date = models.DateField(default=datetime.date.today)
    compte = models.ForeignKey(Compte)
    montant = CurField()
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                            verbose_name=u"catégorie")
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name='compte_virement_set',
                                        default=None)
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True, related_name='moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                           verbose_name=u"imputation")
    notes = models.TextField(blank=True, default='')
    inscription_automatique = models.BooleanField(default=False)
    periodicite = models.CharField(max_length=1, choices=typesperiod, default="u")
    intervalle = models.IntegerField(default=0)
    periode_perso = models.CharField(max_length=1, choices=typesperiodperso, blank=True, default="")
    date_limite = models.DateField(null=True, blank=True, default=None)

    class Meta:
        db_table = 'echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"echéances"
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
        return u"%s" % (self.id,)

    def save(self, *args, **kwargs):
        self.alters_data = True
        if not self.moyen:
            if self.compte.moyen_credit_defaut and self.montant >= 0:
                self.moyen = self.compte.moyen_credit_defaut
            if self.compte.moyen_debit_defaut and self.montant <= 0:
                self.moyen = self.compte.moyen_debit_defaut
        if not self.moyen_virement and self.compte_virement:
            if self.compte_virement.moyen_credit_defaut and self.montant <= 0:
                self.moyen_virement = self.compte_virement.moyen_credit_defaut
            if self.compte_virement.moyen_debit_defaut and self.montant >= 0:
                self.moyen_virement = self.compte_virement.moyen_debit_defaut
        super(Echeance, self).save(*args, **kwargs)


class Generalite(models.Model):
    """config dans le fichier"""
    titre = models.CharField(max_length=40, blank=True, default="isbi")
    utilise_exercices = models.BooleanField(default=True)
    utilise_ib = models.BooleanField(default=True)
    utilise_pc = models.BooleanField(default=False)
    affiche_clot = models.BooleanField(default=True)

    class Meta:
        db_table = 'generalite'
        verbose_name = u"généralités"
        verbose_name_plural = u'généralités'

    def __unicode__(self):
        return u"%s" % (self.id,)

    @staticmethod
    def gen():
        try:
            gen_1 = Generalite.objects.get(id=1)
        except Generalite.DoesNotExist:
            Generalite.objects.create(id=1)
            gen_1 = Generalite.objects.get(id=1)
        return gen_1

    @staticmethod
    def dev_g():
        return settings.DEVISE_GENERALE

    @staticmethod
    def last_id(classe):
        """renvoie le dernier  id de la classe demandée"""
        try:
            return classe.objects.latest('id').id
        except classe.DoesNotExist:
            return 0

    def save(self, *args, **kwargs):
        if Generalite.objects.count() > 0:
            return
        else:
            super(Generalite, self).save(*args, **kwargs)


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
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.PROTECT, default=None)
    num_cheque = models.CharField(max_length=20, blank=True, default='')
    pointe = models.BooleanField(default=False)
    rapp = models.ForeignKey(Rapp, null=True, blank=True, on_delete=models.PROTECT, default=None,
                             verbose_name=u'Rapprochement')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.PROTECT, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.PROTECT, default=None,
                           verbose_name=u"projet")
    jumelle = models.OneToOneField('self', null=True, blank=True, related_name='jumelle_set', default=None,
                                   editable=False)
    mere = models.ForeignKey('self', null=True, blank=True, related_name='filles_set', default=None,
                             editable=False)
    automatique = models.BooleanField(default=False,
                                      help_text=u'si cette operation est crée a cause d\'une echeance')
    piece_comptable = models.CharField(max_length=20, blank=True, default='')


    class Meta:
        db_table = 'ope'
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
        return Ope.objects.filter(mere=None)

    def __unicode__(self):
        return u"(%s) le %s : %s %s" % (self.id, self.date, self.montant, settings.DEVISE_GENERALE)

    @models.permalink
    def get_absolute_url(self):
        return 'gsb_ope_detail', (), {'pk':str(self.id)}

    def clean(self):
        self.alters_data = True
        super(Ope, self).clean()
        #verification qu'il n'y ni pointe ni rapprochee
        if self.pointe and self.rapp is not None:
            raise ValidationError(u"cette operation ne peut pas etre a la fois pointée et rapprochée")

    def save(self, *args, **kwargs):
        self.alters_data = True
        if not self.moyen:
            if self.montant >= 0:
                if self.compte.moyen_credit_defaut:
                    self.moyen = self.compte.moyen_credit_defaut
                else:
                    self.moyen_id = settings.MD_CREDIT
            if  self.montant <= 0:
                if self.compte.moyen_debit_defaut:
                    self.moyen = self.compte.moyen_debit_defaut
                else:
                    self.moyen_id = settings.MD_DEBIT
        super(Ope, self).save(*args, **kwargs)


@receiver(pre_delete, sender=Ope)
def verif_ope_rapp(sender, **kwargs):
    instance = kwargs['instance']
    #on evite que cela soit une operation rapproche
    if instance.rapp:
        raise IntegrityError()
    if instance.jumelle:
        if instance.jumelle.rapp:
            raise IntegrityError()
    if instance.mere:
        if instance.mere.rapp:
            raise IntegrityError()


@receiver(pre_delete, sender=Ope_titre)
def verif_ope_titre(sender, **kwargs):
    instance = kwargs['instance']
    if instance.ope:
        if instance.ope.rapp:
            raise IntegrityError()


class Virement(object):
    """raccourci pour creer un virement entre deux comptes"""

    def __init__(self, ope=None):
        if ope:
            if type(ope) != type(Ope()):
                raise TypeError('pas ope')
            self.origine = ope
            self.dest = self.origine.jumelle
            if not isinstance(self.dest, Ope):
                raise Ex_jumelle_neant(self.origine.id)
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


    def save(self):
        if self._init:
            nom_tiers = "%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)
            tier = Tiers.objects.get_or_create(nom=nom_tiers, defaults={'nom':nom_tiers})[0]
            self.origine.tiers = tier
            self.dest.tiers = tier
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
            raise TypeError('pas ope')
        if not isinstance(compte_dest, Compte):
            raise TypeError('pas ope')
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
            raise Exception('attention, on ne peut intialiser un form que si virement est bound')
        return tab

    def __unicode__(self):
        return "%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)
