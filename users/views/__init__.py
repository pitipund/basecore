from .api import *  # noqa
from .views import *  # noqa
from .web import *  # noqa
from django.conf import settings

if 'PRX' in settings.DJANGO_INCLUDE_APPS:
    from .user_profile import *  # noqa

if 'AGN' in settings.DJANGO_INCLUDE_APPS:
    from .AGN import *  # noqa
