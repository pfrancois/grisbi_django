# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from chartjs.views.pie import HighChartPieView
from gsb import models
from django.db.models import Sum


class PieHighChartJSONView(HighChartPieView):
    def get_data(self):
        dat = list(models.Cat.objects.filter(ope__date__year=2015).annotate(montant=Sum("ope__montant")).value_list('montant', flat=True),)
        print(dat)
        return dat

pie_highchart = TemplateView.as_view(template_name='gsb/chart.djhtm')
pie_highchart_json = PieHighChartJSONView.as_view()
