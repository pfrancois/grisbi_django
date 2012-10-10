# -*- coding: utf-8 -*-
"""les vues qui sont implementés ici
import_file : vue qui gere les import
option_index: vue qui gere l'index de toutes les options possible accesibles vie le menu option
gestion_echeances:vue qui gere les echeances
"""

from __future__ import absolute_import
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response
from . import forms as gsb_forms
import logging, os, time
from .models import Echeance
from django.contrib.auth.decorators import login_required
from .import_gsb import import_gsb_050
from django.contrib import messages
from .views import Mytemplateview,Myredirectview
from .models import Compte,Cat,Tiers,Moyen,Echeance

@login_required
def import_file(request):
    logger = logging.getLogger('gsb.import')
    nomfich = ""
    etape_nb = 1
    liste_import = {"gsb_0_5_0":gsb_forms.ImportForm2_gsb_0_5_0,
                    "qif":gsb_forms.ImportForm2_qif}
    if request.method == 'POST':
        if request.session.get('import_etape_nb', '1') == 1:
            form = gsb_forms.ImportForm1(request.POST, request.FILES)
            if form.is_valid():
                nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.gsb" % (
                    request.FILES['nom_du_fichier'].name, time.strftime("%Y-%b-%d_%H-%M-%S")))
                destination = open(nomfich, 'wb+')
                for chunk in request.FILES['nom_du_fichier'].chunks():
                    destination.write(chunk)
                destination.close()
                #renomage ok
                logger.debug("enregistrement fichier ok")
                request.session['nomfich'] = nomfich
                request.session['import_type'] = form.cleaned_data['type_f']
                try:
                    form = liste_import[form.cleaned_data['type_f']]()
                    etape_nb = 2
                except KeyError:
                    messages.error(request, message="type d'import inconnu")
        else:
            try:
                form = liste_import[request.session['import_type']](request.POST)
                if form.is_valid():
                    # on recupere les info pour le nom
                    try:
                        info = u"%s le %s" % (request.META['REMOTE_ADDR'], time.strftime(u"%d/%m/%Y a %Hh%Mm%Ss"))
                    except KeyError:
                        info = u"%s le %s" % ('0.0.0.0', time.strftime(u"%d/%m/%Y a %Hh%Mm%Ss") )
                        #-----------------------gestion des imports
                    try:
                        nomfich = request.session['nomfich']
                        #on essaye d'ouvrir le fichier
                        destination = open(nomfich, 'r')
                        #si on peut
                        destination.close()
                        if request.session['import_type'] == 'qif':
                            if nomfich[-3:] == "qif":
                                #import_qif(nomfich, compte=form.cleaned_data['compte']) #pas encore fait
                                pass
                            else:
                                raise ValueError("pas le bon format")
                        elif request.session['import_type'] == 'gsb_0_5_0':
                            if nomfich[-3:] == "gsb":
                                if form.cleaned_data['replace'] == 'remplacement':
                                    logger.warning(
                                        u"remplacement data par fichier %s format %s %s" % (nomfich, request.session['import_type'], info))
                                    import_gsb_050(nomfich=nomfich, efface_table=True)
                                else:
                                    logger.warning(
                                        u"fusion data par fichier %s format %s %s" % (nomfich, request.session['import_type'], info))
                                    import_gsb_050(nomfich=nomfich, efface_table=False)
                            else:
                                raise ValueError("pas le bon format")
                        else:
                            raise NotImplementedError(u' %s pas implementé' % request.session['import_type'])
                    except Exception as exp:
                        logger.warning(u"probleme d'importation à cause de %s(%s) " % (type(exp), exp))
                        messages.error(request, u"erreur dans l'import du fichier %s" % nomfich)
                    else:
                        messages.success(request, u"import du fichier %s ok" % nomfich)
                        return HttpResponseRedirect(reverse('gsb.views.index'))
            except KeyError:
                messages.error(request, message="type d'import inconnu")
                form = gsb_forms.ImportForm1()
                etape_nb = 1
    else:
        form = gsb_forms.ImportForm1()
        etape_nb = 1
    request.session['import_etape_nb'] = etape_nb
    param = {'form':form,
             'titre':u"importation d'un fichier: étape %s" % etape_nb,
             'etape_nb':etape_nb}
    return render_to_response('gsb/import.djhtm',
                              param,
                              context_instance=RequestContext(request))



def gestion_echeances(request):
    """vue qui gere les echeances"""
    Echeance.check(request)
    return render_to_response('gsb/options.djhtm', {'titre':u'integration des échéances échues', }, context_instance=RequestContext(request))


def verif_element_config(element,request,collection=None):
    id=getattr(settings,element,None)
    if id is None:
        messages.error(request,"%s non definit dans setting.py"%element)
    if collection is not None:
        objet=collection.objects.filter(id=id)
        if not objet.exists():
            messages.error(request, u"%s n'existe pas"%element)

def verif_config(request):
    verif_element_config("NB_JOURS_AFF",request)
    verif_element_config("ID_CPT_M",request,Compte)
    verif_element_config("TAUX_VERSEMENT",request)
    verif_element_config("ID_CAT_COTISATION",request,Cat)
    verif_element_config("ID_CAT_OST",request,Cat)
    verif_element_config("ID_CAT_PMV",request,Cat)
    verif_element_config("ID_TIERS_COTISATION",request,Tiers)
    verif_element_config("MD_CREDIT",request,Moyen)
    verif_element_config("MD_DEBIT",request,Moyen)
    verif_element_config("TITRE",request)
    verif_element_config("DEVISE_GENERALE",request)
    verif_element_config("TAUX_VERSEMENT",request)
    verif_element_config("AFFICHE_CLOT",request)
    verif_element_config("UTILISE_EXERCICES",request)

    return render_to_response(
                'generic.djhtm',
                {'resultats':(u"vous trouverez les résultats de la verification de la config",),
                   'titre_long':"verif config",
                   'titre':"verif _config",
                },
                context_instance=RequestContext(request)
    )

class Echeance_view(Mytemplateview):
    template_name='generic.djhtm'
    titre=u"écheances échus"
    def get_context_data(self, **kwargs):
        return {
            'titre': self.titre
        }
    def dispatch(self,  request, *args, **kwargs):
        """on a besoin pour le method decorator"""
        Echeance.check(request)
        return super(Echeance_view, self).dispatch(request, *args, **kwargs)