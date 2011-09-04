# -*- coding: utf-8 -*-

from django.db import models #@UnusedImport
import datetime #@UnusedImport
import decimal #@UnusedImport
from django.db import transaction #@UnusedImport
from django.conf import settings #@UnusedImport
#from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError #@UnusedImport
from django.utils.encoding import force_unicode
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


    def __init__(self, verbose_name = None, name = None, max_digits = 15, decimal_places = 3, default = 0.000, **kwargs):
        super(CurField, self).__init__(verbose_name, name, max_digits, decimal_places, default = default, **kwargs)


    def get_internal_type(self):
        return "DecimalField"


class Tiers(models.Model):
    """
    un tiers, c'est a dire une personne ou un titre
    pour les titres, c'est remplis dans le champ note avec TYPE@ISIN
    """

    nom = models.CharField(max_length = 40, unique = True)
    notes = models.CharField(max_length = 40, blank = True)
    is_titre = models.BooleanField(default = False)

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
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_tiers_change = Echeance.objects.filter(tiers = self).update(tiers = new)
        nb_tiers_change += Ope.objects.filter(tiers = self).update(tiers = new)
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
    nom = models.CharField(max_length = 40, unique = True)
    isin = models.CharField(max_length = 60, unique = True)
    tiers = models.OneToOneField(Tiers, null = True, blank = True, editable = False, on_delete=models.SET_NULL)
    type = models.CharField(max_length = 60, choices = typestitres, default = 'ZZZ')
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
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le meme type de titre")
        for cours in Cours.objects.filter(titre = self):
            try:
                if new.cours_set.get(date = cours.date).valeur != cours.valeur:
                    raise Gsb_exc('attention les titre %s et %s ne peuvent etre fusionne car pas les meme histo de cours')
            except Cours.DoesNotExist:
                new.cours_set.create(date = cours.date, valeur = cours.valeur)
        nb_change = 0
        nb_change += Ope_titre.objects.filter(titre = self).update(titre = new)
        #on doit aussi reaffecter le tiers associe
        self.tiers.fusionne(new.tiers)
        self.delete()
        return nb_change

    def save(self, *args, **kwargs):
        self.alters_data = True
        if (not self.tiers):
            self.tiers = Tiers.objects.get_or_create(nom = 'titre_ %s' % self.nom, defaults = {"nom":'titre_ %s' % self.nom, "is_titre":True, "notes":"%s@%s" % (self.isin, self.type)})[0]
        if self.tiers.notes != "%s@%s" % (self.isin, self.type):
            self.tiers.notes = "%s@%s" % (self.isin, self.type)
        super(Titre, self).save(*args, **kwargs)

    def investi(self, compte=None):
        """renvoie le montant investi
        @param compte: Compte , si None, renvoie sur  l'ensemble des comptes titres
        """
        if compte:
            return Ope_titre.investi(compte, self)
        else:
            valeur = Ope.objects.filter(tiers = self.tiers).aggregate(invest = models.Sum('montant'))['invest']
        if not valeur:
            return 0
        else:
            return valeur * -1

    def nb(self, compte = None):
        """renvoie le nombre de titre detenus dans un compte C ou dans tous les comptes si pas de compte donnee"""
        if compte:
            return Ope_titre.nb(compte, self)
        else:
            nombre = Ope_titre.objects.filter(titre = self).aggregate(nombre = models.Sum('nombre'))['nombre']
            if not nombre:
                return 0
            else:
                return nombre

    def encours(self, compte = None):
        """renvoie l'encours detenu dans ce titre dans un compte ou dans tous les comptes si pas de compte donné"""
        if compte:
            return Ope_titre.nb(compte, self) * self.last_cours
        else:
            return self.nb() * self.last_cours


class Cours(models.Model):
    """cours des titres"""
    valeur = CurField(default = 1.000)
    titre = models.ForeignKey(Titre, unique_for_date = "date")
    date = models.DateField(default = datetime.date.today)
    class Meta:
        db_table = 'cours'
        verbose_name_plural = u'cours'
        unique_together = ("titre", "date")
        ordering = ['date']
        get_latest_by = 'date'

    def __unicode__(self):
        return u"le %(date)s, 1 %(titre)s : %(valeur)s" % {'titre':self.titre.nom, 'date':self.date, 'valeur':self.valeur}


class Banque(models.Model):
    """banques"""
    cib = models.CharField(max_length = 15, blank = True)
    nom = models.CharField(max_length = 40, unique = True)
    notes = models.TextField(blank = True)
    class Meta:
        db_table = 'banque'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        self.alters_data = True
        nb_change = Compte.objects.filter(banque = self).update(banque = new)
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
    nom = models.CharField(max_length = 60, unique = True)
    type = models.CharField(max_length = 1, choices = typesdep, default = 'd', verbose_name = "type de la catégorie")
    class Meta:
        db_table = 'cat'
        verbose_name = u"catégorie"
        ordering = ['nom']

    def __unicode__(self):
        return self.nom
    @transaction.commit_on_success
    def fusionne(self, new):
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le meme type de titre")
        nb_change = Echeance.objects.filter(cat = self).update(cat = new)
        nb_change += Ope.objects.filter(cat = self).update(cat = new)
        self.delete()
        return nb_change


class Ib(models.Model):
    """imputations budgetaires
     c'est juste un deuxieme type de categories ou apparentes"""
    nom = models.CharField(max_length = 60, unique = True)
    type = models.CharField(max_length = 1, choices = Cat.typesdep, default = u'd')
    class Meta:
        db_table = 'ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom
    @transaction.commit_on_success
    def fusionne(self, new):
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        if self.type != new.type:
            raise TypeError("pas le meme type de titre")

        nb_change = Echeance.objects.filter(ib = self).update(ib = new)
        nb_change += Ope.objects.filter(ib = self).update(ib = new)
        self.delete()
        return nb_change

class Exercice(models.Model):
    """listes des exercices des comptes
    attention, il ne faut confondre exercice et rapp. les exercices sont les meme pour tous les comptes alors q'un rapp est pour un seul compte
    """
    date_debut = models.DateField(default = datetime.date.today)
    date_fin = models.DateField(null = True, blank = True)
    nom = models.CharField(max_length = 40, unique = True)
    class Meta:
        db_table = 'exercice'
        ordering = ['date_debut']
        get_latest_by = 'date_debut'

    def __unicode__(self):
        return u"%s au %s" % (self.date_debut.strftime("%d/%m/%Y"), self.date_fin.strftime("%d/%m/%Y"))

    @transaction.commit_on_success
    def fusionne(self, new):
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_change = Echeance.objects.filter(exercice = self).update(exercice = new)
        nb_change += Ope.objects.filter(exercice = self).update(exercice = new)
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
    nom = models.CharField(max_length = 40, unique = True)
    titulaire = models.CharField(max_length = 120, blank = True, default = '')
    type = models.CharField(max_length = 24, choices = typescpt, default = 'b')
    banque = models.ForeignKey(Banque, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    guichet = models.CharField(max_length = 15, blank = True, default = '')#il est en charfield comme celui d'en dessous parce qu'on n'est pas sur qu'il n y ait que des chiffres
    num_compte = models.CharField(max_length = 60, blank = True, default = '')
    cle_compte = models.IntegerField(null = True, blank = True, default = 0)
    solde_init = CurField()
    solde_mini_voulu = CurField(null = True, blank = True)
    solde_mini_autorise = CurField(null = True, blank = True)
    ouvert = models.BooleanField(default = True)
    notes = models.TextField(blank = True, default = '')
    moyen_credit_defaut = models.ForeignKey('Moyen', null = True, blank = True, on_delete = models.SET_NULL, related_name = "moyen_credit_set", default = None)
    moyen_debit_defaut = models.ForeignKey('Moyen', null = True, blank = True, on_delete = models.SET_NULL, related_name = "moyen_debit_set", default = None)

    class Meta:
        db_table = 'compte'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom
    @property
    def solde(self):
        """renvoie le solde du compte"""
        req = Ope.objects.filter(compte__id__exact = self.id, mere__exact = None).aggregate(solde = models.Sum('montant'))
        if req['solde'] is None:
            solde = decimal.Decimal(0) + decimal.Decimal(self.solde_init)
        else:
            solde = decimal.Decimal(req['solde']) + decimal.Decimal(self.solde_init)
        return solde

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne deux compte, verifie avant que c'est le meme type
        @param Compte
        """
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        if new.type != self.type:
            raise Gsb_exc("attention ce ne sont pas deux compte de meme type")
        nb_change = Echeance.objects.filter(compte = self).update(compte = new)
        nb_change += Echeance.objects.filter(compte_virement = self).update(compte_virement = new)
        nb_change += Ope.objects.filter(compte = self).update(compte = new)
        self.delete()
        return nb_change

    @models.permalink
    def get_absolute_url(self):
        return ('mysite.gsb.views.cpt_detail', (), {'cpt_id':str(self.id)})

    def save(self, *args, **kwargs):
        """verifie qu'on ne cree pas un compte avec le type 't'
        """
        self.alters_data = True
        if self.type == 't' and not isinstance(self, Compte_titre):
            raise Gsb_exc("il faut creer un compte titre")
        else:
            super(Compte, self).save(*args, **kwargs)


class Compte_titre(Compte):
    """
    comptes titres
    compte de classe "t" avec des fonctions en plus. une compta matiere
    """
    titre = models.ManyToManyField('titre', through = "Ope_titre")
    class Meta:
        db_table = 'cpt_titre'
    @transaction.commit_on_success
    def achat(self, titre, nombre, prix = 1, date = datetime.date.today(), frais = 0, virement_de = None):
        """fonction pour achat de titre:
        @param Titre
        @param int
        @param decimal
        @param date
        @param decimal
        @param Compte
        """
        self.alters_data = True
        cat_ost = Cat.objects.get_or_create(nom = u"operation sur titre:", defaults = {'nom':u'operation sur titre:'})[0]
        cat_frais = Cat.objects.get_or_create(nom = u"frais bancaires:", defaults = {'nom':u'frais bancaires:'})[0]
        if isinstance(titre, Titre):
            #ajout de l'operation dans le compte_espece rattache
            Ope.objects.create(date = date,
                                montant = decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)) * -1,
                                tiers = titre.tiers,
                                cat = cat_ost,
                                notes = "achat %s@%s" % (nombre, prix),
                                moyen = None,
                                automatique = True,
                                compte = self,
                                )
            if decimal.Decimal(force_unicode(frais)):
                self.ope_set.create(date = date,
                                montant = decimal.Decimal(force_unicode(frais)) * -1,
                                tiers = titre.tiers,
                                cat = cat_frais,
                                notes = "frais achat %s@%s" % (nombre, prix),
                                moyen = None,
                                automatique = True
                                )
            #gestion des cours
            titre.cours_set.get_or_create(date = date, defaults = {'date':date, 'valeur':prix})
            #ajout des titres dans portefeuille
            Ope_titre.objects.create(titre = titre, compte = self, nombre = decimal.Decimal(force_unicode(nombre)), date = date, cours = prix)
            #virement
            if virement_de:
                vir = Virement()
                vir.create(virement_de, self, decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)), date)

        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def vente(self, titre, nombre, prix = 1, date = datetime.date.today(), frais = 0, virement_vers = None):
        """fonction pour vente de titre:
        @param Titre
        @param int
        @param decimal
        @param date
        @param decimal
        @param Compte
        """

        self.alters_data = True
        cat_ost = Cat.objects.get_or_create(nom = u"operation sur titre:", defaults = {'nom':u'operation sur titre:'})[0]
        cat_frais = Cat.objects.get_or_create(nom = u"frais bancaires:", defaults = {'nom':u'frais bancaires:'})[0]
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            nb_titre_avant = Ope_titre.nb(titre = titre, compte = self)
            if not nb_titre_avant:
                raise Titre.doesNotExist('titre pas en portefeuille')
            #compta matiere
            Ope_titre.objects.create(titre = titre, compte = self, nombre = decimal.Decimal(force_unicode(nombre)) * -1, date = date, cours = prix)
            #ajout de l'operation dans le compte_espece ratache
            self.ope_set.create(date = date,
                                montant = decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)),
                                tiers = titre.tiers,
                                cat = cat_ost,
                                notes = "vente %s@%s" % (nombre, prix),
                                moyen = None,
                                automatique = True
                                )
            if decimal.Decimal(force_unicode(frais)):
                self.ope_set.create(date = date,
                                montant = decimal.Decimal(force_unicode(frais)) * -1,
                                tiers = titre.tiers,
                                cat = cat_frais,
                                notes = "frais vente %s@%s" % (nombre, prix),
                                moyen = None,
                                automatique = True
                                )
            #gestion des cours
            titre.cours_set.get_or_create(date = date, defaults = {'date':date, 'valeur':prix})
            if virement_vers:
                vir = Virement()
                vir.create(self, virement_vers, decimal.Decimal(force_unicode(prix)) * decimal.Decimal(force_unicode(nombre)), date)

        else:
            raise TypeError("pas un titre")

    @transaction.commit_on_success
    def revenu(self, titre, montant = 1, date = datetime.date.today(), frais = 0, virement_vers = None):
        """fonction pour ost de titre:
        @param Titre
        @param decimal
        @param date
        @param decimal
        @param Compte
        """
        self.alters_data = True
        cat_ost = Cat.objects.get_or_create(nom = u"operation sur titre:", defaults = {'nom':u'operation sur titre:'})[0]
        cat_frais = Cat.objects.get_or_create(nom = u"frais bancaires:", defaults = {'nom':u'frais bancaires:'})[0]
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            if not Ope_titre.nb(titre = titre, compte = self):
                raise Titre.doesNotExist('titre pas en portefeuille')
            #ajout de l'operation dans le compte_espece ratache
            self.ope_set.create(date = date,
                                montant = decimal.Decimal(force_unicode(montant)),
                                tiers = titre.tiers,
                                cat = cat_ost,
                                notes = "revenu",
                                moyen = None,
                                automatique = True
                                )
            if decimal.Decimal(force_unicode(frais)):
                self.ope_set.create(date = date,
                                montant = decimal.Decimal(force_unicode(frais)) * -1,
                                tiers = titre.tiers,
                                cat = cat_frais,
                                notes = "frais revenu %s@%s" % (montant),
                                moyen = None,
                                automatique = True
                                )
            if virement_vers:
                vir = Virement()
                vir.create(self, virement_vers, decimal.Decimal(force_unicode(montant)), date)

        else:
            raise TypeError("pas un titre")
    @property
    def solde(self):
        """renvoie le solde"""
        solde_espece = super(Compte_titre, self).solde
        solde_titre = 0
        for titre in self.titre.all().distinct():
            solde_titre += solde_titre + titre.encours(self)
        return solde_espece + solde_titre

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne deux compte_titre
        @param Compte_titre
        """
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_change = Echeance.objects.filter(compte = self).update(compte = new)
        nb_change += Ope_titre.objects.filter(compte = self).update(compte = new)
        nb_change += Echeance.objects.filter(compte_virement = self).update(compte_virement = new)
        nb_change += Ope.objects.filter(compte = self).update(compte = new)
        self.delete()
        return nb_change

    @models.permalink
    def get_absolute_url(self):
        return ('cpt_detail', (), {'pk':str(self.id)})

    def save(self, *args, **kwargs):
        """verifie qu'on a pas changé le type de compte"""
        self.alters_data = True
        if self.type != 't':
            self.type = 't'
        super(Compte_titre, self).save(*args, **kwargs)


class Ope_titre(models.Model):
    """ope titre en compta matiere"""
    titre = models.ForeignKey(Titre)
    compte = models.ForeignKey(Compte_titre)
    nombre = models.IntegerField()
    date = models.DateField()
    cours = CurField(default = 1)
    invest = CurField(default = 0,editable=False)
    class Meta:
        db_table = 'ope_titre'
        verbose_name_plural = u'Opérations titres(compta_matiere)'
        verbose_name = u'Opérations titres(compta_matiere)'
        ordering = ['compte']
    def save(self, *args, **kwargs):
        self.invest = self.nombre * self.cours
        super(Ope_titre, self).save(*args, **kwargs)
    @staticmethod
    def nb(compte, titre):
        """renvoie le nombre de titre T detenus dans un compte C"""
        if not isinstance(titre, Titre):
            raise TypeError("pas un titre")
        if not isinstance(compte, Compte_titre):
            raise TypeError("pas un compte titre")
        nombre = Ope_titre.objects.filter(compte = compte, titre = titre).aggregate(nombre = models.Sum('nombre'))['nombre']
        if not nombre:
            return 0
        else:
            return nombre
    @staticmethod
    def investi(compte, titre):
        """"prend en compte l'ensemble des depenses (achart et frais) et des revenus(vente et revenus annexes)"""
        if not isinstance(titre, Titre):
            raise TypeError("pas un titre")
        if not isinstance(compte, Compte_titre):
            raise TypeError("pas un compte titre")

        valeur = Ope.objects.filter(compte = compte, tiers = titre.tiers).aggregate(invest = models.Sum('montant'))['invest']
        if not valeur:
            return 0
        else:
            return valeur * -1


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
    nom = models.CharField(max_length = 20, unique = True)
    type = models.CharField(max_length = 1, choices = typesdep, default = 'd')
    class Meta:
        db_table = 'moyen'
        verbose_name = u"moyen de paiment"
        verbose_name_plural = u"moyens de paiment"
        ordering = ['nom']

    def __unicode__(self):

        return "%s (%s)" % (self.nom, self.type)

    @transaction.commit_on_success
    def fusionne(self, new):
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_change = Compte.objects.filter(moyen_credit_defaut = self).update(moyen_credit_defaut = new)
        nb_change += Compte.objects.filter(moyen_debit_defaut = self).update(moyen_debit_defaut = new)
        nb_change += Echeance.objects.filter(moyen = self).update(moyen = new)
        nb_change += Echeance.objects.filter(moyen_virement = self).update(moyen_virement = new)
        nb_change += Ope.objects.filter(moyen = self).update(moyen = new)
        self.delete()
        return nb_change


class Rapp(models.Model):
    """rapprochement d'un compte"""
    nom = models.CharField(max_length = 20, unique = True)
    date = models.DateField(null = True, blank = True, default = datetime.date.today)
    class Meta:
        db_table = 'rapp'
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
            raise TypeError
    @property
    def solde(self):
        req = self.ope_set.aggregate(solde = models.Sum('montant'))
        if req['solde'] is None:
            solde = 0
        else:
            solde = req['solde']
        return solde

    def fusionne(self, new):
        self.alters_data = True
        if type(new) != type(self):
            raise TypeError("pas la meme classe d'objet")
        nb_change = Compte.objects.filter(moyen_credit_defaut = self).update(moyen_credit_defaut = new)
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

    date = models.DateField(default = datetime.date.today)
    compte = models.ForeignKey(Compte)
    montant = CurField()
    tiers = models.ForeignKey(Tiers, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    cat = models.ForeignKey(Cat, null = True, blank = True, on_delete = models.SET_NULL, default = None, verbose_name = u"catégorie")
    compte_virement = models.ForeignKey(Compte, null = True, blank = True, related_name = 'compte_virement_set', default = None)
    moyen = models.ForeignKey(Moyen, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    moyen_virement = models.ForeignKey(Moyen, null = True, blank = True, related_name = 'moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    ib = models.ForeignKey(Ib, null = True, blank = True, on_delete = models.SET_NULL, default = None, verbose_name = u"imputation")
    notes = models.TextField(blank = True, default = "")
    inscription_automatique = models.BooleanField(default = False)
    periodicite = models.CharField(max_length = 1, choices = typesperiod, default = "u")
    intervalle = models.IntegerField(default = 0)
    periode_perso = models.CharField(max_length = 1, choices = typesperiodperso, blank = True, default = "")
    date_limite = models.DateField(null = True, blank = True, default = None)
    class Meta:
        db_table = 'echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"echéances"
        ordering = ['date']
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
    titre = models.CharField(max_length = 120, blank = True, default = "isbi")
    utilise_exercices = models.BooleanField(default = True)
    utilise_ib = models.BooleanField(default = True)
    utilise_pc = models.BooleanField(default = False)
    affiche_clot = models.BooleanField(default = True)
    class Meta:
        db_table = 'generalite'
        verbose_name = u"généralités"
        verbose_name_plural = u'généralités'

    def __unicode__(self):
        return u"%s" % (self.id,)

    @staticmethod
    def gen():
        try:
            gen_1 = Generalite.objects.get(id = 1)
        except Generalite.DoesNotExist:
            Generalite.objects.create(id = 1)
            gen_1 = Generalite.objects.get(id = 1)
        return gen_1

    @staticmethod
    def dev_g():
        return settings.DEVISE_GENERALE

class Ope(models.Model):
    """operation"""
    compte = models.ForeignKey(Compte)
    date = models.DateField(default = datetime.date.today)
    date_val = models.DateField(null = True, blank = True, default = None)
    montant = CurField()
    tiers = models.ForeignKey(Tiers, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    cat = models.ForeignKey(Cat, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    notes = models.TextField(blank = True)
    moyen = models.ForeignKey(Moyen, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    num_cheque = models.CharField(max_length = 120, blank = True, default = '')
    pointe = models.BooleanField(default = False)
    rapp = models.ForeignKey(Rapp, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    exercice = models.ForeignKey(Exercice, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    ib = models.ForeignKey(Ib, null = True, blank = True, on_delete = models.SET_NULL, default = None)
    jumelle = models.OneToOneField('self', null = True, blank = True, related_name = 'jumelle_set', default = None, editable = False)
    mere = models.ForeignKey('self', null = True, blank = True, related_name = 'filles_set', default = None, editable = False)
    automatique = models.BooleanField(default = False)
    piece_comptable = models.CharField(max_length = 120, blank = True, default = '')

    class Meta:
        db_table = 'ope'
        get_latest_by = 'date'
        order_with_respect_to = 'compte'
        verbose_name = u"opération"
        ordering = ['date']
        permissions = (
            ('can_import', 'peut importer des fichiers'),
            ('can_export', 'peut exporter des fichiers'),
        )

    @staticmethod
    def non_meres():
        return Ope.objects.filter(mere = None)

    def __unicode__(self):
        return u"(%s) le %s : %s %s" % (self.id, self.date, self.montant, settings.DEVISE_GENERALE)

    @models.permalink
    def get_absolute_url(self):
        return ('gsb_ope_detail', (), {'pk':str(self.id)})
    def clean(self):
        self.alters_data = True
        super(Ope, self).clean()
        #verification qu'il n'y ni pointe ni rapprochee
        if self.pointe and self.rapp is not None:
            raise ValidationError(u"cette operation ne peut pas etre a la fois pointée et rapprochée")

    def save(self, *args, **kwargs):
        self.alters_data = True
        if not self.moyen:
            if self.compte.moyen_credit_defaut and self.montant >= 0:
                self.moyen = self.compte.moyen_credit_defaut
            if self.compte.moyen_debit_defaut and self.montant <= 0:
                self.moyen = self.compte.moyen_debit_defaut
        super(Ope, self).save(*args, **kwargs)


class Virement(object):
    """raccourci pour creer un virement entre deux comptes"""
    def __init__(self, ope = None):
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
            tier = Tiers.objects.get_or_create(nom = nom_tiers, defaults = {'nom':nom_tiers})[0]
            self.origine.tiers = tier
            self.dest.tiers = tier
            self.origine.save()
            self.dest.save()
        else:
            raise Gsb_exc('pas initialise')

    @staticmethod
    def create(compte_origine, compte_dest, montant, date = None, notes = ""):
        '''
        cree un nouveau virement
        '''
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
               'pointe':self.pointe,
               'piece_comptable_compte_origine':self.origine.piece_comptable,
               'piece_comptable_compte_destination':self.dest.piece_comptable}
            if self.origine.moyen:
                tab['moyen_origine'] = self.origine.moyen.id
            else:
                tab['moyen_origine'] = None
            if self.dest.moyen:
                tab['moyen_destination'] = self.dest.moyen.id
            else:
                tab['moyen_destination'] = None
        else:
            raise Exception('attention, on ne peut intialiser un form que si virement est bound')
        return tab

    def __unicode__(self):
        return "%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)

