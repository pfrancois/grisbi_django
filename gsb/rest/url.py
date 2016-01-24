# coding=utf-8
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from . import view

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'Tiers', view.TiersViewSet)
router.register(r'Titres', view.TitreViewSet)
router.register(r'Cours', view.CoursViewSet)
router.register(r'Banques', view.BanqueViewSet)
router.register(r'Cats', view.CatViewSet)
router.register(r'Ibs', view.IbViewSet)
router.register(r'Exercices', view.ExerciceViewSet)
router.register(r'Comptes', view.CompteViewSet)
router.register(r'Ope_Titres', view.OpeTitreViewSet)
router.register(r'Ope', view.OpeViewSet)
# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browseable API.
urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^', include(router.urls)),
]
