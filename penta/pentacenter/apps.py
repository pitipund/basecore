from django.apps import AppConfig


class PentaCenterConfig(AppConfig):
    name = 'his.penta.pentacenter'
    verbose_name = "pentacenter"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass

