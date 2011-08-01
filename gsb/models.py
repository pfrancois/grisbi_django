# -*- coding: utf-8 -*-

from django.db import models #@UnusedImport
import datetime #@UnusedImport
import decimal #@UnusedImport
from django.db import transaction #@UnusedImport
from django.conf import settings #@UnusedImport
#from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError #@UnusedImport
#from mysite.gsb.shortcuts import * #todo reflechir comment enlever cette reference circulaire
#import logging 
class gsb_exc(Exception): pass
class Ex_jumelle_neant(Exception): pass

class Tiers(models.Model):
    """
    un tiers, c'est a dire une personne ou un titre
    """
    
    nom = models.CharField(max_length = 40, unique = True)
    notes = models.TextField(blank = True)
    is_titre = models.BooleanField(default = False)

    class Meta:
        db_table = 'tiers'
        verbose_name_plural = u'tiers'
        ordering = ['nom']


    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        nb_tiers_change = Echeance.objects.select_related().filter(tiers = self).update(tiers = new)
        nb_tiers_change+=Titre.objects.select_related().filter(tiers = self).update(tiers = new)
        nb_tiers_change+=Ope.objects.select_related().filter(tiers = self).update(tiers = new)
        return nb_tiers_change

class Titre(models.Model):
    """
    les titres englobe les actifs financier mais aussi les devises
    afin de pouvoir faire le lien dans les operation, il y a un line vers les tiers
    :model:`gsb.tiers`
    """
    typestitres = (
    ('ACT', u'action'),
    ('OPC', u'opcvm'),
    ('CSL', u'compte sur livret'),
    ('DEV', u'devise'),
    ('OBL', u'obligation'),
    ('ZZZ', u'autre')
    )
    nom = models.CharField(max_length = 40, unique = True)
    isin = models.CharField(max_length = 60, unique = True)
    tiers = models.OneToOneField(Tiers, null = True, blank = True, editable = False)
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

    @staticmethod
    def devises():
        """liste des devises"""
        return Titre.objects.filter(type = 'DEV')

    @transaction.commit_on_success
    def fusionne(self, new):
        """fusionnne ce titre avec le titre new"""
        nb_change = Cours.objects.select_related().filter(titre=self).update(titre=new)
        nb_change+=Tiers.objects.select_related().filter(titre=self).update(titre=new)
        nb_change+=Titres_detenus.objects.select_related().filter(titre=self).update(titre=new)
        nb_change+=Histo_ope_titres.objects.select_related().filter(titre=self).update(titre=new)
        if self.type=='DEV':#gestion specifique des devises
            nb_change+=Compte.objects.select_related().filter(devise=self).update(devise=new)
            nb_change+=Echeance.objects.select_related().filter(devise=self).update(devise=new)
            nb_change+=Ope.objects.select_related().filter(devise=self).update(devise=new)
            nb_change+=Generalite.objects.select_related().filter(devise=self).update(devise=new)
        #on doit aussi reaffecter le tiers associe
        self.tiers.fusionne(new.tiers)
        self.delete()
        return nb_change

    def save(self, *args, **kwargs):
        if (not self.tiers) and (self.type!='DEV'):
            tiers, created = Tiers.objects.get_or_create(nom = 'titre_ %s'%self.nom, defaults = {"nom":'titre_ %s'%self.nom})
            if created:
                tiers.is_titre = True
                tiers.notes = "%s@%s" % (self.isin, self.type)#on met les notes qui vont bien
                tiers.save()
            self.tiers = tiers
        super(Titre, self).save(*args, **kwargs)

class Cours(models.Model):
    valeur = models.DecimalField(max_digits=15, decimal_places=3, default=1.000)
    titre = models.ForeignKey(Titre, unique_for_date="date")
    date = models.DateField(default=datetime.date.today)
    class Meta:
        db_table = 'cours'
        verbose_name_plural = u'cours'
        unique_together = ("titre", "date")
        ordering = ['date']
        get_latest_by= 'date'

    def __unicode__(self):
        return u"le %(date)s, 1 %(titre)s : %(valeur)s" % {'titre':self.titre.nom, 'date':self.date, 'valeur':self.valeur}


class Banque(models.Model):
    cib = models.CharField(max_length=15, blank=True)
    nom = models.CharField(max_length=40, unique=True)
    notes = models.TextField(blank=True)
    class Meta:
        db_table = 'banque'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        nb_change = Compte.objects.select_related().filter(banque=self).update(banque=new)
        self.delete()
        return nb_change


class Cat(models.Model):
    typesdep = (
    ('r', u'recette'),
    ('d', u'dépense'),
    ('v', u'virement')
    )
    nom = models.CharField(max_length=60, unique=True)
    type = models.CharField(max_length=1, choices=typesdep, default='d', verbose_name="type de la catégorie")
    class Meta:
        db_table = 'cat'
        verbose_name = u"catégorie"
        ordering = ['nom']

    def __unicode__(self):
        return self.nom
    @transaction.commit_on_success
    def fusionne(self, new):
        nb_change = Echeance.objects.select_related().filter(cat=self).update(cat=new)
        nb_change+=Ope.objects.select_related().filter(cat=self).update(cat=new)
        self.delete()
        return nb_change


class Ib(models.Model):
    nom = models.CharField(max_length=60, unique=True)
    type = models.CharField(max_length=1, choices=Cat.typesdep, default=u'd')
    class Meta:
        db_table = 'ib'
        verbose_name = u"imputation budgétaire"
        verbose_name_plural = u'imputations budgétaires'
        ordering = ['nom']

    def __unicode__(self):
        return self.nom
    @transaction.commit_on_success
    def fusionne(self, new):
        nb_change = Echeance.objects.select_related().filter(ib=self).update(ib=new)
        nb_change+=Ope.objects.select_related().filter(ib=self).update(ib=new)
        self.delete()
        return nb_change

class Exercice(models.Model):
    date_debut = models.DateField(default=datetime.date.today)
    date_fin = models.DateField(null=True, blank=True)
    nom = models.CharField(max_length=40, unique=True)
    class Meta:
        db_table = 'exercice'
        ordering = ['date_debut']
        get_latest_by = 'date_debut'

    def __unicode__(self):
        return u"%s au %s" % (self.date_debut.strftime("%d/%m/%Y"), self.date_fin.strftime("%d/%m/%Y"))
    @transaction.commit_on_success
    def fusionne(self, new):
        nb_change = Echeance.objects.select_related().filter(exercice=self).update(exercice=new)

        nb_change+=Ope.objects.select_related().filter(exercice=self).update(exercice=new)
        self.delete()
        return nb_change


class Compte(models.Model):
    typescpt = (
    ('b', u'bancaire'),
    ('e', u'espece'),
    ('p', u'passif'),
    ('t', u'titre')
    )
    nom = models.CharField(max_length=40, unique=True)
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
    ouvert= models.BooleanField(default=True)
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
            if self.devise.isin != settings.DEVISE_GENERALE:
                solde = solde / self.devise.last_cours
            return solde
        else:
            return solde

    @transaction.commit_on_success
    def fusionne(self, new):
        nb_change=Echeance.objects.select_related().filter(compte=self).update(compte=new)
        nb_change+=Echeance.objects.select_related().filter(compte_virement=self).update(compte_virement=new)
        nb_change+=Ope.objects.select_related().filter(compte=self).update(compte=new)
        self.delete()
        return nb_change

    @models.permalink
    def get_absolute_url(self):
        return ('cpt_detail', (), {'pk':str(self.id)})

    def save(self, *args, **kwargs):
        if self.type=='t' and not isinstance(self, Compte_titre):
            raise gsb_exc("il faut creer un compte titre")
        else:
            super(Compte, self).save(*args, **kwargs)
            

class Compte_titre(Compte):
    titres_detenus = models.ManyToManyField(Titre, through='Titres_detenus')
    class Meta:
        db_table = 'cpt_titre'
    @transaction.commit_on_success
    def achat(self, titre, nombre, prix=1, date=datetime.date.today(), frais='0.0', virement_de=None): #@UnusedVariable
        cat_ost, created=Cat.objects.get_or_create(nom=u"operation sur titre:", defaults={'nom':u'operation sur titre:'}) #@UnusedVariable
        cat_frais, created=Cat.objects.get_or_create(nom=u"frais bancaires:", defaults={'nom':u'frais bancaires:'})
        if isinstance(titre, Titre):
            #ajout de l'operation dans le compte_espece rattache
            Ope.objects.create(date=date,
                                montant=decimal.Decimal(str(prix))*decimal.Decimal(str(nombre))*-1,
                                tiers=titre.tiers,
                                cat=cat_ost,
                                notes="achat %s@%s"%(nombre, prix),
                                moyen=None,
                                automatique=True,
                                compte=self,
                                )
            if decimal.Decimal(str(frais)):
                self.ope_set.create(date=date,
                                montant=decimal.Decimal(str(frais))*-1,
                                tiers=titre.tiers,
                                cat=cat_frais,
                                notes="frais achat %s@%s"%(nombre, prix),
                                moyen=None,
                                automatique=True
                                )
            #gestion des cours
            if not titre.cours_set.filter(date=date).exists():
                titre.cours_set.create(date=date, valeur=prix)
            #ajout des titres dans portefeuille
            titre_detenu, created=Titres_detenus.objects.get_or_create(titre=titre, compte=self, defaults={'titre':titre, 'compte':self, 'nombre':decimal.Decimal(str(nombre))})
            if not created:
                titre_detenu.nombre=titre_detenu.nombre+decimal.Decimal(str(nombre))
                titre_detenu.save()
            Histo_ope_titres.objects.create(titre=titre_detenu.titre, nombre=titre_detenu.nombre, compte=titre_detenu.compte, date=date)
        else:
            raise Exception('attention ceci n\'est pas un titre')

    @transaction.commit_on_success
    def vente(self, titre, nombre, prix=1, date=datetime.date.today(), frais='0.0', virement_vers=None):
        cat_ost=Cat.objects.get_or_create(nom=u"operation sur titre:", defaults={'nom':u'operation sur titre:'})[0]
        cat_frais=Cat.objects.get_or_create(nom=u"frais bancaires:", defaults={'nom':u'frais bancaires:'})[0]
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            try:
                titre_detenu=Titres_detenus.objects.get(titre=titre, compte=self)
                titre_detenu.nombre=titre_detenu.nombre-decimal.Decimal(str(nombre))
                titre_detenu.save()
            except Titres_detenus.DoesNotExist:
                raise Titre.doesNotExist('titre pas en portefeuille')
            Histo_ope_titres.objects.create(titre=titre_detenu.titre, nombre=titre_detenu.nombre, compte=titre_detenu.compte, date=date)
            #ajout de l'operation dans le compte_espece ratache
            self.ope_set.create(date=date,
                                montant=decimal.Decimal(str(prix))*decimal.Decimal(str(nombre)),
                                tiers=titre.tiers,
                                cat=cat_ost,
                                notes="vente %s@%s"%(nombre, prix),
                                moyen=None,
                                automatique=True
                                )
            if decimal.Decimal(str(frais)):
                self.ope_set.create(date=date,
                                montant=decimal.Decimal(str(frais))*-1,
                                tiers=titre.tiers,
                                cat=cat_frais,
                                notes="frais vente %s@s"%(nombre, prix),
                                moyen=None,
                                automatique=True
                                )
            #gestion des cours
            if not titre.cours_set.filter(date=date).exists():
                titre.cours_set.create(date=date, valeur=prix)
        else:
            raise Exception('attention ceci n\'est pas un titre')

    @transaction.commit_on_success
    def revenu(self, titre, nombre, prix=1, date=datetime.date.today(), frais='0.0', virement_vers=None):
        cat_ost = Cat.objects.get_or_create(nom=u"operation sur titre:", defaults={'nom':u'operation sur titre:'})[0]
        cat_frais = Cat.objects.get_or_create(nom=u"frais bancaires:", defaults={'nom':u'frais bancaires:'})[0]
        if isinstance(titre, Titre):
            #extraction des titres dans portefeuille
            try:
                Titres_detenus.objects.get(titre=titre, compte=self)
            except Titres_detenus.DoesNotExist:
                raise Titre.doesNotExist('titre pas en portefeuille')
            #ajout de l'operation dans le compte_espece ratache
            self.ope_set.create(date=date,
                                montant=decimal.Decimal(str(prix))*decimal.Decimal(str(nombre)),
                                tiers=titre.tiers,
                                cat=cat_ost,
                                notes="revenu",
                                moyen=None,
                                automatique=True
                                )
            if decimal.Decimal(str(frais)):
                self.ope_set.create(date=date,
                                montant=decimal.Decimal(str(frais))*-1,
                                tiers=titre.tiers,
                                cat=cat_frais,
                                notes="frais revenu %s@%s"%(nombre, prix),
                                moyen=None,
                                automatique=True
                                )
            #gestion des cours
            if not titre.cours_set.filter(date=date):
                titre.cours_set.create(date=date, valeur=prix)
        else:
            raise Exception('attention ceci n\'est pas un titre')

    def solde(self, devise_generale=False):
        solde_espece=super(Compte_titre, self).solde(devise_generale)
        return solde_espece

    @transaction.commit_on_success
    def fusionne(self, new):
        nb_change=Echeance.objects.select_related().filter(compte=self).update(compte=new)
        nb_change+=Histo_ope_titres.objects.select_related().filter(compte=self).update(compte=new)
        nb_change+=Titres_detenus.objects.select_related().filter(compte=self).update(compte=new)
        nb_change+=Echeance.objects.select_related().filter(compte_virement=self).update(compte_virement=new)
        nb_change+=Ope.objects.select_related().filter(compte=self).update(compte=new)
        self.delete()
        return nb_change

    @models.permalink
    def get_absolute_url(self):
        return ('cpt_detail', (), {'pk':str(self.id)})

    def save(self, *args, **kwargs):
        if self.type!='t':
            self.type='t'
        super(Compte, self).save(*args, **kwargs)


class Titres_detenus(models.Model):

    titre = models.ForeignKey(Titre)
    compte = models.ForeignKey(Compte_titre, related_name='titres_detenus_set', )
    nombre = models.PositiveIntegerField()
    date = models.DateField(default=datetime.date.today)
    class Meta:
        db_table = 'titres_detenus'
        verbose_name_plural = u'titres détenus'
        verbose_name = u'titres_detenus'
        ordering = ['compte']
    def __unicode__(self):
        return"%s %s dans %s"%(self.nombre, self.titre.nom, self.compte)
    @property
    def valeur(self):
        return self.nombre*self.titre.objects.get(isin=self.isin).last_cours

class Histo_ope_titres(models.Model):
    titre = models.ForeignKey(Titre)
    compte = models.ForeignKey(Compte_titre)
    nombre = models.PositiveIntegerField()
    date = models.DateField()
    class Meta:
        db_table = 'histo_titres_detenus'
        verbose_name_plural = u'Titres détenus (historique)'
        verbose_name = u'Histo_ope_titres'
        ordering = ['compte']

class Moyen(models.Model):

    #TODO reflechir a supprimer ca
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
        return self.nom

    @transaction.commit_on_success
    def fusionne(self, new):
        nb_change = Compte.objects.select_related().filter(moyen_credit_defaut = self).update(moyen_credit_defaut = new)
        nb_change+= Compte.objects.select_related().filter(moyen_debit_defaut = self).update(moyen_debit_defaut = new)
        nb_change+= Echeance.objects.select_related().filter(moyen = self).update(moyen = new)
        nb_change+= Echeance.objects.select_related().filter(moyen_virement = self).update(moyen_virement = new)
        nb_change+= Ope.objects.select_related().filter(moyen = self).update(moyen = new)
        self.delete()
        return nb_change


class Rapp(models.Model):
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

    def solde(self, devise_generale = False):
        req = self.ope_set.aggregate(solde = models.Sum('montant'))
        if req['solde'] is None:
            solde = 0
        else:
            solde = req['solde']
        if devise_generale:
            solde = solde / self.compte.devise.last_cours
            return solde
        else:
            return solde

    def fusionne(self, new):
        nb_change = Compte.objects.select_related().filter(moyen_credit_defaut = self).update(moyen_credit_defaut = new)
        self.delete()
        return nb_change

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
        ('na', 'non applicable')
    )

    date = models.DateField(default = datetime.date.today)
    compte = models.ForeignKey(Compte)
    montant = models.DecimalField(max_digits = 15, decimal_places = 3, default = 0.000)
    devise = models.ForeignKey(Titre, related_name = 'devise_set')
    tiers = models.ForeignKey(Tiers, null = True, blank = True, on_delete = models.SET_NULL, default=None)
    cat = models.ForeignKey(Cat, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name=u"catégorie")
    compte_virement = models.ForeignKey(Compte, null=True, blank=True, related_name='compte_virement_set', default=None)
    moyen = models.ForeignKey(Moyen, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    moyen_virement = models.ForeignKey(Moyen, null=True, blank=True, related_name='moyen_virement_set')
    exercice = models.ForeignKey(Exercice, null=True, blank=True, on_delete=models.SET_NULL, default=None)
    ib = models.ForeignKey(Ib, null=True, blank=True, on_delete=models.SET_NULL, default=None, verbose_name=u"imputation")
    notes = models.TextField(blank=True, default="")
    inscription_automatique = models.BooleanField(default=False)
    periodicite = models.CharField(max_length=1, choices=typesperiod, default="u")
    intervalle = models.IntegerField(default=0)
    periode_perso = models.CharField(max_length=1, choices=typesperiodperso, blank=True, default="")
    date_limite = models.DateField(null=True, blank=True, default=None)
    class Meta:
        db_table = 'echeance'
        verbose_name = u"échéance"
        verbose_name_plural = u"echéances"
        ordering = ['date']
        get_latest_by= 'date'

    def __unicode__(self):
        return u"%s" % (self.id, )
    def save(self, *args, **kwargs):
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
    titre = models.CharField(max_length=120, blank=True, default="isbi")
    utilise_exercices = models.BooleanField(default=True)
    utilise_ib = models.BooleanField(default=True)
    utilise_pc = models.BooleanField(default=False)
    affiche_clot = models.BooleanField(default=True)
    class Meta:
        db_table = 'generalite'
        verbose_name = u"généralités"
        verbose_name_plural = u'généralités'

    def __unicode__(self):
        return u"%s" % (self.id, )

    @staticmethod
    def gen():
        try:
            gen_1 = Generalite.objects.get(id=1)
        except Generalite.DoesNotExist:
            Generalite.objects.create(id=1)
            gen_1 = Generalite.objects.get(id = 1)
        return gen_1

    @staticmethod
    def dev_g():
        if settings.UTIDEV:
            dev = Titre.objects.get_or_create(isin = settings.DEVISE_GENERALE, defaults = {'nom':settings.DEVISE_GENERALE, 'isin':settings.DEVISE_GENERALE, 'type':'DEV', 'tiers':None})[0]
            dev = dev.isin
        else:
            dev = settings.DEVISE_GENERALE
        return dev

class Ope(models.Model):
    compte = models.ForeignKey(Compte)
    date = models.DateField(default = datetime.date.today)
    date_val = models.DateField(null = True, blank = True, default = None)
    montant = models.DecimalField(max_digits = 15, decimal_places = 3, default = 0.000)
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
        if settings.UTIDEV:
            return u"(%s) le %s : %s %s" % (self.id, self.date, self.montant, self.compte.devise.isin)
        else:
            return u"(%s) le %s : %s %s" % (self.id, self.date, self.montant, settings.DEVISE_GENERALE)

    @models.permalink
    def get_absolute_url(self):
        return ('gsb_ope_detail', (), {'pk':str(self.id)})
    def clean(self):
        super(Ope, self).clean()
        #verification qu'il n'y ni poitee ni rapprochee
        if self.pointe is not None and self.rapp is not None:
            raise ValidationError(u"cette operation ne peut pas etre a la fois pointée et rapprochée")

    def save(self, *args, **kwargs):
        if not self.moyen:
            if self.compte.moyen_credit_defaut and self.montant >= 0:
                self.moyen = self.compte.moyen_credit_defaut
            if self.compte.moyen_debit_defaut and self.montant <= 0:
                self.moyen = self.compte.moyen_debit_defaut
        super(Ope, self).save(*args, **kwargs)


class Virement(object):
    def __init__(self, ope=None):
        if ope:
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
        self.origine.montant = montant
        self.dest.montant = montant
    def getmontant(self):
        return self.origine.montant
    montant = property(getmontant, setmontant)

    def setnotes(self, notes):
        self.origine.notes = notes
        self.dest.notes = notes
    def getnotes(self):
        return self.origine.notes
    notes = property(getnotes, setnotes)

    def setpointe(self, p):
        self.origine.pointe = p
        self.dest.pointe = p
    def getpointe(self):
        return self.origine.pointe
    pointe = property(getpointe, setpointe)

    def setrapp(self, r):
        self.origine.rapp = r
        self.dest.rapp = r
    def getrapp(self):
        return self.origine

    def save(self):
        nom_tiers = "%s => %s" % (self.origine.compte.nom, self.dest.compte.nom)
        t = Tiers.objects.get_or_create(nom=nom_tiers, defaults={'nom':nom_tiers})[0]
        self.origine.tiers = t
        self.origine.tiers = t
        self.origine.save()
        self.dest.save()

    def create(self, compte_origine, compte_dest, montant, date, notes=""):
        self.origine = Ope()
        self.dest = Ope()
        self.origine.compte = compte_origine
        self.dest.compte = compte_dest
        self.montant = montant
        self.date = date
        self.notes = notes
        self.save()
        self.origine.jumelle = self.dest
        self.dest.jumelle = self.origine
        self.save()

    def delete(self):
        self.origine.jumelle = None
        self.dest.jumelle = None
        self.origine.delete()
        self.dest.delete()

    def init_form(self):
        """renvoit les donnnés afin d'intialiser virementform"""
        if self._init:
            t = {'compte_origine':self.origine.compte.id,
               'compte_destination':self.dest.compte.id,
               'montant':self.montant,
               'date':self.date,
               'notes':self.notes,
               'pointe':self.pointe,
               'piece_comptable_compte_origine':self.origine.piece_comptable,
               'piece_comptable_compte_destination':self.dest.piece_comptable}
            if self.origine.moyen:
                t['moyen_origine'] = self.origine.moyen.id
            else:
                t['moyen_origine'] = None
            if self.dest.moyen:
                t['moyen_destination'] = self.dest.moyen.id
            else:
                t['moyen_destination'] = None
            if self.origine.rapp:
                t['rapp_origine'] = self.origine.rapp.id
            else:
                t['rapp_origine'] = None
            if self.dest.rapp:
                t['rapp_destination'] = self.dest.rapp.id
            else:
                t['rapp_destination'] = None

        else:
            raise Exception('attention, on ne peut intialiser un form que si virement est bound')
        return t
