from django.conf import settings


def picura_context(request):
    return {'picura_version': settings.PICURA_VERSION}
