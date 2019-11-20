from django.utils import timezone
from django.conf import settings

from django.db import models

class ExtensionSupport(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=400, default="", blank=True, null=True)
    url = models.URLField()
    icon = models.ImageField(upload_to=settings.EXTENSION_SUPPORT_IM_PATH, verbose_name="Icon")
    enabled = models.BooleanField(default=True)
    sortkey = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Extension support"

    def admin_icon(self):
        return '<img src="%s" height="24" border="0" />' % self.icon.url
