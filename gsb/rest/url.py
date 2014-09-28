# coding=utf-8
from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter
from . import view

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'Tiers', view.TiersViewSet)
router.register(r'Titres', view.TitreViewSet)
# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^', include(router.urls)),
)
