from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def welcome(request):
    context = {}
    return render(request, 'core/welcome.html', context)
