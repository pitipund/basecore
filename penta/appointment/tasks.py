# -*- coding: utf-8 -*-

import logging
from constance import config
from datetime import datetime, timedelta
from dateutil import relativedelta
from celery import shared_task

from his.users.models import Employee, EmployeeInfo, Position

from his.penta.appointment.kala import KalaSlot
from his.penta.appointment.models import Appointment, AppointmentUserTimeslot, Client, ProviderAvailableSlot, \
    ServiceAppointment
from his.penta.pentacenter.models import Device
from his.penta.pentacenter.tasks import android_push_message, ios_push_message2
from django.conf import settings

logger = logging.getLogger(__name__)


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
        data_message['message_title'] = app
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
def push_upcoming_airtech_notification(appointment_id):
    logger.debug("push_upcoming_airtech_notification..............")
    try:
        _app = Appointment.objects.get(id=appointment_id)
        final_slot = AppointmentUserTimeslot.objects.filter(appointment_id=_app.id, is_finalize=True).first()

        if final_slot:
            try:
                ts = KalaSlot(final_slot.timeslot)
                final_slot = ts.toDatetime()
                final_slot = final_slot+timedelta(hours=7)
                final_slot_str = final_slot.strftime("%d/%m/%Y %H:%M")

            except:
                final_slot_str = ""
        else:
            final_slot_str = ""

        msg_obj = {'appointment_id': appointment_id,
                   'action': "notify"}
        if _app.service_type is None:
            msg_obj['service_type'] = "generic_appointment"
        else:
            service = ServiceAppointment.objects.filter(provider__provider_type=_app.service_type.provider_type,
                                                        appointment=_app).first()
            # if not service.is_provider_accept:
            #    return 406 #Avoid push notification if provider not accept.

            msg_obj['service_id'] = service.id
            msg_obj['service_type'] = _app.service_type.name
        NotificationPentaCenter(
                                msg="Upcoming appointment (%s)" % final_slot_str,
                                receiver_user_id_list=_app.invitee.values_list('id', flat=True),
                                app="pentacenter", data_message=msg_obj)
        return 200
    except Exception as e:
        logger.exception(e.message)


@shared_task
def create_provider_available_slot():
    employee_info = EmployeeInfo.objects.filter(employee__status=Employee.STATUS.ACTIVE)
    positions = Position.objects.filter(id__in=employee_info.values_list('duty__position', flat=True))
    # clients = Client.objects.filter(object_id__in=employee_info.values_list('main_division_id', flat=True))
    # Above will get non-division clients, leading to incorrect behavior. Below filters non-division client out
    division_clients = Client.objects.filter(content_type__app_label='core', content_type__model='division')
    clients = division_clients.filter(object_id__in=employee_info.values_list('main_division_id', flat=True))
    for obj in employee_info.values('duty__position_id', 'main_division_id').distinct():
        position = list(filter(lambda p: p.id == obj['duty__position_id'], positions))
        client = list(filter(lambda c: c.object_id == obj['main_division_id'], clients))
        if position and client:
            for i in range(config.HRM_NO_MONTH_PROVIDER_AVAILABLE_SLOT+1):
                dt = datetime.now() + relativedelta.relativedelta(months=i)
                ProviderAvailableSlot.objects.create_provider_available_slot_one_month(
                    client=client[0],
                    position=position[0],
                    be_year=dt.year + 543,
                    month=dt.month,
                    duration=config.HRM_MIN_MINUTE_FOR_SLOT)
