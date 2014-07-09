# -*- coding: utf-8
""""import_file : vue qui gere les import"""
from __future__ import absolute_import
import time
# import logging
import os

from django.conf import settings  # @Reimport
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Max
from django.db import transaction

from .. import forms as gsb_forms
from .. import models
from .. import views
from .. import utils

def isin_default():
    nb=max(models.Titre.objects.all().aggregate(Max('pk'))['pk__max'],0)+1
    return "ZZ_%s"%nb

class ImportException(utils.utils_Exception):
   pass


class ImportForm1(gsb_forms.Baseform):
    """form d'importation, defini juste un fichier"""
    nom_du_fichier = gsb_forms.forms.FileField()


class property_ope_base(object):
    """defini toutes les proprietes d'une ope"""

    @property
    def id(self):
        return None

    @property
    def cat(self):
        return None

    @property
    def automatique(self):
        return False

    @property
    def cpt(self):
        return None

    @property
    def date(self):
        return None

    @property
    def date_val(self):
        return None

    @property
    def exercice(self):
        return None

    @property
    def ib(self):
        return None

    @property
    def jumelle(self):
        """renvoie le nom du compte jumelle"""
        return None

    @property
    def mere(self):
        return None

    @property
    def montant(self):
        return 0

    @property
    def moyen(self):
        return None

    @property
    def notes(self):
        return ''

    @property
    def num_cheque(self):
        return ''

    @property
    def piece_comptable(self):
        return ''

    @property
    def pointe(self):
        return False

    @property
    def rapp(self):
        return None

    @property
    def tiers(self):
        return None

    @property
    def monnaie(self):
        return None

    @property
    def ope_titre(self):
        return False

    @property
    def ope_pmv(self):
        return False

    @property
    def ligne(self):
        return 0

    @property
    def has_fille(self):
        return False


class Table(object):
    """obj avec cache
    c'est l'object abstract sur lequel tt les autres se reposes
    """
    #nom de l'objet effectif
    element = None
    #si readonly, pas possible d'en ceer de nouveau
    readonly = False

    def auto(self):
        """les objets a creer automatiquement dans tt les cas"""
        return None

    # noinspection PyProtectedMember
    def __init__(self, request):
        if self.element is None:
            raise NotImplementedError("table de l'element non choisi")
        else:
            self.last_id_db = self.element.objects.aggregate(id_max=Max('id'))['id_max']
        #dict qui referme juste les id (cache)
        self.id = dict()
        #dict qui renferme les objects a creer
        self.created_items = list()
        #la requete qui demande ca, utile pour les messages
        self.request = request
        if self.auto() is not None:
            # noinspection PyTypeChecker
            for param in self.auto():
                c, created = self.element.objects.get_or_create(**param)
                self.id[c.nom] = c.pk
                if created:
                    messages.info(self.request, u'création du %s "%s"' % (self.element._meta.object_name, c))

        self.nb_created = 0

    def goc(self, nom, obj=None):
        """remvoie un obj a partir du cache en prenant un nom ou en le creant"""
        #verif qu'il n'y a pas de nom vide ou d'objet
        #indispensable car utilisable par deux possiblite
        if nom == "" or nom is None:
            if not obj is None:
                nom = obj['nom']
            else:
                return None
        #sinon c'est on peut commencer
        try:
            #dans le cas le plus simple, c'est deja ds le cache
            pk = self.id[nom]
            #si c'est pas dans le cache
        except KeyError:
            #on essaye de voir si l'objet existe ds la base de donnee
            try:
                if obj is None:
                    arguments = {"nom": nom}
                else:
                    arguments = obj
                with transaction.atomic():
                    pk = self.element.objects.get(**arguments).id
                self.id[nom] = pk
            #on cree un objet
            except self.element.DoesNotExist:
                if not self.readonly:  # on cree donc l'element
                    argument_def = self.arg_def(nom, obj)
                    created=None
                    try:
                        with transaction.atomic():
                            #permet de creer un objet avec un id defini
                            #donc on verifie avant s'il n'existe pas deja
                            if obj is not None and 'id' in obj.keys():
                                requete = self.element.objects.filter(id=obj['id'])
                                if requete.exists() and requete[0].nom != obj['nom']:
                                    raise ImportException(
                                        "attention probleme dans import obj %s, un obj avec meme id mais pas meme nom a déja ete cree" % obj)
                            created = self.element.objects.create(**argument_def)
                            self.nb_created += 1
                    except IntegrityError as e:
                        raise ImportException("%s" % e)
                    #une fois cree on met a jour le cache
                    pk = created.pk
                    self.id[nom] = pk
                    self.created_items.append(created)
                    # noinspection PyProtectedMember
                    messages.info(self.request, u'création du %s "%s"' % (self.element._meta.object_name, created))
                else:
                    #pas possible de creer un objet read only
                    # noinspection PyProtectedMember
                    raise ImportException(u"%s '%s' non créée parce que c'est read only" % (self.element._meta.object_name, nom))
        return pk

    def arg_def(self, nom, obj=None):
        """fonction qui renvoi les element de l'objet a creer"""
        if obj is not None:
            return obj
        else:
            raise NotImplementedError("methode arg_def non defini")


class Cat_cache(Table):
    element = models.Cat

    def auto(self):
        return [{'id': settings.ID_CAT_OST, 'defaults': {'nom': u'Opération sur titre', 'id': settings.ID_CAT_OST, 'type': 'd'}},
                {'id': settings.ID_CAT_VIR, 'defaults': {'nom': u'Virement', 'id': settings.ID_CAT_VIR, 'type': 'v'}},
                {'id': settings.ID_CAT_PMV,
                        'defaults': {'nom': u'Revenus de placements:Plus-values', 'id': settings.ID_CAT_PMV, 'type': 'r'}},
                {'id': settings.REV_PLAC, 'defaults': {'nom': u"Revenus de placements:interets", 'id': settings.REV_PLAC, 'type': 'r'}},
                {'id': settings.ID_CAT_COTISATION,
                 'defaults': {'nom': u'Impôts:Cotisations sociales', 'id': settings.ID_CAT_COTISATION, 'type': 'd'}},
                {'nom': u"Opération Ventilée", 'defaults': {'nom': u"Opération Ventilée", 'type': 'd'}},
                {'nom': u"Frais bancaires", 'defaults': {'nom': u"Frais bancaires", 'type': 'd'}},
                {'nom': u"Non affecté", 'defaults': {'nom': u"Non affecté", 'type': 'd'}},
                {'nom': u"Avance", 'defaults': {'nom': u"Avance", 'type': 'd'}},
                {'nom': u"Remboursement", 'defaults': {'nom': u"Remboursement", 'type': 'r'}},]

    def arg_def(self, nom, obj=None):
        """definition des argument par defaut
        on prend le nom et lq categorie depense"""
        if obj is None:
            return {"nom": nom, "type": 'd'}
        else:
            return obj


class Moyen_cache(Table):
    element = models.Moyen
    def auto(self):
        return [{'id': settings.MD_CREDIT, 'defaults': {'nom': 'CREDIT', 'id': settings.MD_CREDIT, 'type': 'r'}},
                {'id': settings.MD_DEBIT, 'defaults': {'nom': 'DEBIT', 'id': settings.MD_DEBIT, 'type': 'd'}},
                {'nom': u"Virement", 'defaults': {'nom': u"Virement", 'type': 'v'}},
                {'nom': u"carte bancaire", 'defaults': {'nom': u"carte bancaire", 'type': 'd'}},
        ]

    def goc(self, nom="", obj=None, montant=-1):
        #pas besoin d'argdef car comme on redefini cette methode
        if obj is not None:
            return super(Moyen_cache, self).goc('', obj=obj)
        if montant > 0:
            return super(Moyen_cache, self).goc('', obj={"nom": nom, "type": "r"})
        else:
            return super(Moyen_cache, self).goc('', obj={"nom": nom, "type": "d"})

class IB_cache(Table):
    element = models.Ib

    def arg_def(self, nom, obj=None):
        if obj is None:
            return {"nom": nom, "type": 'd'}
        else:
            return obj


class Compte_cache(Table):
    element = models.Compte
    def arg_def(self, nom, obj=None):
        if obj is None:
            return {"nom": nom, "type": 'b', 'moyen_credit_defaut_id': settings.MD_CREDIT, 'moyen_debit_defaut_id': settings.MD_DEBIT}
        else:
            return obj


class Banque_cache(Table):
    element = models.Banque

    def arg_def(self, nom, obj=None):
        if obj is None:
            return {"nom": nom}
        else:
            return obj


class Exercice_cache(Table):
    element = models.Exercice

    def arg_def(self, nom, obj=None):
        if obj is None:
            return {"nom": nom, 'date_debut': utils.today(), 'date_fin': utils.today()}
        else:
            return obj


class Tiers_cache(Table):
    element = models.Tiers

    def auto(self):
        return [{'id': settings.ID_TIERS_COTISATION, 'defaults': {'nom': 'secu', 'id': settings.ID_TIERS_COTISATION}}, ]

    def arg_def(self, nom, obj=None):
        if obj is None:
            return {"nom": nom}
        else:
            return obj


class Titre_cache(Table):
    element = models.Titre

    def arg_def(self, nom, obj=None):
        if obj is None:
            return {"nom": nom, 'isin':isin_default(), "type": "ZZZ"}
        else:
            return obj


class Cours_cache(Table):
    element = models.Cours

    def __init__(self, request, titre_cache):
        super(Cours_cache, self).__init__(request)
        self.TC = titre_cache

    # noinspection PyMethodOverriding
    def goc(self, titre, date, montant):
        titre_id = self.TC.goc(nom=titre)
        try:
            pk = self.id[titre_id][date]
        except KeyError:
            try:
                el = models.Cours.objects.get(date=date, titre_id=titre_id)
                pk = el.id
                if el.valeur != montant:
                    raise ImportException(
                        u'difference de montant %s et %s pour le titre %s à la date %s' % (el.valeur, montant, el.titre.nom, date))
            except self.element.DoesNotExist:
                arg_def = {'titre_id': titre_id, 'date': date, "valeur": montant}
                el = models.Cours.objects.create(**arg_def)
                self.created_items.append(el)
                self.nb_created += 1
                pk = el.id
        if self.id.get(titre_id) is not None:
            self.id[titre_id][date] = pk
        else:
            self.id[titre_id] = dict()
            self.id[titre_id][date] = pk
        return pk


class Ope_cache(Table):
    element = models.Ope

    def goc(self, nom, obj=None):
        raise NotImplementedError("methode goc non defini")

    def create(self, ope):
        self.created_items.append(ope)
        self.nb_created += 1


class Rapp_cache(Table):
    element = models.Rapp
    date_en_cours = None

    def __init__(self, request):
        super(Rapp_cache, self).__init__(request)
        self.dates = {}

    def goc(self, nom=None, date=None, obj=None):
        if nom or obj:
            if obj:
                date = obj['date']
            self.date_en_cours = date
            pk = super(Rapp_cache, self).goc(nom, obj)
            if self.dates.get(pk, None) is not None:
                i = self.dates[pk]
                i.append(date)
            else:
                self.dates[pk] = [date]
            return pk
        else:
            return None

    def arg_def(self, nom, obj=None):

        if not obj:
            return {"nom": nom, 'date': self.date_en_cours}
        else:
            return obj

    def sync_date(self):
        for r in self.id.values():
            date_max = max(self.dates[r])
            rapp = self.element.objects.get(pk=r)
            if rapp.date < date_max:
                rapp.date = date_max
                rapp.save()
                messages.info(self.request, u"date pour le rapp %s mise a jour au %s" % (rapp, date_max))


class moyen_defaut_cache(object):
    def __init__(self):
        self.id = {}
        for c in models.Compte.objects.all():
            self.id[c.nom] = {"c": c.moyen_credit().id, "d": c.moyen_debit().id}

    def goc(self, compte, montant):
        if compte in self.id.keys():
            if montant > 0:
                return self.id[compte]['c']
            else:
                return self.id[compte]['d']
        else:
            if montant > 0:
                return settings.MD_CREDIT
            else:
                return settings.MD_DEBIT


class Import_base(views.Myformview):
    # chemin du template
    template_name = "gsb/import.djhtm"
    # classe du reader
    reader = None
    # nom du type de fichier
    type_f = None
    # formulaire utilise
    form_class = ImportForm1
    url = "outils_index"
    test = False
    creation_de_compte = False
    # affiche les resultats plutot qu'une importation
    resultat = False
    debug = False
    extensions = None

    def form_valid(self, form):
        self.test = False
        nomfich = form.cleaned_data['nom_du_fichier'].name
        nomfich, fileExtension = os.path.splitext(nomfich)
        if fileExtension not in self.extensions:
            messages.error(self.request, u"attention cette extension '%s' n'est pas compatible avec ce format d'import %s" % (
            fileExtension, self.extensions))
            return self.form_invalid(form)
        nomfich = os.path.join(settings.PROJECT_PATH, 'upload',
                               "%s-%s.%s" % (nomfich, time.strftime("%Y-%b-%d_%H-%M-%S"), fileExtension[1:]))
        # commme on peut avoir plusieurs extension on prend par defaut la premiere
        # si le repertoire n'existe pas on le crée
        try:
            destination = open(nomfich, 'w+b')
        except IOError:  # pragma: no cover
            os.makedirs(os.path.join(settings.PROJECT_PATH, 'upload'))
            destination = open(nomfich, 'w+b')
        for chunk in self.request.FILES['nom_du_fichier'].chunks():
            destination.write(chunk)
        destination.close()
        # renomage ok
        result = self.import_file(nomfich)
        if not result:  # probleme importation raise # pragma: no cover
            os.remove(nomfich)
            return self.form_invalid(form)
        else:
            if self.resultat:  # pragma: no cover
                return self.render_to_response(self.get_context_data(form=form, resultat=self.resultat))
            else:
                return HttpResponseRedirect(self.get_success_url())
                # return self.render_to_response(self.get_context_data(form=form))

    def import_file(self, nomfich):
        raise NotImplementedError("methode goc non defini")

    def get_success_url(self):
        return reverse(self.url)

    def get_form(self, form_class):
        form = super(Import_base, self).get_form(form_class)
        form.fields['nom_du_fichier'].label = u"nom_du_fichier %s" % self.type_f
        return form

    def init_cache(self):
        self.moyens = Moyen_cache(self.request)
        self.cats = Cat_cache(self.request)
        self.ibs = IB_cache(self.request)
        self.comptes = Compte_cache(self.request)
        self.banques = Banque_cache(self.request)
        self.exos = Exercice_cache(self.request)
        self.tiers = Tiers_cache(self.request)
        self.opes = Ope_cache(self.request)
        self.titres = Titre_cache(self.request)
        self.cours = Cours_cache(self.request, self.titres)
        self.moyen_par_defaut = moyen_defaut_cache()
        self.rapps = Rapp_cache(self.request)
