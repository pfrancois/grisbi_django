# -*- coding: utf-8
from mysite.gsb.models import Compte_titre,Cours,Ope_titre,Ope,Cat
from mysite.gsb.forms import  error_css_class, required_css_class
from django.http import  HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from decimal import Decimal
from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.utils.encoding import force_unicode
from django.conf import settings

#-----------les urls.py
urlpatterns = patterns('mysite.gsb.forms_perso',(r'^$', 'chgt_ope_titre'),)

#---------------les fields, widgets  et forms tres perso



#----------les views tres perso
def chgt_ope_titre(request):
    nb_ope=0
    for ope in Ope_titre.objects.all():
        if not ope.ope:
            print ope.id
            if ope.cours * ope.nombre * -1 >0:#vente
                moyen=ope.compte.moyen_credit_defaut
            else:#achat
                moyen=ope.compte.moyen_credit_defaut
            nb_ope+=1
            ope.ope=Ope.objects.create(date = ope.date,
                                            montant = ope.cours * ope.nombre * -1,
                                            tiers = ope.titre.tiers,
                                            cat = Cat.objects.get_or_create(nom = u"operation sur titre:",
                                                                        defaults = {'nom':u'operation sur titre:'})[0],
                                            notes = "%s@%s" % (ope.nombre, ope.cours),
                                            moyen = moyen,
                                            automatique = True,
                                            compte = ope.compte,
                                            )
            cours=Cours.objects.get_or_create(titre=ope.titre,date=ope.date,defaults={'titre':ope.titre,
                                                                                      'date':ope.date,
                                                                                      'valeur':ope.cours})
            ope.ope.date = ope.date
            ope.ope.montant = ope.cours * ope.nombre * -1
            ope.ope.note = "%s@%s" % (ope.nombre, cours)
            ope.ope.save()
            ope.save()
            print nb_ope
    return render(request,'generic.djhtm',{'titre':'chgt'})
