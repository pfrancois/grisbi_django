# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        template_update="""create trigger update_{type} after update on gsb_{type}
        begin
            insert into gsb_db_log (datamodel,date_created,id_model,memo,uuid)
                values ('{type}',datetime('NOW'),old.id, 'U',old.uuid);
        end;""".format
        template_insert="""create trigger insert_{type} after insert on gsb_{type}
        begin
            insert into gsb_db_log (datamodel,date_created,id_model,memo,uuid)
                values ('{type}',datetime('NOW'),new.id, 'I',new.uuid);
        end;""".format
        template_delete="""create trigger delete_{type} delete on gsb_{type}
        begin
            insert into gsb_db_log (datamodel,date_created,id_model,memo,uuid)
                values ('{type}',datetime('NOW'),old.id, 'D',old.uuid);
        end;
        """.format

        for element in ("ope","cat","banque","compte","cours","echeance","exercice","ib","moyen","ope_titre","rapp","tiers","titre"):
            query=template_update(type=element)
            db.execute(query)
            query=template_insert(type=element)
            db.execute(query)
            query=template_delete(type=element)
            db.execute(query)

    def backwards(self, orm):
        for element in ("ope","cat","banque","compte","cours","echeance","exercice","ib","moyen","ope_titre","rapp","tiers","titre"):
            query="drop trigger update_{type};".format(type=element)
            db.execute(query)
            query="drop trigger insert_{type};".format(type=element)
            db.execute(query)
            query="drop trigger delete_{type};".format(type=element)
            db.execute(query)


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'gsb.banque': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Banque'},
            'cib': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '5', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.cat': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Cat'},
            'couleur': ('colorful.fields.RGBColorField', [], {'default': "'#FFFFFF'", 'max_length': '7'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'d'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.compte': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Compte'},
            'banque': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Banque']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'cle_compte': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'couleur': ('colorful.fields.RGBColorField', [], {'default': "'#FFFFFF'", 'max_length': '7'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'guichet': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '15', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'moyen_credit_defaut': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compte_moyen_credit_set'", 'on_delete': 'models.PROTECT', 'default': 'None', 'to': u"orm['gsb.Moyen']", 'blank': 'True', 'null': 'True'}),
            'moyen_debit_defaut': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compte_moyen_debit_set'", 'on_delete': 'models.PROTECT', 'default': 'None', 'to': u"orm['gsb.Moyen']", 'blank': 'True', 'null': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'num_compte': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'db_index': 'True', 'blank': 'True'}),
            'ouvert': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'solde_init': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '15', 'decimal_places': '2'}),
            'solde_mini_autorise': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'null': 'True', 'max_digits': '15', 'decimal_places': '2', 'blank': 'True'}),
            'solde_mini_voulu': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'null': 'True', 'max_digits': '15', 'decimal_places': '2', 'blank': 'True'}),
            'titre': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['gsb.Titre']", 'through': u"orm['gsb.Ope_titre']", 'symmetrical': 'False'}),
            'titulaire': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'b'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.config': {
            'Meta': {'object_name': 'Config'},
            'derniere_import_money_journal': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'gsb.cours': {
            'Meta': {'ordering': "['-date']", 'unique_together': "(('titre', 'date'),)", 'object_name': 'Cours'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 7, 7, 0, 0)', 'db_index': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'titre': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Titre']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'}),
            'valeur': ('django.db.models.fields.DecimalField', [], {'default': '1.0', 'max_digits': '15', 'decimal_places': '3'})
        },
        u'gsb.db_log': {
            'Meta': {'object_name': 'db_log'},
            'datamodel': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_model': ('django.db.models.fields.IntegerField', [], {}),
            'memo': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'gsb.echeance': {
            'Meta': {'ordering': "['date']", 'object_name': 'Echeance'},
            'cat': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Cat']", 'on_delete': 'models.PROTECT'}),
            'compte': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Compte']"}),
            'compte_virement': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'echeance_virement_set'", 'null': 'True', 'blank': 'True', 'to': u"orm['gsb.Compte']"}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 7, 7, 0, 0)', 'db_index': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_limite': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
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
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'}),
            'valide': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'gsb.exercice': {
            'Meta': {'ordering': "['-date_debut']", 'object_name': 'Exercice'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_debut': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 7, 7, 0, 0)'}),
            'date_fin': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ib': {
            'Meta': {'ordering': "['type', 'nom']", 'object_name': 'Ib'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'd'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.moyen': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Moyen'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'d'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ope': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'Ope'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'automatique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cat': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Cat']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'compte': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Compte']"}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 7, 7, 0, 0)', 'db_index': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_val': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'exercice': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Exercice']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'ib': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Ib']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jumelle': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'jumelle_set'", 'null': 'True', 'default': 'None', 'to': u"orm['gsb.Ope']", 'blank': 'True', 'unique': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'mere': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'filles_set'", 'null': 'True', 'blank': 'True', 'to': u"orm['gsb.Ope']"}),
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
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ope_titre': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Ope_titre'},
            'compte': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Compte']"}),
            'cours': ('django.db.models.fields.DecimalField', [], {'default': '1', 'max_digits': '15', 'decimal_places': '6'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nombre': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '15', 'decimal_places': '6'}),
            'titre': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Titre']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.rapp': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Rapp'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 7, 7, 0, 0)', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.tiers': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Tiers'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_titre': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'titre': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['gsb.Titre']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'gsb.titre': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Titre'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isin': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '12', 'db_index': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'ZZZ'", 'max_length': '3'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['gsb']