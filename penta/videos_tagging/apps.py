from django.apps import AppConfig


class VideoTaggingConfig(AppConfig):
    name = 'videos_tagging'
    verbose_name = "videos_tagging"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass

