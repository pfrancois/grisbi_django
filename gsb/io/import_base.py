# -*- coding: utf-8
""""import_file : vue qui gere les import"""
from __future__ import absolute_import
import time
# import logging
import os

from django.conf import settings  # @Reimport
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.db.models import Max
from django.db import transaction

from .. import forms as gsb_forms
from .. import models
from .. import views
from .. import utils


class ImportException(Exception):
    def __init__(self, message):
        super(ImportException, self).__init__(message)
        self.msg = message

    def __str__(self):
        return self.msg


class ImportForm1(gsb_forms.Baseform):
    nom_du_fichier = gsb_forms.forms.FileField()


class property_ope_base(object):
    """defini toutes les proprietes d'ope"""

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
    """obj avec cache"""
    element = None
    readonly = False

    def auto(self):
        return None

    def __init__(self, request):
        self.id = dict()
        self.create_item = list()
        self.request = request
        if self.auto() is not None:
            for param in self.auto():
                c, created = self.element.objects.get_or_create(**param)
                self.id[c.nom] = c.pk
                if created:
                    messages.info(self.request, u'création du %s "%s"' % (self.element._meta.object_name, c))

        if self.element is None:
            raise NotImplementedError("table de l'element non choisi")
        else:
            self.last_id_db = self.element.objects.aggregate(id_max=Max('id'))['id_max']
        self.nb_created = 0

    def goc(self, nom, obj=None):
        if nom == "" or nom is None:
            if not obj is None:
                nom = obj['nom']
            else:
                return None
        try:
            pk = self.id[nom]
        except KeyError:
            try:
                if obj is None:
                    arguments = {"nom": nom}
                else:
                    arguments = obj
                with transaction.atomic():
                    pk = self.element.objects.get(**arguments).id
                self.id[nom] = pk
            except self.element.DoesNotExist:
                if not self.readonly:  # on cree donc l'element
                    argument_def = self.arg_def(nom, obj)
                    try:
                        with transaction.atomic():
                            created = self.element.objects.create(**argument_def)
                            self.nb_created += 1
                    except IntegrityError as e:
                        raise ImportException("%s" % e)
                    pk = created.pk
                    self.id[nom] = pk
                    self.create_item.append(created)
                    messages.info(self.request, u'création du %s "%s"' % (self.element._meta.object_name, created))
                else:
                    raise ImportException(u"%s '%s' non créée alors que c'est read only" % (self.element._meta.object_name, nom))
        return pk

    def arg_def(self, nom, obj=None):
        raise NotImplementedError("methode arg_def non defini")


class Cat_cache(Table):
    element = models.Cat

    def auto(self):
        return [{'id': settings.ID_CAT_OST, 'defaults': {'nom': u'Opération sur titre', 'id': settings.ID_CAT_OST, 'type': 'd'}},
                {'id': settings.ID_CAT_VIR, 'defaults': {'nom': u'Virement', 'id': settings.ID_CAT_VIR, 'type': 'v'}},
                {'id': settings.ID_CAT_PMV, 'defaults': {'nom': u'Revenus de placements:Plus-values', 'id': settings.ID_CAT_PMV, 'type': 'r'}},
                {'id': settings.REV_PLAC, 'defaults': {'nom': u"Revenus de placements:interets", 'id': settings.REV_PLAC, 'type': 'r'}},
                {'id': settings.ID_CAT_COTISATION, 'defaults': {'nom': u'Impôts:Cotisations sociales', 'id': settings.ID_CAT_COTISATION, 'type': 'd'}},
                {'nom': u"Opération Ventilée", 'defaults': {'nom': u"Opération Ventilée", 'type': 'd'}},
                {'nom': u"Frais bancaires", 'defaults': {'nom': u"Frais bancaires", 'type': 'd'}},
                {'nom': u"Non affecté", 'defaults': {'nom': u"Non affecté", 'type': 'd'}},
            ]

    def arg_def(self, nom, obj=None):
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
            ]

    def goc(self, nom, obj=None, montant=None):
        if obj is not None:
            return super(Moyen_cache, self).goc('', obj=obj)
        if montant is None:
            raise ValueError('attention, vous devez remplir soit obj soit montant')
        if montant > 0:
            return super(Moyen_cache, self).goc('', obj={"nom": nom, "type": "r"})
        else:
            return super(Moyen_cache, self).goc('', obj={"nom": nom, "type": "d"})

    def arg_def(self, nom, obj=None):
        if obj is None:
            return {"nom": nom, "type": 'd'}
        else:
            return obj


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

    def __init__(self, request):
        super(Titre_cache, self).__init__(request)
        self.id = {"nom": dict(), "isin": dict()}

    def goc(self, nom=None, isin=None, obj=None):
        if nom is None and isin is None and obj is None:  # cas ou pas de parametre
            return None
        if nom is None:
            return self.goc_isin(isin, obj)
        else:
            return self.goc_titre(nom, obj)

    def goc_titre(self, nom, obj=None):
        if nom is not None and "titre_ " in nom:  # cas ou on utiliserait les nom de tiers
            nom = nom.replace("titre_ ", '')
            nom = nom.strip()
        try:
            pk = self.id["nom"][nom]
        except KeyError:  # on essaye de le recuperer
            try:
                if obj is None:
                    arguments = {"nom": nom}
                else:
                    arguments = obj
                pk = self.element.objects.get(**arguments).id
                self.id["nom"][nom] = pk
                self.id["isin"][self.element.objects.get(**arguments).isin] = pk
            except self.element.DoesNotExist:# on doit le creer
                if not self.readonly:  # on cree donc l'operation
                    argument_def = self.arg_def(nom, None, obj)
                    try:
                        with transaction.atomic():
                            if obj is not None:
                                if models.Titre.objects.filter(id=obj['id']).exists() or models.Titre.objects.filter(nom=obj['nom']).exists() or models.Titre.objects.filter(isin=obj['isin']).exists():
                                    raise IntegrityError("ce titre existe deja")
                            created = self.element.objects.create(**argument_def)
                            self.nb_created += 1
                    except IntegrityError as e:
                        raise ImportException("%s" % e)
                    pk = created.pk
                    self.id["nom"][created.nom] = pk
                    self.id["isin"][created.isin] = pk
                    self.create_item.append(created)
                    messages.info(self.request, u'création du %s "%s"' % (self.element._meta.object_name, created))
                else:
                    raise ImportException("%s '%s' non cree alors que c'est read only" % (self.element._meta.object_name, nom))
        return pk

    def goc_isin(self, isin, obj=None):
        try:
            pk = self.id["isin"][isin]
        except KeyError:  # on essaye de le recuperer
            try:
                if obj is None:
                    arguments = {"isin": isin}
                else:
                    arguments = obj
                pk = self.element.objects.get(**arguments).id
                self.id["nom"][self.element.objects.get(**arguments).nom] = pk
                self.id["isin"][isin] = pk
            except self.element.DoesNotExist:
                if not self.readonly:  # on cree donc l'operation
                    argument_def = self.arg_def(None, isin, obj)
                    try:
                        with transaction.atomic():
                            if obj is not None:
                                if models.Titre.objects.filter(id=obj['id']).exists() or models.Titre.objects.filter(nom=obj['nom']).exists() or models.Titre.objects.filter(isin=obj['isin']).exists():
                                    raise IntegrityError("ce titre existe deja")
                            created = self.element.objects.create(**argument_def)
                            self.nb_created += 1
                    except IntegrityError as e:
                        raise ImportException("%s" % e)
                    pk = created.pk
                    self.id["nom"][created.nom] = pk
                    self.id["isin"][created.isin] = pk
                    self.create_item.append(created)
                    messages.info(self.request, u'création du %s "%s"' % (self.element._meta.object_name, created))
                else:
                    raise ImportException("%s '%s' non cree alors que c'est read only" % (self.element._meta.object_name, isin))
        return pk

    def arg_def(self, nom=None, isin=None, obj=None):
        if obj is None:
            if nom:
                arg_nom = nom
            else:
                arg_nom = "inconnu%s%s" % (self.nb_created + 1, utils.today())
            if isin:
                arg_isin = isin
            else:
                arg_isin = "%s%s" % (self.nb_created + 1, utils.today())
            return {"nom": arg_nom, "isin": arg_isin, "type": "ZZZ"}
        else:
            return obj


class Cours_cache(Table):
    element = models.Cours

    def __init__(self, request, titre_cache):
        super(Cours_cache, self).__init__(request)
        self.TC = titre_cache

    def goc(self, titre, date, montant, methode="nom"):
        if methode == "nom":
            titre_id = self.TC.goc(nom=titre)
        else:
            titre_id = self.TC.goc(isin=titre)
        try:
            pk = self.id[titre_id][date]
        except KeyError:
            try:
                el = models.Cours.objects.get(date=date, titre_id=titre_id)
                pk = el.id
                if el.valeur != montant:
                    raise ImportException(u'difference de montant %s et %s pour le titre %s à la date %s' % (el.valeur, montant, el.titre.nom, date))
            except self.element.DoesNotExist:
                arg_def = {'titre_id': titre_id, 'date': date, "valeur": montant}
                el = models.Cours.objects.create(**arg_def)
                self.create_item.append(el)
                self.nb_created += 1
                pk = el.id
        if self.id.get(titre_id) is not None:
            self.id[titre_id][date] = pk
        else:
            self.id[titre_id] = dict()
            self.id[titre_id][date] = pk
        return pk

    def arg_def(self, nom, obj=None):
        raise NotImplementedError


class Ope_cache(Table):
    element = models.Ope

    def goc(self, nom, obj=None):
        raise NotImplementedError("methode goc non defini")

    def create(self, ope):
        self.create_item.append(ope)
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
            try:
                credit = c.moyen_credit().id
            except models.Moyen.DoesNotExist:
                credit = None
            try:
                debit = c.moyen_debit().id
            except models.Moyen.DoesNotExist:
                debit = None

            self.id[c.nom] = {"c": credit, "d": debit}

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
            messages.error(self.request, u"attention cette extension '%s' n'est pas compatible avec ce format d'import %s" % (fileExtension, self.extensions))
            return self.form_invalid(form)
        nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.%s" % (nomfich, time.strftime("%Y-%b-%d_%H-%M-%S"), fileExtension[1:]))
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
                #return self.render_to_response(self.get_context_data(form=form))

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
