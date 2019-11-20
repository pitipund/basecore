from django.db import models
from his.penta.curator.models import User, CuratorTag


class UserTagHeatmap(models.Model):
    user = models.ForeignKey(User)
    tag = models.ForeignKey(CuratorTag)
    heat = models.IntegerField(default=2)

    class Meta:
        unique_together = ('user', 'tag')

    def __str__(self):
        return '{} {}: {}'.format(self.user, self.tag, self.heat)

    def __unicode__(self):
        return '{} {}: {}'.format(self.user, self.tag, self.heat)
