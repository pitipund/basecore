# -*- coding: utf-8 -*-

import logging
from celery import shared_task

import his.penta.django_facebook_messenger.api as fb_api
from datetime import datetime
from django.conf import settings

from his.penta.curator.models import UserProfile
from his.penta.pentacenter.models import Device
from his.penta.sqool.models import FacebookUserCache
from his.penta.pentacenter.tasks import android_push_message, ios_push_message2

logger = logging.getLogger(__name__)


@shared_task
def NotificationPentaCenter(msg="", receiver_user_id_list=[], app="pentacenter", data_message={}):
    logger.debug("========================== receiver_user_id_listreceiver_user_id_listreceiver_user_id_list")
    logger.debug(receiver_user_id_list)
    device_token_list_android = [d.device_token for d in Device.objects.filter(user__id__in=receiver_user_id_list,
                                                                               device_type__iexact='android',
                                                                               app__name="pentacenter")]
    device_token_list_ios = [d.device_token for d in
                             Device.objects.filter(user__id__in=receiver_user_id_list, device_type__iexact='ios',
                                                   app__name="pentacenter")]
    # any fields able to customize

    if 'message_id' not in data_message:
        data_message['message_id'] = 0
    if 'channel_id' not in data_message:
        data_message['channel_id'] = 0
    if 'message_title' not in data_message:
        data_message['message_title'] = ""
    if 'message_body' not in data_message:
        data_message['message_body'] = msg
    if 'message_app' not in data_message:
        data_message['message_app'] = "appointment"
    if 'send_at' not in data_message:
        data_message['send_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # make list unique bcoz we dont trust devicetoken list is unique
    device_token_list_android = list(set(device_token_list_android))
    device_token_list_ios = list(set(device_token_list_ios))
    logger.debug("gonna send android")
    logger.debug(device_token_list_android)
    logger.debug("gonna send ios")
    logger.debug(device_token_list_ios)
    logger.debug("with msg %s", msg)

    # Start sending
    #  IF apply_aync not working!!!!!!!!!!!!   TRY cmd 'sudo pkill -9 -f celery' once!!!!!!!!!  "

    # Android can do multiple in single-shot
    if device_token_list_android:
        # android_push_message(settings.ANDROID_API_KEY , device_token_list_android , msg , data_message )
        android_push_message.apply_async((settings.ANDROID_API_KEY, device_token_list_android, msg, data_message))

    logger.debug(data_message)
    # Normal loop for iOS
    if device_token_list_ios:
        for device_token in device_token_list_ios:
            # custom message for ios

            if 'message_body' in data_message:
                data_message.pop('message_body')

            data_message['content_available'] = True
            data_message['alert'] = msg
            data_message['badge'] = None

            # ios_push_message2(device_token , msg , data_message)
            ios_push_message2.apply_async((device_token, msg, data_message))

    logger.debug(data_message)
    return ""


@shared_task
def update_fb_user_profile_picture():
    user_profiles = UserProfile.objects.exclude(facebook_id='')
    for profile in user_profiles:
        logger.debug('update profile for id %s', profile.facebook_id)
        pic_url = fb_api.get_user_pic(profile.facebook_id, pic_only=True)
        profile.image_url = pic_url
        profile.save()
    for fb_user in FacebookUserCache.objects.all():
        logger.debug('update profile for id %s', fb_user.facebook_id)
        pic_url = fb_api.get_user_pic(fb_user.facebook_id, pic_only=True)
        fb_user.image_url = pic_url
        fb_user.save()
