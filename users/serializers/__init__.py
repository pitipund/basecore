from django.conf import settings
from .serializers import *  # noqa

if 'AGN' in settings.DJANGO_INCLUDE_APPS:
    from .AGN import *  # noqa
