# -*- coding: utf-8
""""import_file : vue qui gere les import"""
from __future__ import absolute_import
import time
import decimal
import logging
import os
from django.conf import settings  # @Reimport
from django.http import HttpResponseRedirect

from django.utils.decorators import method_decorator

from . import forms as gsb_forms
from .models import (Tiers, Titre, Cat, Ope, Banque, Ib,
                     Exercice, Rapp, Moyen, Echeance, Compte, Compte_titre, Ope_titre)
from django.db import transaction
from . import views
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages


class Import_exception(Exception):
    pass


class ImportForm1(gsb_forms.Baseform):
    nom_du_fichier = gsb_forms.forms.FileField()
    #attention les entete des choices doivent exister dans le tableau liste_import
    replace = gsb_forms.forms.ChoiceField(label="destination", choices=(
        ('remplacement', 'remplacement des données par le fichier'),
        ('fusion', 'fusion des données avec le fichier')
        ))


class property_ope_base(object):
    """defini toutes le proprietes d'ope"""

    @property
    def pk(self):
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
        return None

    @property
    def mere(self):
        return None

    @property
    def mt(self):
        return 0

    @property
    def moyen(self):
        return None

    @property
    def notes(self):
        return ''

    @property
    def num_cheque(self):
        return None

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
        return None

    @property
    def ope_pmv(self):
        return False

    @property
    def ligne(self):
        return 0


class Import_base(views.Myformview):
    #chemin du template
    template_name = "gsb/import.djhtm"
    #classe du reader
    reader = None
    #extension du fichier
    extension = (None, )
    #nom du type de fichier
    type_f = None
    #formulaire utilise
    form_class = ImportForm1
    url = "outils_index"
    test = False
    remplacement = False

    def form_valid(self, form):
        logger = logging.getLogger('gsb.import')
        self.test = False
        nomfich = form.cleaned_data['nom_du_fichier'].name
        nomfich = nomfich[:-4]
        nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.%s" % (
            nomfich, time.strftime("%Y-%b-%d_%H-%M-%S"), self.extension))
        destination = open(nomfich, 'wb+')
        for chunk in self.request.FILES['nom_du_fichier'].chunks():
            destination.write(chunk)
        destination.close()
        #renomage ok
        logger.debug(u"enregistrement fichier ok")
        if self.import_file(nomfich) == False:
            os.remove(nomfich)
            return self.form_invalid(form)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def import_file(self, nomfich):
        logger = logging.getLogger('gsb.import')
        #definition du nom du fichier
        self.listes = dict()
        self.nb = dict()
        self.listes['id'] = dict()
        try:
            with transaction.commit_on_success():
                opes = self.tableau_import(nomfich)
                if self.remplacement:  # utilise uniquement si remplacement
                    for ope in opes:
                        try:
                            obj = Ope.objects.get(pk=ope['pk'])
                            #on supprime les risques d'integrité referentielle
                            if obj.rapp is not None:
                                obj.rapp = None
                                obj.save()
                            if obj.mere_id is not None:
                                try:
                                    obj.mere_id = None
                                    obj.save()
                                    ope_mere = Ope.objects.get(pk=obj.mere_id)
                                    ope_mere.delete()
                                    ope_soeurs = Ope.objects.filter(mere=obj.mere_id).delete()
                                except Ope.DoesNotExist:
                                    pass
                            if ope.jumelle is not None:
                                try:
                                    obj.jumelle = None
                                    obj.save()
                                    ope_jumelle = Ope.objects.get(pk=obj.mere_id)
                                    ope_jumelle.delete()
                                except Ope.DoesNotExist:
                                    pass
                        except Ope.DoesNotExist:
                            pass
                #troisieme tour pour gerer les ope_titres
                opes_apres_titre = list()
                for ope in opes:
                    nb_titre = 0
                    if self.remplacement:
                        id = ope['pk']
                        #on efface effacer les ope_titre (et donc les ope et op_pmv)
                        try:
                            op_t = Ope_titre.objects.get(ope_id=id)
                            op_t.delete()
                        except Ope_titre.DoesNotExist:
                            pass
                    if ope['ope_titre'] is not None:  # pas besoin de prendre en compte les pmv car c'est pris en compte de base
                        #gestion des ope_titre
                        nb_titre += 1
                        try:
                            titre = self.listes['titre']['nom']  # pylint: disable=W0622
                        except KeyError:
                            tiers = Tiers.object(get=ope['tiers_id'])
                            name = tiers.nom[7:]
                            if name == '' or name is None or name == 0:
                                raise Import_exception('probleme import operation %s:un titre ne peut etre vide' % ope.ligne)
                            isin = "ZZ%s%s" % (utils.today().strftime('%d%m%Y'), nbttitre)
                            titre = self.element('titre', nom_titre, Titre,
                                               {'nom': name, 'type': 'ZZZ', 'isin': isin, 'tiers': tiers})
                            self.listes['titre']['nom'] = titre
                        #on recupere le reste
                        s = ope['notes']
                        s = s.partition('@')
                        try:
                            nombre = s[0]
                            cours = s[2]
                        except KeyError:
                            raise Import_exception('probleme import operation %s:pas bon format des notes pour importation' % ope.ligne)
                        try:
                            cpt_titre = Compte_titre.objects.get(id=ope['compte_id'])
                        except Compte.DoesNotExist:
                            raise Import_exception('probleme import operation %s:pas de compte titre' % ope.ligne)
                        if nombre > 0:
                            ope_titre = cpt_titre.achat(titre, nombre, cours, ope['date'])
                        else:
                            ope_titre = cpt_titre.vente(titre, nombre, cours, ope['date'])
                        self.listes['id'][ope['pk']] = ope_titre.ope.id
                    else:
                        if ope['ope_pmv'] == False:
                            opes_apres_titre.append(ope)
                for ope in opes_apres_titre:
                    try:
                        if self.remplacement:
                            obj = Ope.objects.get(pk=ope['pk'])
                            obj.automatique = ope['automatique']
                            obj.cat_id = ope['cat_id']
                            obj.compte_id = ope['compte']
                            obj.date = ope['date']
                            obj.date_val = ope['date_val']
                            obj.exercice = ope['exercice']
                            obj.ib_id = ope['ib_id']
                            #supprime car gere en dessous
                            #obj.jumelle_id=ope['jumelle_id']
                            #obj.mere_id=ope['mere_id']
                            obj.montant = ope['montant']
                            obj.moyen_id = ope['moyen_id']
                            obj.notes = ope['notes']
                            obj.num_cheque = ope['num_cheque']
                            obj.piece_comptable = ope['piece_comptable']
                            obj.pointe = ope['pointe']
                            #gere aussi en dessous
                            #obj.rapp_id=ope['rapp_id']
                            obj.tiers_id = ope['tiers_id']
                            obj.save()
                            self.listes['id'][ope['pk']] = obj.id
                        else:
                            raise Ope.DoesNotExist
                    except Ope.DoesNotExist:
                        #on a enlevé les id
                        ope_db = Ope.objects.create(automatique=ope['automatique'], cat_id=ope['cat_id'], compte_id=ope['compte_id'], date=ope['date'], date_val=ope['date_val'], exercice_id=ope['exercice_id'], ib_id=ope['ib_id'], montant=ope['montant'], moyen_id=ope['moyen_id'], notes=ope['notes'], num_cheque=ope['num_cheque'], piece_comptable=ope['piece_comptable'], pointe=ope['pointe'], tiers_id=ope['tiers_id'])
                        self.listes['id'][ope['pk']] = ope_db.id
                    try:
                        self.nb['ope'] += 1
                    except KeyError:
                        self.nb['ope'] = 1

                #second tour pour gerer les mere et virements et le rapp
                for ope in opes_apres_titre:
                    if ope['jumelle_id'] is not None or ope['mere_id'] is not None or ope['rapp_id'] is not None:
                        id = self.listes['id'][ope['pk']]
                        ope_db = Ope.objects.get(id=id)
                        if ope['jumelle_id'] is not None:
                            id_jumelle = self.listes['id'][ope['jumelle']]
                            ope_db.jumelle_id = id_jumelle
                        if ope['mere_id'] is not None:
                            id_mere = self.listes['id'][ope['mere']]
                            ope_db.mere_id = id_mere
                        if ope['rapp_id'] is not None:
                            ope_db.rapp_id = ope['rapp_id']
                        ope_db.save()
        except Import_exception as e:
            if self.test == False:
                messages.error(self.request, e)
                return False
            else:
                raise e
        resultats = list()
        for key, value in self.nb.iteritems():
            if self.test == False:
                messages.success(self.request, (u"%s %s ajoutés" % (value, key)))

    def get_success_url(self):
        return reverse(self.url)

    def get_form(self, form_class):
        form = super(Import_base, self).get_form(form_class)
        form.fields['nom_du_fichier'].label = "nom_du_fichier %s" % self.type_f
        del form.fields['replace']
        return form

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if form.is_valid():
            nomfich = form.cleaned_data['nom_du_fichier'].name
            ext = os.path.splitext(nomfich)[1][1:]
            ext = ext.lower()
            if ext not in self.extension:
                messages.error(self.request, u"attention, l'extension du fichier '%s' est incompatible avec le type du fichier '%s'" % (ext, self.type_f))
                return self.form_invalid(form)
            else:
                return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """on a besoin pour le method decorator"""
        return super(Import_base, self).dispatch(*args, **kwargs)

    def element(self, liste, name, model, nouveau):
        """
        permet d'avoir un get_or_create avec gestion des erreurs
        @param liste: nom de la liste ou l'on doit chercher le nom
        @param name: nom de l'element a chercher
        @param model: classe model a chercher
        @param nouveau: dic pour creer un nouveau objet
        """
        logger = logging.getLogger('gsb.import')
        try:
            id = self.listes[liste][name]  # pylint: disable=W0622
        except KeyError:
            logger = logging.getLogger('gsb.import')
            #si c'est un nom vide pas besoin de creer
            if name == '' or name is None or name == 0:
                return None
            obj, created = model.objects.get_or_create(nom=name, defaults=nouveau)
            logger.info(u'element %s cree: %s' % (model._meta.verbose_name, name))
            try:
                self.listes[liste][name] = obj.id
            except KeyError:
                self.listes[liste] = {name: obj.id}

            if created:
                try:
                    self.nb[liste] += 1
                except KeyError:
                    self.nb[liste] = 1
            id = obj.id
        return id

    def tableau_import(self, nomfich):
        raise NotImplementedError("il faut definir comment on importe")
