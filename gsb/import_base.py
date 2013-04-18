# -*- coding: utf-8
""""import_file : vue qui gere les import"""
from __future__ import absolute_import
import time
import logging
import os

from django.conf import settings  # @Reimport
from django.http import HttpResponseRedirect
from django.db import transaction
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.decorators import method_decorator

from . import forms as gsb_forms
from .models import Tiers, Titre, Cat, Ib, Exercice, Compte, Moyen, Rapp, Ope
from . import views
from .utils import FormatException

class ImportException(Exception):
    pass


class ImportForm1(gsb_forms.Baseform):
    nom_du_fichier = gsb_forms.forms.FileField()
    # attention les entete des choices doivent exister dans le tableau liste_import
    replace = gsb_forms.forms.ChoiceField(label="destination", choices=(
        ('remplacement', 'remplacement des données par le fichier'),
        ('fusion', 'fusion des données avec le fichier')
        ))


class property_ope_base(object):
    """defini toutes le proprietes d'ope"""
        
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
    

class Import_base(views.Myformview):
    # chemin du template
    template_name = "gsb/import.djhtm"
    # classe du reader
    reader = None
    # extension du fichier
    extension = (None,)
    # nom du type de fichier
    type_f = None
    # formulaire utilise
    form_class = ImportForm1
    url = "outils_index"
    test = False
    creation_de_compte = False
    #affiche les resultats plutot qu'une importation
    resultat=False
    debug=False

    def form_valid(self, form):
        # logger = logging.getLogger('gsb.import')
        self.test = False
        nomfich = form.cleaned_data['nom_du_fichier'].name
        nomfich = nomfich[:-4]
        nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.%s" % (
            nomfich, time.strftime("%Y-%b-%d_%H-%M-%S"), self.extension[0]))
        # commme on peut avoir plusieurs extension on prend par defaut la premiere
        # si le repertoire n'existe pas on le crée
        try:
            destination = open(nomfich, 'wb+')
        except IOError :
            os.makedirs(os.path.join(settings.PROJECT_PATH, 'upload'))
            destination = open(nomfich, 'wb+')
        for chunk in self.request.FILES['nom_du_fichier'].chunks():
            destination.write(chunk)
        destination.close()
        # renomage ok
        # logger.debug(u"enregistrement fichier ok")
        result=self.import_file(nomfich)
        if  result == False:  # probleme importation
            os.remove(nomfich)
            return self.form_invalid(form)
        else:
            if self.debug:
                os.remove(nomfich)
            if self.resultat:
                return self.render_to_response(self.get_context_data(form=form,resultat=self.resultat))
            else:
                return HttpResponseRedirect(self.get_success_url())
            

    def import_file(self, nomfich):
        logger = logging.getLogger('gsb.import')  # @UnusedVariable
        self.erreur = list()
        # definition du nom du fichier
        self.nb = dict()
        self.id = dict()
        self.listes = { 'titre':dict(), 'cat':dict(), 'ib':dict(), 'tiers':dict(), 'moyen':dict(), 'rapp':dict(), 'compte':dict(), 'ope':dict(), 'exercice':dict() }
        self.ajouter = {'titre':list(), 'cat':list(), 'ib':list(), 'tiers':list(), 'moyen':list(), 'rapp':list(), 'ope':list(), 'exercice':list(), "ope_titre":list()}
        # personalisation avec ajout de compte
        if self.creation_de_compte:
            self.ajouter['compte'] = list()
        # on ajoute les moyens par defaut
        try:
            self.listes['moyen'][Moyen.objects.get(id=settings.MD_DEBIT).nom] = settings.MD_DEBIT
        except Moyen.DoesNotExist:
            self.listes['moyen']['DEBIT'] = settings.MD_DEBIT
            Moyen.objects.create(id=settings.MD_DEBIT, nom='DEBIT', type="d")
        try:
            self.listes['moyen'][Moyen.objects.get(id=settings.MD_CREDIT).nom] = settings.MD_CREDIT
        except Moyen.DoesNotExist:
            self.listes['moyen']['CREDIT'] = settings.MD_CREDIT
            Moyen.objects.create(id=settings.MD_CREDIT, nom='CREDIT', type="r")
        # on ajoute le moyen pour le virement
        moyen_virement = Moyen.objects.filter(type='v')
        if moyen_virement.exists():
            self.listes['moyen'][moyen_virement[0].nom] = moyen_virement[0].id
            self.listes['moyen']['Virement']=moyen_virement[0].id
        else:
            self.listes['moyen']['Virement'] = Moyen.objects.create(nom='Virement', type="v").id
        # on gere la categorie Operation sur titre
        try:
            self.listes['cat'][Cat.objects.get(id=settings.ID_CAT_OST).nom] = settings.ID_CAT_OST
        except Cat.DoesNotExist:
            self.listes['moyen']['Operation sur titre'] = settings.ID_CAT_OST
            Cat.objects.create(id=settings.ID_CAT_OST, nom='Operation sur titre', type="d")
        try:
            self.listes['cat'][Cat.objects.get(id=settings.ID_CAT_PMV).nom] = settings.ID_CAT_PMV
        except Cat.DoesNotExist:
            self.listes['moyen']['Revenus de placement:Plus-values'] = settings.ID_CAT_PMV
            Cat.objects.create(id=settings.ID_CAT_PMV, nom='Revenus de placement:Plus-values', type="d")   
        try:
            self.tableau_import(nomfich)
            if len(self.erreur):
                messages.warning(self.request, "attention traitement interrompu")
                for err in self.erreur:
                    messages.warning(self.request, err)
                return False
        except (FormatException,ImportException) as e:
            if self.test == False:
                for err in self.erreur:
                    messages.warning(self.request, err)
                messages.error(self.request, e)
                return False
            else:
                raise e
    
        with transaction.commit_on_success():
            # import final
            # les comptes
            nb_ajout = 0
            if self.creation_de_compte:
                for obj in self.ajouter['compte']:
                        Compte.objects.create(id=obj['id'], nom=obj['nom'], type=obj['type'])
                        nb_ajout += 1
                if not self.test:
                    messages.info(self.request, "%s compte ajoutes" % nb_ajout)
            else:
                if 'compte' in self.ajouter:
                    raise ImportException("probleme alors que les comptes ne doivent pas etre cree, il y a en attente d'etre cree")
            # les tiers
            self.create('tiers', Tiers)
            
            # les titres
            nb_ajout = 0
            for titre in self.ajouter['titre']:
                Titre.objects.create(id=titre['id'], nom=titre['nom'], type='ZZZ', isin=titre['isin'], tiers_id=titre['tiers_id'])
                nb_ajout += 1
            if not self.test:
                messages.info(self.request, "%s titres ajoutes" % nb_ajout)

            # les categories
            self.create('cat', Cat)
            # les ib
            if settings.UTILISE_IB == True:
                self.create('ib', Ib)
            # les moyens
            self.create('moyen', Moyen)
            # les exercices
            if settings.UTILISE_EXERCICES == True:
                self.create('exercice', Exercice)
            # les rapp
            self.create('rapp', Rapp)
            #les opes
            for ope in self.ajouter['ope']:
                Ope.objects.create(
                        id=ope['id'],
                        automatique=ope['automatique'],
                        cat_id=ope['cat_id'],
                        compte_id=ope['compte_id'],
                        date=ope['date'],
                        date_val=ope['date_val'],
                        exercice_id=ope['exercice_id'],
                        ib_id=ope['ib_id'],
                        jumelle_id=ope['jumelle_id'],
                        mere_id=ope['mere_id'],
                        montant=ope['montant'],
                        moyen_id=ope['moyen_id'],
                        notes=ope['notes'],
                        num_cheque=ope['num_cheque'],
                        piece_comptable=ope['piece_comptable'],
                        pointe=ope['pointe'],
                        rapp_id=ope['rapp_id'],
                        tiers_id=ope['tiers_id'])
            # les ope_titres
            for obj in self.ajouter['ope_titre']:
                cpt = Compte.objects.get(id=obj["compte_id"])
                titre = Titre.objects.get(id=obj['titre_id'])
                if obj['nombre'] > 0:
                    ope_titre = cpt.achat(titre=titre, nombre=obj['nombre'], prix=obj['cours'], date=obj['date'])
                    ope = ope_titre.ope
                    ope.rapp_id = obj['rapp_id']
                    ope.pointe = obj['pointe']
                    ope.exercice_id = obj['exercice_id']
                    ope.save()
                else:
                    ope_titre = cpt.vente(titre=titre, nombre=obj['nombre'], prix=obj['cours'], date=obj['date'])
                    ope = ope_titre.ope_pmv
                    ope.rapp_id = obj['rapp_id']
                    ope.pointe = obj['pointe']
                    ope.exercice_id = obj['exercice_id']
                    ope.save()
                    ope = ope_titre.ope
                    ope.rapp_id = obj['rapp_id']
                    ope.pointe = obj['pointe']
                    ope.exercice_id = obj['exercice_id']
                    ope.save()
            print "troisieme tour"
            for obj in Ope.objects.filter(cat__nom="Virement"):
                if obj.montant<0:
                    nom= u"%s => %s"%(obj.compte.nom, obj.jumelle.compte.nom)
                else:
                    nom= u"%s => %s"%(obj.jumelle.compte.nom, obj.compte.nom)
                obj.tiers=Tiers.objects.get_or_create(nom=nom,defaults={"nom":nom})[0]
                obj.save()
    def get_success_url(self):
        return reverse(self.url)

    def get_form(self, form_class):
        form = super(Import_base, self).get_form(form_class)
        form.fields['nom_du_fichier'].label = u"nom_du_fichier %s" % self.type_f
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
        try:
            obj_id = self.listes[liste][name]  # pylint: disable=W0622
        except KeyError:
            # si c'est un nom vide pas besoin de creer
            if name == '' or name is None or name == 0:
                return None
            try:  # on regarde si ca existe
                obj_id = model.objects.get(nom=name).id
            except model.DoesNotExist:  # on demande la creation plus tard
                obj_id = self.ajout(obj=liste, model=model, nouveau=nouveau)
            self.listes[liste][name] = obj_id
        return obj_id
            
    def ajout(self, obj, model, nouveau):
        try:
            last_id = self.id[obj]
        except KeyError:
            last_id = model.objects.aggregate(id_max=Max('id'))['id_max']
            if last_id is None:
                last_id = 0
        if 'id' not in nouveau or nouveau['id'] < last_id:  # on cree un operation
            last_id += 1
            self.id[obj] = last_id
            nouveau['id'] = last_id
        self.ajouter[obj].append(nouveau)
        return last_id
    
    def tableau_import(self, nomfich):
        raise NotImplementedError(u"il faut definir comment on importe")
    def create(self, obj, model):
        nb_ajout = 0
        nom_ajoute = [objet['nom'] for objet in self.ajouter[obj]] 
        try:
            for objet in self.ajouter[obj]:
                model.objects.create(**objet)
                nb_ajout += 1
            if nb_ajout > 0 and not self.test:
                messages.info(self.request, u"%s %s ajoutés (%s)" % (nb_ajout, obj, nom_ajoute))
        except KeyError as e:
            messages.error(self.request, e)

        
