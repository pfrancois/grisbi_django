# -*- coding: utf-8 -*-

from django.db import models
import datetime

class champs(models.Model):
    class Meta:
        abstract = True


    def save(self, *args, **kwargs):
        super(champs, self).save(*args, **kwargs)


class Tiers(models.Model):
    nom = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    is_titre = models.BooleanField(default=False)

    class Meta:
        db_table = 'tiers'
        verbose_name_plural = u'tiers'
        ordering = ['nom']


    def __unicode__(self):
        return self.nom


class Devise(models.Model):
    nom = models.CharField(max_length=120)
    dernier_tx_de_change = models.DecimalField(max_digits=15, decimal_places=3, default='1.000')
    date_dernier_change = models.DateField(default=datetime.date.today, help_text=u"il faut creer un cours")
    isocode = models.CharField(max_length=3, unique=True)
    class Meta:
        db_table = 'devise'
        ordering = ['nom']


    def __unicode__(self):
        return self.isocode


class Titre(models.Model):
    typestitres = (
    ('ACT', u'action'),
    ('OPC', u'opcvm'),
    ('CSL', u'compte sur livret'),
    ('DEV', u'devise'),
    ('OBL', u'obligation'),
    ('ZZZ', u'autre')
    )
    nom = models.CharField(max_length=120)
    isin = models.CharField(max_length=60, unique=True)
    tiers = models.ForeignKey(Tiers)
    type = models.CharField(max_length=60, choices=typestitres)
    class Meta:
        db_table = u'titre'
        ordering = ['nom']


    def __unicode__(self):
        return "%s (%s)" % (self.nom, self.isin)

    def latest_cours (self):
        r = Cours.objects.filter(isin=self.isin).order_by("-date")[0]
        return r


class Cours(models.Model):
    valeur = models.DecimalField(max_digits=15, decimal_places=3, default=1.000)
    isin = models.ForeignKey(Titre, to_field="isin")
    date = models.DateField(default=datetime.date.today)
    class Meta:
        db_table = 'cours'
        verbose_name_plural = u'cours'
        unique_together = ("isin", "date")
        ordering = ['date']


    def __unicode__(self):
        return u"%s le %s : %s" % (self.isin, self.date, self.valeur)


class Banque(models.Model):
    cib = models.CharField(max_length=15, blank=True)
    nom = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = 'banque'
        ordering = ['nom']


    def __unicode__(self):
        return self.nom


class Cat(models.Model):
    typesdep = (
    ('r', u'recette'),
    ('d', u'depense'),
    ('v', u'virement')
    )
    nom = models.CharField(max_length=120)
    type = models.CharField(max_length=1, choices=typesdep, default='d', verbose_name="type de la catégorie")
    class Meta:
        db_table = 'cat'
        verbose_name = u"catégorie"
        ordering = ['nom']


    def __unicode__(self):
        return self.nom


class Scat(models.Model):
    cat = models.ForeignKey(Cat)
    nom = models.CharField(max_length=120)
    grisbi_id = models.IntegerField(verbose_name=u"id dans cette catégorie")
    class Meta:
        db_table = 'scat'
        order_with_respect_to = 'cat'
        unique_together = ("cat", "grisbi_id")
        verbose_name = u"sous-catégorie"


    def __unicode__(self):
        return self.nom


class Ib(models.Model):
    nom = models.CharField(max_length=120)
    type = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    class Meta:
        db_table = 'ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
        ordering = ['nom']


    def __unicode__(self):
        return self.nom


class Sib(models.Model):
    nom = models.CharField(max_length=120)
    grisbi_id = models.IntegerField(verbose_name=u"id dans cette imputation")
    ib = models.ForeignKey(Ib)
    class Meta:
        db_table = 'sib'
        order_with_respect_to = 'ib'
        unique_together = ("ib", "grisbi_id")
        verbose_name = u"sous-imputation budgétaire"
        verbose_name_plural = u'sous-imputations budgétaires'


    def __unicode__(self):
        return self.nom


class Exercice(models.Model):
    date_debut = models.DateField(default=datetime.date.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=120)
    class Meta:
        db_table = 'exercice'
        ordering = ['date_debut']


    def __unicode__(self):
        return u"%s au %s" % (self.date_debut, self.date_fin)


class Compte(models.Model):
    typescpt = (
    ('b', u'bancaire'),
    ('e', u'espece'),
    ('a', u'actif'),
    ('p', u'passif')
    )
    nom = models.CharField(max_length=120)
    titulaire = models.CharField(max_length=120, blank=True, default='')
    type = models.CharField(max_length=24, choices=typescpt)
    devise = models.ForeignKey(Devise)
    banque = models.ForeignKey(Banque, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    guichet = models.CharField(max_length=15, blank=True)
    num_compte = models.CharField(max_length=60, blank=True)
    cle_compte = models.IntegerField(null=True, blank=True)
    solde_init = models.DecimalField(max_digits=15, decimal_places=3, default=0.000)
    solde_mini_voulu = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    solde_mini_autorise = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    cloture = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    moyen_credit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL,
                                            related_name="moyen_credit_set")
    moyen_debit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL,
                                           related_name="moyen_debit_set")
    class Meta:
        db_table = 'compte'


    def __unicode__(self):
        return self.nom

    def solde(self, devise_generale=False):
        req = Ope.objects.filter(compte__id__exact=self.id, mere__exact=None).aggregate(solde=models.Sum('montant'))
        if req['solde'] is None:
            solde = 0 + self.solde_init
        else:
            solde = req['solde'] + self.solde_init
        if devise_generale:
            solde = solde / self.devise.dernier_tx_de_change
            return solde
        else:
            return solde


class Moyen(models.Model):
    typesdep = (
    ('v', u'virement'),
    ('d', u'depense'),
    ('r', u'recette'),
    )
    compte = models.ForeignKey(Compte)
    nom = models.CharField(max_length=120)
    signe = models.CharField(max_length=1, choices=typesdep, blank=True)
    affiche_numero = models.BooleanField(default=False)
    num_auto = models.BooleanField(default=False)
    num_en_cours = models.BigIntegerField(null=True, blank=True)
    grisbi_id = models.IntegerField(verbose_name=u"id dans ce compte")
    class Meta:
        db_table = 'moyen'
        verbose_name = u"moyen de paiment"
        verbose_name_plural = u"moyens de paiment"
        unique_together = ("compte", "grisbi_id")
        ordering = ['nom']


    def __unicode__(self):
        return self.nom


class Rapp(models.Model):
    nom = models.CharField(max_length=120)
    date = models.DateField(null=True, blank=True, default=datetime.date.today)
    solde = models.FloatField(default=0)
    class Meta:
        db_table = 'rapp'
        verbose_name = u"rapprochement"
        ordering = ['nom']


    def __unicode__(self):
        return self.nom

    def compte(self):#petit raccourci mais normalement, c'est bon. on prend le compte de la premiere ope
        if self.ope_set.all():
            return self.ope_set.all()[0].compte.id


class Echeance(models.Model):
    date = models.DateField(default=datetime.date.today)
    compte = models.ForeignKey(Compte)
    montant = models.DecimalField(max_digits=15, decimal_places=3, default=0.000)
    devise = models.ForeignKey(Devise)
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    scat = models.ForeignKey(Scat, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name='compte_virement_set')
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True, related_name='moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    sib = models.ForeignKey(Sib, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    notes = models.TextField(blank=True, default="")
    inscription_automatique = models.BooleanField(default=False)
    periodicite = models.TextField(default="")#TODO gerer ca
    intervalle = models.IntegerField(default=0)
    periode_perso = models.TextField(blank=True, default="")
    date_limite = models.DateField(null=True, blank=True, default=None)
    class Meta:
        db_table = 'echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"Echéances"
        ordering = ['date']


    def __unicode__(self):
        return u"%s" % (self.id,)


class Generalite(models.Model):
    titre = models.CharField(max_length=120, blank=True)
    utilise_exercices = models.BooleanField(default=True)
    utilise_ib = models.BooleanField(default=True)
    utilise_pc = models.BooleanField(default=False)
    devise_generale = models.ForeignKey(Devise)
    class Meta:
        db_table = 'generalite'
        verbose_name = u"généralités"
        verbose_name_plural = u'généralités'


    def __unicode__(self):
        return u"%s" % (self.id,)


class Ope(models.Model):
    typespointage = (
    ('na', u'rien'),
    ('p', u'pointée'),
    ('r', u'raprochée')
    )
    compte = models.ForeignKey(Compte)
    date = models.DateField(default=datetime.date.today)
    date_val = models.DateField(null=True, blank=True, default=None)
    montant = models.DecimalField(max_digits=15, decimal_places=3, default=0.000)
    devise = models.ForeignKey(Devise)
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    scat = models.ForeignKey(Scat, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    notes = models.TextField(blank=True)
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    numcheque = models.CharField(max_length=120, blank=True, default='')
    pointe = models.CharField(max_length=2, choices=typespointage, default=u'na')
    rapp = models.ForeignKey(Rapp, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    sib = models.ForeignKey(Sib, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    jumelle = models.OneToOneField('self', null=True, blank=True, related_name='jumelle_set')
    mere = models.ForeignKey('self', null=True, blank=True, related_name='filles_set')
    is_mere = models.BooleanField(default=False, help_text=u"permet d'eviter de faire de nombreuses requetes")
    class Meta:
        db_table = 'ope'
        get_latest_by = 'date'
        order_with_respect_to = 'compte'
        verbose_name = u"opération"
        ordering = ['date']


    def __unicode__(self):
        return u"%s" % (self.id,)
