from django.apps import AppConfig


class TagHeatmapConfig(AppConfig):
    name = 'tag_heatmap'
    verbose_name = "tag_heatmap"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass

