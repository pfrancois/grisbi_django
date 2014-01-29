# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'config'
        db.create_table('gsb_config', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('derniere_import_money_journal', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ('derniere_export_money_journal', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0))),
        ))
        db.send_create_signal(u'gsb', ['config'])

        # Adding model 'Tiers'
        db.create_table('gsb_tiers', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('is_titre', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('titre', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gsb.Titre'], unique=True, null=True, blank=True)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Tiers'])

        # Adding model 'Titre'
        db.create_table(u'gsb_titre', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('isin', self.gf('django.db.models.fields.CharField')(unique=True, max_length=12, db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='ZZZ', max_length=3)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Titre'])

        # Adding model 'Cours'
        db.create_table('gsb_cours', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2014, 1, 27, 0, 0), db_index=True)),
            ('valeur', self.gf('django.db.models.fields.DecimalField')(default=1.0, max_digits=15, decimal_places=3)),
            ('titre', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gsb.Titre'])),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Cours'])

        # Adding unique constraint on 'Cours', fields ['titre', 'date']
        db.create_unique('gsb_cours', ['titre_id', 'date'])

        # Adding model 'Banque'
        db.create_table('gsb_banque', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cib', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=5, blank=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Banque'])

        # Adding model 'Cat'
        db.create_table('gsb_cat', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='d', max_length=1)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('couleur', self.gf('colorful.fields.RGBColorField')(default='#FFFFFF', max_length=7)),
        ))
        db.send_create_signal(u'gsb', ['Cat'])

        # Adding model 'Ib'
        db.create_table('gsb_ib', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'd', max_length=1)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Ib'])

        # Adding model 'Exercice'
        db.create_table('gsb_exercice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_debut', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2014, 1, 27, 0, 0))),
            ('date_fin', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Exercice'])

        # Adding model 'Compte'
        db.create_table('gsb_compte', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('titulaire', self.gf('django.db.models.fields.CharField')(default='', max_length=40, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='b', max_length=1)),
            ('banque', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Banque'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('guichet', self.gf('django.db.models.fields.CharField')(default='', max_length=15, blank=True)),
            ('num_compte', self.gf('django.db.models.fields.CharField')(default='', max_length=20, db_index=True, blank=True)),
            ('cle_compte', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('solde_init', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=15, decimal_places=2)),
            ('solde_mini_voulu', self.gf('django.db.models.fields.DecimalField')(default=0.0, null=True, max_digits=15, decimal_places=2, blank=True)),
            ('solde_mini_autorise', self.gf('django.db.models.fields.DecimalField')(default=0.0, null=True, max_digits=15, decimal_places=2, blank=True)),
            ('ouvert', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('moyen_credit_defaut', self.gf('django.db.models.fields.related.ForeignKey')(related_name='compte_moyen_credit_set', on_delete=models.PROTECT, default=None, to=orm['gsb.Moyen'], blank=True, null=True)),
            ('moyen_debit_defaut', self.gf('django.db.models.fields.related.ForeignKey')(related_name='compte_moyen_debit_set', on_delete=models.PROTECT, default=None, to=orm['gsb.Moyen'], blank=True, null=True)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('couleur', self.gf('colorful.fields.RGBColorField')(default='#FFFFFF', max_length=7)),
        ))
        db.send_create_signal(u'gsb', ['Compte'])

        # Adding model 'Ope_titre'
        db.create_table('gsb_ope_titre', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('titre', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gsb.Titre'])),
            ('compte', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gsb.Compte'])),
            ('nombre', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=15, decimal_places=6)),
            ('date', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('cours', self.gf('django.db.models.fields.DecimalField')(default=1, max_digits=15, decimal_places=6)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Ope_titre'])

        # Adding model 'Moyen'
        db.create_table('gsb_moyen', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='d', max_length=1)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Moyen'])

        # Adding model 'Rapp'
        db.create_table('gsb_rapp', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nom', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2014, 1, 27, 0, 0), null=True, blank=True)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Rapp'])

        # Adding model 'Echeance'
        db.create_table('gsb_echeance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2014, 1, 27, 0, 0), db_index=True)),
            ('date_limite', self.gf('django.db.models.fields.DateField')(default=None, null=True, db_index=True, blank=True)),
            ('intervalle', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('periodicite', self.gf('django.db.models.fields.CharField')(default='u', max_length=1)),
            ('valide', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('compte', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gsb.Compte'])),
            ('montant', self.gf('django.db.models.fields.DecimalField')(default=0.0, max_digits=15, decimal_places=2)),
            ('tiers', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gsb.Tiers'], on_delete=models.PROTECT)),
            ('cat', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gsb.Cat'], on_delete=models.PROTECT)),
            ('moyen', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Moyen'], on_delete=models.PROTECT)),
            ('ib', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Ib'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('compte_virement', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='echeance_virement_set', null=True, blank=True, to=orm['gsb.Compte'])),
            ('moyen_virement', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='echeance_moyen_virement_set', null=True, to=orm['gsb.Moyen'])),
            ('exercice', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Exercice'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('inscription_automatique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'gsb', ['Echeance'])

        # Adding model 'Ope'
        db.create_table('gsb_ope', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('compte', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gsb.Compte'])),
            ('date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2014, 1, 27, 0, 0), db_index=True)),
            ('date_val', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('montant', self.gf('django.db.models.fields.DecimalField')(default=0.0, max_digits=15, decimal_places=2)),
            ('tiers', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Tiers'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('cat', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Cat'], null=True, on_delete=models.PROTECT, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('moyen', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Moyen'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('num_cheque', self.gf('django.db.models.fields.CharField')(default='', max_length=20, blank=True)),
            ('pointe', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rapp', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Rapp'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('exercice', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Exercice'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('ib', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['gsb.Ib'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('jumelle', self.gf('django.db.models.fields.related.OneToOneField')(related_name='jumelle_set', null=True, default=None, to=orm['gsb.Ope'], blank=True, unique=True)),
            ('mere', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='filles_set', null=True, blank=True, to=orm['gsb.Ope'])),
            ('automatique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('piece_comptable', self.gf('django.db.models.fields.CharField')(default='', max_length=20, blank=True)),
            ('lastupdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('ope_titre_ost', self.gf('django.db.models.fields.related.OneToOneField')(related_name='ope_ost', unique=True, null=True, to=orm['gsb.Ope_titre'])),
            ('ope_titre_pmv', self.gf('django.db.models.fields.related.OneToOneField')(related_name='ope_pmv', unique=True, null=True, to=orm['gsb.Ope_titre'])),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'gsb', ['Ope'])

    def backwards(self, orm):
        # Removing unique constraint on 'Cours', fields ['titre', 'date']
        db.delete_unique('gsb_cours', ['titre_id', 'date'])

        # Deleting model 'config'
        db.delete_table('gsb_config')

        # Deleting model 'Tiers'
        db.delete_table('gsb_tiers')

        # Deleting model 'Titre'
        db.delete_table(u'gsb_titre')

        # Deleting model 'Cours'
        db.delete_table('gsb_cours')

        # Deleting model 'Banque'
        db.delete_table('gsb_banque')

        # Deleting model 'Cat'
        db.delete_table('gsb_cat')

        # Deleting model 'Ib'
        db.delete_table('gsb_ib')

        # Deleting model 'Exercice'
        db.delete_table('gsb_exercice')

        # Deleting model 'Compte'
        db.delete_table('gsb_compte')

        # Deleting model 'Ope_titre'
        db.delete_table('gsb_ope_titre')

        # Deleting model 'Moyen'
        db.delete_table('gsb_moyen')

        # Deleting model 'Rapp'
        db.delete_table('gsb_rapp')

        # Deleting model 'Echeance'
        db.delete_table('gsb_echeance')

        # Deleting model 'Ope'
        db.delete_table('gsb_ope')

    models = {
        u'gsb.banque': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Banque'},
            'cib': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '5', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.cat': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Cat'},
            'couleur': ('colorful.fields.RGBColorField', [], {'default': "'#FFFFFF'", 'max_length': '7'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
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
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.config': {
            'Meta': {'object_name': 'config'},
            'derniere_export_money_journal': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'derniere_import_money_journal': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'gsb.cours': {
            'Meta': {'ordering': "['-date']", 'unique_together': "(('titre', 'date'),)", 'object_name': 'Cours'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 1, 27, 0, 0)', 'db_index': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
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
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 1, 27, 0, 0)', 'db_index': 'True'}),
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
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'valide': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'gsb.exercice': {
            'Meta': {'ordering': "['-date_debut']", 'object_name': 'Exercice'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_debut': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 1, 27, 0, 0)'}),
            'date_fin': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ib': {
            'Meta': {'ordering': "['type', 'nom']", 'object_name': 'Ib'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'd'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.moyen': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Moyen'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'d'", 'max_length': '1'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.ope': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'Ope'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'automatique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cat': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['gsb.Cat']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'compte': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gsb.Compte']"}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 1, 27, 0, 0)', 'db_index': 'True'}),
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
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
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
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.rapp': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Rapp'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 1, 27, 0, 0)', 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
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
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        },
        u'gsb.titre': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Titre'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isin': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '12', 'db_index': 'True'}),
            'lastupdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'ZZZ'", 'max_length': '3'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['gsb']
