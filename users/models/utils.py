import base64
import os
import urllib.parse
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.signing import Signer
from django.urls import RegexURLPattern
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

__all__ = [
    'enum_choices', 'get_resolved_urls', 'SelfReferenceCheckMixIn',
    'base64_decode', 'base64_encode', 'user_signer'
]


def enum_choices(ienum):
    return [(e.value, e.name) for e in ienum]


def get_resolved_urls(url_patterns, namespace=''):
    """Get URL name & namespace from nested urls.py"""
    url_patterns_resolved = []
    for entry in url_patterns:
        if hasattr(entry, 'url_patterns'):
            url_patterns_resolved += get_resolved_urls(
                entry.url_patterns, entry.namespace or namespace)
        else:
            cloned_entry = RegexURLPattern(entry.regex, entry.callback,
                                           default_args=entry.default_args, name=entry.name)
            cloned_entry.namespace = namespace
            url_patterns_resolved.append(cloned_entry)
    return url_patterns_resolved


class SelfReferenceCheckMixIn(object):
    MAX_DEPTH = 100

    def clean(self):
        if self.pk is None:
            return
        instance = self
        depth = SelfReferenceCheckMixIn.MAX_DEPTH
        while instance and depth > 0:
            instance = instance.parent
            if instance and instance.pk == self.pk:
                raise ValidationError({'parent': _('Circular reference detected on field "%s"') % 'parent'})
            depth -= 1


def base64_encode(value):
    # need to safe "A-Z a-z 0-9 - _ . ! ~ * ' ( )"
    # because JS won't encode them
    # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent
    value = urllib.parse.quote(value, encoding='UTF-8', safe="-_.!~*'()")
    byte_value = base64.b64encode(value.encode())
    return byte_value.decode()


def base64_decode(value):
    byte_value = base64.b64decode(value)
    value = byte_value.decode()
    return urllib.parse.unquote(value, encoding='UTF-8')


def uuid():
    return base64.urlsafe_b64encode(uuid4().bytes).decode("ascii").rstrip("=")


@deconstructible
class UploadToDir(object):

    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        name, ext = os.path.splitext(filename)
        if instance and instance.id:
            new_name = "%d%s" % (instance.id, ext)
            return os.path.join(self.sub_path, new_name)
        else:
            name = slugify(name)
            if len(name) == 0:
                name = uuid()
            new_name = "%s%s" % (name, ext)
            return os.path.join(self.sub_path, new_name)


user_signer = Signer(sep='.')
