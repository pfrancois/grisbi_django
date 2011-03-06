# -*- coding: utf-8 -*-

from django.db import models
import datetime

class Tiers(models.Model):
    
    nom = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = u'tiers'
        verbose_name_plural = u'tiers'


class Devise(models.Model):
    
    nom = models.CharField(max_length=120)
    dernier_tx_de_change = models.FloatField(default=1.0, editable=False, help_text = u"il faut creer un cours")
    date_dernier_change  = models.DateField(default=datetime.date.today, editable=False, help_text = u"il faut creer un cours")
    isocode = models.CharField(max_length=3,unique=True)
    class Meta:
        db_table = u'devise'

class Titre(models.Model):
    typestitres = (
        (u'ACT', u'action'),
        (u'OPC', u'opcvm'),
        (u'LIV', u'compte sur livret'),
        (u'DEV', u'devise'),
        (u'OBL', u'obligation'),
        (u'ZZZ', u'autre')
    )
    nom = models.CharField(max_length=120)
    isin = models.CharField(max_length=60, primary_key=True)
    tiers = models.ForeignKey(Tiers)
    type = models.CharField(max_length=60, choices=typestitres)
    class Meta:
        db_table = u'titre'

class Cours(models.Model):
    valeur = models.FloatField()
    isin = models.BigIntegerField()
    date_cours = models.DateField(default=datetime.date.today)
    class Meta:
        db_table = u'cours'
        unique_together = ("isin", "date_cours")


class Banque(models.Model):
    
    cib = models.CharField(max_length=15, blank=True)
    nom = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = u'banque'

class Cat(models.Model):
    typesdep = (
        (u'r',u'recette'),
        (u'd',u'depense'),
        (u'v',u'virement')
    )
    
    nom = models.CharField(max_length=120)
    typecat = models.CharField(max_length=1, choices=typesdep, default=u'd')
    class Meta:
        db_table = u'cat'
        verbose_name = u"catégorie"

class Scat(models.Model):
    
    cat = models.ForeignKey(Cat)
    nom = models.CharField(max_length=120)
    grisbi_id = models.BigIntegerField()
    class Meta:
        db_table = u'scat'
        order_with_respect_to = u'cat'
        unique_together = (u"cat", u"grisbi_id")
        verbose_name = u"sous-catégorie"


class Ib(models.Model):
    
    nom = models.CharField(max_length=120)
    typeimp = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    class Meta:
        db_table = u'ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'

class Sib(models.Model):
    
    nom = models.CharField(max_length=120)
    grisbi_id = models.BigIntegerField()
    ib = models.ForeignKey(Ib)
    class Meta:
        db_table = u'sib'
        order_with_respect_to = u'ib'
        unique_together = (u"ib", u"grisbi_id")
        verbose_name = u"sous-imputation budgétaire"
        verbose_name_plural = u'sous-imputations budgétaires'

class Exercice(models.Model):
    
    date_debut = models.DateField(default=datetime.date.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=120)
    class Meta:
        db_table = u'exercice'

class Compte(models.Model):
    typescpt = (
        (u'bq',u'bancaire'),
        (u'esp',u'espece'),
        (u'a',u'actif'),
        (u'p',u'passif')
    )   
    
    nom = models.CharField(max_length=120)
    titulaire = models.CharField(max_length=120, blank=True)
    type = models.CharField(max_length=24, choices=typescpt)
    devise = models.ForeignKey(Devise)
    banque = models.ForeignKey(Banque, null=True, blank=True)
    guichet = models.CharField(max_length=15, blank=True)
    num_compte = models.CharField(max_length=60, blank=True)
    cle_compte = models.BigIntegerField(null=True, blank=True)
    solde_init = models.FloatField(default=0)
    solde_mini_voulu = models.FloatField(null=True, blank=True)
    solde_mini_autorise = models.FloatField(null=True, blank=True)
    date_dernier_releve = models.DateField(null=True, blank=True, default=datetime.date.today)
    solde_dernier_releve = models.FloatField(null=True, blank=True)
    compte_cloture = models.BooleanField(default=False)
    nb_lignes_ope = models.BigIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = u'compte'

class Moyen(models.Model):
    
    compte = models.ForeignKey(Compte)
    nom = models.CharField(max_length=120)
    signe = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    affiche_numero = models.BooleanField(default=False)
    num_auto = models.BooleanField(default=False)
    num_en_cours = models.BigIntegerField(null=True, blank=True)
    grisbi_id = models.BigIntegerField()
    class Meta:
        db_table = u'moyen'
        unique_together = ("compte", "grisbi_id")

class Rapp(models.Model):
  
    nom = models.CharField(max_length=120)
    date = models.DateField(default=datetime.date.today)
    compte = models.ForeignKey(Compte, null=True, blank=True)
    class Meta:
        db_table = u'rapp'
        verbose_name = u"rapprochement"
        verbose_name_plural = u'rapprochement'

class Echeance(models.Model):
    
    date_ech = models.DateField(default=datetime.date.today)
    compte = models.ForeignKey(Compte)
    montant = models.FloatField()
    devise = models.ForeignKey(Devise)
    tiers = models.ForeignKey(Tiers)
    Cat = models.ForeignKey(Cat, null=True, blank=True)
    Scat = models.ForeignKey(Scat, null=True, blank=True)
    compte_virement = models.ForeignKey(Compte, null=True, blank=True,related_name=u'compte_virement_set')
    moyen = models.ForeignKey(Moyen, null=True, blank=True)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True,related_name=u'moyen_virement_set')
    Exercice = models.ForeignKey(Exercice, null=True, blank=True)
    ib = models.ForeignKey(Ib, null=True, blank=True)
    sib = models.ForeignKey(Sib, null=True, blank=True)
    notes = models.TextField(blank=True)
    inscription_automatique = models.BooleanField(default=False)
    periodicite = models.TextField(default=False)
    intervalle = models.BigIntegerField()
    periode_perso = models.TextField(blank=True)
    date_limite = models.DateField(null=True, blank=True)
    class Meta:
        db_table = u'echeance'
        verbose_name = u"échéance"
        verbose_name = u"Echéances"

class Generalite(models.Model):
    
    titre = models.CharField(max_length=120, blank=True)
    utilise_exercices = models.BooleanField(default=True)
    utilise_ib = models.BooleanField(default=True)
    utilise_pc = models.BooleanField(default=False)
    devise_generale = models.ForeignKey(Devise)
    class Meta:
        db_table = u'generalite'
        verbose_name = u"généralités"
        verbose_name_plural = u'généralités'


class Ope(models.Model):
    typescpt = (
        (u'na',u'rien'),
        (u'p',u'pointée'),
        (u'r',u'raprochée')
    )   

    compte = models.ForeignKey(Compte)
    date_ope = models.DateField(default=datetime.date.today)
    date_val = models.DateField(null=True, blank=True)
    montant = models.FloatField()
    devise = models.ForeignKey(Devise)
    tiers = models.ForeignKey(Tiers, null=True, blank=True)
    Cat = models.ForeignKey(Cat, null=True, blank=True)
    Scat = models.ForeignKey(Scat, null=True, blank=True)
    is_mere = models.BooleanField(default=False, editable=False, help_text=u"pas editable car change automatique")
    notes = models.TextField(blank=True)
    Moyen = models.ForeignKey(Moyen, null=True, blank=True)
    numcheque = models.CharField(max_length=120, blank=True)
    pointe = models.CharField(max_length=2, choices=typescpt, default=u'na')
    rapp = models.ForeignKey(Rapp, null=True, blank=True)
    Exercice = models.ForeignKey(Exercice, null=True, blank=True)
    ib = models.ForeignKey(Ib, null=True, blank=True)
    sib = models.ForeignKey(Sib, null=True, blank=True)
    jumelle = models.ForeignKey('self', null=True, blank=True, related_name=u'+')
    mere = models.ForeignKey('self', null=True, blank=True, related_name=u'filles_set')
    class Meta:
        db_table = u'ope'
        get_latest_by = u'date_ope'
        order_with_respect_to = 'compte'
        verbose_name = u"opération"
