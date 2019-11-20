from django.apps import AppConfig


class FeedConfig(AppConfig):
    name = 'feed'
    verbose_name = "feed"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass

