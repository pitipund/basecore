from __future__ import unicode_literals

import os
from typing import Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q
from django.conf import settings
from jsonfield import JSONField

from his.framework.models import BaseActionLog, LabeledIntEnum, StatableModel, EnumField
from his.penta.appointment.models import Client, ClientServiceSlot, ProviderAssign, SwapShiftBroadcast, SwapShiftRequest
from his.penta.curator.models import CuratorChannel
from his.penta.pentacenter.models import BaseChannel, BaseUserSubscription, Notification
from his.penta.showtime.utils import UploadToDir
from his.users.models import User as HisUser

User = get_user_model()


class ChatChannelQuerySet(models.QuerySet):
    def get_or_create_private_channel(self, user1, user2):
        queryset_channels_user1 = self.filter(is_private=True, subscriptions__subscribed_user=user1)
        queryset_channels_user2 = self.filter(is_private=True, subscriptions__subscribed_user=user2)

        # queryset = queryset_channels_user1.intersection(queryset_channels_user2)  not support in mysql
        intersect = set(queryset_channels_user1) & set(queryset_channels_user2)
        if len(intersect) > 0:
            return intersect.pop(), False

        chat_channel = ChatChannel()
        chat_channel.name = 'Private Channel for User %s and %s' % (user1.username, user2.username)
        chat_channel.is_private = True
        chat_channel.save()

        # auto create user chat subscription
        user_chat_subscription = UserChatSubscription()
        user_chat_subscription.channel = chat_channel
        user_chat_subscription.subscribed_user = user1
        user_chat_subscription.editable = True
        user_chat_subscription.action = UserChatSubscription.ACTION.CREATE_GROUP
        user_chat_subscription.user = user1
        user_chat_subscription.save()

        user_chat_subscription = UserChatSubscription()
        user_chat_subscription.channel = chat_channel
        user_chat_subscription.subscribed_user = user2
        user_chat_subscription.editable = True
        user_chat_subscription.action = UserChatSubscription.ACTION.CREATE_GROUP
        user_chat_subscription.user = user2
        user_chat_subscription.save()

        return chat_channel, True


class ChatChannel(BaseChannel):
    application_name = 'sqool'

    client = models.ForeignKey(Client, blank=True, null=True, related_name='client_chat_channel')
    name = models.CharField(max_length=200, blank=True, null=False, default='')
    channel = models.ForeignKey(CuratorChannel, models.SET_NULL, blank=True, null=True)
    icon = models.ImageField(upload_to=os.path.join(settings.SQOOL_PATH), null=True, blank=True)
    icon_url = models.URLField(null=True, blank=True)

    sqool_group = models.ForeignKey(Group, models.SET_NULL, null=True, blank=True)
    is_private = models.BooleanField(default=False)

    latest_message = models.ForeignKey('Message', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    fb_is_support = models.BooleanField(default=False, db_index=True,
                                        help_text='Is customer support inbox from Facebook')
    fb_page_name = models.CharField(max_length=64, blank=True, default='', db_index=True)
    fb_recipient = models.CharField(max_length=32, blank=True, default='', db_index=True)
    fb_inbox_id = models.CharField(max_length=32, blank=True, default='', db_index=True)
    fb_latest_message_id = models.CharField(max_length=64, blank=True, default='')
    fb_unread_count = models.IntegerField(default=0)

    objects = ChatChannelQuerySet.as_manager()

    def real_icon(self):
        if self.icon:
            return self.icon.url
        if self.icon_url:
            return self.icon_url
        return os.path.join(settings.MEDIA_URL, settings.THUMBNAIL_IM_PATH, 'no_content.png')

    def __str__(self):
        return '[%s] %s' % (self.id, self.name)

    def __unicode__(self):
        return self.name

    def bump_latest_message(self, last_message=None):
        if not last_message:
            last_message = self.messages.first()
        if last_message.fb_message_id:
            self.fb_latest_message_id = last_message.fb_message_id
        self.latest_message = last_message
        self.updated_at = last_message.send_at
        self.save()

    def get_name(self, user=None):
        if self.is_private and user is not None:
            user_chat_subscriptions = UserChatSubscription.objects.filter(channel=self).exclude(
                subscribed_user=user)
            user_chat_subscription = user_chat_subscriptions.first()
            if user_chat_subscription:
                return user_chat_subscription.subscribed_user.get_full_name()
        return self.name


class Message(models.Model):
    upload_dir = UploadToDir(settings.SQOOL_PATH)
    PAYLOAD_VERSION = 1

    CONTENT_TYPE_TEXT = 'text'
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'
    CONTENT_TYPE_FILE = 'file'
    CONTENT_TYPE_SWAP = 'swap'
    CONTENT_TYPE_ACTIVITY = 'activity'

    CONTENT_CHOICES = (
        (CONTENT_TYPE_TEXT, "text"),
        (CONTENT_TYPE_IMAGE, "image"),
        (CONTENT_TYPE_VIDEO, "video"),
        (CONTENT_TYPE_FILE, "file"),
        (CONTENT_TYPE_SWAP, "swap"),
        (CONTENT_TYPE_ACTIVITY, 'activity')
    )

    author = models.ForeignKey(HisUser, models.CASCADE, null=True, blank=True)
    channel = models.ForeignKey(ChatChannel, models.CASCADE, related_name='messages')
    content = models.TextField()
    content_type = models.CharField(max_length=10, choices=CONTENT_CHOICES)

    content_file = models.FileField("Content file", upload_to=upload_dir,
                                    null=True, blank=True, max_length=200)  # File name is too long
    content_url = models.URLField("Content URL", null=True, blank=True, max_length=400)
    content_thumbnail = models.ImageField('Thumbnail', upload_to=upload_dir,
                                          null=True, blank=True, max_length=200)
    content_thumbnail_url = models.URLField('Thumbnail URL', null=True, blank=True, max_length=400)
    content_payload = JSONField(default={}, blank=True)

    user_read_count = models.IntegerField(default=0)  # going to be deprecated

    send_at = models.DateTimeField(auto_now_add=True, db_index=True)
    edit_at = models.DateTimeField(auto_now_add=True)

    fb_message_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)

    class Meta:
        ordering = ('-send_at',)  # newest first
        get_latest_by = '-send_at'

    def __str__(self):
        return '[%s] %s (%s)' % (self.id, self.content, self.content_type)

    def image_(self):
        if self.content_file:
            return '<a href="{0}"><img src="{0}"></a>'.format(self.content_file.url)
        return ''

    def image_tag(self):
        if self.content_file:
            return u'<img src="%s" width=100 />' % self.content_file.url
        return ''

    def set_content_payload(self, data: Dict):
        if 'version' not in self.content_payload:
            self.content_payload['version'] = Message.PAYLOAD_VERSION
        self.content_payload['data'] = data

    image_.allow_tags = True
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True


class UserChatSubscription(BaseUserSubscription, StatableModel):
    SUBSCRIPTION_MAIN = 'subscribe_main'
    SUBSCRIPTION_HELP = 'subscribe_help'
    SUBSCRIPTION_OWNER = 'channel_owner'
    SUBSCRIPTION_ADMIN = 'channel_admin'

    SUBSCRIPTION_CHOICES = (
        (SUBSCRIPTION_MAIN, "subscribe_main"),
        (SUBSCRIPTION_HELP, "subscribe_help"),
        (SUBSCRIPTION_OWNER, "channel_owner"),
        (SUBSCRIPTION_ADMIN, "channel_admin"),
    )

    class ACTION(LabeledIntEnum):
        REQUEST = 1
        ACCEPT = 2

        EDIT = 5

        REJECT = 10
        LEAVE = 11
        LEAVE_AND_MOVE = 12

        CREATE_GROUP = 20

    class STATUS(LabeledIntEnum):
        REQUESTED = 1, 'ส่งคำขอ'
        ACCEPTED = 2, 'ยืนยัน'

        CANCELED = 10, 'ยกเลิก'

    TRANSITION = [
        (None, ACTION.CREATE_GROUP, STATUS.ACCEPTED),
        (None, ACTION.REQUEST, STATUS.REQUESTED),
        (STATUS.REQUESTED, ACTION.EDIT, STATUS.REQUESTED),
        (STATUS.REQUESTED, ACTION.ACCEPT, STATUS.ACCEPTED),
        (STATUS.REQUESTED, ACTION.REJECT, STATUS.CANCELED),

        (STATUS.ACCEPTED, ACTION.EDIT, STATUS.ACCEPTED),
        (STATUS.ACCEPTED, ACTION.LEAVE, STATUS.CANCELED),
        (STATUS.ACCEPTED, ACTION.LEAVE_AND_MOVE, STATUS.CANCELED)
    ]

    editable = models.BooleanField(default=False, db_index=True)
    map_schedule = models.BooleanField(default=False)
    schedule_color = models.CharField(blank=True, null=True, max_length=10)

    latest_read_message = models.ForeignKey(Message, models.SET_NULL, null=True)
    latest_read_time = models.DateTimeField(auto_now_add=True)  # avoid MySQL datetime error

    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES)

    def get_unread_messages_count(self):
        if self.latest_read_message_id:
            return Message.objects.filter(channel_id=self.channel_id,
                                          id__gt=self.latest_read_message_id).count()
        return Message.objects.filter(channel_id=self.channel_id).count()

    def common_leave_group(self, user_sub_action, client: Client, user: User, action_log: str):
        # leave
        self.editable = False
        self.map_schedule = False
        self.action = user_sub_action
        self.user = user
        self.save()

        pa_for_cancel = ProviderAssign.objects \
            .filter(client_service_slot__client=client,
                    provider_available_slots__provider=user.employee.provider.last(),
                    status__in=[ProviderAssign.STATUS.DRAFTED, ProviderAssign.STATUS.CONFIRMED])
        pa_for_cancel_id = pa_for_cancel.values_list("id", flat=True)

        swap_shift_broadcasts = SwapShiftBroadcast.objects \
            .filter(source_provider_assign__in=pa_for_cancel_id, status=SwapShiftBroadcast.STATUS.REQUESTED)

        swap_shift_requests = SwapShiftRequest.objects \
            .filter(Q(source_assign_slot__in=pa_for_cancel_id) | Q(destination_assign_slot__in=pa_for_cancel_id)) \
            .filter(status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])

        # reject broadcast
        for ssb in swap_shift_broadcasts:
            ssb.isnurse_cancel(user=user, action_log=action_log)

        # reject offer
        for ssr in swap_shift_requests:
            ssr.common_reject(user=user, action_log=action_log)

        # cancel Provider Assign
        for pa in pa_for_cancel:
            pa.action = ProviderAssign.ACTION.CANCEL
            pa.user = user
            pa.save()

    def leave_group(self, user: User):
        self.common_leave_group(user_sub_action=UserChatSubscription.ACTION.LEAVE,
                                client=self.channel.chatchannel.client,
                                user=user,
                                action_log="Leave group.")

    def leave_and_move_schedule(self, move_to: ChatChannel, user: User):
        # --------- leave
        self.common_leave_group(user_sub_action=UserChatSubscription.ACTION.LEAVE_AND_MOVE,
                                client=move_to.client,
                                user=user,
                                action_log="Move schedule.")

        # --------- Provider Assign ยัายไปที่ใหม่
        pa_for_move = ProviderAssign.objects \
            .filter(client_service_slot__client=self.channel.chatchannel.client,
                    provider_available_slots__provider=user.employee.provider.last(),
                    status__in=[ProviderAssign.STATUS.DRAFTED, ProviderAssign.STATUS.CONFIRMED])
        pa_for_move_id = pa_for_move.values_list("id", flat=True)
        client_service_slots = ClientServiceSlot.objects \
            .filter(client=move_to.client,
                    start_slot__in=pa_for_move.values_list("client_service_slot__start_slot", flat=True),
                    end_slot__in=pa_for_move.values_list("client_service_slot__end_slot", flat=True),
                    active=True)
        for pa in pa_for_move:
            css = list(filter(lambda css: css.start_slot == pa.client_service_slot.start_slot, client_service_slots))
            if css:
                pa.client_service_slot = css[0]
                pa.action = ProviderAssign.ACTION.EDIT
                pa.user = user
                pa.save()

        # reject offer
        swap_shift_requests = SwapShiftRequest.objects \
            .filter(Q(source_assign_slot__in=pa_for_move_id) | Q(destination_assign_slot__in=pa_for_move_id)) \
            .filter(status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])
        for ssr in swap_shift_requests:
            ssr.common_reject(user=user, action_log="Leave and Move.")

        # reject broadcast
        swap_shift_broadcasts = SwapShiftBroadcast.objects \
            .filter(source_provider_assign__in=pa_for_move_id, status=SwapShiftBroadcast.STATUS.REQUESTED)
        for ssb in swap_shift_broadcasts:
            ssb.isnurse_cancel(user=user)


class UserChatSubscriptionActionLog(BaseActionLog(UserChatSubscription)):
    note = models.TextField(null=True, blank=True)


class MessageNotification(Notification):
    default_policy = Notification.POLICY_NO_REPEAT

    message = models.ForeignKey(Message, models.CASCADE, related_name='notification')


class ReportMessage(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    message = models.ForeignKey(Message, models.CASCADE)
    report_at = models.DateTimeField(auto_now_add=True)
    remark = models.TextField(default="")


class BlockUserChannel(models.Model):
    user = models.ForeignKey(User, related_name="blocker_user")
    blocked_user = models.ForeignKey(User, related_name="blocked_user")
    channel = models.ForeignKey(ChatChannel, models.CASCADE)

    block_at = models.DateTimeField(auto_now_add=True)


class FacebookUserCache(models.Model):
    facebook_id = models.CharField(max_length=64, unique=True)
    full_name = models.CharField(max_length=200, null=False, blank=True, default='')
    image_url = models.URLField(max_length=400, null=True, blank=True)


class UserConnectionQuerySet(models.QuerySet):
    def get_user_connection_from_user(self, user: User):
        user_connection = UserConnection.objects.filter(user=user, active=True).first()
        if user_connection is None:
            user_connection = UserConnection()
            user_connection.user = user
            user_connection.created_by = user
            user_connection.save()
        return user_connection


class UserConnection(models.Model):
    """
        Relation between user. e.g.
        - user A has friend ( B, C )
            - user = <user A>
            - connections = [ <user B>, <user C> ]
        """
    user = models.ForeignKey(HisUser, related_name='+')
    connections = models.ManyToManyField(HisUser, through='UserConnectionRelation',
                                         through_fields=('user_connection', 'connected_user'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(HisUser, null=True, blank=True, related_name='+')
    edited_at = models.DateTimeField(auto_now=True)
    edited_by = models.ForeignKey(HisUser, null=True, blank=True, related_name='+')
    active = models.BooleanField(default=True)

    objects = UserConnectionQuerySet.as_manager()

    class Meta:
        verbose_name = 'User Connection'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '[%s] %s (Friend: %s)' % (self.id, self.user.get_full_name(), self.connections.count())

    def add_connection(self, friend_user: HisUser, created_user: HisUser,
                       connection_type=None):
        connection_type = UserConnectionRelation.CONNECTION_TYPE.FRIEND if connection_type is None else connection_type
        user_connection_relation = UserConnectionRelation.objects.filter(
            user_connection=self,
            connected_user=friend_user,
            connection_type=connection_type,
            active=True
        ).first()
        if user_connection_relation:
            return False
        user_connection_relation = UserConnectionRelation()
        user_connection_relation.user_connection = self
        user_connection_relation.connected_user = friend_user
        user_connection_relation.connection_type = connection_type
        user_connection_relation.created_by = created_user
        user_connection_relation.save()
        return True


class UserConnectionRelation(models.Model):
    class CONNECTION_TYPE(LabeledIntEnum):
        FRIEND = 1, 'Friend'
        FOLLOW = 2, 'Follow'  # In the future.

    user_connection = models.ForeignKey(UserConnection)
    connected_user = models.ForeignKey(HisUser)
    connection_type = EnumField(CONNECTION_TYPE, default=CONNECTION_TYPE.FRIEND)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(HisUser, null=True, blank=True, related_name='+')
    edited_at = models.DateTimeField(auto_now=True)
    edited_by = models.ForeignKey(HisUser, null=True, blank=True, related_name='+')
    active = models.BooleanField(default=True)
