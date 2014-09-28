__author__ = 'francois'
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
