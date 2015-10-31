# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import colorful.fields
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('gsb', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tiers',
            options={'verbose_name_plural': 'tiers', 'ordering': ['nom']},
        ),
        migrations.AlterField(
            model_name='banque',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='cat',
            name='couleur',
            field=colorful.fields.RGBColorField(default='#FFFFFF'),
        ),
        migrations.AlterField(
            model_name='cat',
            name='type',
            field=models.CharField(verbose_name='type de la catégorie', max_length=1, choices=[('r', 'recette'), ('d', 'dépense'), ('v', 'virement')], default='d'),
        ),
        migrations.AlterField(
            model_name='compte',
            name='couleur',
            field=colorful.fields.RGBColorField(default='#FFFFFF'),
        ),
        migrations.AlterField(
            model_name='compte',
            name='guichet',
            field=models.CharField(max_length=15, default='', blank=True),
        ),
        migrations.AlterField(
            model_name='compte',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='compte',
            name='num_compte',
            field=models.CharField(db_index=True, max_length=20, default='', blank=True),
        ),
        migrations.AlterField(
            model_name='compte',
            name='titulaire',
            field=models.CharField(max_length=40, default='', blank=True),
        ),
        migrations.AlterField(
            model_name='compte',
            name='type',
            field=models.CharField(max_length=1, choices=[('b', 'bancaire'), ('e', 'espece'), ('p', 'passif'), ('t', 'titre'), ('a', 'autre actifs')], default='b'),
        ),
        migrations.AlterField(
            model_name='config',
            name='derniere_import_money_journal',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='db_log',
            name='date_time_action',
            field=models.DateTimeField(null=True, auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='echeance',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='echeance',
            name='periodicite',
            field=models.CharField(max_length=1, choices=[('u', 'unique'), ('s', 'semaine'), ('m', 'mois'), ('a', 'année'), ('j', 'jour')], default='u'),
        ),
        migrations.AlterField(
            model_name='ib',
            name='type',
            field=models.CharField(max_length=1, choices=[('r', 'recette'), ('d', 'dépense'), ('v', 'virement')], default='d'),
        ),
        migrations.AlterField(
            model_name='moyen',
            name='type',
            field=models.CharField(max_length=1, choices=[('v', 'virement'), ('d', 'depense'), ('r', 'recette')], default='d'),
        ),
        migrations.AlterField(
            model_name='ope',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='ope',
            name='num_cheque',
            field=models.CharField(max_length=20, default='', blank=True),
        ),
        migrations.AlterField(
            model_name='ope',
            name='piece_comptable',
            field=models.CharField(max_length=20, default='', blank=True),
        ),
        migrations.AlterField(
            model_name='tiers',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='titre',
            name='type',
            field=models.CharField(max_length=3, choices=[('ACT', 'action'), ('OPC', 'opcvm'), ('CSL', 'compte sur livret'), ('OBL', 'obligation'), ('ZZZ', 'autre')], default='ZZZ'),
        ),
    ]
