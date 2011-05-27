# -*- coding: utf-8 -*-

from django.db import models
import datetime

class Tiers(models.Model):
    nom = models.CharField(max_length=40,unique=True)
    notes = models.TextField(blank=True)
    is_titre = models.BooleanField(default=False)

    class Meta:
        db_table = 'tiers'
        verbose_name_plural = u'tiers'
        ordering = ['nom']


    def __unicode__(self):
        return self.nom

class Titre(models.Model):
    typestitres = (
    ('ACT', u'action'),
    ('OPC', u'opcvm'),
    ('CSL', u'compte sur livret'),
    ('DEV', u'devise'),
    ('OBL', u'obligation'),
    ('ZZZ', u'autre')
    )
    nom = models.CharField(max_length=40,unique=True)
    isin = models.CharField(max_length=60, unique=True)
    tiers = models.ForeignKey(Tiers,null=True,blank=True)
    type = models.CharField(max_length=60, choices=typestitres)
    class Meta:
        db_table = u'titre'
        ordering = ['nom']

    def __unicode__(self):
        return "%s (%s)" % (self.nom, self.isin)
    def last_cours(self):
        return self.cours_set.latest()
    def devise():
        return Titre.objects.filter(type='DEV')
    devise=staticmethod(devise)

class Cours(models.Model):
    valeur = models.DecimalField(max_digits=15, decimal_places=3, default=1.000)
    isin = models.ForeignKey(Titre, to_field="isin", unique_for_date="date")
    date = models.DateField(default=datetime.date.today)
    class Meta:
        db_table = 'cours'
        verbose_name_plural = u'cours'
        unique_together = ("isin", "date")
        ordering = ['date']
        get_latest_by= 'date'


    def __unicode__(self):
        return u"%s le %s : %s" % (self.isin, self.date, self.valeur)


class Banque(models.Model):
    cib = models.CharField(max_length=15, blank=True)
    nom = models.CharField(max_length=40,unique=True)
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
    nom = models.CharField(max_length=60,unique=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d', verbose_name="type de la catégorie")
    class Meta:
        db_table = 'cat'
        verbose_name = u"catégorie"
        ordering = ['nom']

    def __unicode__(self):
        return self.nom


class Ib(models.Model):
    nom = models.CharField(max_length=60,unique=True)
    type = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    class Meta:
        db_table = 'ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

class Exercice(models.Model):
    date_debut = models.DateField(default=datetime.date.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=40,unique=True)
    class Meta:
        db_table = 'exercice'
        ordering = ['date_debut']
        get_latest_by= 'date_debut'

    def __unicode__(self):
        return u"%s au %s" % (self.date_debut.strftime("%d/%m/%Y"), self.date_fin.strftime("%d/%m/%Y"))


class Compte(models.Model):
    typescpt = (
    ('b', u'bancaire'),
    ('e', u'espece'),
    ('a', u'actif'),
    ('p', u'passif')
    )
    nom = models.CharField(max_length=40,unique=True)
    titulaire = models.CharField(max_length=120, blank=True, default='')
    type = models.CharField(max_length=24, choices=typescpt, default='b')
    devise = models.ForeignKey(Titre)
    banque = models.ForeignKey(Banque, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    guichet = models.CharField(max_length=15, blank=True, default='')#il est en charfield comme celui d'en dessous parce qu'on n'est pas sur qu'il ny ait que des chiffres
    num_compte = models.CharField(max_length=60, blank=True, default='')
    cle_compte = models.IntegerField(null=True, blank=True, default=0)
    solde_init = models.DecimalField(max_digits=15, decimal_places=3, default=0.000)
    solde_mini_voulu = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True, default=0.000)
    solde_mini_autorise = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True, default=0.000)
    cloture = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    moyen_credit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL, related_name="moyen_credit_set", default=None)
    moyen_debit_defaut = models.ForeignKey('Moyen', null=True, blank=True, on_delete=models.SET_NULL, related_name="moyen_debit_set", default=None)
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
            solde = solde / self.devise.last_cours().valeur
            return solde
        else:
            return solde


class Moyen(models.Model):
    typesdep = (
    ('v', u'virement'),
    ('d', u'depense'),
    ('r', u'recette'),
    )
    nom = models.CharField(max_length=20,unique=True)
    type = models.CharField(max_length=1, choices=typesdep,default='d')
    class Meta:
        db_table = 'moyen'
        verbose_name = u"moyen de paiment"
        verbose_name_plural = u"moyens de paiment"
        ordering = ['nom']

    def __unicode__(self):
        return self.nom


class Rapp(models.Model):
    nom = models.CharField(max_length=20,unique=True)
    date = models.DateField(null=True, blank=True, default=datetime.date.today)
    class Meta:
        db_table = 'rapp'
        verbose_name = u"rapprochement"
        ordering = ['nom']
        get_latest_by= 'date'


    def __unicode__(self):
        return self.nom

    def compte(self):#petit raccourci mais normalement, c'est bon. on prend le compte de la premiere ope
        if self.ope_set.all():
            return self.ope_set.all()[0].compte.id
        else:
            raise TypeError
    def solde(self, devise_generale=False):
        req = self.ope_set.aggregate(solde=models.Sum('montant'))
        if req['solde'] is None:
            solde = 0
        else:
            solde = req['solde']
        if devise_generale:
            solde = solde / self.compte().devise.last_cours().valeur
            return solde
        else:
            return solde

class Echeance(models.Model):
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
        ('na','non applicable')
    )

    date = models.DateField(default=datetime.date.today)
    compte = models.ForeignKey(Compte)
    montant = models.DecimalField(max_digits=15, decimal_places=3, default=0.000)
    devise = models.ForeignKey(Titre, default=None)
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name='compte_virement_set', default=None)
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True, related_name='moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    notes = models.TextField(blank=True, default="")
    inscription_automatique = models.BooleanField(default=False)
    periodicite = models.CharField(max_length=1, choices=typesperiod, default="u")
    intervalle = models.IntegerField(default=0)
    periode_perso = models.CharField(max_length=1, choices=typesperiodperso, blank=True, default="")
    date_limite = models.DateField(null=True, blank=True, default=None)
    class Meta:
        db_table = 'echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"Echéances"
        ordering = ['date']
        get_latest_by= 'date'

    def __unicode__(self):
        return u"%s" % (self.id,)


class Generalite(models.Model):
    titre = models.CharField(max_length=120, blank=True, default="grisbi")
    utilise_exercices = models.BooleanField(default=True)
    utilise_ib = models.BooleanField(default=True)
    utilise_pc = models.BooleanField(default=False)
    devise_generale = models.ForeignKey(Titre)
    affiche_clot = models.BooleanField(default=True)
    class Meta:
        db_table = 'generalite'
        verbose_name = u"généralités"
        verbose_name_plural = u'généralités'


    def __unicode__(self):
        return u"%s" % (self.id,)
    def gen():
        return Generalite.objects.get(id=1)
    gen=staticmethod(gen)

class Ope(models.Model):
    compte = models.ForeignKey(Compte)
    date = models.DateField(default=datetime.date.today)
    date_val = models.DateField(null=True, blank=True, default=None)
    montant = models.DecimalField(max_digits=15, decimal_places=3, default=0.000)
    tiers = models.ForeignKey(Tiers, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    notes = models.TextField(blank=True)
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    num_cheque = models.CharField(max_length=120, blank=True, default='')
    pointe = models.BooleanField(default=False)
    rapp = models.ForeignKey(Rapp, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    jumelle = models.OneToOneField('self', null=True, blank=True, related_name='jumelle_set', default=None)
    mere = models.ForeignKey('self', null=True, blank=True, related_name='filles_set', default=None)
    automatique = models.BooleanField(default=False)
    piece_comptable = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        db_table = 'ope'
        get_latest_by = 'date'
        order_with_respect_to = 'compte'
        verbose_name = u"opération"
        ordering = ['date']
        permissions = (
            ('can_import','peut importer des fichiers'),
            ('can_export','peut exporter des fichiers'),
        )

    def non_meres():
        return Ope.objects.filter(mere=None)
    non_meres=staticmethod(non_meres)
    def __unicode__(self):
        return u"(%s) le %s : %s %s" % (self.id,self.date,self.montant,self.compte.devise.isin)
