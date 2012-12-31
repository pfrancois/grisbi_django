# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.db import connection, transaction

import time
import decimal
import logging
import os
from django.conf import settings  # @Reimport
from django.contrib.auth.decorators import login_required
import django.utils.encoding as dj_encoding
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from .models import (Tiers, Titre, Cat, Ope, Banque, Ib,
                     Exercice, Rapp, Moyen, Echeance, Compte, Ope_titre)
from .import_base import Import_exception, ImportForm1
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et

from . import utils


@login_required
def import_gsb_0_5_x(request):
    logger = logging.getLogger('gsb.import')
    nomfich = ""
    if request.method == 'POST':
        form = ImportForm1(request.POST, request.FILES)
        form.extension = "gsb"
        form.type_f = "fichier gsb 0.5.x"
        if form.is_valid():
            nomfich = form.cleaned_data['nom_du_fichier']
            nomfich = nomfich[:-4]
            nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "%s-%s.%s" % (
                 nomfich, time.strftime("%Y-%b-%d_%H-%M-%S"), "gsb"))
            destination = open(nomfich, 'wb+')
            for chunk in request.FILES['nom_du_fichier'].chunks():
                destination.write(chunk)
            destination.close()
            # renomage ok
            logger.debug("enregistrement fichier ok")
            # on recupere les info pour le nom
            try:
                info = u"%s le %s" % (request.META['REMOTE_ADDR'], time.strftime(u"%d/%m/%Y a %Hh%Mm%Ss"))
            except KeyError:
                info = u"%s le %s" % ('0.0.0.0', time.strftime(u"%d/%m/%Y a %Hh%Mm%Ss"))
                #-----------------------gestion des imports
            try:
                # on essaye d'ouvrir le fichier
                destination = open(nomfich, 'r')
                # si on peut
                destination.close()
                if form.cleaned_data['replace'] == 'remplacement':
                    logger.warning(
                        u"remplacement data par fichier %s format %s %s" % (
                        nomfich, request.session['import_type'], info))
                    import_gsb_050(nomfich=nomfich, efface_table=True)
                else:
                    logger.warning(
                        u"fusion data par fichier %s format %s %s" % (
                        nomfich, request.session['import_type'], info))
                    import_gsb_050(nomfich=nomfich, efface_table=False)
            except Exception as exp:
                logger.warning(u"probleme d'importation à cause de %s(%s) " % (type(exp), exp))
                messages.error(request, u"erreur dans l'import du fichier %s" % nomfich)
            else:
                messages.success(request, u"import du fichier %s ok" % nomfich)
                return HttpResponseRedirect(reverse('index'))
    else:
        form = ImportForm1()
        form.extension = "gsb"
        form.type_f = "fichier gsb 0.5.x"
        param = {'form': form}
        return render(request, "gsb/import.djhtm", param)


def import_gsb_050(nomfich, efface_table=True):
    logger = logging.getLogger('gsb.import')
    liste_type_period = Echeance.typesperiod
    liste_type_titre = [e[0] for e in Titre.typestitres]
    tabl_correspondance_moyen = {}
    tabl_correspondance_compte = {}
    tabl_correspondance_tiers = {}
    tabl_correspondance_banque = {}
    tabl_correspondance_cat = {}
    tabl_correspondance_ib = {}
    tabl_correspondance_exo = {}
    tabl_correspondance_rapp = {}
    tabl_correspondance_ech = {}
    tabl_correspondance_ope = {}
    if efface_table:
        for table in (
            'ope', 'echeance', 'rapp', 'moyen', 'compte', 'cat', 'exercice', 'ib', 'banque',
            'titre', 'tiers', 'Ope_titre'):
            connection.cursor().execute("delete from gsb_%s;" % table)  # @UndefinedVariable
            transaction.commit_unless_managed()
    logger.info(u"debut du chargement")
    time.clock()
    xml_tree = et.parse(nomfich)
    xml_tree.getroot()
    # verification du format
    xml_generalite = str(xml_tree.find('Generalites/Version_fichier').text)
    if xml_generalite != '0.5.0':
        # logger.critical("le format n'est pas reconnu")
        raise Import_exception(u"le format n'est pas reconnu")
    percent = 1
    #------------------------------generalites#------------------------------
    # les generalités sont maintenant dans setting.py
    #------------------------------devises---------------------------
    nb = 0
    nb_nx = 0
    nb_titre = 0
    if len(xml_tree.find('//Detail_des_devises')) > 1:
        raise Import_exception(u"attention ce ne sera pas possible d'importer car il y a plusieurs devises")
        #------------ TIERS et titres -------------------
    nb_tiers_final = len(xml_tree.find('//Detail_des_tiers'))
    for xml_tiers in xml_tree.find('//Detail_des_tiers'):
        affiche = False
        created = False
        if nb == int(nb_tiers_final * int("%s0" % percent) / 100):  # logging
            affiche = True
            logger.info("tiers %s soit %% %s" % (xml_tiers.get('No'), "%s0" % percent))
            percent += 1
        nb += 1
        query = {'nom': xml_tiers.get('Nom'), 'notes': xml_tiers.get('Informations')}
        if xml_tiers.get('Nom')[:6] != 'titre_':  # creation du tiers titre
            element, created = Tiers.objects.get_or_create(nom=xml_tiers.get('Nom'), defaults=query)
        else:
            # test puis creation du titre (et donc du tiers automatiquement)
            try:
                Tiers.objects.get(nom=xml_tiers.get('Nom'))
            except Tiers.DoesNotExist:
                nb_titre += 1
                s = dj_encoding.smart_unicode(xml_tiers.get('Informations'))
                nom = dj_encoding.smart_unicode(xml_tiers.get('Nom'))
                s = s.partition('@')
                # on utilise partition et non split car c'est pas sur et pas envie de mettre une usine a gaz
                # comme le tiers est sous la forme titre_ nomtiers
                titre = Titre(nom=nom[7:])
                # dans les notes ISIN@TYPE
                if not s[1]:  # pas de @ et donc pas de type
                    if s[0] == '':
                        titre.isin = "ZZ%sN%s" % (utils.today().strftime('%d%m%Y'), nb_titre)
                    else:
                        titre.isin = s[0]
                    titre.type = "ZZZ"
                else:
                    if s[0] == '':  # pas d'isin
                        titre.isin = "XX%sN%s" % (utils.today().strftime('%d%m%Y'), nb_titre)
                    else:
                        titre.isin = s[0]
                    if s[2] in liste_type_titre:  # verification que le type existe
                        titre.type = s[2]
                    else:
                        titre.type = 'ZZZ'
                element, created = Tiers.objects.get_or_create(nom=xml_tiers.get('Nom'), defaults=query)
                titre.tiers = element
                titre.save()
                element.notes = "%s@%s" % (titre.isin, titre.type)
                element.is_titre = True
                element.save()
                logger.debug(u'titre cree %s isin (%s) as %s' % (titre.nom, titre.isin, titre.type))
        tabl_correspondance_tiers[xml_tiers.get('No')] = element.id
        if created:
            nb_nx += 1
            if affiche:
                logger.debug('tiers %s cree au numero %s' % (int(xml_tiers.get('No')), element.id))

    logger.warning(u'%s tiers et %s titres dont %s nx' % (nb, nb_titre, nb_nx))
    #-------------------------categories et des sous categories-----------------------
    nb_cat = 0
    nb_nx = 0
    for xml_cat in xml_tree.find('//Detail_des_categories'):
        nb_cat += 1
        query = {'nom': "%s" % (xml_cat.get('Nom'),), 'type': Cat.typesdep[int(xml_cat.get('Type'))][0]}
        element, created = Cat.objects.get_or_create(nom=query['nom'], defaults=query)
        tabl_correspondance_cat[xml_cat.get('No')] = {'0': element.id}
        if created:
            nb_nx += 1
            logger.debug('cat %s cree au numero %s' % (int(xml_cat.get('No')), element.id))
        for xml_scat in xml_cat:
            nb_cat += 1
            query = {'nom': "%s:%s" % (xml_cat.get('Nom'), xml_scat.get('Nom')),
                     'type': Cat.typesdep[int(xml_cat.get('Type'))][0]}
            element, created = Cat.objects.get_or_create(nom=query['nom'], defaults=query)
            tabl_correspondance_cat[xml_cat.get('No')][xml_scat.get('No')] = element.id
            if created:
                nb_nx += 1
                logger.debug(
                    'scat %s:%s cree au numero %s' % (int(xml_cat.get('No')), int(xml_scat.get('No')), element.id))
    logger.warning(u"%s catégories dont %s nouveaux" % (nb_cat, nb_nx))

    #------------------------------imputations----------------------------------
    nb_ib = 0
    nb_nx = 0
    for xml_ib in xml_tree.find('//Detail_des_imputations'):
        nb_ib += 1
        query = {'nom': "%s" % (xml_ib.get('Nom'),), 'type': Cat.typesdep[int(xml_ib.get('Type'))][0]}
        element, created = Ib.objects.get_or_create(nom=query['nom'], defaults=query)
        tabl_correspondance_ib[xml_ib.get('No')] = {'0': element.id}
        if created:
            nb_nx += 1
            logger.debug('ib %s cree au numero %s' % (int(xml_ib.get('No')), element.id))
        for xml_sib in xml_ib:
            logger.debug("ib %s:sib %s" % (xml_ib.get('No'), xml_sib.get('No')))
            nb_ib += 1
            query = {'nom': "%s:%s" % (xml_ib.get('Nom'), xml_sib.get('Nom')),
                     'type': Cat.typesdep[int(xml_ib.get('Type'))][0]}
            element, created = Ib.objects.get_or_create(nom=query['nom'], defaults=query)
            tabl_correspondance_ib[xml_ib.get('No')][xml_sib.get('No')] = element.id
            if created:
                logger.debug(
                    'sib %s:%s cree au numero %s' % (int(xml_ib.get('No')), int(xml_sib.get('No')), element.id))
    logger.warning(u"%s imputations dont %s nouveaux" % (nb_ib, nb_nx))

    #------------------------------banques------------------------------
    nb_bq = 0
    for xml_bq in xml_tree.find('Banques/Detail_des_banques'):
        nb_bq += 1
        logger.debug("banque %s" % xml_bq.get('No'))
        element, created = Banque.objects.get_or_create(nom=xml_bq.get('Nom'), defaults={'cib': xml_bq.get('Code'),
                                                                                         'notes': xml_bq.get(
                                                                                             'Remarques')})
        tabl_correspondance_banque[xml_bq.get('No')] = element.id
    logger.warning(u'%s banques' % nb_bq)

    #------------------------------exercices#------------------------------
    nb = 0
    nb_nx = 0
    for xml_exercice in xml_tree.find('Exercices/Detail_des_exercices'):
        nb += 1
        logger.debug("exo %s" % xml_exercice.get('No'))
        element, created = Exercice.objects.get_or_create(nom=xml_exercice.get('Nom'),
                                                          defaults={'nom': xml_exercice.get('Nom'),
                                                                    'date_debut': utils.datefr2datesql(
                                                                        xml_exercice.get('Date_debut')),
                                                                    'date_fin': utils.datefr2datesql(
                                                                        xml_exercice.get('Date_fin'))})
        tabl_correspondance_exo[xml_exercice.get('No')] = element.id
        if created:
            nb_nx += 1
    logger.warning(u'%s exercices dont %s nouveaux' % (nb, nb_nx))

    #------------------------------rapp#------------------------------
    nb = 0
    nb_nx = 0
    for xml_rapp in xml_tree.find('Rapprochements/Detail_des_rapprochements'):
        nb += 1
        logger.debug("rapp %s" % xml_rapp.get('No'))
        element, created = Rapp.objects.get_or_create(nom=dj_encoding.smart_unicode(xml_rapp.get('Nom')),
                                                      defaults={'nom': xml_rapp.get('Nom')})
        if created:
            nb_nx += 1
        tabl_correspondance_rapp[xml_rapp.get('No')] = element.id
    logger.warning(u'%s rapprochements dont %s nouveaux ' % (nb, nb_nx))

    #------------------------------comptes#------------------------------
    nb = 0
    nb_tot_moyen = 0
    nb_nx = 0
    for xml_cpt in xml_tree.findall('//Compte'):
        nb += 1
        nb_moyen = 0
        type_compte = Compte.typescpt[int(xml_cpt.find('Details/Type_de_compte').text)][0]
        if type_compte in ('t',):
            logger.debug("cpt_titre %s" % xml_cpt.find('Details/Nom').text)
            element, created = Compte.objects.get_or_create(nom=xml_cpt.find('Details/Nom').text, defaults={
                'nom': xml_cpt.find('Details/Nom').text,
                'ouvert': not bool(int(xml_cpt.find('Details/Compte_cloture').text)),
            })
        else:
            logger.debug("cpt %s" % xml_cpt.find('Details/Nom').text)
            element, created = Compte.objects.get_or_create(nom=xml_cpt.find('Details/Nom').text, defaults={
                'nom': xml_cpt.find('Details/Nom').text,
                'ouvert': not bool(int(xml_cpt.find('Details/Compte_cloture').text)),
            })

        tabl_correspondance_compte[xml_cpt.find('Details/No_de_compte').text] = element.id
        if created:
            nb_nx += 1
            if xml_cpt.find('Details/Titulaire').text is None:
                element.titulaire = ''
            else:
                element.titulaire = xml_cpt.find('Details/Titulaire').text
            element.type = Compte.typescpt[int(xml_cpt.find('Details/Type_de_compte').text)][0]
            if xml_cpt.find('Details/Banque') is None or int(xml_cpt.find('Details/Banque').text) == 0:
                element.banque = None
            else:
                element.banque_id = tabl_correspondance_banque[xml_cpt.find('Details/Banque').text]
            if xml_cpt.find('Details/Guichet').text is None:
                element.guichet = ''
            else:
                element.guichet = xml_cpt.find('Details/Guichet').text
            if xml_cpt.find('Details/No_compte_banque').text is not None:
                element.num_compte = xml_cpt.find('Details/No_compte_banque').text
            else:
                element.num_compte = ''
            if xml_cpt.find('Details/Cle_du_compte').text is not None:
                element.cle_compte = int(xml_cpt.find('Details/Cle_du_compte').text)
            else:
                element.cle_compte = None
            element.solde_init = utils.fr2decimal(xml_cpt.find('Details/Solde_initial').text)
            element.solde_mini_voulu = utils.fr2decimal(xml_cpt.find('Details/Solde_mini_voulu').text)
            element.solde_mini_autorise = utils.fr2decimal(xml_cpt.find('Details/Solde_mini_autorise').text)
            element.solde_mini_autorise = utils.fr2decimal(xml_cpt.find('Details/Solde_mini_autorise').text)
            if xml_cpt.find('Details/Commentaires').text is not None:
                element.notes = xml_cpt.find('Details/Commentaires').text
            else:
                element.notes = ''
            element.save()
            #---------------MOYENS---------------------
        nb_nx_moyens = 0
        tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text] = {}
        for xml_moyen in xml_cpt.find('Detail_de_Types'):
            nb_tot_moyen += 1
            nb_moyen += 1
            logger.debug("moyen %s" % xml_moyen.get('No'))
            moyen, created = Moyen.objects.get_or_create(nom=xml_moyen.get('Nom'),
                                                         defaults={'nom': xml_moyen.get('Nom'),
                                                                   'type':
                                                                       Moyen.typesdep[int(xml_moyen.get('Signe'))][
                                                                       0], }
            )
            if created:
                nb_nx_moyens += 1
            tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text][xml_moyen.get('No')] = moyen.id
        try:
            element.moyen_credit_defaut_id = tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text][
                                             xml_cpt.find('Details/Type_defaut_credit').text]
        except (KeyError, TypeError):
            element.moyen_credit_defaut_id = None
        try:
            element.moyen_debit_defaut_id = tabl_correspondance_moyen[xml_cpt.find('Details/No_de_compte').text][
                                            xml_cpt.find('Details/Type_defaut_debit').text]
        except (KeyError, TypeError):
            element.moyen_debit_defaut_id = None
        element.save()
    logger.warning(u'%s comptes dont %s nouveaux' % (nb, nb_nx))
    nb_tot_ope = 0

    #------------------------------OPERATIONS-----------------------
    list_ope = xml_tree.findall('//Operation')
    nb_ope_final = len(list_ope)
    percent = 1
    nb_inconnu = 0
    for xml_ope in list_ope:
        logger.debug(u'opération %s' % xml_ope.get('No'))
        try:
            ope_tiers = Tiers.objects.get(id=tabl_correspondance_tiers[xml_ope.get('T')])
        except KeyError:
            if int(xml_ope.get('Ro')):
                ope_tiers, tiers_created = Tiers.objects.get_or_create(nom='virement', defaults={'nom': 'virement'})
                if tiers_created:
                    tabl_correspondance_tiers[xml_ope.get('T')] = ope_tiers.id
            else:
                nb_inconnu += 1
                inconnu = Tiers.objects.create(nom='inconnu%s' % nb_inconnu)
                ope_tiers = inconnu
                tabl_correspondance_tiers[xml_ope.get('T')] = inconnu.id
        ope_montant = utils.fr2decimal(xml_ope.get('M'))
        ope_date = utils.datefr2datesql(xml_ope.get('D'))
        ope_date_val = utils.datefr2datesql(xml_ope.get('Db'))
        ope_cpt = Compte.objects.get(id=tabl_correspondance_compte[xml_ope.find('../../Details/No_de_compte').text])
        if ope_tiers and ope_tiers.is_titre and ope_cpt.type == 't':
            # compta matiere et cours en meme tps
            ope_cpt_titre = Compte.objects.get(id=ope_cpt.id)
            ope_notes = dj_encoding.smart_unicode(xml_ope.get('N'))
            s = ope_notes.partition('@')
            if s[1]:  # TODO gestion des csl
                ope_nb = decimal.Decimal(str(s[0]))
                ope_cours = decimal.Decimal(str(s[2]))
                Ope_titre.objects.create(titre=ope_tiers.titre, compte=ope_cpt_titre, nombre=ope_nb, date=ope_date,
                                         cours=ope_cours)
                ope_tiers.titre.cours_set.get_or_create(date=ope_date, defaults={'date': ope_date, 'valeur': ope_cours})
                # on cree de toute facon l'operation
        nb_tot_ope += 1
        if nb_tot_ope == int(nb_ope_final * int("%s0" % percent) / 100):
            logger.info(
                "ope %s, ope %s sur %s soit %s%%" % (xml_ope.get('No'), nb_tot_ope, nb_ope_final, "%s0" % percent))
            percent += 1
        ope = Ope(compte=ope_cpt,
                  date=ope_date,
                  date_val=ope_date_val,  # date de valeur
                  montant=ope_montant,  # montant
        )  # on cree toujours car la proba que ce soit un doublon est bien bien plus faible que celle que ce soit une autre
        ope.save()
        tabl_correspondance_ope[xml_ope.get('No')] = ope.id
        logger.debug('ope %s cree id %s' % (xml_ope.get('No'), ope.id))
        # numero du moyen de paiment
        ope.num_cheque = xml_ope.get('Ct')
        # statut de pointage
        if int(xml_ope.get('P')) == 1:
            ope.pointe = True
        if int(xml_ope.get('A')) == 1:
            ope.automatique = True
            # gestion des tiers
        if ope_tiers:
            ope.tiers_id = ope_tiers
        try:
            if xml_ope.get('C') and int(xml_ope.get('C')):
                ope.cat_id = tabl_correspondance_cat[xml_ope.get('C')][xml_ope.get('Sc')]
            else:
                ope.cat = None
        except KeyError:
            ope.cat = None
        try:
            if xml_ope.get('I') and int(xml_ope.get('I')):
                ope.ib_id = tabl_correspondance_ib[xml_ope.get('I')][xml_ope.get('Si')]
            else:
                ope.ib = None
        except KeyError:
            ope.ib = None
        try:  # moyen de paiment
            ope.moyen_id = tabl_correspondance_moyen[str(ope.compte_id)][xml_ope.get('Ty')]
        except KeyError:
            ope.moyen = None
        try:  # gestion des rapprochements
            ope.rapp_id = tabl_correspondance_rapp[xml_ope.get('R')]
            # gestion de la date du rapprochement
            if ope.rapp.date > utils.strpdate(ope.date):
                ope.rapp.date = utils.strpdate(ope.date)
                ope.rapp.save()
        except KeyError:
            ope.rapp = None
        ope.notes = xml_ope.get('N')
        ope.piece_comptable = xml_ope.get('Pc')
        # exercices
        try:
            ope.exercice_id = tabl_correspondance_exo[xml_ope.get('E')]
        except KeyError:
            ope.exercice = None
        ope.save()
    nb_tot_ope = 0
    percent = 1
    for xml_ope in list_ope:
        nb_tot_ope += 1
        if nb_tot_ope == int(nb_ope_final * int("%s0" % percent) / 100):
            logger.info(
                "2*ope %s, ope %s sur %s soit %s%%" % (xml_ope.get('No'), nb_tot_ope, nb_ope_final, "%s0" % percent))
            percent += 1
            # gestion des virements
        if int(xml_ope.get('Ro')):
            logger.debug('virement vers %s' % xml_ope.get('Ro'))
            ope = Ope.objects.get(id=tabl_correspondance_ope[xml_ope.get('No')])
            ope.jumelle_id = tabl_correspondance_ope[xml_ope.get('Ro')]
            ope.save()
            # gestion des ventilations
        # bool(int(xml_ope.get('Ov'))) pas besoin car on regarde avec des requetes sql
        if int(xml_ope.get('Va')):
            logger.debug('ventilation de %s' % tabl_correspondance_ope[xml_ope.get('Va')])
            ope = Ope.objects.get(id=tabl_correspondance_ope[xml_ope.get('No')])
            ope.mere_id = tabl_correspondance_ope[xml_ope.get('Va')]
            ope.save()

    logger.warning(u"%s operations" % nb_tot_ope)

    #------------------------------echeances#------------------------------
    nb = 0
    for xml_ech in xml_tree.find('Echeances/Detail_des_echeances'):
        nb += 1
        logger.debug("echeance %s" % xml_ech.get('No'))
        element = Echeance(
            date=utils.datefr2datesql(xml_ech.get('Date')),
            montant=utils.fr2decimal(xml_ech.get('Montant')),
            compte_id=tabl_correspondance_compte[xml_ech.get('Compte')],
        )
        tabl_correspondance_ech[xml_ech.get('No')] = element.id
        try:
            element.tiers_id = tabl_correspondance_tiers[xml_ech.get('Tiers')]
        except KeyError:
            element.tiers = None
        element.inscription_automatique = bool(int(xml_ech.get('Automatique')))  # not in bdd
        try:
            element.moyen_id = tabl_correspondance_moyen[xml_ech.get('Compte')][xml_ech.get('Type')]
        except KeyError:
            element.moyen = None
        try:
            element.exercice_id = tabl_correspondance_exo[xml_ech.get('Exercice')]
        except KeyError:
            element.moyen = None
        element.notes = xml_ech.get('Notes')
        try:
            element.cat_id = tabl_correspondance_cat[xml_ech.get('Categorie')][xml_ech.get('Sous-categorie')]
        except KeyError:
            element.cat = None
        try:
            element.ib_id = tabl_correspondance_ib[xml_ech.get('Imputation')][xml_ech.get('Sous-imputation')]
        except KeyError:
            element.ib = None
        if xml_ech.get('Virement_compte') != xml_ech.get('Compte'):
            element.compte_virement_id = tabl_correspondance_compte[xml_ech.get('Virement_compte')]
            try:
                element.moyen_virement_id = tabl_correspondance_compte[xml_ech.get('Type_contre_ope')]
            except KeyError:
                element.moyen_virement = None
        else:
            element.compte_virement = None
            element.moyen_virement = None
        if  int(xml_ech.get('Periodicite')) == 4:  # c'est le mode personalise
            if int(xml_ech.get('Periodicite_personnalisee')) == 7 and int(
                xml_ech.get('Intervalle_periodicite')) == 0:  # on cree les semaine
                element.periodicite = 'h'
                element.intervalle = 1
            else:
                liste_type_periode_perso = ('j', 'm', 'a')
                element.periodicite = liste_type_periode_perso[int(xml_ech.get('Intervalle_periodicite'))]
                element.intervalle = int(xml_ech.get('Periodicite_personnalisee'))
        else:
            element.periodicite = liste_type_period[int(xml_ech.get('Periodicite'))][0]
            element.intervalle = 1

        element.date_limite = utils.datefr2datesql(xml_ech.get('Date_limite'))
        element.save()
    logger.warning(u'fini')
