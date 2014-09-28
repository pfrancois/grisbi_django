from rest_framework import serializers
from .. import models

        
class TiersSerializer(serializers.ModelSerializer):
    #titre= serializers.Field(source='titre.nom')
    class Meta(object):
        model = models.Tiers
        fields = ('nom', 'is_titre', 'uuid','id', 'lastupdate', 'titre', 'notes', 'url', 'lastupdate','date_created')

class TitreSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Titre
        fields = ('url','nom','uuid','type','isin','lastupdate','date_created','tiers')

class CoursSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Cours
        fields ={'url', 'date','valeur','titre', 'uuid','lastupdate','date_created'}

class BanqueSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Banque
        fields ={'url', 'cib','nom','notes', 'uuid','lastupdate','date_created'}