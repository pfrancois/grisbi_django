# -*- coding: utf-8 -*-

from django.db import models
import datetime

class Tiers(models.Model):
    nom = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = u'tiers'
        verbose_name_plural = u'tiers'
    def __unicode__(self):
        return self.nom

class Devise(models.Model):
    nom = models.CharField(max_length=120)
    dernier_tx_de_change = models.FloatField(default=1.0, help_text = u"il faut creer un cours")
    date_dernier_change  = models.DateField(default=datetime.date.today, help_text = u"il faut creer un cours")
    isocode = models.CharField(max_length=3, unique=True)
    class Meta:
        db_table = u'devise'
    def __unicode__(self):
        return self.isocode

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
    def __unicode__(self):
        return self.isin
    def latest_c (self):
        req = Ope.objects.filter(compte__pk = self.id, mere__exact = None).aggregate(solde = models.Sum('montant'))
        return req['solde']

class Cours(models.Model):
    valeur = models.FloatField()
    isin = models.ForeignKey(Titre, to_field = "isin")
    date = models.DateField(default = datetime.date.today)
    class Meta:
        db_table = u'cours'
        verbose_name_plural = u'cours'
        unique_together = ("isin", "date")
    def __unicode__(self):
        return u"%s le %s : %s" % (self.isin, self.date, self.valeur)


class Banque(models.Model):
    cib = models.CharField(max_length=15, blank=True)
    nom = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = u'banque'
    def __unicode__(self):
        return self.nom

class Cat(models.Model):
    typesdep = (
        (u'r',u'recette'),
        (u'd',u'depense'),
        (u'v',u'virement')
    )
    nom = models.CharField(max_length=120)
    typecat = models.CharField(max_length=1, choices=typesdep, default=u'd', verbose_name="type de la catégorie")
    class Meta:
        db_table = u'cat'
        verbose_name = u"catégorie"
    def __unicode__(self):
        return self.nom


class Scat(models.Model):
    cat = models.ForeignKey(Cat)
    nom = models.CharField(max_length=120)
    grisbi_id = models.IntegerField(verbose_name=u"id dans cette catégorie")
    class Meta:
        db_table = u'scat'
        order_with_respect_to = u'cat'
        unique_together = (u"cat", u"grisbi_id")
        verbose_name = u"sous-catégorie"
    def __unicode__(self):
        return self.nom

class Ib(models.Model):
    nom = models.CharField(max_length=120)
    typeimp = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    class Meta:
        db_table = u'ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
    def __unicode__(self):
        return self.nom

class Sib(models.Model):
    nom = models.CharField(max_length=120)
    grisbi_id = models.IntegerField(verbose_name=u"id dans cette imputation")
    ib = models.ForeignKey(Ib)
    class Meta:
        db_table = u'sib'
        order_with_respect_to = u'ib'
        unique_together = (u"ib", u"grisbi_id")
        verbose_name = u"sous-imputation budgétaire"
        verbose_name_plural = u'sous-imputations budgétaires'
    def __unicode__(self):
        return self.nom

class Exercice(models.Model):
    date_debut = models.DateField(default=datetime.date.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=120)
    class Meta:
        db_table = u'exercice'
    def __unicode__(self):
        return u"%s au %s" % (self.date_debut, self.date_fin)

class Compte(models.Model):
    typescpt = (
        (u'b',u'bancaire'),
        (u'e',u'espece'),
        (u'a',u'actif'),
        (u'p',u'passif')
    )
    nom = models.CharField(max_length=120)
    titulaire = models.CharField(max_length=120, blank=True)
    type = models.CharField(max_length=24, choices=typescpt)
    devise = models.ForeignKey(Devise)
    banque = models.ForeignKey(Banque, null=True, blank=True, on_delete=models.SET_NULL)
    guichet = models.CharField(max_length=15, blank=True)
    num_compte = models.CharField(max_length=60, blank=True)
    cle_compte = models.IntegerField(null=True, blank=True)
    solde_init = models.FloatField(default=0)
    solde_mini_voulu = models.FloatField(null=True, blank=True)
    solde_mini_autorise = models.FloatField(null=True, blank=True)
    date_dernier_releve = models.DateField(null=True, blank=True, default=datetime.date.today)
    solde_dernier_releve = models.FloatField(null=True, blank=True)
    cloture = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = u'compte'
    def __unicode__(self):
        return self.nom
    def solde(self):
        req = Ope.objects.filter(compte__id__exact=self.id,mere__exact=None).aggregate(solde=models.Sum('montant'))
        if req['solde'] == None:
            solde = 0 + self.solde_init
        else:
            solde = req['solde'] + self.solde_init
        return solde

class Moyen(models.Model):
    compte = models.ForeignKey(Compte)
    nom = models.CharField(max_length=120, )
    signe = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    affiche_numero = models.BooleanField(default=False)
    num_auto = models.BooleanField(default=False)
    num_en_cours = models.BigIntegerField(null=True, blank=True)
    grisbi_id = models.IntegerField(verbose_name=u"id dans ce compte")
    class Meta:
        db_table = u'moyen'
        verbose_name = u"moyen de paiment"
        verbose_name_plural = u"moyens de paiment"
        unique_together = ("compte", "grisbi_id")
    def __unicode__(self):
        return self.nom

class Rapp(models.Model):
    nom = models.CharField(max_length=120)
    compte = models.ForeignKey(Compte, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        db_table = u'rapp'
        verbose_name = u"rapprochement"
    def __unicode__(self):
        return self.nom


class Echeance(models.Model):
    date_ech = models.DateField(default=datetime.date.today)
    compte = models.ForeignKey(Compte)
    montant = models.FloatField()
    devise = models.ForeignKey(Devise)
    tiers = models.ForeignKey(Tiers)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL)
    scat = models.ForeignKey(Scat, null=True, blank=True, on_delete=models.SET_NULL)
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name=u'compte_virement_set')
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True,related_name=u'moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL)
    sib = models.ForeignKey(Sib, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    inscription_automatique = models.BooleanField(default=False)
    periodicite = models.TextField(default=False)
    intervalle = models.IntegerField()
    periode_perso = models.TextField(blank=True)
    date_limite = models.DateField(null=True, blank=True)
    class Meta:
        db_table = u'echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"Echéances"
    def __unicode__(self):
        return u"%s" % (self.id)

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
    def __unicode__(self):
        return u"%s" % (self.id)

class Ope(models.Model):
    typescpt = (
        (u'na',u'rien'),
        (u'p',u'pointée'),
        (u'r',u'raprochée')
    )
    compte = models.ForeignKey(Compte)
    date = models.DateField(default=datetime.date.today)
    date_val = models.DateField(null=True, blank=True)
    montant = models.FloatField()
    devise = models.ForeignKey(Devise)
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL)
    scat = models.ForeignKey(Scat, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL)
    numcheque = models.CharField(max_length=120, blank=True)
    pointe = models.CharField(max_length=2, choices=typescpt, default=u'na')
    rapp = models.ForeignKey(Rapp, null=True, blank=True, on_delete=models.SET_NULL)
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL)
    sib = models.ForeignKey(Sib, null=True, blank=True, on_delete=models.SET_NULL)
    jumelle = models.ForeignKey('self', null=True, blank=True, related_name=u'+')
    mere = models.ForeignKey('self', null=True, blank=True, related_name=u'filles_set')
    is_mere = models.BooleanField(default=False, help_text=u"permet d'eviter de faire de nombreuses requetes")
    class Meta:
        db_table = u'ope'
        get_latest_by = u'date'
        order_with_respect_to = 'compte'
        verbose_name = u"opération"
    def __unicode__(self):
        return u"%s" % (self.id)
