from django.db import models
from django.db.models.query import QuerySet
from his.penta.showtime.utils import VIDEO_TYPE_CHOICES


class SoopVideoQuerySet(QuerySet):
    def available_videos(self):
        return self.filter(isAvailable=True)

    def with_keyword(self, keyword):
        return self.available_videos().filter(name__icontains=keyword)


class SoopVideo(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    url = models.URLField()
    video_type = models.CharField(max_length=1, choices=VIDEO_TYPE_CHOICES)
    video_id = models.CharField(max_length=500, blank=True, null=True)
    thumbnail_url = models.CharField(max_length=200)
    isAvailable = models.BooleanField(default=True)
    payload = models.TextField(blank=True, null=True)
    objects = SoopVideoQuerySet.as_manager()

    class Meta:
        app_label = 'apis'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def queueItem(self):
        return {
            'name': self.name,
            'queue_id': 's_%s' % self.video_id,
            'thumbnail': self.thumbnail_url,
            'type': "local",
            'video_id': self.video_id
        }
