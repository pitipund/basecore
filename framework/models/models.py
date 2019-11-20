import inspect
from typing import Type

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import checks
from django.db import models
from django.db.models.base import ModelBase
from django.utils.module_loading import import_string
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from his.framework.models.fields import EnumField, _StatableStatusField
from his.framework.utils import LabeledIntEnum, _

User = get_user_model()


class StatablePermission(object):
    """Default Statable Permission that allow all actions

    You can override statable permission from ``settings.py`` by setting::

        STATABLE_PERMISSION = 'some_package.module.PermissionClass'
    """

    def has_action_permission(self, user, statable, action):
        """
        :param user: django's User
        :param statable: Statable instance
        :param action: Action NAME, e.g. OPD_EDIT (allow/disallow action)
        :return: bool
        """
        return True


class EditableModel(models.Model):
    """Base object that keep tracks who changed this object"""
    edit_user = models.ForeignKey(User, null=True, blank=True, editable=False, verbose_name='ผู้บันทึก',
                                  related_name='+')
    created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')
    edited = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')

    class Meta:
        abstract = True


class TimeStampModel(models.Model):
    """Base object that keep tracks who and when changed this object"""
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, blank=True, null=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, blank=True, null=True, related_name='+')

    class Meta:
        abstract = True


class DescriptionModel(TimeStampModel):
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "%s" % self.name


class AbstractCheckerModelMixin(models.Model):
    """ a model which is able to enforce children to implement all abstractmethod defined in abstract model
    to mark a function as abstractmethod, decorate a function with @abstractmethod from 'abc'
    """

    _will_check_abstract_method = True

    @classmethod
    def _check_model(cls):
        errors = super()._check_model()

        _will_check_abstract_method = cls.__dict__.get('_will_check_abstract_method', True)
        if _will_check_abstract_method and not cls._meta.abstract:
            model_functions = filter(callable, map(lambda attr: getattr(cls, attr, None), dir(cls)))
            abstract_functions = filter(lambda func: getattr(func, '__isabstractmethod__', False), model_functions)
            for abstract_function in abstract_functions:
                errors.append(
                    checks.Error(
                        "'%s' is abstracted but not implemented." % (abstract_function.__name__),
                        obj=cls,
                    )
                )

        return errors

    class Meta:
        abstract = True


class StatableModel(EditableModel):
    """ a model which is able to track every status changing of an entity.

    required :attr:`ACTION` an Enum of actions which an entity is allowed to be done.

    required :attr:`STATUS` an Enum of statuses which an entity is allowed to have.

    required :attr:`TRANSITION` a list of tuple which contained rule of state changing.

    required :class:`ActionLog` a model class which keep a state change history.

    :Definition:

    >>> from his.framework.models import StatableModel
    >>> from his.framework.utils import LabeledIntEnum
    >>>
    >>>
    >>> class Oreo(StatableModel):
    >>>
    >>>     class ACTION(LabeledIntEnum):
    >>>         BUY = 1, 'buy oreo from a store.'
    >>>         UNPACK = 2, 'unpack the oreo, ready to eat.'
    >>>         PICK = 3, 'pick the oreo in to my hand.'
    >>>         RETURN = 4, 'return the oreo in to a pack.'
    >>>         EAT = 5, 'eating the oreo until it ran out.'
    >>>         DISCARD = 6, 'throw the oreo away.'
    >>>
    >>>     class STATUS(LabeledIntEnum):
    >>>         OWNED = 1, 'i have the own oreo.'
    >>>         UNPACKED = 2, 'the oreo is already unpacked.'
    >>>         PICKED = 3, 'the oreo is already in the hand.'
    >>>         EATEN = 5, 'the oreo is already eaten.'
    >>>         DISCARDED = 6, 'the oreo was threw away.'
    >>>
    >>>     TRANSITION = [
    >>>         (None, ACTION.BUY, STATUS.OWNED),
    >>>         (STATUS.OWNED, ACTION.UNPACK, STATUS.UNPACKED),
    >>>         (STATUS.OWNED, ACTION.DISCARD, STATUS.DISCARDED),
    >>>         (STATUS.UNPACKED, ACTION.PICK, STATUS.PICKED),
    >>>         (STATUS.PICKED, ACTION.RETURN, STATUS.UNPACKED),
    >>>         (STATUS.PICKED, ACTION.EAT, STATUS.EATEN),
    >>>     ]
    >>>
    >>>     size = models.CharField(max_length=10, help_text='a size of the oreo.')
    >>>     flavor = models.CharField(max_length=30, help_text='a flavor of the oreo.')
    >>>
    >>>     # this is a function that will always be called after EAT (optional).
    >>>     def do_eat(self):
    >>>         print("hmmm delicious.")
    >>>
    >>>     # this is a function that will always be called before DISCARD (optional).
    >>>     def pre_discard(self):
    >>>         print("nahhh.")
    >>>
    >>>     # this is a function that will always be called after DISCARD (optional).
    >>>     def do_discard(self):
    >>>         print("such a pity.")
    >>>
    >>>
    >>> # this class is required to keep a history of actions.
    >>> class OreoActionLog(BaseActionLog(Oreo)):
    >>>     location = models.CharField(max_length=100, help_text='a place where the action is performed')
    >>>     note = models.TextField(blank=True, help_text='you can take note whatever you want when doing action.')
    >>>

    :Usage:

    >>> import datetime, random
    >>>
    >>>
    >>> def buy_oreo(size:str, flavor:str, buyer:User, store:str):
    >>>     if random.randint(0,1):
    >>>         # this is the way you create a statable model (1)
    >>>         oreo = Oreo.objects.create(
    >>>             size=size,
    >>>             flavor=flavor,
    >>>             user=buyer,
    >>>             action=Oreo.ACTION.BUY,
    >>>             action_log_kwargs = {
    >>>                 'store': store,  # this is the way you put an attribute data into action log instance.
    >>>             }
    >>>         )
    >>>     else :
    >>>         # this is the way you create a statable model (2)
    >>>         oreo = Oreo()
    >>>         oreo.size=size
    >>>         oreo.flavor=flavor
    >>>         oreo.user=buyer
    >>>         oreo.action=Oreo.ACTION.BUY
    >>>         oreo.action_log_kwargs = {
    >>>             'store': store,  # this is the way you put an attribute data into action log instance.
    >>>         }
    >>>
    >>>     return oreo
    >>>
    >>>
    >>> def discard_oreo(oreo:Oreo, thrower:User, location:str, reason:str):
    >>>     buying_action = oreo.get_action(Oreo.ACTION.BUY)  # you can get a latest action log with this function.
    >>>
    >>>     buyer = buying_action.user  # you can access to user who performed the action
    >>>     if buyer != thrower:
    >>>         raise Exception('you could not throw others oreo!!')
    >>>
    >>>     buying_time = buying_action.datetime  # you can access to datetime when the action is performed
    >>>     if datetime.datetime.now() - buying_time < datetime.timedelta(hours=1):
    >>>         raise Exception('too early to throw it away!!')
    >>>
    >>>     if not location:
    >>>         raise Exception('invalid location.')
    >>>
    >>>     if not reason:
    >>>         raise Exception('please just give me a reason why you throwing it...')
    >>>
    >>>     # this is the way you update (perform an action on) a statable model
    >>>     oreo.action = Oreo.ACTION.DISCARD
    >>>     oreo.user = thrower
    >>>     oreo.action_log_kwargs = {
    >>>         'location': location,
    >>>         'note': reason,
    >>>     }
    >>>     oreo.save()
    >>>     print('good bye oreo.')
    >>>
    """

    OPTION_ANY_STATUS = object()
    ACTION = None
    STATUS = None
    TRANSITION = None

    _will_check_workflow = True

    status = _StatableStatusField(default=0, editable=False)

    @classmethod
    def _check_model(cls):
        errors = super()._check_model()

        _will_check_workflow = cls.__dict__.get('_will_check_workflow', True)
        if _will_check_workflow and not cls._meta.abstract:
            if not inspect.isclass(cls.ACTION):
                errors.append(
                    checks.Error('a StatableModel must have an attribute "ACTION" as an inner-class', obj=cls)
                )
            elif not issubclass(cls.ACTION, LabeledIntEnum):
                errors.append(
                    checks.Info('a StatableModel ACTION should be LabeledIntEnum', obj=cls)
                )

            if not inspect.isclass(cls.STATUS):
                errors.append(
                    checks.Error('a StatableModel must have an attribute "STATUS" as an inner-class', obj=cls)
                )
            elif not issubclass(cls.STATUS, LabeledIntEnum):
                errors.append(
                    checks.Info('a StatableModel STATUS should be LabeledIntEnum', obj=cls)
                )

            if type(cls.TRANSITION) is not list:
                errors.append(
                    checks.Error('a StatableModel must have an attribute "TRANSITION" as a list', obj=cls)
                )
            else:
                errors.extend(cls._build_transition_map())

        return errors

    @classmethod
    def _build_transition_map(cls):
        errors = []
        cls._transition_map = {}
        for transition in cls.TRANSITION[:]:
            if transition[0] is StatableModel.OPTION_ANY_STATUS:
                cls.TRANSITION.remove(transition)
                for status in cls.STATUS:
                    cls.TRANSITION.append((
                        status,
                        transition[1],
                        status if transition[2] is StatableModel.OPTION_ANY_STATUS else transition[2],
                    ))

        for transition in cls.TRANSITION:
            transition_input = (transition[0], transition[1])
            if transition[0] is None:
                cls._initial_action = transition[1]
            if transition_input not in cls._transition_map:
                cls._transition_map[transition_input] = transition[2]
                continue

            errors.append(
                checks.Error('multiple TRANSITION output found (status:%s action:%s)' % (
                    transition[0].name,
                    transition[1].name,
                ), obj=cls)
            )

        return errors

    @classmethod
    def _get_transition_map(cls):
        """this way is more precise than hasattr because the inherited attribute will not be in vars(cls)"""
        if '_transition_map' not in vars(cls):
            if cls._build_transition_map():
                raise Exception(
                    'there are some errors in TRANSITION of %s.\nPlease use runserver to execute checks.' % (
                        cls.__name__,
                    ))

        return cls._transition_map

    @classmethod
    def _get_initial_action(cls):
        cls._get_transition_map()
        return cls._initial_action

    @classmethod
    def _get_next_status(cls, status, action):
        status = status and cls.STATUS(status)
        action = action and cls.ACTION(action)
        transition_input = (status or None, action)
        if transition_input in cls._get_transition_map():
            next_status = cls._get_transition_map()[transition_input]
        else:
            status_label = status and (status.label or status.name)
            action_label = action and (action.label or action.name)
            model_name = cls._meta.verbose_name.title()
            message = _('%(model)s: an instance with status "%(status)s" is not allowed to do action "%(action)s"') % {
                'model': model_name,
                'status': status_label,
                'action': action_label,
            }
            status_name = status and status.name
            action_name = action and action.name
            raise serializers.ValidationError({'code': 'ACTION_NOT_ALLOWED',
                                               'message': message,  # Human readable message
                                               'status': status_name,  # e.g. ARRIVED (Enum constant for check)
                                               'action': action_name})  # e.g. OPD_ARRIVE (Enum constant for check)
        return next_status

    @classmethod
    def get_permission_class(cls):
        """Get permission class from Django's settings.py
        This allow us to config StatableModel to use different permission class
        """
        if not hasattr(cls, '_permission'):
            cls._permission = import_string(getattr(settings, 'STATABLE_PERMISSION',
                                                    'his.framework.models.models.StatablePermission'))()
        return cls._permission

    def get_action(self, *actions):
        """
        :param actions: an enum or an enum.value of Action.
        :return: first found action instance or None if not found.
        """
        actions_map = {}
        actions_all = self.actions.all()
        for action in actions_all:
            if actions_map.get(action.action):
                actions_map[action.action] = max(actions_map[action.action], action, key=lambda a: a.datetime)
            else:
                actions_map[action.action] = action

        for action in actions:
            action = actions_map.get(action)
            if action:
                return action

    def get_allowed_action(self):
        cls = self.__class__
        if '_allowed_action' not in cls.__dict__:  # this will not use inherited attribute
            cls._allowed_action = {}
            for status, action, next_status in cls.TRANSITION:
                cls._allowed_action.setdefault(status, []).append(action)

        result = cls._allowed_action.get(self.status or None) or []
        return result[:]

    def get_permitted_allowed_action(self, user):
        permission_class = self.get_permission_class()
        return [
            action for action in self.get_allowed_action()
            if permission_class.has_action_permission(user, self, action.name)
        ]

    def __init__(self, *args, **kwargs):
        action = kwargs.pop('action', None)
        user = kwargs.pop('user', None)
        action_log_kwargs = kwargs.pop('action_log_kwargs', {})
        super().__init__(*args, **kwargs)
        self.action = action
        self.user = user
        self.action_log_kwargs = action_log_kwargs

    def is_action_allowed(self, action):
        try:
            self.__class__._get_next_status(self.status, action)
            return True
        except serializers.ValidationError as e:
            return False

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

        if not self.action:
            raise Exception('instance.action must be defined')

        if not self.user:
            raise Exception('instance.user must be defined')

        self.action = self.ACTION(self.action)

        # Call function pre_action every save
        self.pre_action()

        # Call function pre_<action_name> based on the action_name (e.g. pre_perform, pre_order)
        pre_save_function = getattr(self, 'pre_%s' % (self.action.name.lower()), None)
        if callable(pre_save_function):
            pre_save_function()

        if not self.get_permission_class().has_action_permission(self.user, self, self.action.name):
            raise PermissionDenied('%s: User %s has no permission to perform action "%s"' % (
                self.__class__.__name__,
                self.user,
                self.action.name,
            ))

        if self.pk:
            updated_instance = self.__class__.objects.filter(pk=self.pk).values('status').first()
            self.status = updated_instance['status'] if updated_instance else None
        else:
            self.status = None

        self.status = self._get_next_status(self.status, self.action)
        self.edit_user = self.user

        result = super(StatableModel, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

        self.actions.model.objects.create(
            statable=self,
            user=self.user,
            action=self.action,
            **self.action_log_kwargs
        )

        # Call function do_<action_name> based on the action_name (e.g. do_perform, do_order)
        post_save_function = getattr(self, 'do_%s' % (self.action.name.lower()), None)
        if callable(post_save_function):
            post_save_function()

        # Call function do_action every save
        self.do_action()

        return result

    def pre_action(self):
        # this function is called before save and pre_<action>
        pass

    def do_action(self):
        # this function is called after save and do_<action>
        pass

    def save_for_test(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True


def BaseActionLog(_statable: Type[StatableModel]) -> Type[models.Model]:
    """ create an action log base class which is related to a statable model. """

    class _BaseActionLog(models.Model):
        related_statable = _statable
        statable = models.ForeignKey(_statable, related_name='actions')
        user = models.ForeignKey(User, related_name='+')
        action = EnumField(_statable.ACTION)
        datetime = models.DateTimeField(auto_now=True)

        class Meta:
            abstract = True

        def __str__(self):
            return '%s %s' % (self.action.name, self.datetime.strftime('%c'))

    return _BaseActionLog


class ProxyTypeManager(models.Manager):
    """ a model manager which help filtering instances which have match type with the specialized class.
    only work with a model mixed with :class:`ProxyTypeModelMixIn`.
    """

    def all_type(self):
        return super().get_queryset()

    def get_queryset(self):
        if self.model.PROXY_TYPE:
            return self.all_type().filter(type=self.model.PROXY_TYPE)
        return self.all_type()


class ProxyTypeModelMixIn(models.Model):
    """ a model mixin which help reusing a model fields and table with proxy model.
    this will help specifying a behavior of an each type (can be used with :class:`StatableModel`).
    it also help up/down casting. recommend to use with :class:`ProxyTypeManager`

    required :attr:`TYPE` an Enum of types which will be a proxy model. (defined in parent model).

    required :attr:`PROXY_TYPE` a element of TYPE which described a model. (defined in proxy model).

    :Definition:

    >>> class Snack(ProxyTypeModelMixIn, models.Model):
    >>>     class TYPE(LabeledIntEnum):
    >>>         OREO = 1
    >>>         PRINGLES = 2
    >>>
    >>>     type =  EnumField(TYPE)
    >>>     is_eaten = models.BooleanField(default=False)
    >>>     objects = ProxyTypeManager()
    >>>
    >>>     def eat(self):
    >>>         print('yukkk an abstract snack!!')
    >>>
    >>> class Oreo(Snack)
    >>>     PROXY_TYPE = Snack.TYPE.PRINGLES
    >>>
    >>>     def eat(self):
    >>>         print('oreo are sweet.')
    >>>
    >>>     class Meta:
    >>>         proxy = True
    >>>
    >>>
    >>> class Pringles(Snack)
    >>>     PROXY_TYPE = Snack.TYPE.PRINGLES
    >>>
    >>>     def eat(self):
    >>>         print('pringles are crispy.')
    >>>
    >>>     class Meta:
    >>>         proxy = True

    :Usage:

    >>> def eat_all_snack():
    >>>     for snack in Snack.objects.all():
    >>>         snack.eat()  # "yukkk an abstract snack!!"
    >>>
    >>> def eat_all_oreo_by_casting():
    >>>     oreos = []
    >>>     for snack in Snack.objects.filter(type=Snack.TYPE.OREO)
    >>>         snack.eat()  # "yukkk an abstract snack!!"
    >>>         snack.specialize()  # cast to Oreo
    >>>         snack.eat()  # "oreo are sweet."
    >>>
    >>>     return oreos
    >>>
    >>> def eat_all_pringles_directly():
    >>>     for pringles in Pringles.objects.all():
    >>>         pringles.eat()  # "pringles are crispy."
    """

    PROXY_TYPE = 0

    class TYPE(LabeledIntEnum):
        pass

    objects = ProxyTypeManager()

    @classmethod
    def _check_model(cls):
        errors = super()._check_model()
        if cls._meta.proxy and (not cls.PROXY_TYPE or not isinstance(cls.PROXY_TYPE, cls.TYPE)):
            errors.append(
                checks.Error('must have an attribute "PROXY_TYPE" '
                             'which is a member of "cls.TYPE"', obj=cls)
            )
        return errors

    @classmethod
    def _initial_type_mapper(cls):
        if not cls._meta.proxy:
            cls._TYPE_MAPPER = getattr(cls, '_TYPE_MAPPER', {})
        else:
            cls._TYPE_MAPPER[cls.PROXY_TYPE] = cls

    @classmethod
    def _prepare(cls):
        ModelBase._prepare(cls)
        cls._initial_type_mapper()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.PROXY_TYPE and not self.type:
            self.type = None
        elif self.PROXY_TYPE:
            self.type = self.PROXY_TYPE
        return super().save(force_insert, force_update, using, update_fields)

    def specialize(self):
        self.__class__ = self._TYPE_MAPPER[self.type]

    class Meta:
        abstract = True


class TypedSupportManager(models.Manager):
    """ A manager which help adding a property of typed support model to RelateManager of parent model.

    .. warning:: UNDER CONSTRUCTION.
    """
    use_for_related_fields = True

    def _get_supporter(self, type):
        self._supporter_cache = getattr(self, '_supporter_cache', {})
        if type not in self._supporter_cache:
            self._supporter_cache[type] = self.filter(type=type).first()

        return self._supporter_cache[type]

    def _set_supporter(self, type, value):
        self._supporter_cache = getattr(self, '_supporter_cache', {})
        if not isinstance(value, self.model):
            raise TypeError('value is not %s' % (self.model))

        self._supporter_cache[type] = value

    def contribute_to_class(self, *args, **kwargs):
        super().contribute_to_class(*args, **kwargs)

        def create_property(type):
            def fget(self):
                return self._get_supporter(type=type)

            def fset(self, value):
                self._set_supporter(type=type, value=value)

            setattr(self.__class__, type.name, property(fget, fset))

        [create_property(type) for type in self.model.TYPE]
