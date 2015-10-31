# -*- coding: utf-8 -*-
"""les vues qui sont implementés ici
option_index: vue qui gere l'index de toutes les options possible accesibles vie le menu option
gestion_echeances:vue qui gere les echeances
"""


from django.template import RequestContext
from django.conf import settings
from django.shortcuts import render_to_response
from django.contrib import messages
from .views import Mytemplateview
from .models import Compte, Cat, Tiers, Moyen, Echeance
from .io import import_base


def verif_element_config(element, request, collection=None):
    id_elem = getattr(settings, element, None)
    if id_elem is None:
        messages.error(request, "%s non definit dans setting.py" % element)
    if collection is not None:
        objet = collection.objects.filter(id=id_elem)
        if not objet.exists():
            messages.error(request, "%s n'existe pas" % element)


def verif_config(request):
    import_base.Moyen_cache(request)
    import_base.Cat_cache(request)
    import_base.IB_cache(request)
    import_base.Compte_cache(request)
    import_base.Banque_cache(request)
    import_base.Exercice_cache(request)
    import_base.Tiers_cache(request)
    import_base.Ope_cache(request)
    titres = import_base.Titre_cache(request)
    import_base.Cours_cache(request, titres)
    import_base.Moyen_defaut_cache()
    import_base.Rapp_cache(request)
    verif_element_config("ID_CPT_M", request, Compte)
    verif_element_config("TAUX_VERSEMENT", request)
    verif_element_config("ID_CAT_COTISATION", request, Cat)
    verif_element_config("ID_CAT_OST", request, Cat)
    verif_element_config("ID_CAT_PMV", request, Cat)
    verif_element_config("ID_TIERS_COTISATION", request, Tiers)
    verif_element_config("MD_CREDIT", request, Moyen)
    verif_element_config("MD_DEBIT", request, Moyen)
    verif_element_config("TITRE", request)
    verif_element_config("DEVISE_GENERALE", request)
    verif_element_config("TAUX_VERSEMENT", request)
    verif_element_config("AFFICHE_CLOT", request)
    verif_element_config("UTILISE_EXERCICES", request)
    return render_to_response(
        'generic.djhtm',
        {'resultats': ("vous trouverez les résultats de la verification de la config",),
         'titre_long': "verif config",
         'titre': "verif _config",
        },
        context_instance=RequestContext(request)
    )


class Echeance_view(Mytemplateview):
    template_name = 'generic.djhtm'
    titre = "écheances échus"

    def get_context_data(self, **kwargs):
        return {
            'titre': self.titre
        }

    def dispatch(self, request, *args, **kwargs):
        """on a besoin pour le method decorator"""
        Echeance.check_if_necessary(request)
        return super(Echeance_view, self).dispatch(request, *args, **kwargs)
