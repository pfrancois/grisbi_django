# coding=utf-8
from django_ajax.decorators import ajax
from gsb import models as models_gsb
#from gsb import utils
#import datetime
#import decimal
from django.db import models
#import django.utils.timezone as tz
from django.utils.encoding import smart_text
#


@ajax
def ajax_view(request):
    data = models_gsb.Cat.objects.filter(ope__date__year=2015).annotate(montant=models.Sum("ope__montant")).values_list('nom', 'montant')
    depenses = [[el[0], smart_text(el[1])] for el in data if el[1] < 0]
    recettes = [[el[0], smart_text(el[1])] for el in data if el[1] > 0]
    return [depenses, recettes]
