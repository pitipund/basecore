import datetime
from enum import Enum
from typing import Type

from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import BLANK_CHOICE_DASH
from rest_framework.relations import PrimaryKeyRelatedField

from his.framework.utils import _, LabeledIntEnum


class DecimalRangeField(models.DecimalField):
    """ A model's field which support to set min value and max value of DecimalField. """

    def __init__(self, verbose_name=None, name=None, max_digits=None, decimal_places=None, min_value=None,
                 max_value=None, **kwargs):
        self.max_digits, self.decimal_places = max_digits, decimal_places
        self.min_value, self.max_value = min_value, max_value
        super(models.DecimalField, self).__init__(verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value': self.max_value}
        defaults.update(kwargs)
        return super(DecimalRangeField, self).formfield(**defaults)


class PriceField(models.DecimalField):
    """ A model's field which contain a default constraint of DecimalField to be use for storing price. """

    def __init__(self, *args, **kwargs):
        kwargs["max_digits"] = 12
        kwargs["decimal_places"] = 2
        super().__init__(*args, **kwargs)


class QuantityField(models.DecimalField):
    """ A model's field which contain a default constraint of DecimalField to be use for storing quantity. """

    def __init__(self, *args, **kwargs):
        kwargs["max_digits"] = 8
        kwargs["decimal_places"] = 0
        super().__init__(*args, **kwargs)


class _EnumFormField(forms.TypedChoiceField):
    def prepare_value(self, value):
        if isinstance(value, Enum):
            return value.value
        else:
            return value


class _DummyEnum(LabeledIntEnum):
    """Dummy Enum to skip migration for changes of choice field"""
    TEST = 1


class EnumField(models.IntegerField):
    """ A model's field which represent as an Enum instance.
    It is able to generate choices from :class:`his.framework.utils.LabeledIntEnum`.
    Do not pass a list of tuple to `enum` argument even thought it accept.
    Because it will lose capability of enum representation. (it's intended to be use only for migrations)

    :Example:

    >>> from his.framework.models import EnumField
    >>> from his.framework.utils import LabeledIntEnum
    >>> from django.db import models
    >>>
    >>> class MyModel(models.Model):
    >>>
    >>>     MY_LEGACY_CHOICE_APPLE = 1
    >>>     MY_LEGACY_CHOICE_BANANA = 2
    >>>     MY_LEGACY_CHOICES = (
    >>>         (MY_LEGACY_CHOICE_APPLE, 'my name is apple.'),
    >>>         (MY_LEGACY_CHOICE_BANANA, 'my name is banana.'),
    >>>     )
    >>>
    >>>     class MY_CHOICES(LabeledIntEnum):
    >>>         APPLE = 1, 'my name is apple.'
    >>>         BANANA = 2, 'my name is banana.'
    >>>
    >>>     # used legacy choices with IntegerField (least convenience)
    >>>     fieldA = models.IntegerField(choices=MY_LEGACY_CHOICES)
    >>>
    >>>     # used enum choices with IntegerField
    >>>     fieldB = models.IntegerField(choices=[(e.value, e.name) for e in MY_CHOICES])
    >>>
    >>>     # used enum choices with EnumField (most convenience)
    >>>     fieldC = EnumField(MY_CHOICES)
    >>>
    """

    def __init__(self, enum: Type[LabeledIntEnum], **kwargs):
        if type(enum) is list:
            self.enum = None
            kwargs['choices'] = enum
        else:
            self.enum = enum
            kwargs['choices'] = [(e.value, e.name) for e in enum]
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'choices' in kwargs:
            # we pop choices, and put _DummyEnum to skip making migrations for 'choices' change during development
            #   when in production choices change should create migration (so we can perform data migrations)
            kwargs.pop('choices')
            args = [_DummyEnum]
            # actual code after we go live::
            #     kwargs['enum'] = kwargs.pop('choices')
        if 'default' in kwargs:
            if isinstance(kwargs['default'], LabeledIntEnum):
                kwargs['default'] = kwargs['default'].value
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return value
        if not self.enum:
            return super().to_python(value)
        try:
            return self.enum(value)
        except ValueError:
            return super().to_python(value)

    def _get_flatchoices(self):
        """Django Amdin list_filter call this method for list of choices on the right"""
        return [(e.value, e.label or e.name) for e in self.enum]

    flatchoices = property(_get_flatchoices)

    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH, limit_choices_to=None):
        """Choice for display in ComboBox by Django Admin form field

        we display both name and label to make it easier to understand"""
        first_choice = (blank_choice if include_blank else [])
        return first_choice + [(e.value, '%s - %s' % (e.name, e.label)) for e in self.enum]

    def formfield(self, **kwargs):
        default = {}
        default['choices_form_class'] = _EnumFormField
        default.update(kwargs)
        return super().formfield(**default)


class _StatableStatusField(models.IntegerField):
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop('choices', None)
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return value
        try:
            return self.model.STATUS(value)
        except ValueError:
            return super().to_python(value)
        except AttributeError:
            # NATT: this code path is required for RunPython in migration file
            #       RunPython create anonymous Model class that has no .STATUS attribute (based on migratoin history)
            #       we need to get actual class to be able to read .STATUS enum
            try:
                return apps.get_model(self.model._meta.app_label, model_name=self.model._meta.model_name).STATUS(value)
            except LookupError:
                # this code path is required when a model of the migration has been deleted
                return value

    @property
    def enum(self):
        return self.model.STATUS

    @property
    def flatchoices(self):
        """Django Admin list_filter call this method for list of choices on the right"""
        return [(e.value, e.label or e.name) for e in self.enum]

    def contribute_to_class(self, *args, **kwargs):
        super().contribute_to_class(*args, **kwargs)
        if getattr(self.model, 'STATUS', None):
            self.choices = self.flatchoices


class RunningNumberField(models.CharField):
    """ A model's field which auto-generate a running number for a model.
    a prefix can be overridden with an attribute :attr:`override_XXXX_prefix`, see example.
    an overridden type can be string or callable, see example.

    .. warning:: overridden on inheritance (abstract,proxy) is still not support yet.

    :param length: a fixed length of a code
    :param prefix: a character or %Y for a year number, %M for a month number, %D for a day number

    :Example 1:

    >>> from his.framework.models import RunningNumberField
    >>> from django.db import models
    >>>
    >>>
    >>> class MyModel(models.Model):
    >>>     my_code = RunningNumberField(length=10, prefix='%Y%M')
    >>>
    >>>
    >>> class MyProxyModelA(MyAbstractModel):
    >>>     override_my_code_prefix = 'A%Y%M'
    >>>
    >>>     class Meta:
    >>>         proxy = True
    >>>
    >>>
    >>> class MyProxyModelB(MyAbstractModel):
    >>>     override_my_code_prefix = 'B%Y%M'
    >>>
    >>>     class Meta:
    >>>         proxy = True

    :Example 2:

    >>> from his.framework.models import RunningNumberField
    >>> from django.db import models
    >>> import random
    >>>
    >>>
    >>> class MyAbstractModel(models.Model):
    >>>     my_code = RunningNumberField(length=10, prefix='%Y%M')
    >>>
    >>>     class Meta:
    >>>         abstract = True
    >>>
    >>>
    >>> class MyConcreteModelA(MyAbstractModel):
    >>>     override_my_code_prefix = 'A%Y%M'
    >>>
    >>>
    >>> class MyConcreteModelB(MyAbstractModel):
    >>>     def override_my_code_prefix(self):
    >>>         return '%s%%Y%%M'%(random.choice(['B','C','D']))
    """

    def __init__(self, length: int, prefix: str = '', **kwargs):
        if type(length) is not int:
            raise TypeError('length is not int')
        if type(prefix) is not str:
            raise TypeError('prefix is not str')
        if len(prefix) > length:
            raise TypeError('prefix is too long')

        self.length = length
        self.prefix = prefix

        kwargs['max_length'] = length
        kwargs['unique'] = True
        kwargs['editable'] = False
        # kwargs['default'] = self.generate_running_number
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['length'] = self.length
        kwargs['prefix'] = self.prefix
        # kwargs['default'] = ''
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        if add:
            value = self.generate_running_number()
            setattr(model_instance, self.attname, value)
            return value
        return super().pre_save(model_instance, add)

    def generate_running_number(self):
        prefix = getattr(self.model, 'override_%s_prefix' % (self.name), self.prefix)
        if callable(prefix):
            prefix = prefix()

        YY, MM, DD = datetime.date.today().strftime('%y-%m-%d').split('-')
        prefix = prefix.replace('%Y', YY).replace('%M', MM).replace('%D', DD)

        instance = self.model.objects.filter(**{self.name + '__startswith': prefix}).only(self.name).last()
        last_number = getattr(instance, self.name) if instance else ''
        if last_number[:len(prefix)] != prefix:
            running = 1
        else:
            running = int(last_number[len(self.prefix):] or 0) + 1

        return prefix + ('%%0%dd' % (self.length - len(prefix))) % (running)


class DefaultStartRunningNumberField(RunningNumberField):
    def pre_save(self, model_instance, add):
        if add:
            value = self.generate_running_number(model_instance)
            setattr(model_instance, self.attname, value)
            return value
        return super().pre_save(model_instance, add)

    def generate_running_number(self, model_instance):
        prefix = getattr(self.model, 'override_%s_prefix' % (self.name,), self.prefix)
        if callable(prefix):
            prefix = prefix(model_instance)

        YY, MM, DD = datetime.date.today().strftime('%y-%m-%d').split('-')
        prefix = prefix.replace('%Y', YY).replace('%M', MM).replace('%D', DD)

        default_start_number = -1
        get_default_start_number_function_name = 'get_%s_default_start_running_number' % (self.name,)
        get_default_start_number = getattr(self.model, get_default_start_number_function_name, None)
        if get_default_start_number and callable(get_default_start_number):
            default_start_number = get_default_start_number(model_instance)
            try:
                default_start_number = int(default_start_number)
            except Exception:
                print('get_%s_default_start_number return value not int' % (self.name,))
                default_start_number = -1

        instance = self.model.objects.filter(**{self.name + '__startswith': prefix}).only(self.name).last()
        last_number = getattr(instance, self.name) if instance else ''
        if last_number[:len(prefix)] != prefix:
            if default_start_number == -1:
                running = 1
            else:
                running = default_start_number
        else:
            running = int(last_number[len(prefix):] or 0) + 1
            if default_start_number > running:
                running = default_start_number

        return prefix + ('%%0%dd' % (self.length - len(prefix))) % (running,)


class SelfReferenceForeignKey(models.ForeignKey):
    """ A model's field which refers itself as a foreign key, also prevents a circular reference

        You must call .full_clean() to run validation on model before .save()
        (this was called automatically in Django admin, but RestFramework's ModelSerializer DOES NOT)

    .. warning:: calling update() directly will break non-circular-reference constraint.
    """
    MAXIMUM_SEARCH_DEPT = 100
    ERROR_MESSEGE = _('Circular reference detected on field "%s"')

    def __init__(self, *args, **kwargs):
        kwargs["to"] = "self"
        super().__init__(*args, **kwargs)

    def _check_cycle(self, value, model_instance):
        ref_to_id = value
        cls = model_instance.__class__
        dept = 0

        if model_instance.pk is None:
            return
        if ref_to_id == model_instance.pk:
            raise ValidationError(self.ERROR_MESSEGE % self.name)

        while ref_to_id:
            ref_to = cls.objects.filter(pk=ref_to_id).first()

            if ref_to:
                ref_to_id = getattr(ref_to, self.attname, None)
            if ref_to_id == model_instance.pk:
                raise ValidationError(self.ERROR_MESSEGE % self.name)

            if dept == self.MAXIMUM_SEARCH_DEPT:
                break

            dept += 1

    def validate(self, value, model_instance):
        self._check_cycle(value, model_instance)
        super(SelfReferenceForeignKey, self).validate(value, model_instance)


class CustomPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    """
    This field accepts a models.Model instance when it serializes a value
    to representation
    """

    def to_representation(self, value):
        if self.pk_field is not None:
            return self.pk_field.to_representation(value.pk)
        if isinstance(value.pk, models.Model):
            value = value.pk
        return value.pk
