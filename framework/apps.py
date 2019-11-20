from collections import OrderedDict

from django.apps import AppConfig


class FrameworkConfig(AppConfig):
    name = 'his.framework'
    config = OrderedDict([
        ('ENABLE_COLLECT_REQUEST', (False, 'Enable collect request. \n'
                                           '(need to enable /admin/speedinfo/viewprofiler/)', bool)),
    ])
