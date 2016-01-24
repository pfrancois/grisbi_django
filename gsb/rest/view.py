# coding=utf-8
from rest_framework import viewsets
from .. import models
from . import serializer


class TiersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Tiers.objects.all()
    serializer_class = serializer.TiersSerializer


class TitreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Titre.objects.all()
    serializer_class = serializer.TitreSerializer


class CoursViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    #@todo faire que ca demande un titre
    """
    queryset = models.Cours.objects.all()
    serializer_class = serializer.CoursSerializer


class BanqueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Banque.objects.all()
    serializer_class = serializer.BanqueSerializer


class CatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Cat.objects.all()
    serializer_class = serializer.CatSerializer


class IbViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Ib.objects.all()
    serializer_class = serializer.IbSarializer


class ExerciceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Exercice.objects.all()
    serializer_class = serializer.ExerciceSerializer


class CompteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Compte.objects.all()
    serializer_class = serializer.CompteSerializer


class OpeTitreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Ope_titre.objects.all()
    serializer_class = serializer.Ope_titreSerializer


class OpeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Ope.objects.all()
    serializer_class = serializer.OpeSerializer
