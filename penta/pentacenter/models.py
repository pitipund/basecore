# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

from his.penta.curator.models import CuratorChannel, CuratorSupport
from his.users.models import User as HisUser

User = get_user_model()


class App(models.Model):
    name = models.CharField(max_length=20, blank=True, default='', unique=True)

    class Meta:
        app_label = 'pentacenter'

    def __unicode__(self):
        return self.name


class Device(models.Model):
    device_type = models.CharField(max_length=20, null=True, blank=True, default='')
    unique_id = models.CharField(max_length=50, null=True, blank=True, default='')
    user = models.ForeignKey(User, models.CASCADE, related_name='devices')
    device_token = models.CharField(max_length=200, null=True, blank=True, default='', db_index=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    app = models.ForeignKey(App, null=True, default=None, db_index=True)

    class Meta:
        app_label = 'pentacenter'

    def __unicode__(self):
        return "%s 's %s: %s" % (self.device_type, self.user.username,
                                 self.device_token[:8])

    def __str__(self):
        return "%s 's %s: %s" % (self.device_type, self.user.username,
                                 self.device_token[:8])


# Create your models here.
class PentaCenterChannelLog(models.Model):
    live_channel = models.ForeignKey(CuratorSupport, null=True, blank=True, default=None, db_index=True)
    url = models.URLField(blank=True, null=True)
    watch_at = models.DateTimeField(db_index=True, auto_now_add=True)
    duration_second = models.IntegerField(blank=True, null=True, default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    device = models.ForeignKey(Device, null=True, blank=True, default=None, db_index=True)

    class Meta:
        app_label = 'pentacenter'
        get_latest_by = 'create_at'
        ordering = ["-watch_at"]


class UserChannelInterest(models.Model):
    SOURCE_CHOICES = (('livewatch', 'livewatch'),
                      ('follow', 'follow'),
                      ('channelwatch', 'channelwatch'),
                      ('', ''))
    channel = models.ForeignKey(CuratorChannel, null=True, blank=True, default=None, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    calculated_at = models.DateTimeField(db_index=True, auto_now_add=True)
    source = models.CharField(choices=SOURCE_CHOICES, max_length=15, null=True, blank=True, default='')

    class Meta:
        app_label = 'pentacenter'
        unique_together = ('channel', 'user', 'source')


class ChannelOnairTime(models.Model):
    channel = models.ForeignKey(CuratorChannel, null=True, blank=True, default=None, db_index=True)
    live_source = models.ForeignKey(CuratorSupport, null=True, blank=True, default=None, db_index=True)
    time = models.CharField(max_length=5, db_index=True)  # HH:MM
    weekday = models.IntegerField(db_index=True)  # 0 = Monday , 6 = Sunday

    class Meta:
        app_label = 'pentacenter'
        unique_together = ('live_source', 'weekday', 'time')


# Base Channel

class BaseChannel(models.Model):
    application_name = 'generic'

    application = models.CharField(max_length=100, blank=True, default='')
    owner = models.ForeignKey(User, models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'pentacenter'

    def __str__(self):
        return self.owner.username if self.owner else 'BaseChanel: %s' % (str(self.id),)

    def save(self, *args, **kwargs):
        if not self.application:
            self.application = self.application_name
        super(BaseChannel, self).save(*args, **kwargs)

    def _convert_user_models_to_id_list(self, users):
        if isinstance(users, (int,)) or isinstance(users, User):
            users = [users]
        if users:
            if isinstance(users[0], User):
                tmp = []
                for user in users:
                    tmp.append(user.id)
                users = tmp
            for user in users:
                assert isinstance(user, (int,))
        return list(users) if users is not None else []

    def send_notification(self, title, message, extra_dict=None,
                          only_users=None, except_users=None,
                          force_send_user=False, addition_users=None):
        """
        :param title:
        :param message:
        :param extra_dict:
        :param only_users: list of `User` or User `id` to send notifications (replace default user list)
        :param except_users: list of `User` or User `id` to exclude from default list
        :param force_send_user: if True this function will ignore UserSubscription and
                            directly use users from `only_users`.
                            `Notification` will not be created for Users in `only_users`
                            who didn't subscribe to `channels`. Cannot be used with `except_users`
        :param addition_users: list of user ids, tell this function to also send
                               notifications to users in `addition_users`.
                               `Notification` will not be created for Users in `addition_users`.
                               *Duplicate notification may be occur if you specific user id in
                               `only_users` and `addition_users` simultaneously.
        """
        from his.penta.pentacenter.tasks import send_notification as penta_send_notification
        only_users = self._convert_user_models_to_id_list(only_users)
        except_users = self._convert_user_models_to_id_list(except_users)
        addition_users = self._convert_user_models_to_id_list(addition_users)
        penta_send_notification.apply_async([
            self.id, title, message, extra_dict, only_users, except_users, force_send_user, addition_users
        ])


class BaseUserSubscription(models.Model):
    channel = models.ForeignKey(BaseChannel, models.CASCADE,
                                related_name='subscriptions')
    subscribed_user = models.ForeignKey(HisUser, related_name='channel_subscriptions')
    application = models.CharField(max_length=100, blank=True, default='')
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'pentacenter'

    def save(self, *args, **kwargs):
        if not self.application:
            self.application = self.channel.application
        super(BaseUserSubscription, self).save(*args, **kwargs)


class NotificationBroadcastPayload(models.Model):
    """
    For efficiency, you should use this Model when send
    a notification to multiple user
    """
    payload = models.TextField()

    class Meta:
        app_label = 'pentacenter'


class NotificationQuerySet(QuerySet):

    def update_read_notification(self, device=None):
        # TODO Implement ME. Don't forget to update device notification status too.
        pass


class Notification(models.Model):
    POLICY_URGENT = 'U'
    POLICY_ENSURE = 'E'
    POLICY_NO_REPEAT = 'N'
    POLICY_NONE = '-'

    # override this property
    default_policy = POLICY_NO_REPEAT

    CHOICES_POLICY = (
        (POLICY_URGENT, 'Urgent'),
        (POLICY_ENSURE, 'Ensure'),
        (POLICY_NO_REPEAT, 'No Repeat'),
        (POLICY_NONE, 'None')
    )

    user = models.ForeignKey(User, models.CASCADE)  # redundant but for performance
    subscription = models.ForeignKey(BaseUserSubscription, models.CASCADE)

    application = models.CharField(max_length=100, blank=True, default='')
    policy = models.CharField(max_length=1, choices=CHOICES_POLICY, default='-')

    payload = models.TextField(blank=True, default='')  # Message for one user
    broadcast_payload = models.ForeignKey(NotificationBroadcastPayload, models.SET_NULL,
                                          null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        app_label = 'pentacenter'

    def save(self, *args, **kwargs):
        if not self.application:
            self.application = self.subscription.application
        if not self.policy:
            self.policy = self.default_policy
        if not self.user:
            self.user_id = self.subscription.user_id
        super(Notification, self).save(*args, **kwargs)

    def get_payload(self):
        if self.payload:
            return self.payload
        return self.broadcast_payload.payload

    @transaction.atomic
    def mark_received(self):
        if self.received_at is None:
            self.received_at = timezone.now()
            self.save()


class DeviceNotificationStatus(models.Model):
    device = models.ForeignKey(Device, models.CASCADE, related_name='notifications')
    notification = models.ForeignKey(Notification, models.CASCADE,
                                     related_name='device_notifications')

    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'pentacenter'
        unique_together = ('device', 'notification')

    @transaction.atomic
    def mark_received(self):
        now = timezone.now()
        if self.notification.received_at is None:
            self.notification.received_at = now
            self.save()
        self.received_at = now
        self.save()
