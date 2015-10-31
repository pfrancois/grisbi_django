# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
import colorful.fields
import gsb.utils
from decimal import Decimal
import gsb.model_field
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Banque',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cib', models.CharField(db_index=True, max_length=5, blank=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('notes', models.TextField(default=b'', blank=True)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
            ],
            options={
                'ordering': ['nom'],
                'db_table': 'gsb_banque',
            },
        ),
        migrations.CreateModel(
            name='Cat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=50, verbose_name='nom de la cat\xe9gorie', db_index=True)),
                ('type', models.CharField(default=b'd', max_length=1, verbose_name='type de la cat\xe9gorie', choices=[(b'r', 'recette'), (b'd', 'd\xe9pense'), (b'v', 'virement')])),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
                ('couleur', colorful.fields.RGBColorField(default=b'#FFFFFF', max_length=7)),
            ],
            options={
                'ordering': ['nom'],
                'db_table': 'gsb_cat',
                'verbose_name': 'cat\xe9gorie',
            },
        ),
        migrations.CreateModel(
            name='Compte',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('titulaire', models.CharField(default=b'', max_length=40, blank=True)),
                ('type', models.CharField(default=b'b', max_length=1, choices=[(b'b', 'bancaire'), (b'e', 'espece'), (b'p', 'passif'), (b't', 'titre'), (b'a', 'autre actifs')])),
                ('guichet', models.CharField(default=b'', max_length=15, blank=True)),
                ('num_compte', models.CharField(default=b'', max_length=20, db_index=True, blank=True)),
                ('cle_compte', models.IntegerField(default=0, null=True, blank=True)),
                ('solde_init', gsb.model_field.CurField(default=Decimal('0.00'), max_digits=15, decimal_places=2)),
                ('solde_mini_voulu', gsb.model_field.CurField(default=0.0, null=True, max_digits=15, decimal_places=2, blank=True)),
                ('solde_mini_autorise', gsb.model_field.CurField(default=0.0, null=True, max_digits=15, decimal_places=2, blank=True)),
                ('ouvert', models.BooleanField(default=True)),
                ('notes', models.TextField(default=b'', blank=True)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
                ('couleur', colorful.fields.RGBColorField(default=b'#FFFFFF', max_length=7)),
                ('banque', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Banque', null=True)),
            ],
            options={
                'ordering': ['nom'],
                'db_table': 'gsb_compte',
            },
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('derniere_import_money_journal', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ],
            options={
                'db_table': 'gsb_config',
            },
        ),
        migrations.CreateModel(
            name='Cours',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=gsb.utils.today, db_index=True)),
                ('valeur', gsb.model_field.CurField(default=1.0, max_digits=15, decimal_places=3)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
            ],
            options={
                'ordering': ['-date'],
                'db_table': 'gsb_cours',
                'verbose_name_plural': 'cours',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Db_log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_time_action', gsb.model_field.CreationDateTimeField()),
                ('datamodel', models.CharField(max_length=20)),
                ('id_model', models.IntegerField()),
                ('uuid', models.CharField(max_length=255)),
                ('type_action', models.CharField(max_length=255)),
                ('memo', models.CharField(max_length=255)),
                ('date_ref', models.DateField(default=datetime.date.today)),
            ],
        ),
        migrations.CreateModel(
            name='Echeance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=gsb.utils.today, db_index=True)),
                ('date_limite', models.DateField(default=None, null=True, db_index=True, blank=True)),
                ('intervalle', models.IntegerField(default=1)),
                ('periodicite', models.CharField(default=b'u', max_length=1, choices=[(b'u', 'unique'), (b's', 'semaine'), (b'm', 'mois'), (b'a', 'ann\xe9e'), (b'j', 'jour')])),
                ('valide', models.BooleanField(default=True)),
                ('montant', gsb.model_field.CurField(default=0.0, max_digits=15, decimal_places=2)),
                ('notes', models.TextField(default=b'', blank=True)),
                ('inscription_automatique', models.BooleanField(default=False, help_text='inutile')),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
                ('cat', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='cat\xe9gorie', to='gsb.Cat')),
                ('compte', models.ForeignKey(to='gsb.Compte')),
                ('compte_virement', models.ForeignKey(related_name='echeance_virement_set', default=None, blank=True, to='gsb.Compte', null=True)),
            ],
            options={
                'ordering': ['date'],
                'db_table': 'gsb_echeance',
                'verbose_name': '\xe9ch\xe9ance',
                'verbose_name_plural': 'ech\xe9ances',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Exercice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_debut', models.DateField(default=gsb.utils.today)),
                ('date_fin', models.DateField(null=True, blank=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
            ],
            options={
                'ordering': ['-date_debut'],
                'db_table': 'gsb_exercice',
                'get_latest_by': 'date_debut',
            },
        ),
        migrations.CreateModel(
            name='Ib',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('type', models.CharField(default='d', max_length=1, choices=[(b'r', 'recette'), (b'd', 'd\xe9pense'), (b'v', 'virement')])),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
            ],
            options={
                'ordering': ['type', 'nom'],
                'db_table': 'gsb_ib',
                'verbose_name': 'imputation budg\xe9taire',
                'verbose_name_plural': 'imputations budg\xe9taires',
            },
        ),
        migrations.CreateModel(
            name='Moyen',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('type', models.CharField(default=b'd', max_length=1, choices=[(b'v', 'virement'), (b'd', 'depense'), (b'r', 'recette')])),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
            ],
            options={
                'ordering': ['nom'],
                'db_table': 'gsb_moyen',
                'verbose_name': 'moyen de paiment',
                'verbose_name_plural': 'moyens de paiment',
            },
        ),
        migrations.CreateModel(
            name='Ope',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=gsb.utils.today, db_index=True)),
                ('date_val', models.DateField(default=None, null=True, blank=True)),
                ('montant', gsb.model_field.CurField(default=0.0, max_digits=15, decimal_places=2)),
                ('notes', models.TextField(default=b'', blank=True)),
                ('num_cheque', models.CharField(default=b'', max_length=20, blank=True)),
                ('pointe', models.BooleanField(default=False)),
                ('automatique', models.BooleanField(default=False, help_text="si cette op\xe9ration est cr\xe9e \xe0 cause d'une \xe9cheance")),
                ('piece_comptable', models.CharField(default=b'', max_length=20, blank=True)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
                ('cat', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='gsb.Cat', null=True, verbose_name='Cat\xe9gorie')),
                ('compte', models.ForeignKey(to='gsb.Compte')),
                ('exercice', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Exercice', null=True)),
                ('ib', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Ib', null=True, verbose_name='projet')),
                ('jumelle', models.OneToOneField(related_name='jumelle_set', null=True, default=None, editable=False, to='gsb.Ope', blank=True)),
                ('mere', models.ForeignKey(related_name='filles_set', default=None, blank=True, to='gsb.Ope', null=True, verbose_name='Mere')),
                ('moyen', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Moyen', null=True)),
            ],
            options={
                'ordering': ['-date'],
                'db_table': 'gsb_ope',
                'verbose_name': 'op\xe9ration',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Ope_titre',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre', gsb.model_field.CurField(default=0, max_digits=15, decimal_places=6)),
                ('date', models.DateField(db_index=True)),
                ('cours', gsb.model_field.CurField(default=1, max_digits=15, decimal_places=6)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
                ('compte', models.ForeignKey(verbose_name='compte titre', to='gsb.Compte')),
            ],
            options={
                'ordering': ['-date'],
                'db_table': 'gsb_ope_titre',
                'verbose_name': 'Op\xe9ration titres(compta_matiere)',
                'verbose_name_plural': 'Op\xe9rations titres(compta_matiere)',
            },
        ),
        migrations.CreateModel(
            name='Rapp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('date', models.DateField(default=gsb.utils.today, null=True, blank=True)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
            ],
            options={
                'ordering': ['-date'],
                'db_table': 'gsb_rapp',
                'verbose_name': 'rapprochement',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Tiers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('notes', models.TextField(default=b'', blank=True)),
                ('is_titre', models.BooleanField(default=False)),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
                ('sort_nom', models.CharField(max_length=40, db_index=True)),
            ],
            options={
                'ordering': ['sort_nom'],
                'db_table': 'gsb_tiers',
                'verbose_name_plural': 'tiers',
            },
        ),
        migrations.CreateModel(
            name='Titre',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=40, db_index=True)),
                ('isin', models.CharField(unique=True, max_length=12, db_index=True)),
                ('type', models.CharField(default=b'ZZZ', max_length=3, choices=[(b'ACT', 'action'), (b'OPC', 'opcvm'), (b'CSL', 'compte sur livret'), (b'OBL', 'obligation'), (b'ZZZ', 'autre')])),
                ('lastupdate', gsb.model_field.ModificationDateTimeField()),
                ('date_created', gsb.model_field.CreationDateTimeField()),
                ('uuid', gsb.model_field.uuidfield(unique=True, max_length=36, editable=False, blank=True)),
            ],
            options={
                'ordering': ['nom'],
                'db_table': 'gsb_titre',
            },
        ),
        migrations.AddField(
            model_name='tiers',
            name='titre',
            field=models.OneToOneField(null=True, blank=True, editable=False, to='gsb.Titre'),
        ),
        migrations.AddField(
            model_name='ope_titre',
            name='titre',
            field=models.ForeignKey(to='gsb.Titre'),
        ),
        migrations.AddField(
            model_name='ope',
            name='ope_titre_ost',
            field=models.OneToOneField(related_name='ope_ost', null=True, editable=False, to='gsb.Ope_titre'),
        ),
        migrations.AddField(
            model_name='ope',
            name='ope_titre_pmv',
            field=models.OneToOneField(related_name='ope_pmv', null=True, editable=False, to='gsb.Ope_titre'),
        ),
        migrations.AddField(
            model_name='ope',
            name='rapp',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Rapp', null=True, verbose_name='Rapprochement'),
        ),
        migrations.AddField(
            model_name='ope',
            name='tiers',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Tiers', null=True),
        ),
        migrations.AddField(
            model_name='echeance',
            name='exercice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Exercice', null=True),
        ),
        migrations.AddField(
            model_name='echeance',
            name='ib',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='gsb.Ib', null=True, verbose_name='imputation'),
        ),
        migrations.AddField(
            model_name='echeance',
            name='moyen',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=None, to='gsb.Moyen'),
        ),
        migrations.AddField(
            model_name='echeance',
            name='moyen_virement',
            field=models.ForeignKey(related_name='echeance_moyen_virement_set', blank=True, to='gsb.Moyen', null=True),
        ),
        migrations.AddField(
            model_name='echeance',
            name='tiers',
            field=models.ForeignKey(to='gsb.Tiers', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='cours',
            name='titre',
            field=models.ForeignKey(to='gsb.Titre'),
        ),
        migrations.AddField(
            model_name='compte',
            name='moyen_credit_defaut',
            field=models.ForeignKey(related_name='compte_moyen_credit_set', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='gsb.Moyen', null=True),
        ),
        migrations.AddField(
            model_name='compte',
            name='moyen_debit_defaut',
            field=models.ForeignKey(related_name='compte_moyen_debit_set', on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='gsb.Moyen', null=True),
        ),
        migrations.AddField(
            model_name='compte',
            name='titre',
            field=models.ManyToManyField(to='gsb.Titre', through='gsb.Ope_titre'),
        ),
        migrations.AlterOrderWithRespectTo(
            name='ope',
            order_with_respect_to='compte',
        ),
        migrations.AlterUniqueTogether(
            name='cours',
            unique_together=set([('titre', 'date')]),
        ),
    ]
