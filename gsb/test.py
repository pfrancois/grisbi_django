# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.shortcuts import render

#logger = logging.getLogger('gsb.test')
from django.contrib import messages

def test(request):
    messages.info(request, 'This is an info message.')
    messages.info(request, 'This is another info message.')
    messages.success(request, 'This is a success message.')
    messages.warning(request, 'This is a warning message.')
    messages.error(request, 'This is an error message.')
    messages.error(request, 'This is another error message.')
    return render(request, 'generic.djhtm', )
