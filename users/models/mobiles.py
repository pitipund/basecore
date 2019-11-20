import importlib
import string
import random
import logging

from datetime import timedelta
from typing import Union

from allauth.account.models import EmailAddress, EmailConfirmation, EmailConfirmationHMAC
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from constance import config
from rest_framework.authtoken.models import Token
from allauth.account import app_settings as account_settings
from fcm_django.fcm import fcm_send_bulk_message, fcm_send_message, fcm_send_single_device_data_message

from his.framework.models import EnumField
from his.framework.utils import LabeledIntEnum
from ..settings import FCM_DJANGO_SETTINGS as SETTINGS

from .base import User

logger = logging.getLogger(__name__)

__all__ = ['UserOTP', 'APIToken', 'MobileDevice', 'MobileDeviceSetting', 'UserFCMToken']

OTP_BACKEND = getattr(settings, "OTP_BACKEND", None)
if OTP_BACKEND:
    mod_name, class_name = OTP_BACKEND.rsplit('.', 1)
    mod = importlib.import_module(mod_name)
    OTPService = getattr(mod, class_name)
    otp_service = OTPService()
else:
    otp_service = None


class UserOTPQuery(models.QuerySet):

    def filter_valid(self):
        return self.filter(expired_at__gt=timezone.now(), is_used=False)

    def clear_expired_otp(self):
        return self.filter(Q(expired_at__lt=timezone.now()) | Q(is_used=True)).delete()

    def set_used(self):
        return self.update(is_used=True)


class UserOTPManager(models.Manager):

    def create_user_otp(self, user: User, email_key: str = None) -> 'UserOTP':
        ref = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for __ in range(4))
        password = ''.join(random.SystemRandom().choice(string.digits) for __ in range(6))
        if email_key:
            expired_at = timezone.now() + timedelta(days=account_settings.EMAIL_CONFIRMATION_EXPIRE_DAYS)
        else:
            expired_at = timezone.now() + timedelta(minutes=config.users_OTP_TIMEOUT)
        obj = self.model(user=user,
                         ref=ref, password=password,
                         email_key=email_key,
                         expired_at=expired_at)
        obj.save(force_insert=True, using=self.db)
        if otp_service:
            otp_service.send_otp(user.username, _("Your OTP password is {} \nref. code: {}".format(password, ref)))
        return obj

    def get_user_otp_with_confirmation(self, user: User,
                                       confirmation: Union[EmailConfirmation, EmailConfirmationHMAC],
                                       email_address: EmailAddress = None):
        if not email_address:
            email_address, __ = EmailAddress.objects.get_or_create(user=user, email=user.email)
        otps = self.filter_valid().filter(user=user, email_key__isnull=False).order_by('-id')
        ret_otp = None
        for otp in otps:
            if confirmation.from_key(otp.email_key).email_address == email_address:
                return otp
        if not ret_otp:
            raise ObjectDoesNotExist('UserOTP with this confirmation not found')


class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    ref = models.CharField(verbose_name=_('reference'), max_length=4)
    password = models.CharField(verbose_name=_('Password'), max_length=6)
    expired_at = models.DateTimeField(verbose_name=_('expired at'), db_index=True)
    is_used = models.BooleanField(default=False)
    email_key = models.CharField(verbose_name=_('OTP email matching key'),
                                 max_length=64,  # EmailConfirmation key max length
                                 null=True, blank=True, db_index=True)

    objects = UserOTPManager.from_queryset(UserOTPQuery)()

    class Meta:
        verbose_name = _('user OTP')
        verbose_name_plural = _('user OTPs')
        unique_together = ('user', 'ref', 'password')

    def __str__(self):
        return '<OTP {}-{}>'.format(self.ref, self.password)

    def is_not_expired(self):
        return not self.is_used and timezone.now() < self.expired_at
    is_not_expired.boolean = True

    def set_used(self, value=True):
        self.is_used = value
        self.save()


class APIToken(Token):
    """
    Do not create APIToken directly
    Use MobileDevice.get_token() to create this
    """
    # allow user to have multiple keys for multiple devices
    user = models.ForeignKey(
        User, related_name='auth_tokens',
        on_delete=models.CASCADE, verbose_name=_("User")
    )

    class Meta:
        verbose_name = _('API token')
        verbose_name_plural = _('API tokens')


class FCMDeviceQuerySet(models.QuerySet):
    def send_message(
            self,
            title=None,
            body=None,
            icon=None,
            data=None,
            sound=None,
            badge=None,
            api_key=None,
            **kwargs):
        """
        Send notification for all active devices in queryset and deactivate if
        DELETE_INACTIVE_DEVICES setting is set to True.
        """
        if self:
            registration_ids = list(self.filter(active=True).values_list(
                'device_token',
                flat=True
            ))
            if not registration_ids:
                return [{'failure': len(self), 'success': 0}]

            result = fcm_send_bulk_message(
                registration_ids=registration_ids,
                title=title,
                body=body,
                icon=icon,
                data=data,
                sound=sound,
                badge=badge,
                api_key=api_key,
                **kwargs
            )

            self._deactivate_devices_with_error_results(
                registration_ids,
                result['results']
            )
            return result

    def _deactivate_devices_with_error_results(self, registration_ids, results):
        for (index, item) in enumerate(results):
            if 'error' in item:
                error_list = ['MissingRegistration', 'MismatchSenderId', 'InvalidRegistration', 'NotRegistered']
                if item['error'] in error_list:
                    print(item['error'])
                    registration_id = registration_ids[index]
                    print(registration_id)
                    self.filter(device_token=registration_id).update(
                        active=False
                    )
                    self._delete_inactive_devices_if_requested(registration_id)

    def _delete_inactive_devices_if_requested(self, registration_id):
        if SETTINGS["DELETE_INACTIVE_DEVICES"]:
            self.filter(device_token=registration_id).delete()


class MobileDeviceSetting(models.Model):
    device = models.OneToOneField('MobileDevice', on_delete=models.CASCADE,
                                  related_name='device_setting',
                                  blank=True)
    appointment = models.BooleanField(default=True)
    chat = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('device setting')
        verbose_name_plural = _('devices setting')

    def __str__(self):
        return '[Setting]'


class MobileDevice(models.Model):

    class Type(LabeledIntEnum):
        etc = 0, 'etc'
        browser = 1, 'browser'
        android = 2, 'android'
        ios = 3, 'ios'

    user = models.ForeignKey(User, models.CASCADE, related_name='mobile_devices')
    device_id = models.CharField(max_length=64, blank=True, default='')
    device_type = EnumField(Type, default=0, db_index=True)
    device_name = models.CharField(max_length=64, blank=True, default='')
    device_token = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    is_authorized = models.BooleanField(default=False)

    api_token = models.OneToOneField(APIToken, models.SET_NULL, null=True, blank=True,
                                     related_name='device', related_query_name='device')
    objects = FCMDeviceQuerySet.as_manager()

    active = models.BooleanField(_("Is active"), default=True,
                                 help_text=_("Inactive devices will not be sent notifications"))

    class Meta:
        verbose_name = _('device')
        verbose_name_plural = _('devices')
        unique_together = ('user', 'device_id', 'device_type')

    def __str__(self):
        return '[%s] %s (%s)' % (self.device_type.label, self.device_name, self.device_token[:8])

    def get_token(self) -> APIToken:
        """
        get Token and activate device in process
        """
        if self.api_token:
            return self.api_token
        self.api_token = APIToken.objects.create(user_id=self.user_id)
        self.save()
        return self.api_token

    def is_active(self):
        return self.api_token is not None
    is_active.boolean = True

    def deactivate(self):
        self.api_token.delete()
        # although, in database, api_token field is already set to null,
        # this will keep is_activated() do the work correctly
        self.api_token = None

    def deauthorize(self):
        self.api_token.delete()
        self.api_token = None
        self.is_authorized = False
        self.save()

    def send_message(
            self,
            title=None,
            body=None,
            icon=None,
            data=None,
            sound=None,
            badge=None,
            api_key=None,
            send_notification=True,
            send_data_message=False,
            **kwargs):
        """
        Send single notification message.
        """

        if send_data_message:
            fcm_send_single_device_data_message(
                registration_id=str(self.device_token),
                data_message=data,
                api_key=api_key,
                **kwargs
            )

        if send_notification:
            result = fcm_send_message(
                registration_id=str(self.device_token),
                title=title,
                body=body,
                icon=icon,
                data=data,
                sound=sound,
                badge=badge,
                api_key=api_key,
                **kwargs
            )
            self._deactivate_device_on_error_result(result)
            return result

    def _deactivate_device_on_error_result(self, result):
        device = MobileDevice.objects.filter(device_token=self.device_token)
        if 'error' in result['results'][0]:
            print('send message user %s device %s error' % (self.user.username, self.device_name))
            print(result['results'])
            error_list = ['MissingRegistration', 'MismatchSenderId', 'InvalidRegistration', 'NotRegistered']
            if result['results'][0]['error'] in error_list:
                device.update(active=False)
                self._delete_inactive_device_if_requested(device)

    @staticmethod
    def _delete_inactive_device_if_requested(device):
        if SETTINGS["DELETE_INACTIVE_DEVICES"]:
            device.delete()


class UserFCMToken(models.Model):
    user = models.ForeignKey(User, related_name='user_fcm_tokens')
    fcm_token = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')

    class Meta:
        verbose_name = 'User FCM Token'

    def __str__(self):
        return '%s (active=%s)' % (self.user.get_full_name(), self.active)
