# coding=utf-8
from rest_framework import serializers
from .. import models


class TiersSerializer(serializers.ModelSerializer):
    # titre= serializers.Field(source='titre.nom')
    class Meta(object):
        model = models.Tiers
        fields = ('nom', 'is_titre', 'uuid', 'id', 'lastupdate', 'titre', 'notes', 'lastupdate', 'date_created')


class TitreSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Titre
        fields = ('nom', 'uuid', 'type', 'isin', 'lastupdate', 'date_created', 'tiers')


class CoursSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Cours
        fields = ('date', 'valeur', 'titre', 'uuid', 'lastupdate', 'date_created')


class BanqueSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Banque
        fields = ('cib', 'nom', 'notes', 'uuid', 'lastupdate')


class CatSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Cat
        fields = ('nom', 'type', 'couleur', 'uuid', 'lastupdate', 'date_created')


class IbSarializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Ib
        fields = ('nom', 'type', 'uuid', 'lastupdate', 'date_created')


class ExerciceSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Exercice
        fields = ('date_debut', 'date_fin', 'nom', 'uuid', 'lastupdate', 'date_created')


class CompteSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Compte
        fields = (
            'nom', 'type', 'titulaire', 'banque', 'ouvert', 'notes', 'moyen_credit_defaut', 'moyen_debit_defaut',
            'couleur', 'uuid', 'lastupdate', 'date_created')


class Ope_titreSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Ope_titre
        fields = ('titre', 'compte', 'nombre', 'date', 'cours', 'uuid', 'lastupdate', 'date_created')


class MoyenSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Moyen
        fields = ('nom', 'type', 'uuid', 'lastupdate', 'date_created')


class RappSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Rapp
        fields = ('nom', 'date', 'uuid', 'lastupdate', 'date_created')


class EcheanceSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Echeance
        fields = (
            'date', 'date_limite', 'intervalle', 'periodicite', 'valide', 'compte', 'montant', 'tiers', 'cat', 'moyen',
            'ib', 'compte_virement', 'moyen_virement', 'exercice', 'notes', 'inscription_automatique', 'uuid', 'lastupdate',
            'date_created')


class OpeSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.Ope
        fields = (
            'compte', 'date', 'date_val', 'montant', 'tiers', 'cat', 'moyen', 'ib', 'num_cheque', 'pointe', 'exercice',
            'notes', 'uuid', 'lastupdate', 'date_created')