import logging

from datetime import date, datetime
from typing import Union

from constance import config
from django.db import models, transaction
from django.core import urlresolvers
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .devices import Location
from .utils import enum_choices, SelfReferenceCheckMixIn, get_resolved_urls
from his.framework.utils import LabeledIntEnum

logger = logging.getLogger(__name__)


__all__ = [
    'Screen', 'HISPermission', 'Role', 'ApplicationDefaultRole', 'RoleGroup'
]


class Screen(models.Model):
    """หน้าจอภายในระบบ"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='red')
    url = models.CharField(max_length=200, unique=True)
    display_seq = models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')
    top_level = models.BooleanField(default=True, help_text='Display this screen in main menu')

    class Meta:
        ordering = ('display_seq', 'id')

    def __str__(self):
        return self.name


class HISPermissionManager(models.Manager):
    EXCLUDE_URL_NAMESPACE = ('tools', 'admin', 'management_site')

    def operation_map(self):
        if hasattr(self, 'METHOD_OPEARTION_MAP'):
            return self.METHOD_OPERATION_MAP

        self.METHOD_OPERATION_MAP = {
            'get': HISPermission.OPERATION.RETRIEVE,
            'post': HISPermission.OPERATION.CREATE,
            'put': HISPermission.OPERATION.UPDATE,
            'delete': HISPermission.OPERATION.DELETE
        }
        return self.METHOD_OPERATION_MAP

    def populate_screen_permissions(self):
        for screen in Screen.objects.using(self.db).all():
            self.get_screen_permission(screen, create=True)

    def populate_action_permissions(self, clean=True, dry=True):
        # This is imported here to avoid user --> core dependencies
        from his.core.utils import get_his_apps
        from his.framework.models import StatableModel

        existing_perms = set(self.filter(type=HISPermission.TYPE.ACTION)
                             .values_list('identifier', flat=True))
        for app in get_his_apps():
            for model in app.get_models():
                if issubclass(model, StatableModel):
                    for action in model.ACTION:
                        identifier = self._get_action_identifier(model, action)
                        if identifier in existing_perms:
                            existing_perms.remove(identifier)
                        else:
                            self.get_action_permission(model, action, create=True)
                    # all action permission
                    identifier = self._get_action_identifier(model, HISPermission.ALL_ACTION)
                    if identifier in existing_perms:
                        existing_perms.remove(identifier)
                    else:
                        self.get_action_permission(model, HISPermission.ALL_ACTION, create=True)
        if clean:
            for identifier in existing_perms:
                his_perm = self.get(type=HISPermission.TYPE.ACTION,
                                    identifier=identifier)
                logger.debug('Stale permission (model/action not found): %s' % his_perm)
                if not dry:
                    his_perm.delete()
                    logger.debug('Deleted')

    def _get_url_name(self, url):
        if url.name:
            return url.name
        else:
            return "%s.%s" % (url.callback.__module__, url.callback.__name__)

    def _has_method_in_view(self, method, url):
        if hasattr(url.callback, 'view_class'):
            # rest_framework's APIView
            return hasattr(url.callback.view_class, method)
        elif hasattr(url.callback, 'actions'):
            return method in url.callback.actions
        # View type not support yet
        return False

    def populate_resource_permissions(self, clean=True, dry=True):
        """auto populate permisison from URLs, StatableModel
        """
        existing_perms = set(self.filter(type=HISPermission.TYPE.RESOURCE)
                             .values_list('operation', 'identifier'))
        urls = urlresolvers.get_resolver()
        urls = get_resolved_urls(urls.url_patterns)
        for url in urls:
            # Only generate for namespaced url only
            if url.namespace and url.namespace not in self.EXCLUDE_URL_NAMESPACE:
                # determine available permission
                if hasattr(url.callback, 'view_class') or hasattr(url.callback, 'actions'):
                    url_name = self._get_url_name(url)
                    not_generated = True
                    for method, operation in self.operation_map().items():
                        if self._has_method_in_view(method, url):
                            not_generated = False
                            url_identifier = HISPermission.get_resource_identifier(url.namespace, url_name)
                            if (operation, url_identifier) in existing_perms:
                                existing_perms.remove((operation, url_identifier))
                            else:
                                self.get_or_create(type=HISPermission.TYPE.RESOURCE,
                                                   identifier=url_identifier,
                                                   operation=operation)
                    if not_generated:
                        logger.debug('not generating permission for %s' % url)
                else:
                    logger.debug('url %s has no view_class' % url)
        if clean:
            for operation, identifier in existing_perms:
                his_perm = self.get(type=HISPermission.TYPE.RESOURCE,
                                    identifier=identifier,
                                    operation=operation)
                logger.debug('Stale permission (resource not found): %s' % his_perm)
                if not dry:
                    his_perm.delete()
                    logger.debug('Deleted')

    def _clone_permission_to_hispermission(self, p):
        """Clone django permission to MANAGEMENT permission, or CUSTOM permission"""
        h = HISPermission(permission_ptr_id=p.id)
        h.type = HISPermission.TYPE.MANAGEMENT
        if p.codename.startswith('add_'):
            h.operation = HISPermission.OPERATION.CREATE
        elif p.codename.startswith('change_'):
            h.operation = HISPermission.OPERATION.UPDATE
        elif p.codename.startswith('delete_'):
            h.operation = HISPermission.OPERATION.DELETE
        else:
            h.operation = HISPermission.OPERATION.NONE
            h.type = HISPermission.TYPE.CUSTOM
        h.identifier = "%s.%s" % (p.content_type.app_label, p.content_type.model)
        h.name = p.name
        h.content_type = p.content_type
        h.codename = p.codename
        h.save(using=self.db)

    def populate_management_permission(self):
        """Create HISPermission for each model registered in management_site"""
        from his.admin import management_site
        from constance.admin import Config

        existing_perms = set(HISPermission.objects.using(self.db).filter(
            type=HISPermission.TYPE.MANAGEMENT).values_list('content_type', 'codename'))
        models = []
        for model in management_site._registry.keys():
            if model == Config:
                # handle constance config as special case
                try:
                    p = Permission.objects.using(self.db).get(codename='change_config')
                    self._clone_permission_to_hispermission(p)
                except Permission.DoesNotExist:
                    logger.warning('Fail to find constance permission')
                continue
            if model._meta.app_label == 'constance':
                # skip Constance item registered in management site
                continue
            admin_obj = management_site._registry[model]

            # include inline models as management permission
            models.append(model)
            models += [inline.model for inline in admin_obj.inlines]

        # content_types = ContentType.objects.db_manager(self.db).get_for_models(*models).values()
        content_types = [ContentType.objects.db_manager(self.db).get_for_model(model).id for model in models]
        for p in Permission.objects.using(self.db).filter(content_type__in=content_types):
            if (p.content_type_id, p.codename) in existing_perms:
                continue
            self._clone_permission_to_hispermission(p)

    def populate_custom_permissions(self):
        """Custom model permissions are populated when you run:
            python manage.py migrate
        """
        ct = ContentType.objects.db_manager(self.db).get_for_model(HISPermission)
        custom_permissions = (Permission.objects.using(self.db).exclude(codename__startswith='add_')
                              .exclude(codename__startswith='change_')
                              .exclude(codename__startswith='delete_')
                              .exclude(content_type=ct))
        for perm in custom_permissions:
            self._clone_permission_to_hispermission(perm)

    def _get_action_identifier(self, model_class, action):
        model_label = model_class._meta.label
        if action == HISPermission.ALL_ACTION:
            identifier = HISPermission.get_action_identifier(model_label, HISPermission.ALL_ACTION)
        elif isinstance(action, str):  # action pass as string
            identifier = HISPermission.get_action_identifier(model_label, action)
        else:  # action as object enum
            identifier = HISPermission.get_action_identifier(model_label, action.name)
        return identifier

    def get_action_permission(self, model_class, action, create=False):
        """Get HISPermission instance, given StatableMmodel and Action"""
        identifier = self._get_action_identifier(model_class, action)
        if create:
            perm, _ = self.get_or_create(type=HISPermission.TYPE.ACTION, identifier=identifier)
        else:
            perm = self.get(type=HISPermission.TYPE.ACTION, identifier=identifier)
        return perm

    def get_screen_permission(self, screen: Screen, create=False):
        data = dict(type=HISPermission.TYPE.SCREEN,
                    identifier=screen.url,
                    operation=HISPermission.OPERATION.NONE)
        if create:
            screen, _ = self.get_or_create(**data)
        else:
            screen = self.get(**data)
        return screen

    def refresh_permission(self):
        with transaction.atomic():
            self.populate_management_permission()
            self.populate_screen_permissions()
            self.populate_action_permissions(clean=True, dry=False)
            self.populate_resource_permissions(clean=True, dry=False)
            self.populate_custom_permissions()


class HISPermission(Permission):
    ALL_ACTION = '__ALL__'

    class TYPE(LabeledIntEnum):
        MANAGEMENT = 1  # Permission to manage Role/Permission
        SCREEN = 2  # Permission to access screen
        RESOURCE = 3  # Permission to CRUD resource
        ACTION = 4  # Permission to perform `action`
        CUSTOM = 5  # Custom permission defined in each module

    class OPERATION(LabeledIntEnum):
        NONE = 0
        RETRIEVE = 1
        CREATE = 2
        UPDATE = 3
        DELETE = 4

    HTTP_VERBS_MAP = {
        'GET': 'RETRIEVE',
        'POST': 'CREATE',
        'PUT': 'UPDATE',
        'DELETE': 'DELETE'
    }

    type = models.IntegerField(choices=enum_choices(TYPE), default=2)
    identifier = models.CharField(max_length=100,
                                  help_text='Screen URL, Resource URL Name เช่น  fully_qualified_url, Action Name')
    operation = models.IntegerField(choices=enum_choices(OPERATION), default=0,
                                    help_text='ใช้กับ Permission ประเภท Resource เท่านั้น')
    objects = HISPermissionManager()

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ('type', 'identifier', 'operation')

    def __str__(self):
        if self.type == HISPermission.TYPE.CUSTOM:
            return "Action: %s" % super(HISPermission, self).__str__()
        val = "%s: %s" % (self.get_type_display().capitalize(), self.identifier)
        if self.operation > 0:
            val += " - %s" % (self.get_operation_display())
        return val

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        ct = ContentType.objects.db_manager(using).get_for_model(HISPermission)
        if self.type == HISPermission.TYPE.RESOURCE:
            self.codename = '%s_%s' % (self.get_operation_display(), self.identifier)
            self.name = '%s: %s' % (self.get_type_display(), self.codename)
            self.content_type = ct
        elif self.type in [HISPermission.TYPE.MANAGEMENT, HISPermission.TYPE.CUSTOM]:
            # Do nothing, we directly inherit existing Django's Permission object
            pass
        else:
            if self.type == HISPermission.TYPE.SCREEN:
                self.operation = HISPermission.OPERATION.NONE
                # does not support other operation yet
            self.codename = '%s_%s' % (self.get_type_display(), self.identifier)
            self.name = '%s: %s' % (self.get_type_display(), self.identifier)
            self.content_type = ct
        super(HISPermission, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                        update_fields=update_fields)

    @classmethod
    def get_screen_permission_codename(cls, url):
        return 'users.SCREEN_%s' % url

    @classmethod
    def get_action_identifier(cls, model_label, action):
        return '%s:%s' % (model_label, action)

    @classmethod
    def get_action_permission_codename(cls, model_label, action):
        return 'users.ACTION_%s' % cls.get_action_identifier(model_label, action)

    @classmethod
    def get_resource_identifier(cls, namespace, url_name):
        return '%s:%s' % (namespace, url_name)

    @classmethod
    def get_resource_permission_codename(cls, method, namespace, url_name):
        """
        :param method: HTTP Method
        :param namespace: URL namespace
        :param url_name: URL name in urls.py or fully qualified function name/class name
        :return:
        """
        if method == 'OPTIONS':
            method = 'GET'
        elif method == 'PATCH':
            method = 'PUT'
        operation = cls.HTTP_VERBS_MAP[method]
        return 'users.%s_%s' % (operation, cls.get_resource_identifier(namespace, url_name))


class Role(SelfReferenceCheckMixIn, models.Model):
    class TYPE(LabeledIntEnum):
        GENERAL = 1, 'ผู้ใช้ทั่วไป'
        DOCTOR = 2, 'แพทย์'
        PHARMACIST = 3, 'เภสัชกร'
        REGISTERED_NURSE = 4, 'พยาบาลวิชาชีพ'
        ADMIT_STAFF = 5, 'เจ้าหน้าที่ Admit'
        TECHNICIAN = 6, 'Technician'

    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', null=True, blank=True)
    type = models.IntegerField(choices=enum_choices(TYPE), default=1)
    permissions = models.ManyToManyField(HISPermission, blank=True)
    locations = models.ManyToManyField(Location, blank=True,
                                       help_text='ผู้ใช้ต้องล็อกอินจากสถานที่ใน List ของสถานที่ที่กำหนดจึงจะมีสิทธิ์')
    start_date = models.DateField(default=date.today, verbose_name='วันที่เริ่มต้นใช้ Role')
    end_date = models.DateField(null=True, blank=True, verbose_name='วันที่สิ้นสุดการใช้ Role')

    def __str__(self):
        return self.name

    def is_effective(self):
        """Determine if this role is still effective today"""
        today = datetime.now().date()
        return (self.start_date <= today) and (
            (self.end_date and today <= self.end_date) or self.end_date is None)

    def permission_as_value_list(self, as_value_list=True):
        if as_value_list:
            return self.permissions.values_list('content_type__app_label', 'codename')
        return list(self.permissions.all())

    def effective_permissions(self, location_id: Union[int, None], as_value_list=True):
        """Collect effective permissions from current role & inheried roles (given user logged in at `location`)

        :return: list
        """
        permissions = []
        if not self.is_effective():
            return permissions
        if self.locations.exists():
            # given locations are set, user must login from location listed to have permission
            if self.locations.filter(id=location_id):
                permissions += self.permission_as_value_list(as_value_list)
        else:
            permissions += self.permission_as_value_list(as_value_list)

        # permission from inherited role
        if self.parent:
            permissions += self.parent.effective_permissions(location_id=location_id, as_value_list=as_value_list)
        return permissions


class ApplicationDefaultRoleQueryset(models.QuerySet):

    def create(self, **kwargs):
        obj = super(ApplicationDefaultRoleQueryset, self).create(**kwargs)
        message = 'A new ApplicationDefaultRole "{}" has been created, please assign roles.'.format(obj.name)
        # send_mail('New Application Default Role', message, settings.DEFAULT_FROM_EMAIL, settings.ADMIN)
        logger.warning(message)
        return obj

    def get_default(self) -> 'ApplicationDefaultRole':
        default_name = config.users_DEFAULT_APPLICATION_NAME
        if default_name:
            obj, __ = self.get_or_create(name=default_name)
            return obj
        application_default_role = self.all().first()
        if application_default_role:
            return application_default_role
        return self.get_or_create(name='Default')[0]


class ApplicationDefaultRole(models.Model):
    """For set default role case create user from facebook. (Using application name to map.)"""
    name = models.CharField(max_length=20, unique=True)
    roles = models.ManyToManyField(Role, blank=True)

    objects = ApplicationDefaultRoleQueryset.as_manager()

    class Meta:
        verbose_name = 'Application Default Role'
        verbose_name_plural = 'Application Default Roles'
        ordering = ('id',)

    def __str__(self):
        return '[%s] %s - %s' % (self.id, self.name, [role.name for role in self.roles.all()])

    def apply_role_to_user(self, user):
        with transaction.atomic():
            for role in self.roles.exclude(id__in=list(user.roles.all().values_list('id', flat=True))):
                logger.debug('add role %s to user %s' % (role.name, user))
                user.roles.add(role)

    def is_has_role(self):
        return self.roles.all().exists()
    is_has_role.boolean = True


class RoleGroupQuerySet(models.QuerySet):
    def filter_code_role(self, code: str, role: Role):
        return self.filter(code=code, roles=role)


class RoleGroup(models.Model):
    """Group of role for custom check some permission and user can manually manage role in group.
    e.g. role = [reg_manager, admin] can view secret document
    (secret document is field and it's not appeared in permission system.)"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    roles = models.ManyToManyField(Role, blank=True)

    objects = RoleGroupQuerySet.as_manager()

    class Meta:
        verbose_name = 'Role Group'
        verbose_name_plural = verbose_name

    @classmethod
    def is_in_role_group(cls, code: str, role: Role) -> bool:
        return cls.objects.filter_code_role(code, role).exists()
