# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Ope_titre.invest'
        db.delete_column(u'gsb_ope_titre', 'invest')


    def backwards(self, orm):
        # Adding field 'Ope_titre.invest'
        db.add_column(u'gsb_ope_titre', 'invest',
                      self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=15, decimal_places=2),
                      keep_default=False)


    models = {
        u'gsb.banque': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Banque'},
            'cib': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.cat': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Cat'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'d'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.compte': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Compte'},
            'banque': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Banque']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'cle_compte': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'guichet': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '15', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'moyen_credit_defaut': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compte_moyen_credit_set'", 'on_delete': 'models.PROTECT', 'default': 'None', 'to': u"orm['gsb.Moyen']", 'blank': 'True', 'null': 'True'}),
            'moyen_debit_defaut': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compte_moyen_debit_set'", 'on_delete': 'models.PROTECT', 'default': 'None', 'to': u"orm['gsb.Moyen']", 'blank': 'True', 'null': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'num_compte': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'ouvert': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'solde_init': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'solde_mini_autorise': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'null': 'True', 'max_digits': '15', 'decimal_places': '2', 'blank': 'True'}),
            'solde_mini_voulu': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'null': 'True', 'max_digits': '15', 'decimal_places': '2', 'blank': 'True'}),
            'titre': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['gsb.Titre']", 'through': u"orm['gsb.Ope_titre']", 'symmetrical': 'False'}),
            'titulaire': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'b'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.cours': {
            'Meta': {'ordering': "['-date']", 'unique_together': "(('titre', 'date'),)", 'object_name': 'Cours'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 9, 9, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'titre': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Titre']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'valeur': ('django.db.models.fields.DecimalField', [], {'default': '1.0', 'max_digits': '15', 'decimal_places': '3'})
        },
        u'gsb.echeance': {
            'Meta': {'ordering': "['date']", 'object_name': 'Echeance'},
            'cat': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Cat']", 'on_delete': 'models.PROTECT'}),
            'compte': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Compte']"}),
            'compte_virement': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'echeance_virement_set'", 'null': 'True', 'blank': 'True', 'to': u"orm['gsb.Compte']"}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 9, 9, 0, 0)'}),
            'date_limite': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'exercice': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Exercice']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'ib': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Ib']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inscription_automatique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'intervalle': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'montant': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '15', 'decimal_places': '2'}),
            'moyen': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Moyen']", 'on_delete': 'models.PROTECT'}),
            'moyen_virement': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'echeance_moyen_virement_set'", 'null': 'True', 'to': u"orm['gsb.Moyen']"}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'periodicite': ('django.db.models.fields.CharField', [], {'default': "'u'", 'max_length': '1'}),
            'tiers': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Tiers']", 'on_delete': 'models.PROTECT'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'valide': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'gsb.exercice': {
            'Meta': {'ordering': "['-date_debut']", 'object_name': 'Exercice'},
            'date_debut': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 9, 9, 0, 0)'}),
            'date_fin': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ib': {
            'Meta': {'ordering': "['type', 'nom']", 'object_name': 'Ib'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'd'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.moyen': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Moyen'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'d'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ope': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'Ope'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'automatique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cat': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Cat']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'compte': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Compte']"}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 9, 9, 0, 0)'}),
            'date_val': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'exercice': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Exercice']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'ib': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Ib']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jumelle': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'jumelle_set'", 'null': 'True', 'default': 'None', 'to': u"orm['gsb.Ope']", 'blank': 'True', 'unique': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'mere': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'filles_set'", 'on_delete': 'models.PROTECT', 'default': 'None', 'to': u"orm['gsb.Ope']", 'blank': 'True', 'null': 'True'}),
            'montant': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '15', 'decimal_places': '2'}),
            'moyen': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Moyen']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'num_cheque': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'ope_titre_ost': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ope_ost'", 'unique': 'True', 'null': 'True', 'to': u"orm['gsb.Ope_titre']"}),
            'ope_titre_pmv': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ope_pmv'", 'unique': 'True', 'null': 'True', 'to': u"orm['gsb.Ope_titre']"}),
            'piece_comptable': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'pointe': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rapp': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Rapp']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'tiers': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Tiers']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ope_titre': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Ope_titre'},
            'compte': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Compte']"}),
            'cours': ('django.db.models.fields.DecimalField', [], {'default': '1', 'max_digits': '15', 'decimal_places': '5'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nombre': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '15', 'decimal_places': '5'}),
            'titre': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Titre']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.rapp': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Rapp'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 9, 9, 0, 0)', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.tiers': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Tiers'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_titre': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'titre': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['gsb.Titre']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.titre': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Titre'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isin': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '12', 'db_index': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'ZZZ'", 'max_length': '3'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['gsb']