# coding=utf-8
from rest_framework import viewsets
from .. import models
from . import serializer


class TiersViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Tiers.objects.all()
    serializer_class = serializer.TiersSerializer


class TitreViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Titre.objects.all()
    serializer_class = serializer.TitreSerializer


class CoursViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    #@todo faire que ca demande un titre
    """
    queryset = models.Cours.objects.all()
    serializer_class = serializer.CoursSerializer


class BanqueViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Banque.objects.all()
    serializer_class = serializer.BanqueSerializer


class CatViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Cat.objects.all()
    serializer_class = serializer.CatSerializer


class IbViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Ib.objects.all()
    serializer_class = serializer.IbSarializer


class ExerciceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Exercice.objects.all()
    serializer_class = serializer.ExerciceSerializer


class CompteViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Compte.objects.all()
    serializer_class = serializer.CompteSerializer


class OpeTitreViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Ope_titre.objects.all()
    serializer_class = serializer.Ope_titreSerializer


class OpeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,`update` and `destroy` actions.
    """
    queryset = models.Ope.objects.all()
    serializer_class = serializer.OpeSerializer
