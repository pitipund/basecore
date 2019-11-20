from __future__ import unicode_literals, absolute_import
from datetime import datetime

import logging
import re
from typing import Optional

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError, ImproperlyConfigured, ObjectDoesNotExist
from django.core import signing
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import PermissionDenied

from his.framework.models.mixins import ExtraFieldModelMixin
from his.framework.utils import LabeledIntEnum
from his.users.models.utils import UploadToDir
from his.framework.validators import cid_passport_validator
from .organizations import Employee
from .roles import Role, HISPermission, ApplicationDefaultRole
from .utils import user_signer, base64_encode, base64_decode, enum_choices
from django.db import models, IntegrityError, transaction


logger = logging.getLogger(__name__)


class UserQuerySet(models.QuerySet):
    def pharmacists(self):
        # TODO(natt): filter with role effective date
        return self.filter(roles__type=Role.TYPE.PHARMACIST)

    def registered_nurses(self):
        # TODO(natt): filter with role effective date
        return self.filter(roles__type=Role.TYPE.REGISTERED_NURSE)

    def doctors(self):
        # TODO(natt): filter with role effective date
        return self.filter(roles__type=Role.TYPE.DOCTOR)


class ActiveUserManager(UserManager):
    """We need to implement duplicate methods here to allow
    calling this as manager method and queryset methods with default filter

    .active_users.doctors()  or
    .active_users.filter().doctors()
    """

    def get_queryset(self) -> UserQuerySet:
        return UserQuerySet(self.model, using=self._db).filter(is_active=True)

    def pharmacists(self):
        return self.get_queryset().pharmacists()

    def registered_nurses(self):
        return self.get_queryset().registered_nurses()

    def doctors(self):
        return self.get_queryset().doctors()

    def create_user_from_app(self, username: str, cid: str):
        if not username:
            raise ValidationError('The given username must be set')
        if not cid:
            raise ValidationError('The given cid must be set')
        if re.match('^\d{10,20}$', username) is None:
            raise ValidationError('invalid phone number')

        user = self.model(username=username, cid=cid)
        user.full_clean(exclude=['password'])
        user.save(using=self._db)

        return user

    # def create_superuser(self, username, password, **extra_fields):
    #     super(ActiveUserManager, self).create_superuser(username, '', password, **extra_fields)


class AllUserManager(UserManager):
    def get_system_user(self):
        """Get or create system user to use in automated tasks, e.g. set room status"""
        user, created = self.get_or_create(username='system', is_superuser=True)
        if created:
            user.set_unusable_password()
        return user

    def create_user_from_app(self, username: str, cid: str):
        if not username:
            raise ValidationError('The given username must be set')
        if not cid:
            raise ValidationError('The given cid must be set')
        if re.match('^\d{10,20}$', username) is None:
            raise ValidationError('invalid phone number')

        user = self.model(username=username, citizen_passport=cid)
        user.full_clean(exclude=['password'])
        user.save(using=self._db)

        return user

    def get_create_penta_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return self.create_user(username, None, None)


class UserProfileQuerySet(QuerySet):

    @transaction.atomic()
    def create(self, **kwargs):
        if 'PRX' in settings.DJANGO_INCLUDE_APPS:
            from his.apps.PRX.models import ProxyPatient
            kwargs.setdefault('patient', ProxyPatient.objects.create())
        return super(UserProfileQuerySet, self).create(**kwargs)


@python_2_unicode_compatible
class User(AbstractUser, ExtraFieldModelMixin):
    """
    Now we have Employee model, we should eventually remove 'employee_no' and use '.employee.code' instead
     (to normallize)
    """
    roles = models.ManyToManyField(Role, blank=True)
    employee = models.ForeignKey('Employee', blank=True, null=True, related_name='user_employee')
    pre_name = models.ForeignKey('core.Prename', related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
                                 verbose_name="คำนำหน้าชื่อ")

    image = models.ImageField(blank=True, null=True, upload_to="doctor/images/")
    email = models.EmailField(_('email address'), blank=True, null=True, unique=True,
                              error_messages={'unique': _('This email have already been used.')})
    citizen_passport = models.CharField(max_length=20, blank=True, null=True, validators=[cid_passport_validator],
                                        verbose_name=u'หมายเลขประชาชน/หนังสือเดินทาง')

    @property
    def cid(self):
        """backward compatible for his-proxy"""
        return self.citizen_passport

    @cid.setter
    def cid(self, value):
        """backward compatible for his-proxy"""
        self.citizen_passport = value

    active_users = ActiveUserManager()
    objects = AllUserManager()

    # STATE
    #
    # init                     enter additional info
    #   |                              ___
    #   v        enter password       |   v     all addition
    # Register -------------------> ADD_OPTION --------------> COMPLETED
    #

    class RegisterState(LabeledIntEnum):
        REGISTER = 1, _("register")
        ADD_OPTION = 2, _("add option")
        COMPLETE = 3, _("complete")

    state = models.IntegerField(_('state'), choices=enum_choices(RegisterState), default=RegisterState.REGISTER.value,
                                help_text=_('REGISTER after created account but didn\'t set password yet, '
                                            'ADD_OPTION after set password but no profile, '
                                            'COMPLETE after set profile.'))

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [EMAIL_FIELD]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        if self.email:
            send_mail(subject, message, from_email, [self.email], **kwargs)

    def save(self, *args, **kwargs):
        if self.email == '':
            site = 'localhost.local'
            all_sites = Site.objects.exclude(domain__in=['example.com', 'localhost', '127.0.0.1']).all()
            if all_sites:
                site = '.'.join(all_sites[0].domain.rsplit('.')[-2:])
            self.email = '{}@{}'.format(self.username, site)
        if self.state == self.RegisterState.REGISTER:
            if self.password:
                self.state = self.RegisterState.ADD_OPTION
        super(User, self).save(*args, **kwargs)
        if not self.roles.all().exists():
            application_default_role = ApplicationDefaultRole.objects.get_default()
            application_default_role.apply_role_to_user(self)

    def __str__(self):
        return self.username

    @classmethod
    def is_token_valid(cls, token):
        try:
            user_signer.unsign(token)
        except signing.BadSignature:
            return False
        return True

    @classmethod
    def untokenize(cls, token) -> Optional['User']:
        """
        :param token:
        :return: User object if token is valid, otherwise return None
        """
        if not cls.is_token_valid(token):
            return None
        if '.' in token:
            token, fullname = token.split('.', maxsplit=1)
            token = base64_decode(token)
        token = token if str(token).isdigit() else 0
        return cls.active_users.filter(pk=token).first()

    def tokenize(self):
        token = self.pk
        token = base64_encode(str(token))
        fullname = base64_encode(self.get_full_name())
        return user_signer.sign("%s.%s" % (token, fullname))

    def check_doctor_permission(self):
        try:
            return self.doctor
        except Exception:
            raise PermissionDenied('user "%s" is not doctor.' % (self.get_full_name()))

    def last_change_password(self) -> datetime:
        try:
            return self.passwordhistory_set.latest('created').created
        except PasswordHistory.DoesNotExist:
            return self.date_joined

    def has_role_type(self, role_type: Role.TYPE):
        return self.roles.filter(type=role_type).exists()

    def has_role_name(self, role_name: str):
        return self.roles.filter(name=role_name).exists()

    def has_action_permission(self, model_class: models.Model, action: str):
        """Check whether user has action permission or not

        :param model_class: Accept model class, e.g. Encounter, or model_label: core_Encounter
        :param action: Action name, e.g. 'PROCESS' or Encounter.ACTION.OPD_NEW
        :return: True/False whether user has permission or not
        """
        if hasattr(action, 'name'):
            action = action.name
        if isinstance(model_class, models.Model):
            model_class = model_class._meta.label

        all_actions = HISPermission.get_action_permission_codename(model_class, HISPermission.ALL_ACTION)
        if self.has_perm(all_actions):
            return True
        perm = HISPermission.get_action_permission_codename(model_class, action)
        return self.has_perm(perm)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        fullname = super().get_full_name()
        if self.pre_name and fullname:
            return "%s %s" % (self.pre_name.name, fullname)
        if fullname:
            return fullname
        return self.username

    def get_role_type_str(self):
        types = ['\'%s\'' % Role.TYPE(role_type).name for role_type in self.roles.all().values_list('type', flat=True)]
        return ', '.join(types)

    def set_employee_by_username(self):
        """Return true if found employee"""
        try:
            employee = Employee.objects.get_by_username(self.username)
        except Employee.DoesNotExist:
            return False
        self.employee = employee
        return True

    def has_management_permission(self) -> bool:
        """Return True if user is allowed to access /manage/ page"""
        for perm in self.get_all_permissions():
            if '.add_' in perm:
                return True
            if '.change_' in perm:
                return True
            if '.delete_' in perm:
                return True
        return False

    def get_fcm_tokens(self):
        return self.user_fcm_tokens.filter(active=True).values_list('fcm_token', flat=True)


class UserProfile(ExtraFieldModelMixin):

    class Gender(LabeledIntEnum):
        UNKNOWN = 0, 'Unknown'
        MALE = 1, 'Male'
        FEMALE = 2, 'Female'

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='profile', help_text=_('user'))

    pre_name = models.ForeignKey('core.Prename', null=True, blank=True,
                                 related_name='+', help_text=_('user\'s pre name'))

    gender = models.IntegerField(default=Gender.UNKNOWN.value, choices=enum_choices(Gender), blank=True,
                                 help_text=_('user\'s gender'))

    first_name = models.CharField(_('first name'), max_length=150, blank=True, default='',
                                  help_text=_('user\'s first name'))
    last_name = models.CharField(_('last name'), max_length=150, blank=True, default='',
                                 help_text=_('user\'s last name'))
    middle_name = models.CharField(_('middle name'), max_length=150, blank=True, default='',
                                   help_text=_('user\'s middle name'))
    dob = models.DateField(_('date of birth'), null=True, blank=True,
                           help_text=_('date of birth (YYYY-mm-dd)'))
    address = models.TextField(_('address'), blank=True, default='',
                               help_text=_('Address text'))
    phone_no = models.CharField(_('phone number'), max_length=20, blank=True, default='',
                                help_text=_('phone number'))
    ecp_first_name = models.CharField(_('emergency contact person\'s first name'),
                                      max_length=150, blank=True, default='',
                                      help_text=_('emergency contact person\'s first name'))
    ecp_last_name = models.CharField(_('emergency contact person\'s last name'),
                                     max_length=150, blank=True, default='',
                                     help_text=_('emergency contact person\'s last name'))
    ecp_phone_no = models.CharField(_('emergency contact person\'s phone number'),
                                    max_length=20, blank=True, default='',
                                    help_text=_('emergency contact person\'s phone number'))
    ecp_relationship = models.CharField(_('relationship with emergency contact person'),
                                        max_length=40, blank=True, default='',
                                        help_text=_('relationship with emergency contact person'))
    nationality = models.ForeignKey('core.Nationality', null=True)
    patient = models.ForeignKey('core.Patient', related_name='profiles', null=True)

    url_name = models.CharField(max_length=50, blank=True, null=True)

    upload_dir = UploadToDir(settings.PROFILE_PATH)

    image = models.ImageField(upload_to=upload_dir,
                              blank=True, null=True, verbose_name="Profile image")
    image_url = models.URLField(blank=True, null=True)
    isDisplay_email = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=255, null=False, blank=True, default='', db_index=True)
    facebook_access_token = models.TextField(null=False, blank=True, default='')
    facebook_expires = models.IntegerField(null=True, default=0)
    last_visit_follow_page = models.DateTimeField(null=True, blank=True)
    user_alias = models.CharField(max_length=255, blank=True)

    objects = UserProfileQuerySet.as_manager()

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def save(self, *args, **kwargs):
        # update username to field in UserProfile
        # if hasattr(self, config.PRX_USERNAME_FIELD):
        #     setattr(self, config.PRX_USERNAME_FIELD, self.user.username)
        #
        # if self.is_signed:
        #     # update UserProfile data from Patient when signed agreement
        #     for field in ['first_name', 'last_name', 'dob', 'address']:
        #         # 'phone_no' 'ecp_first_name', 'ecp_last_name', 'ecp_phone_no', 'ecp_relationship']:
        #         setattr(self, field, getattr(self.patient, field))
        #     if self.user:
        #         self.user.cid = self.patient.cid
        # else:
        #     # update Patient data from UserProfile when didn't signed agreement
        #     self.update_patient_data()

        if self.is_form_completed() and self.user.state == User.STATE_ADD_OPTION:
            self.user.state = User.STATE_COMPLETE
            self.user.save()

        # check duplicate user_alias ignore if empty string
        if self.user_alias != '':
            user_profiles = UserProfile.objects.filter(user_alias=self.user_alias)
            if self.id:
                user_profiles = user_profiles.exclude(id=self.id)
            if user_profiles.exists():
                raise ValidationError('user_alias %s is not unique.' % (self.user_alias,))

        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return '[User Profile] {}'.format(self.get_short_name())

    @property
    def is_signed(self):
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        return self.patient and self.patient.proxypatient.is_signed

    def is_form_completed(self):
        ignored_fields = ('patient_id', 'address')
        fields = self._meta.get_fields()
        for field in fields:
            if field.editable and field.attname not in ignored_fields:
                if not getattr(self, field.attname, None):
                    return False
        return True

    def get_short_name(self):
        return self.first_name

    def get_full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def get_age(self):
        return relativedelta(timezone.now().date(), self.dob).years

    def has_phr_access(self):
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        # TODO: fix this
        return self.patient.proxypatient.phr_id is not None
    has_phr_access.boolean = True

    def update_patient_data(self):
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        proxy_patient = self.patient.proxypatient
        proxy_patient.pre_name = self.pre_name
        proxy_patient.gender = self.convert_profile_gender_to_patient_gender(self.gender)
        # self.patient.nationality = self.nationality
        proxy_patient.first_name = self.first_name
        proxy_patient.last_name = self.last_name
        proxy_patient.birthdate = self.dob
        proxy_patient.address = self.address
        proxy_patient.phone_no = self.phone_no
        proxy_patient.ecp_first_name = self.ecp_first_name
        proxy_patient.ecp_last_name = self.ecp_last_name
        proxy_patient.ecp_phone_no = self.ecp_phone_no
        proxy_patient.ecp_relationship = self.ecp_relationship
        proxy_patient.extra = self.extra
        proxy_patient.save()

    def set_patient_hn(self, hn):
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        if not hn:
            raise ValueError('hn is not valid')
        from his.apps.PRX.models import ProxyPatient
        patients = ProxyPatient.objects.filter_hn(hn)
        if patients.exists():
            patient = patients.get()
            try:
                user_profile = UserProfile.objects.get(patient=patient)
                message = '%s (%s)' % (_('This patient has been already registered with another user.'),
                                       user_profile.user.username)
                raise ValidationError({
                    'patient': [message]
                })
            except ObjectDoesNotExist:
                pass
            from his.apps.PRX.tasks import merge_patient
            # Create patient of PHR and add to patient phr_id
            merge_patient(self.patient.id, patient.id)
            self.patient = patient
        else:
            self.patient.proxypatient.update_hn(hn=hn)
        self.save()
        return self

    def load_patient_profile(self):
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        proxy_patient = self.patient.proxypatient
        self.pre_name = proxy_patient.pre_name
        self.gender = self.convert_patient_gender_to_user_profile(proxy_patient.gender)
        self.first_name = proxy_patient.first_name
        self.last_name = proxy_patient.last_name
        self.dob = proxy_patient.birthdate
        self.address = proxy_patient.address
        self.extra = proxy_patient.extra
        # TODO proxy
        extra = proxy_patient.extra_data
        nationality = extra.get('nationality', '')
        self.nationality = self.map_nationality(nationality)
        # self.phone_no = proxy_patient.phone_no  # skip phone number
        # TODO: wait for load patient from dbms complete
        # self.ecp_first_name = self.patient.ecp_first_name
        # self.ecp_last_name = self.patient.ecp_last_name
        # self.ecp_phone_no = self.patient.ecp_phone_no
        # self.ecp_relationship = self.patient.ecp_relationship
        self.save()
        if proxy_patient.cid:
            self.user.cid = proxy_patient.cid
            self.user.save()

    def map_nationality(self, text: str):
        from his.core.models import Nationality
        try:
            if text.index('(') and text.index(')'):
                start = text.index('(') + 1
                end = text.index(')')
                word = text[start:end]
                return Nationality.objects.filter(name__contains=word).first()
        except Exception as e:
            print(e)

        nationalities = Nationality.objects.filter(name__contains=text)
        if nationalities.exists():
            nationality = nationalities.first()
            return nationality

    def convert_profile_gender_to_patient_gender(self, profile_patient: int) -> str:
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        from his.apps.PRX.models import ProxyPatient
        if profile_patient == self.Gender.MALE.value:
            return ProxyPatient.PATIENT_GENDER_CHOICES[0][0]
        elif profile_patient == self.Gender.FEMALE.value:
            return ProxyPatient.PATIENT_GENDER_CHOICES[1][0]
        else:
            return ProxyPatient.PATIENT_GENDER_CHOICES[2][0]

    def convert_patient_gender_to_user_profile(self, patient_gender: str) -> int:
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        from his.apps.PRX.models import ProxyPatient
        if patient_gender == ProxyPatient.PATIENT_GENDER_CHOICES[0][0]:
            return self.Gender.MALE.value
        elif patient_gender == ProxyPatient.PATIENT_GENDER_CHOICES[1][0]:
            return self.Gender.FEMALE.value
        else:
            return self.Gender.UNKNOWN.value

    def add_access_patient(self, hn, relation=''):
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        try:
            with transaction.atomic():
                from his.apps.PRX.models import UserAccessPatient, ProxyPatient
                UserAccessPatient.objects.create(profile=self,
                                                 patient=ProxyPatient.objects.get_or_create_by_hn(hn),
                                                 relation=relation)
        except IntegrityError as e:
            raise e

    def remove_access_patient(self, hn):
        """
        remove access to patient, throw ObjectDoesNotExist Exception if not found
        :param hn:
        :return:
        """
        if 'PRX' not in settings.DJANGO_INCLUDE_APPS:
            raise ImproperlyConfigured('PRX is not in INSTALLED_APPS')
        from his.apps.PRX.models import UserAccessPatient
        from his.apps.PRX.models import ProxyPatient
        user_acess = UserAccessPatient.objects.get(profile=self,
                                                   patient=ProxyPatient.objects.filter_hn(hn).get())
        user_acess.delete()


class PasswordHistory(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่เริ่มต้นบันทึก')
    password = models.CharField(max_length=128, help_text='Old encrypted password')
