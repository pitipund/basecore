import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from his.framework.validators import json_text_validator

"""
DO NOT IMPORT `User` MODEL HERE!!

If you want to do something with `User` do it in models.py.
"""
# TODO: Move other Mixins here


class ExtraFieldModelMixin(models.Model):

    """
    `extra` field is a raw JSON Field.
    You can access it with `extra_data` property which automatic parse `extra` to dictionary
    and use it like ordinary dictionary. The `extra_data` is also support for saving
    data back to `extra` field.

    Anyway, `extra_data` doesn't work with `QuerySet.update()` since it creates update statement
    directly without using `Model.save()`

    `extra` field isn't indexed and not gonna be indexed, so, do not search with this field.

    :Usage:

    >>> user = User.objects.get(id=1)
    >>> user.extra
    '{}'

    >>> user.extra_data
    {}

    >>> user.extra_data = {'pre_name': 'Mr.'}
    >>> user.save()
    >>> user.extra
    '{"pre_name": "Mr."}'

    >>> user.extra_data['gender'] = 'Male'
    >>> user.save()
    >>> user.extra
    '{"pre_name": "Mr.", "gender": "Male"}'

    """

    extra = models.TextField(_('extra json info'), default='{}',
                             validators=[json_text_validator],
                             help_text='must be in JSON format')

    @property
    def extra_data(self):
        extra_data = getattr(self, '__extra_data', None)
        if extra_data is None:
            if self.extra:
                data = json.loads(self.extra)
            else:
                data = {}
            setattr(self, '__extra_data', data)
            extra_data = data
        return extra_data

    @extra_data.setter
    def extra_data(self, data):
        setattr(self, '__extra_data', data)

    def save(self, *args, **kwargs):
        extra_data = getattr(self, '__extra_data', None)
        if extra_data:
            self.extra = json.dumps(extra_data)
        super(ExtraFieldModelMixin, self).save(*args, **kwargs)

    class Meta:
        abstract = True
