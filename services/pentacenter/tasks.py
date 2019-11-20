# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from pyfcm import FCMNotification

import logging
import traceback
from celery import shared_task
from django.conf import settings
# from ios_apn import Pusher, key_file as key_file_production, cert_file_production
# from pentacenter.models import Device
from his.penta.pentacenter.ios_apn import get_pusher
from his.penta.pentacenter.models import BaseChannel, Device, BaseUserSubscription, NotificationBroadcastPayload, Notification, \
    DeviceNotificationStatus

logger = logging.getLogger(__name__)
User = get_user_model()
"""
Settings for push Notification

IOS_PRODUCTION_CERT = '/path/to/production/cert.pem'
IOS_DEVELOPMENT_CERT = '/path/to/development/cert.pem'
IOS_KEY = '/path/to/privatekey.pem'

ANDROID_API_KEY = 'APIkey_from_cloud.google.com'
"""

apn_pushers = {}
gcm_pusher = None


def get_cert_settings(dev=False):
    cert_setting = 'IOS_DEVELOPMENT_CERT' if dev else 'IOS_PRODUCTION_CERT'
    cert = getattr(settings, cert_setting, None)
    key = getattr(settings, 'IOS_KEY', None)
    if cert is None:
        logging.warning('%s was not configured', cert_setting)
    if key is None:
        logging.warning('IOS_KEY was not configured')
    return cert, key


def load_pusher(dev=False):
    cert, key = get_cert_settings(dev)
    if cert and key:
        return get_pusher(dev=dev, cert_file=cert, key=key)
    return None


@shared_task
def ios_push_message(device_token , msg , data_message):
    # if device_token.startswith('sandbox'):
    #     device_token = device_token[len('sandbox'):]
    #     is_sandbox = True
    # else:
    #     is_sandbox = False
    # prod_pusher = Pusher(use_sandbox=is_sandbox, cert_file=cert_file_production, key_file=key_file)
    # try:
    #     prod_pusher.push_message(device_token,
    #                              dict(channel_id=data_message['channel_id'],
    #                                   message_id=data_message['message_id'],
    #                                   alert="PentaCenter:\n" + msg,
    #                                   status='confirmed',
    #                                   content_available=True))
    #     return True, 'success'
    # except:
    #     logger.error(traceback.format_stack())
    #     return False, traceback.format_exc()
    # finally:
    #     prod_pusher.close()
    pass


@shared_task
def ios_push_message2(device_token, msg, data_message, cert_file=None, key_file=None):
    # if cert_file is None:
    #     cert_file = cert_file_production
    # if key_file is None:
    #     key_file = key_file_production
    # if device_token.startswith('sandbox'):
    #     device_token = device_token[len('sandbox'):]
    #     is_sandbox = True
    # else:
    #     is_sandbox = False
    # pusher = Pusher(use_sandbox=is_sandbox, cert_file=cert_file, key_file=key_file)
    # try:
    #     pusher.push_message(device_token, data_message)
    #     return True, 'success'
    # except:
    #     logger.error(traceback.format_exc())
    #     return False, traceback.format_exc()
    pass


@shared_task
def android_push_message(API_KEY, device_token_list, msg, data_message={}, extra_kwargs={}):
    logger.debug("Entering android_push_message")
    try:
        proxy_dict = {}
        logger.debug('setting android pusher')
        push_service = FCMNotification(api_key=API_KEY, proxy_dict=proxy_dict)

        if not data_message:
            data_message = {'message_title': 'Pentacenter', 'message_body': 'null'}

        # message_title = data_message['message_title']

        # Send to multiple devices by passing a list of ids.
        registration_ids = device_token_list

        result = push_service.notify_multiple_devices(registration_ids=registration_ids,
                                                      # message_title=message_title,
                                                      data_message=data_message)
        logger.debug('send success')
        logger.debug(result)
        return True, 'success'
    except:
        logger.exception('Fail to send notification')
        return False, traceback.format_exc()


def get_credential(application_name='generic', credential_name=None):
    """
    get credential from application name or credential name
    :param application_name: key in settings.NOTIFICATION_APP_MAP
    :param credential_name: key in settings.NOTIFICATION_CREDENTIALS
    :return: {
        'android': {'key': <string>},
        'ios':{'cert_file': <file_path>,
               'key_file': <file_path>}
    }
    """
    if not credential_name:
        credential_name = settings.NOTIFICATION_APP_MAP.get(application_name, 'default')
    credential = settings.NOTIFICATION_CREDENTIALS.get(credential_name)
    if not credential:
        raise ValueError('cannot find %s in `NOTIFICATION_CREDENTIALS` settings' % credential_name)
    return credential


def get_android_credential(application_name='generic', credential_name=None):
    """
    get android credential from application name or credential name
    :param application_name: key in settings.NOTIFICATION_APP_MAP
    :param credential_name: key in settings.NOTIFICATION_CREDENTIALS
    :return: {
        'key': <string>,
    }
    """
    credential = get_credential(application_name, credential_name)
    android_credential = credential.get('android')
    if not android_credential:
        raise ValueError('cannot find android credential for %s in `NOTIFICATION_CREDENTIALS` settings'
                         % credential_name if credential_name else 'app ' + application_name)
    return android_credential


def get_ios_credential(application_name='generic', credential_name=None):
    """
    get ios credential from application name or credential name
    :param application_name: key in settings.NOTIFICATION_APP_MAP
    :param credential_name: key in settings.NOTIFICATION_CREDENTIALS
    :return: {
        'cert_file': <file_path>,
        'key_file': <file_path>,
    }
    """
    credential = get_credential(application_name, credential_name)
    ios_credential = credential.get('ios')
    if not ios_credential:
        raise ValueError('cannot find ios credential for %s in `NOTIFICATION_CREDENTIALS` settings'
                         % credential_name if credential_name else 'app ' + application_name)
    return ios_credential


@shared_task
def send_notification_to_android_and_ios(message,
                                         android_tokens=None, android_credential=None,
                                         ios_tokens=None, ios_credential=None):
    """
    :param message: message Json serializable
    :param android_tokens: list of android device tokens
    :param android_credential: android credential
    :param ios_tokens: list of ios device tokens
    :param ios_credential: ios credential
    :return:
    """
    if android_tokens and android_credential:
        logger.debug('Push message to Android:')
        for token in android_tokens:
            logger.debug('    %s' % token)
        android_push_message(android_credential['key'], android_tokens, None, message)
    if ios_tokens and ios_credential:
        for token in ios_tokens:
            message['content_available'] = True
            if 'message_body' in message:
                message['alert'] = message['message_body']
                message.pop('message_body')
            else:
                message['alert'] = message.get('message_title', '')
            message['badge'] = None
            ios_push_message2(token, None, message,
                              cert_file=ios_credential['cert_file'],
                              key_file=ios_credential['key_file'])


@shared_task
def send_notification(channels, title, message, extra_dict=None, only_users=None,
                      except_users=None, force_send_user=False, addition_users=None,
                      credential_setting=None, notification_policy=None):
    """

    :param channels: channel ids you want to send the notification
    :param title: title of message
    :param message: message
    :param extra_dict: extra data to send with message in Dictionary
    :param only_users: list of user id, select users to send (query these users
                       from channel subscription except when `force_send_user` is True)
    :param except_users: list of user id, sent to all subscribed users except these
    :param force_send_user: if True this function will ignore UserSubscription and
                            directly use users from `only_users`.
                            `Notification` will not be created for Users in `only_users`
                            who didn't subscribe to `channels`. Cannot be used with `except_users`
    :param addition_users: list of user ids, tell this function to also send
                           notifications to users in `addition_users`.
                           `Notification` will not be created for Users in `addition_users`.
                           *Duplicate notification may be occur if you specific user id in
                           `only_users` and `addition_users` simultaneously.
    :param credential_setting: force using credential NOTIFICATION_CREDENTIAL with given key.
                               if None, use `application` from `channel`
    :param notification_policy: default: Notification.POLICY_NO_REPEAT
    :return:
    """
    if isinstance(channels, (int, int)):
        channels = [channels]
    if not channels:
        raise TypeError('`channels` must not be empty')
    channels = BaseChannel.objects.filter(id__in=channels)
    if not extra_dict:
        extra_dict = {}
    if notification_policy is None:
        notification_policy = Notification.POLICY_NO_REPEAT

    message = dict({
        'message_title': title,
        'message_body': message,
    }, **extra_dict)

    for channel in channels:
        android_credential = get_android_credential(channel.application, credential_setting)
        ios_credential = get_ios_credential(channel.application, credential_setting)

        message['channel_id'] = channel.id
        subscriptions = BaseUserSubscription.objects.filter(channel=channel)
        addition_user_ids = addition_users
        if only_users:
            subscriptions = subscriptions.filter(user_id__in=only_users)
            if force_send_user:
                addition_user_ids = list(User.objects.filter(id__in=only_users)
                                         .exclude(channel_subscriptions=subscriptions,
                                                  id__in=addition_users)
                                         .values_list('id', flat=True))
                addition_user_ids += addition_users
        elif except_users:
            subscriptions = subscriptions.exclude(user_id__in=except_users)

        android_device_tokens = []
        ios_device_tokens = []

        count = subscriptions.count()
        if count == 0:
            continue
        elif count > 1:
            with transaction.atomic():
                payload = NotificationBroadcastPayload.objects.create(payload=json.dumps(message))
                now = timezone.now()
                for subscription in subscriptions:
                    notification = Notification.objects.create(user=subscription.user,
                                                               subscription=subscription,
                                                               application=subscription.application,
                                                               policy=notification_policy,
                                                               broadcast_payload=payload,
                                                               last_sent_at=now)
                    message['notification_id'] = notification.id
                    user_devices = subscription.user.devices.all()
                    for device in user_devices:
                        if device.device_token:
                            DeviceNotificationStatus.objects.create(device=device,
                                                                    notification=notification,
                                                                    last_sent_at=now)
                        logger.debug("{} {} {}".format(device.id, device.device_type, device.device_token))
                        if device.device_type == 'android':
                            android_device_tokens.append(device.device_token)
                        elif device.device_type == 'ios':
                            ios_device_tokens.append(device.device_token)

            send_notification_to_android_and_ios(message,
                                                 android_device_tokens, android_credential,
                                                 ios_device_tokens, ios_credential)
        else:
            # sent only one user there are some differences.
            with transaction.atomic():
                now = timezone.now()
                subscription = subscriptions[0]  # no subscription loop
                notification = Notification.objects.create(user=subscription.user,
                                                           subscription=subscription,
                                                           application=subscription.application,
                                                           policy=notification_policy,
                                                           payload=json.dumps(message),  # no broadcast payload
                                                           last_sent_at=timezone.now())
                message['notification_id'] = notification.id
                user_devices = subscription.user.devices.all()
                for device in user_devices:
                    if device.device_token:
                        DeviceNotificationStatus.objects.create(device=device,
                                                                notification=notification,
                                                                last_sent_at=now)
                    if device.device_type == 'android':
                        android_device_tokens.append(device.device_token)
                    elif device.device_type == 'ios':
                        ios_device_tokens.append(device.device_token)

            send_notification_to_android_and_ios(message,
                                                 android_device_tokens, android_credential,
                                                 ios_device_tokens, ios_credential)
        if addition_user_ids:
            android_device_tokens = (Device.objects.filter(user_id__in=addition_user_ids,
                                                           device_type='android')
                                     .values_list('device_token', flat=True))
            ios_device_tokens = (Device.objects.filter(user_id__in=addition_user_ids,
                                                       device_type='ios')
                                 .values_list('device_token', flat=True))
            logger.debug('addition user:')
            logger.debug(addition_user_ids)
            send_notification_to_android_and_ios(message,
                                                 android_device_tokens, android_credential,
                                                 ios_device_tokens, ios_credential)


if __name__ == '__main__':
    print('do notify')
    #android_push_message('APA91bGdznYt2_mZAti6cdnL8lbiLl3ayzRWnWlX0_WbMEuzAP3rW94NqipY1zWYzM7iUAdUvNHSuVZbTSnMxIcm_TDjW_d2oCf9Yj6eA4FF1F78_hXUur6ZPFlkVfXnkb2Mc-SQCCZv', Notification.TYPE_NEW  , "sqool test")
    #android_push_message('APA91bF0qXihTSKpS3217ad08IdD_yip3VB60FA9XZ-N7hO-iV5g1OZx-_jDR4wbtRdLWXUc968SiAZLuQcU0oycWZrvEDlTqTdOobYuSPJvES9DtR8C2K3O6POgefJ6k2wMxDM-FCII', Notification.TYPE_NEW  , "sqool test")
    #android_push_message( "AIzaSyB3WzJ_t5_cDhHEkqzLOAyFXHEj9PqE-E0" , ["dxMZ8ZQYWng:APA91bGn-wj7ORNnE7JhAsD_2D1yx1ZyXRB6TP8jAlpjXiOLN90pL0D3JWuA5qDLAFuJJGn0kNxEZHI1dlvVfdXV1YuF1_X8Z_gY25H-Wc8HHrO4EcdoFqfO0BRWKhhO8KpEW4AMhg36"] , "PENTACENTER TESTTT"  )
    android_push_message( "AAAAue-cMf8:APA91bHZ9f5uvCknVP9UOFucnwYYsmjRm1lBY1iadMdATISz2vvLGe4W2t_ACHYftil-zvamxMi5rxGAZBQ0lQvyg1WpMCCj_d3wAfpm5XMQSJFMDkRwhweYWD8XjbFVMrrj9UbEtcKY" , ["c-02pu6BfCI:APA91bE8j9JkhffrC_WlSbfbS0EVTW1ZLjTkOCzfzKuA7MPuH7OTWuZ3agbGyxbALBQps8Uwqn1g2yRMxKbh_JAqodTY-t_EMYlCC6my4mHfGkxylzuvr-8TCLcBU6iZgaBdlY_g5Aij"] , "PENTACENTER TESTTT FROM PENGGGG"  )
    print('done notify')
