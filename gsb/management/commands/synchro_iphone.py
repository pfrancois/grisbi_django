# -*- coding: utf-8 -*-
from django.db import transaction
from django.core.management.base import BaseCommand
from gsb import lecture_plist
from ... import models


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        with transaction.atomic():
            config = models.config.objects.get_or_create(id=1, defaults={'id': 1})[0]
            lastmaj = config.derniere_import_money_journal
            nb_export = lecture_plist.export(lastmaj)
            retour = lecture_plist.import_items(lastmaj)
            #on gere ceux qu'on elimine car deja pris en en compte
            config.derniere_import_money_journal = utils.now()
            config.save()
        self.stdout.write("{nb_ajout} opérations ajoutés,{nb_modif} opérations modifiés, {nb_suppr} opérations modifiés".format(**retour))
        self.stdout.write("%s opérations crées ou modifiés vers iphones" % nb_export)
