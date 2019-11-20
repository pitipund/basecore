import logging

from constance import config
from datetime import datetime, timedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.conf import settings
from django.db.models import Max, Min, Q
from pyfcm import FCMNotification

from rest_framework import serializers

from his.core.services import Messenger
from his.penta.curator.models import CuratorChannel
from his.penta.showtime.utils import UploadToDir

from his.framework.models import BaseActionLog, EnumField, LabeledIntEnum, StatableModel
from his.framework.utils import do_service
from his.users.models import Employee, Position, User

logger = logging.getLogger(__name__)


class Address(models.Model):
    upload_dir = UploadToDir(settings.PREMISE_PATH)

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    address1 = models.CharField(null=True, blank=True, default="", max_length=100)
    address2 = models.CharField(null=True, blank=True, default="", max_length=100)
    province = models.CharField(null=True, blank=True, default="", max_length=30)
    city = models.CharField(null=True, blank=True, default="", max_length=30)
    district = models.CharField(null=True, blank=True, default="", max_length=30)
    zipcode = models.CharField(max_length=10, null=True, blank=True, default="")
    map_image = models.ImageField(upload_to=upload_dir,
                                  blank=True, null=True, verbose_name="Map image")

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class PremiseImage(models.Model):
    upload_dir = UploadToDir(settings.PREMISE_PATH)

    id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to=upload_dir,
                              blank=True, null=True, verbose_name="Premise image")
    image_url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return self.id


class Premise(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    address = models.ForeignKey(Address, null=True, blank=True)
    is_official = models.BooleanField(default=True)
    premise_images = models.ManyToManyField(PremiseImage, blank=True)

    create_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class ProviderType(models.Model):
    technician = 'technician'
    caddy = 'caddy'
    golf_course = 'golf_course'
    customer_house = 'customer_house'
    na = 'na'
    CAT_CHOICES = (
        (na, 'na'),
        (caddy, 'caddy'),
        (technician, 'technician'),
        (golf_course, 'golf_course'),
        (customer_house, 'customer_house')
        # พยายามอย่าใช้ Table นี้อีก
        # ในตาราง Provider ใช้ content_type แทน
    )

    id = models.AutoField(primary_key=True)
    category = models.CharField(default=na, max_length=32, choices=CAT_CHOICES)
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return '[%s] %s' % (self.category, self.name)


class ClientType(models.Model):
    DIVISION = 'division'
    na = 'na'
    CAT_CHOICES = (
        (na, 'na'),
        (DIVISION, 'division')
    )

    id = models.AutoField(primary_key=True)
    category = models.CharField(default=na, max_length=32, choices=CAT_CHOICES)
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return '[%s] %s' % (self.category, self.name)


class AppointmentType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    provider_type = models.ForeignKey(ProviderType, null=True, blank=True)

    def __unicode__(self):
        return self.name


class AppointmentManager(models.QuerySet):
    def create_app(self, service_type, owner, name, remark, invitee_list):
        obj = Appointment()
        obj.service_type = service_type
        obj.owner = owner
        obj.name = name
        obj.remark = remark
        obj.save()

        for invitee in invitee_list:
            obj.invitee.add(invitee)
        obj.save()

        return obj


class Appointment(models.Model):
    id = models.AutoField(primary_key=True)

    service_type = models.ForeignKey(AppointmentType, null=True, blank=True)

    create_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, related_name='owner')

    name = models.CharField(null=True, blank=True, default="", max_length=500)
    place = models.TextField(null=True, blank=True, default="")
    address = models.ForeignKey(Address, null=True, blank=True)
    remark = models.TextField(null=True, blank=True, default="")

    invitee = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='invitee')
    is_active = models.BooleanField(default=True)
    is_finalize = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, editable=False, null=True,
                                     help_text='content type of business logic')
    content_id = models.PositiveIntegerField(editable=False, blank=True, null=True,
                                             help_text='content id of business logic')
    foreign_content = GenericForeignKey('content_type', 'content_id')
    objects = AppointmentManager.as_manager()

    def __unicode__(self):
        return "ID:%s name: %s type: %s (%s)" % (self.id, self.name, self.service_type, self.content_type)

    def __str__(self):
        return "ID:%s name: %s type: %s (%s)" % (self.id, self.name, self.service_type, self.content_type)

    def get_appointment_timeslot_set(self):
        return self.app_timeslot


class UserAvailableSlot(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    start_slot = models.IntegerField(default=0, db_index=True)
    end_slot = models.IntegerField(default=0, db_index=True)
    active = models.BooleanField(default=True)


class UserGolf(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL)


class UserGolfCourt(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL)


class UserCaddy(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    ex_profile = models.TextField(null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="")


class UserCaddyPremise(models.Model):
    id = models.AutoField(primary_key=True)
    caddy = models.ForeignKey(UserCaddy)
    premise = models.ForeignKey(Premise)

    class Meta:
        unique_together = ('caddy', 'premise')


class UserDoctor(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL)


class UserAirTech(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    ex_profile = models.TextField(null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="")


class CompositeChannel(models.Model):
    id = models.AutoField(primary_key=True)
    main_channel = models.ForeignKey(CuratorChannel, related_name="composite")
    member_channel = models.ForeignKey(CuratorChannel, related_name="parent_composite")

    def __unicode__(self):
        return self.main_channel.name + ":" + self.member_channel.name

    def __str__(self):
        return self.main_channel.name + ":" + self.member_channel.name


class Client(models.Model):
    id = models.AutoField(primary_key=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    client_type = models.ForeignKey(ClientType, null=True, blank=True)
    channel = models.ForeignKey(CuratorChannel, null=True, blank=True)

    # user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    # first_name = models.CharField(null=True, blank=True, default="", max_length=30)
    # last_name = models.CharField(null=True, blank=True, default="", max_length=30)
    # email = models.EmailField(null=True, blank=True)
    # tel = models.CharField(null=True, blank=True, default="", max_length=13)
    # create_at = models.DateTimeField(auto_now_add=True)

    @property
    def division(self):
        return self.divisions.first()

    class Meta:
        verbose_name = 'Division, ...'

    def __unicode__(self):
        return "ID:%s first_name: %s(id=%s)" % (self.id, self.first_name, self.user)

    def __str__(self):
        return '[%s] %s:%s' % (self.id, self.content_type, self.object_id)


class ProviderManager(models.QuerySet):
    def get_provider_by_month_and_division(self, client: Client, position: Position, be_year: int, month: int):
        start = do_service('penta.appointment:datetime_to_serial', be_year, month, 1, 0, 0)
        end = do_service('penta.appointment:get_last_day_of_month', be_year, month)
        end = do_service('penta.appointment:datetime_to_serial', end.year, end.month, end.day, end.hour, end.minute)

        provider = Provider.objects \
            .filter(employees__employee_info__main_division=client.object_id,
                    employees__employee_info__duty__position=position) \
            .order_by('-employees__employee_info__head_staff',
                      '-employees__employee_info__incharge',
                      'employees__employee_info__duty__display_seq')

        p_import = Provider.objects \
            .filter(provider_slot__assign_provider_slot__client_service_slot__client=client,
                    provider_slot__assign_provider_slot__client_service_slot__position=position,
                    provider_slot__assign_provider_slot__client_service_slot__start_slot__gte=start,
                    provider_slot__assign_provider_slot__client_service_slot__end_slot__lte=end,
                    provider_slot__assign_provider_slot__slot_status=ProviderAssign.SLOT_STATUS.RESERVED,
                    provider_slot__assign_provider_slot__status__in=[ProviderAssign.STATUS.DRAFTED,
                                                                     ProviderAssign.STATUS.CONFIRMED]) \
            .exclude(id__in=provider.values('id')) \
            .order_by('-employees__employee_info__head_staff',
                      '-employees__employee_info__incharge',
                      'employees__employee_info__duty__display_seq') \
            .distinct()
        return provider, p_import


class Provider(models.Model):
    id = models.AutoField(primary_key=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    provider_type = models.ForeignKey(ProviderType, null=True, blank=True)
    channel = models.ForeignKey(CuratorChannel, null=True, blank=True)

    objects = ProviderManager.as_manager()

    @property
    def employee(self):
        return self.employees.first()

    class Meta:
        verbose_name = 'พยาบาล, ...'

    def __unicode__(self):
        return "ID:%s type: %s object: %s(id=%s)" % (self.id, self.content_type, self.employee, self.object_id)

    def __str__(self):
        return '[%s] %s:%s' % (self.id, self.content_type, self.object_id)


class ServiceAppointmentManager(models.QuerySet):
    def create_sa(self, is_parent, appointment, provider, client):
        obj = ServiceAppointment()
        obj.is_parent = is_parent
        obj.appointment = appointment
        obj.provider = provider
        obj.client = client
        obj.save()
        return obj

    def confirm_appointment(self, appointment: Appointment, app_timeslot, provider: Provider, remark: str, status: str):
        sa = ServiceAppointment.objects.filter(appointment=appointment, is_active=True)
        parent_sa = sa.filter(is_parent=True).first()
        child_sa = sa.filter(is_parent=False, is_provider_accept=True).first()

        if not child_sa:
            # create ServiceAppointment(is_parent=False)
            child_sa = ServiceAppointment.objects.create_sa(
                is_parent=False, appointment=appointment, provider=provider, client=parent_sa.client)

        child_sa.provider = provider
        child_sa.is_provider_ack = True
        child_sa.is_provider_accept = True
        child_sa.remark = remark
        child_sa.save()

        # update status to confirm
        app_timeslot.service_appointment = child_sa
        app_timeslot.status = status
        app_timeslot.save()

        start = datetime(app_timeslot.start_time.year, app_timeslot.start_time.month, app_timeslot.start_time.day,
                         app_timeslot.start_time.hour, app_timeslot.start_time.minute)
        end = datetime(app_timeslot.end_time.year, app_timeslot.end_time.month, app_timeslot.end_time.day,
                       app_timeslot.end_time.hour, app_timeslot.end_time.minute)

        app_start_serial = do_service('penta.appointment:datetime_to_serial',
                                      start.year + 543, start.month, start.day, start.hour, start.minute)
        app_end_serial = do_service('penta.appointment:datetime_to_serial',
                                    end.year + 543, end.month, end.day, end.hour, end.minute)

        provider_assigns = ProviderAssign.objects \
            .filter(provider_available_slots__provider__object_id=child_sa.provider.content_object.user.employee.id,
                    provider_available_slots__start_slot__gte=app_start_serial,
                    provider_available_slots__end_slot__lte=app_end_serial,
                    client_service_slot__client=parent_sa.provider.content_object.client,
                    slot_status=ProviderAssign.SLOT_STATUS.RESERVED) \
            .exclude(status=ProviderAssign.STATUS.CANCELED)
        for pa in provider_assigns:
            app_timeslot.provider_assigns.add(pa)

    def postpone_confirm_appointment(self, appointment: Appointment, app_timeslot, start_datetime: datetime,
                                     end_datetime: datetime, provider: Provider, remark: str, status: str):
        sa = ServiceAppointment.objects.filter(appointment=appointment, is_active=True)
        parent_sa = sa.filter(is_parent=True).first()
        child_sa = sa.filter(is_parent=False, is_provider_accept=True).first()

        if not child_sa:
            # create ServiceAppointment(is_parent=False)
            child_sa = ServiceAppointment.objects.create_sa(
                is_parent=False, appointment=appointment, provider=provider, client=parent_sa.client)

        child_sa.provider = provider
        child_sa.is_provider_ack = True
        child_sa.is_provider_accept = True
        child_sa.remark = remark
        child_sa.save()

        # postpone
        timeslot = do_service('penta.appointment:datetime_to_serial_utc',
                              start_datetime.year, start_datetime.month, start_datetime.day,
                              start_datetime.hour, start_datetime.minute)
        timeslot_end = do_service('penta.appointment:datetime_to_serial_utc',
                                  end_datetime.year, end_datetime.month, end_datetime.day,
                                  end_datetime.hour, end_datetime.minute)
        app_timeslot.timeslot = timeslot
        app_timeslot.timeslot_end = timeslot_end

        # update status to confirm
        app_timeslot.service_appointment = child_sa
        app_timeslot.status = status
        app_timeslot.save()

        start = datetime(app_timeslot.start_time.year, app_timeslot.start_time.month, app_timeslot.start_time.day,
                         app_timeslot.start_time.hour, app_timeslot.start_time.minute)
        end = datetime(app_timeslot.end_time.year, app_timeslot.end_time.month, app_timeslot.end_time.day,
                       app_timeslot.end_time.hour, app_timeslot.end_time.minute)

        app_start_serial = do_service('penta.appointment:datetime_to_serial',
                                      start.year + 543, start.month, start.day, start.hour, start.minute)
        app_end_serial = do_service('penta.appointment:datetime_to_serial',
                                    end.year + 543, end.month, end.day, end.hour, end.minute)

        provider_assigns = ProviderAssign.objects \
            .filter(provider_available_slots__provider__object_id=child_sa.provider.content_object.user.employee.id,
                    provider_available_slots__start_slot__gte=app_start_serial,
                    provider_available_slots__end_slot__lte=app_end_serial,
                    client_service_slot__client=parent_sa.provider.content_object.client,
                    slot_status=ProviderAssign.SLOT_STATUS.RESERVED) \
            .exclude(status=ProviderAssign.STATUS.CANCELED)
        for pa in provider_assigns:
            app_timeslot.provider_assigns.add(pa)

    def cancel_appointment(self, sa, app_timeslot, status: str):
        sa.update(is_provider_accept=False)

        app_timeslot.status = status
        app_timeslot.save()


class ServiceAppointment(models.Model):
    id = models.AutoField(primary_key=True)
    is_parent = models.BooleanField(default=False)
    appointment = models.ForeignKey(Appointment, blank=True, null=True, related_name='app')
    provider = models.ForeignKey(Provider)
    client = models.ForeignKey(Client)
    remark = models.TextField(null=True, blank=True, default="")
    is_provider_accept = models.BooleanField(default=False)
    is_provider_ack = models.BooleanField(default=False)
    is_done = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    objects = ServiceAppointmentManager.as_manager()

    def __str__(self):
        return str(self.id)


class ExtraServiceDetail(models.Model):
    # legacy extra model, for Airtech appointment
    upload_dir = UploadToDir(settings.SERVICE_APP_IMG_PATH)

    id = models.AutoField(primary_key=True)
    service_appointment = models.ForeignKey(ServiceAppointment)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    image = models.ImageField(upload_to=upload_dir,
                              blank=True, null=True, verbose_name="Service appointment img.")
    text = models.CharField(max_length=300, null=True, blank=True, default="")
    is_text_only = models.BooleanField(default=False)
    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.text

    def __str__(self):
        return self.text


class ProviderAvailableSlotQuerySet(models.QuerySet):
    def set_incharge(self, id_list, incharged) -> None:
        ProviderAvailableSlot.objects.filter(id__in=id_list).update(incharge=incharged)

    def create_provider_available_slot_one_month(self, position, client, month, duration, be_year=None):
        provider_slot = []

        last_dt = do_service('penta.appointment:get_last_day_of_month', be_year, month)
        start_dt = datetime(be_year, month, 1, 0, 0) - timedelta(days=1)
        end_dt = datetime(be_year, month, last_dt.day, 0, 0) + timedelta(days=1)

        start = do_service('penta.appointment:datetime_to_serial', be_year, month, 1, 0, 0)
        end = do_service('penta.appointment:datetime_to_serial', be_year, month, last_dt.day, 23, 59)

        pas = ProviderAvailableSlot.objects \
            .filter(provider__employees__status=Employee.STATUS.ACTIVE,
                    provider__employees__employee_info__duty__position=position,
                    provider__employees__employee_info__main_division=client.division,
                    start_slot__gte=start,
                    start_slot__lte=end) \
            .values('provider_id') \
            .distinct()

        providers = Provider.objects \
            .filter(employees__status=Employee.STATUS.ACTIVE,
                    employees__employee_info__duty__position=position,
                    employees__employee_info__main_division=client.division) \
            .exclude(id__in=pas)

        time_slot = do_service('HRM:get_start_end_time_slot', start_dt, end_dt, duration)
        for time in time_slot:
            for provider in providers:
                provider_slot.append(ProviderAvailableSlot(provider=provider,
                                                           start_slot=time['start'],
                                                           end_slot=time['end']))
        ProviderAvailableSlot.objects.bulk_create(provider_slot)

    def create_provider_available_slot_one_month_one_provider(self, provider, month, duration, be_year=None):
        provider_slot = []

        last_dt = do_service('penta.appointment:get_last_day_of_month', be_year, month)
        start_dt = datetime(be_year, month, 1, 0, 0) - timedelta(days=1)
        end_dt = datetime(be_year, month, last_dt.day, 0, 0) + timedelta(days=1)

        start = do_service('penta.appointment:datetime_to_serial', be_year, month, 1, 0, 0)
        end = do_service('penta.appointment:datetime_to_serial', be_year, month, last_dt.day, 23, 59)

        pas = ProviderAvailableSlot.objects \
            .filter(provider=provider, start_slot__gte=start, start_slot__lte=end) \
            .values('provider_id') \
            .distinct()

        if not pas.exists():
            time_slot = do_service('HRM:get_start_end_time_slot', start_dt, end_dt, duration)
            for time in time_slot:
                provider_slot.append(ProviderAvailableSlot(provider=provider,
                                                           start_slot=time['start'],
                                                           end_slot=time['end']))
            ProviderAvailableSlot.objects.bulk_create(provider_slot)


class ProviderAvailableSlot(models.Model):
    id = models.AutoField(primary_key=True)
    provider = models.ForeignKey(Provider, related_name='provider_slot')

    start_slot = models.IntegerField(default=0, db_index=True)
    end_slot = models.IntegerField(default=0, db_index=True)
    active = models.BooleanField(default=True)

    objects = ProviderAvailableSlotQuerySet.as_manager()

    class Meta:
        verbose_name = 'ตารางเวลาพยาบาล, ...'

    def __str__(self):
        return '%s provider: %s [%s(%s)-%s(%s)]' % (self.id,
                                                    self.provider,
                                                    self.start_date_time.strftime('%d/%m/%y %H:%M'), self.start_slot,
                                                    self.end_date_time.strftime('%d/%m/%y %H:%M'), self.end_slot)

    @property
    def start_date_time(self):
        return do_service('penta.appointment:serial_to_datetime', self.start_slot)

    @property
    def start_date_time_utc(self):
        return do_service('penta.appointment:serial_to_datetime_utc', self.start_slot)

    @property
    def end_date_time(self):
        return do_service('penta.appointment:serial_to_datetime', self.end_slot)

    @property
    def provider_assign_slot(self):
        assign_slot = self.assign_provider_slot.exclude(status=ProviderAssign.STATUS.CANCELED).first()
        if assign_slot:
            return assign_slot.id
        return None

    @property
    def division(self):
        assign_slot = self.assign_provider_slot.exclude(status=ProviderAssign.STATUS.CANCELED).first()
        if assign_slot:
            return assign_slot.client_service_slot.client.division
        return None

    @property
    def client(self):
        assign_slot = self.assign_provider_slot.exclude(status=ProviderAssign.STATUS.CANCELED).first()
        if assign_slot:
            return assign_slot.client_service_slot.client
        return None

    def update_for_provider_assign(self, other_pa):
        # e.g prepare provider available slot for OT
        self.type = other_pa.provider_available_slot.type
        self.incharge = False
        self.status = other_pa.provider_available_slot.status
        self.service_capacity = other_pa.provider_available_slot.service_capacity
        self.source = other_pa.provider_available_slot.source
        self.save()
        return self


class ClientServiceSlotQuerySet(models.QuerySet):
    def create_client_service_slot_one_month(self, client: Client, position: Position,
                                             start_morning: str, end_morning: str,
                                             start_afternoon: str, end_afternoon: str,
                                             start_night: str, end_night: str,
                                             month: int, be_year=None):
        # ถ้ามี provider assign แล้ว จะไม่ให้แก้เวลาใน slot อีก
        provider_assign = ProviderAssign.objects.provider_assign_one_month(client, position, be_year, month)
        if not provider_assign.exists():
            client_slot = []

            start = do_service('penta.appointment:datetime_to_serial', be_year, month, 1, 0, 0)
            end = do_service('penta.appointment:get_last_day_of_month', be_year, month)
            last_day = end.day
            end = do_service('penta.appointment:datetime_to_serial',
                             end.year, end.month, last_day, end.hour, end.minute)

            # inactive ClientServiceSlot
            ClientServiceSlot.objects \
                .select_related('client', 'position') \
                .filter(client=client, position=position, start_slot__gte=start, start_slot__lte=end) \
                .update(active=False)

            # create ClientServiceSlot
            start_morning = start_morning.split(':')
            end_morning = end_morning.split(':')
            start_afternoon = start_afternoon.split(':')
            end_afternoon = end_afternoon.split(':')
            start_night = start_night.split(':')
            end_night = end_night.split(':')

            for day in range(1, last_day + 1):
                # morning
                start = do_service('penta.appointment:datetime_to_serial',
                                   be_year, month, day, start_morning[0], start_morning[1])
                end = do_service('penta.appointment:datetime_to_serial',
                                 be_year, month, day, end_morning[0], end_morning[1])
                if start > end:
                    end = datetime(be_year, month, day) + timedelta(days=1)
                    end = do_service('penta.appointment:datetime_to_serial',
                                     end.year, end.month, end.day, end_morning[0], end_morning[1])
                client_slot.append(ClientServiceSlot(client=client,
                                                     position=position,
                                                     start_slot=start,
                                                     end_slot=end,
                                                     slot=ClientServiceSlot.SLOT.MORNING))

                # afternoon
                start = do_service('penta.appointment:datetime_to_serial',
                                   be_year, month, day, start_afternoon[0], start_afternoon[1])
                end = do_service('penta.appointment:datetime_to_serial',
                                 be_year, month, day, end_afternoon[0], end_afternoon[1])
                if start > end:
                    end = datetime(be_year, month, day) + timedelta(days=1)
                    end = do_service('penta.appointment:datetime_to_serial',
                                     end.year, end.month, end.day, end_afternoon[0], end_afternoon[1])
                client_slot.append(ClientServiceSlot(client=client,
                                                     position=position,
                                                     start_slot=start,
                                                     end_slot=end,
                                                     slot=ClientServiceSlot.SLOT.AFTERNOON))

                # night
                start = do_service('penta.appointment:datetime_to_serial',
                                   be_year, month, day, start_night[0], start_night[1])
                end = do_service('penta.appointment:datetime_to_serial',
                                 be_year, month, day, end_night[0], end_night[1])
                if start > end:
                    end = datetime(be_year, month, day) + timedelta(days=1)
                    end = do_service('penta.appointment:datetime_to_serial',
                                     end.year, end.month, end.day, end_night[0], end_night[1])
                client_slot.append(ClientServiceSlot(client=client,
                                                     position=position,
                                                     start_slot=start,
                                                     end_slot=end,
                                                     slot=ClientServiceSlot.SLOT.NIGHT))

            ClientServiceSlot.objects.bulk_create(client_slot)


class ClientServiceSlot(models.Model):
    class SLOT(LabeledIntEnum):
        MORNING = 1, 'เช้า'
        AFTERNOON = 2, 'บ่าย'
        NIGHT = 3, 'ดึก'

    client = models.ForeignKey(Client, related_name='client_slot')
    position = models.ForeignKey(Position, blank=True, null=True)
    start_slot = models.IntegerField(default=0)
    end_slot = models.IntegerField(default=0)
    slot = EnumField(SLOT, blank=True, null=True)
    active = models.BooleanField(default=True)

    objects = ClientServiceSlotQuerySet.as_manager()

    class Meta:
        verbose_name = 'ตารางเวลา Division, ...'

    def __str__(self):
        return '%s [%s(%s)-%s(%s)]' % (self.client,
                                       self.start_date_time.strftime('%d/%m/%y %H:%M'), self.start_slot,
                                       self.end_date_time.strftime('%d/%m/%y %H:%M'), self.end_slot)

    @property
    def start_date_time(self):
        return do_service('penta.appointment:serial_to_datetime', self.start_slot)

    @property
    def start_date_time_utc(self):
        return do_service('penta.appointment:serial_to_datetime_utc', self.start_slot)

    @property
    def end_date_time(self):
        return do_service('penta.appointment:serial_to_datetime', self.end_slot)


class ProviderAssignQuerySet(models.QuerySet):
    def filter_active(self):
        return self.exclude(status=ProviderAssign.STATUS.CANCELED)

    def filter_confirm(self):
        return self.filter(status=ProviderAssign.STATUS.CONFIRMED)

    def filter_swapable(self):
        return self.filter(
            status__in=[ProviderAssign.STATUS.CONFIRMED, ProviderAssign.STATUS.DRAFTED],
            slot_status=ProviderAssign.SLOT_STATUS.RESERVED
        )

    def provider_assign_one_month(self, client: Client, position: Position, be_year: int, month: int):
        start = do_service('penta.appointment:datetime_to_serial', be_year, month, 1, 0, 0)
        end = do_service('penta.appointment:get_last_day_of_month', be_year, month)
        last_day = end.day
        end = do_service('penta.appointment:datetime_to_serial', end.year, end.month, last_day, end.hour, end.minute)
        return self \
            .select_related('client_service_slot__client', 'client_service_slot__position') \
            .filter(client_service_slot__client=client,
                    client_service_slot__position=position,
                    client_service_slot__start_slot__gte=start,
                    client_service_slot__end_slot__lte=end)

    def action_draft(self, provider: Provider, client_service_slot: ClientServiceSlot, type, user,
                     action='draft', incharge=False, mobile=False) -> list:
        client = client_service_slot.client
        client_position = client_service_slot.position
        employee_info = provider.employee.employee_info

        if action == 'draft':
            provider_assign_action = ProviderAssign.ACTION.DRAFT
        elif action == 'swap':
            provider_assign_action = ProviderAssign.ACTION.SWAP

        provider_available_slot = ProviderAvailableSlot.objects \
            .filter(provider=provider,
                    start_slot__gte=client_service_slot.start_slot,
                    start_slot__lt=client_service_slot.end_slot,
                    end_slot__gt=client_service_slot.start_slot,
                    end_slot__lte=client_service_slot.end_slot,
                    active=True) \
            .values_list('id', flat=True)
        if not provider_available_slot.exists():
            raise serializers.ValidationError('ไม่พบ slot เวลา')

        if employee_info.duty.position.id != client_position.id:
            raise serializers.ValidationError('Position ไม่ถูกต้อง')

        be_year = client_service_slot.start_date_time.year + 543
        month = client_service_slot.start_date_time.month
        confirm_pa = self.provider_assign_one_month(client, client_position, be_year, month)
        if confirm_pa.filter(status=ProviderAssign.STATUS.CONFIRMED).exists() and mobile is False:
            raise serializers.ValidationError('ยืนยันตารางเดือนนี้แล้ว ไม่สามารถแก้ไขได้')

        off_leave_pa = self \
            .prefetch_related('provider_available_slots') \
            .filter(client_service_slot=client_service_slot,
                    provider_available_slots__id__in=provider_available_slot,
                    slot_status__in=[ProviderAssign.SLOT_STATUS.OFF,
                                     ProviderAssign.SLOT_STATUS.LEAVE]) \
            .filter_active() \
            .exists()

        if off_leave_pa:
            raise serializers.ValidationError('slot เวลาอยู่ในสถานะ ลา')

        # check slot must not intersect with other slot
        if action == 'swap':
            allow_duplicate = do_service('HRM:get_allow_duplicate_constraint', client.object_id, client_position)
            if allow_duplicate:
                if not allow_duplicate.allowed:
                    pa = self.filter(provider_available_slots__id__in=provider_available_slot) \
                        .exclude(status=ProviderAssign.STATUS.CANCELED)
                    if pa.exists():
                        raise serializers.ValidationError('ไม่สามารถสลับเวรได้ เนื่องจาก '
                                                          'กะเวลาที่เลือกมีช่วงเวลาทับซ้อนกับเวขของแผนกอื่น')
            else:
                raise serializers.ValidationError('ตั้งค่า AllowDuplicateConstraint ก่อน')

        # Import Nurse
        if employee_info.main_division.id != client.object_id:
            allow_duplicate = do_service('HRM:get_allow_duplicate_constraint', client.object_id, client_position)
            if allow_duplicate:
                if not allow_duplicate.allowed:
                    pa = self.filter(provider_available_slots__id__in=provider_available_slot) \
                        .exclude(status=ProviderAssign.STATUS.CANCELED)
                    if pa.exists():
                        raise serializers.ValidationError('ไม่สามารถ Tag เวรได้ เนื่องจาก '
                                                          'กะเวลาที่เลือกมีช่วงเวลาทับซ้อนกับเวลาของแผนกต้นทาง')
            else:
                raise serializers.ValidationError('ตั้งค่า AllowDuplicateConstraint ก่อน')

        provider_assign = self \
            .prefetch_related("provider_available_slots") \
            .filter(client_service_slot=client_service_slot,
                    provider_available_slots__id__in=provider_available_slot,
                    status=ProviderAssign.STATUS.DRAFTED).first()
        if provider_assign:
            provider_assign.type = type
            provider_assign.slot_status = ProviderAssign.SLOT_STATUS.RESERVED
            provider_assign.incharge = incharge
            provider_assign.user = user
            provider_assign.action = ProviderAssign.ACTION.EDIT
            provider_assign.save()
        else:
            pas_list = provider_available_slot
            provider_assign = self.create(
                client_service_slot=client_service_slot,
                type=type,
                incharge=incharge,
                action=provider_assign_action,
                user=user
            )
            provider_assign.provider_available_slots.add(*pas_list)
        return provider_assign

    def action_edit(self, provider_assign, type, user):
        if provider_assign.status == ProviderAssign.STATUS.CONFIRMED:
            raise serializers.ValidationError('ยืนยันตารางเดือนนี้แล้ว ไม่สามารถแก้ไขได้')

        if type == ProviderAssign.TYPE.NORMAL.name:
            type = ProviderAssign.TYPE.NORMAL.value
        elif type == ProviderAssign.TYPE.OT.name:
            type = ProviderAssign.TYPE.OT.value
        elif type == ProviderAssign.TYPE.HOLIDAY.name:
            type = ProviderAssign.TYPE.HOLIDAY.value

        provider_assign.type = type
        provider_assign.action = ProviderAssign.ACTION.EDIT
        provider_assign.user = user
        provider_assign.save()
        return provider_assign

    def action_confirm(self, client: Client, position: Position, be_year: int, month: int, user) -> list:
        start = do_service('penta.appointment:datetime_to_serial', be_year, month, 1, 0, 0)
        end = do_service('penta.appointment:get_last_day_of_month', be_year, month)
        end = do_service('penta.appointment:datetime_to_serial', end.year, end.month, end.day, end.hour, end.minute)

        pa_list = []
        provider_assign = self.filter(client_service_slot__client=client,
                                      client_service_slot__position=position,
                                      client_service_slot__start_slot__gte=start,
                                      client_service_slot__start_slot__lte=end) \
            .exclude(status=ProviderAssign.STATUS.CANCELED)

        if not provider_assign.exists():
            raise serializers.ValidationError('ไม่มีรายการให้ยืนยัน')

        # check hard constraint
        errors = do_service('HRM:hard_or_soft_constraint', client, position, be_year, month)
        hard = do_service('HRM:hard_constraint', errors)
        if hard:
            raise serializers.ValidationError(hard)

        # confirm
        for pa in provider_assign:
            pa.finalize = True
            pa.user = user
            pa.action = ProviderAssign.ACTION.CONFIRM
            pa.save()
            pa_list.append(pa)
        return pa_list

    def action_cancel_confirm(self, client: Client, position: Position, be_year: int, month: int, user) -> list:
        start = do_service('penta.appointment:datetime_to_serial', be_year, month, 1, 0, 0)
        end = do_service('penta.appointment:get_last_day_of_month', be_year, month)
        end = do_service('penta.appointment:datetime_to_serial', end.year, end.month, end.day, end.hour, end.minute)

        pa_list = []
        provider_assigns = self.filter(client_service_slot__client=client,
                                       client_service_slot__position=position,
                                       client_service_slot__start_slot__gte=start,
                                       client_service_slot__start_slot__lte=end,
                                       status=ProviderAssign.STATUS.CONFIRMED)
        if not provider_assigns.exists():
            raise serializers.ValidationError('ไม่มีรายการให้ ยกเลิก')

        for pa in provider_assigns:
            pa.user = user
            pa.action = ProviderAssign.ACTION.CANCEL_CONFIRM
            pa.save()
            pa_list.append(pa)
        return pa_list

    def common_off_leave(self, provider: Provider, client_service_slot: ClientServiceSlot, user, action) -> list:
        client = client_service_slot.client

        target_date = client_service_slot.start_date_time
        start = do_service('penta.appointment:datetime_to_serial',
                           target_date.year + 543, target_date.month, target_date.day, 0, 0)
        end = do_service('penta.appointment:datetime_to_serial',
                         target_date.year + 543, target_date.month, target_date.day, 23, 59)

        client_service_slot = ClientServiceSlot.objects.filter(
            client=client, start_slot__gte=start, start_slot__lte=end, active=True)
        if not client_service_slot.exists():
            raise serializers.ValidationError('ไม่พบ slot เวลาของหน่วยงาน')

        min_max_css = client_service_slot.aggregate(start=Min('start_slot'), end=Max('end_slot'))
        provider_available_slot = ProviderAvailableSlot.objects.filter(
            provider=provider, start_slot__gte=min_max_css['start'], end_slot__lte=min_max_css['end'], active=True)
        if not provider_available_slot.exists():
            raise serializers.ValidationError('ไม่พบ slot เวลาของ Provider')

        pa_id_list = []
        provider_assign = self \
            .filter(client_service_slot__in=client_service_slot, provider_available_slots__in=provider_available_slot) \
            .exclude(status=ProviderAssign.STATUS.CANCELED)

        if action == ProviderAssign.ACTION.OFF:
            slot_status = ProviderAssign.SLOT_STATUS.OFF
        elif action == ProviderAssign.ACTION.LEAVE:
            slot_status = ProviderAssign.SLOT_STATUS.LEAVE

        for css in client_service_slot:
            pa_list = list(filter(lambda pa:
                                  css.id == pa.client_service_slot.id and
                                  provider.id in pa.provider_available_slots.values_list('provider_id', flat=True),
                                  provider_assign))
            if pa_list:
                pa = pa_list[0]
                if pa.finalize:
                    do_service('MAI:cancel_appointment', pa)
                    pa.finalize = False

                pa.type = None
                pa.slot_status = slot_status
                pa.incharge = False
                pa.action = action
                pa.user = user
                pa.save()
                pa_id_list.append(pa)
            else:
                pa = self.create(client_service_slot=css,
                                 slot_status=slot_status,
                                 incharge=False,
                                 action=action,
                                 user=user)
                pas_list = list(filter(lambda pas:
                                       css.start_slot <= pas.start_slot <= css.end_slot and
                                       css.start_slot <= pas.end_slot <= css.end_slot,
                                       provider_available_slot))
                for pas in pas_list:
                    pa.provider_available_slots.add(pas)
                pa_id_list.append(pa)
        return pa_id_list

    def action_off(self, provider: Provider, client_service_slot: ClientServiceSlot, user) -> list:
        return self.common_off_leave(provider=provider, client_service_slot=client_service_slot, user=user,
                                     action=ProviderAssign.ACTION.OFF)

    def action_leave(self, provider: Provider, client_service_slot: ClientServiceSlot, leave_type, remark,
                     user) -> list:
        pa_list = self.common_off_leave(provider=provider, client_service_slot=client_service_slot, user=user,
                                        action=ProviderAssign.ACTION.LEAVE)
        do_service('HRM:request_personal_absent', pa_list, leave_type, remark, user)
        return pa_list

    def action_set_incharge(self, provider_assign, incharge: bool, user) -> list:
        provider = provider_assign.provider_available_slots.first().provider
        client_service_slot = provider_assign.client_service_slot
        client = client_service_slot.client
        position = client_service_slot.position
        start_date_time = client_service_slot.start_date_time
        employee = provider.employee
        if not (employee.employee_info.head_staff or employee.employee_info.incharge):
            raise serializers.ValidationError('%s ไม่สามารถเป็น Incharge ได้' %
                                              provider.employee.get_full_name())

        confirm_pa = self.provider_assign_one_month(client,
                                                    position,
                                                    start_date_time.year + 543,
                                                    start_date_time.month)
        if confirm_pa.filter(status=ProviderAssign.STATUS.CONFIRMED).exists():
            raise serializers.ValidationError('ยืนยันตารางเดือนนี้แล้ว ไม่สามารถแก้ไขได้')

        if incharge:
            # cancel incharge
            incharge_pa = self.filter(client_service_slot=client_service_slot, incharge=True)
            for pa in incharge_pa:
                pa.incharge = False
                pa.action = ProviderAssign.ACTION.SET_INCHARGE
                pa.user = user
                pa.save()

        provider_assign.incharge = incharge
        provider_assign.action = ProviderAssign.ACTION.SET_INCHARGE
        provider_assign.user = user
        provider_assign.save()
        return provider_assign

    def action_cancel(self, provider_assign, user, action='cancel', mobile=False) -> list:
        if not provider_assign:
            raise serializers.ValidationError('ไม่พบ Provider Assign')

        if provider_assign.status == ProviderAssign.STATUS.CONFIRMED and mobile is False:
            raise serializers.ValidationError('ยืนยันตารางเดือนนี้แล้ว ไม่สามารถแก้ไขได้')

        if provider_assign.status == ProviderAssign.STATUS.CANCELED:
            raise serializers.ValidationError('Slot ถูกยกเลิกแล้ว')

        if action == 'cancel':
            provider_assign_action = ProviderAssign.ACTION.CANCEL
        elif action == 'cancel_for_swap':
            provider_assign_action = ProviderAssign.ACTION.CANCEL_FOR_SWAP

        if provider_assign.finalize:
            do_service('MAI:cancel_appointment', provider_assign)
            provider_assign.finalize = False

        provider_assign.incharge = False
        provider_assign.user = user
        provider_assign.action = provider_assign_action
        provider_assign.save()

        return provider_assign

    @transaction.atomic
    def action_swap(self, provider: Provider, client_service_slot: ClientServiceSlot,
                    provider_2: Provider, client_service_slot_2: ClientServiceSlot,
                    user) -> list:
        """
        Swap Shift Structure

                   | css 1             |               | css 2              |
        -------------------------------------------------------------------------------
        provider 1 | XXX_source_1      |               | XXX_destination_2  |
        -------------------------------------------------------------------------------
        provider 2 | XXX_destination_1 |               | XXX_source_2       |
        -------------------------------------------------------------------------------

        """
        # define variable
        provider_source_1 = provider
        provider_source_2 = provider_2
        client_service_slot_source_1 = client_service_slot
        client_service_slot_source_2 = client_service_slot_2

        provider_assign_source_1 = \
            self.filter(client_service_slot=client_service_slot_source_1,
                        provider_available_slots__provider=provider_source_1,
                        status=ProviderAssign.STATUS.DRAFTED)\
                .prefetch_related('provider_available_slots', 'provider_available_slots__provider')

        provider_assign_source_2 = \
            self.filter(client_service_slot=client_service_slot_source_2,
                        provider_available_slots__provider=provider_source_2,
                        status=ProviderAssign.STATUS.DRAFTED)\
                .prefetch_related('provider_available_slots', 'provider_available_slots__provider')

        provider_assign_destination_1 = \
            self.filter(client_service_slot=client_service_slot_source_1,
                        provider_available_slots__provider=provider_source_2,
                        status=ProviderAssign.STATUS.DRAFTED)

        provider_assign_destination_2 = \
            self.filter(client_service_slot=client_service_slot_source_2,
                        provider_available_slots__provider=provider_source_1,
                        status=ProviderAssign.STATUS.DRAFTED)

        if provider_assign_source_1 and provider_assign_source_2:
            provider_id_source_1 = provider_assign_source_1.first().provider_available_slots.first().provider.id
            provider_id_source_2 = provider_assign_source_2.first().provider_available_slots.first().provider.id
            if provider_id_source_1 == provider_id_source_2:
                raise serializers.ValidationError("ไม่สามารถสลับเวรของพนักงานคนเดียวกันได้")

        if not (provider_assign_source_1 and provider_assign_source_2):
            raise serializers.ValidationError("ไม่สามารถสลับเวรกับกะเวลาว่างได้")

        # Checking, Are the destination slots available ?
        if provider_assign_destination_1 or provider_assign_destination_2:
            raise serializers.ValidationError("ไม่สามารถสลับเวรได้ เนื่องจากกะปลายทางมีเวรอยู่แล้ว")
        else:
            provider_assign_source_1 = provider_assign_source_1.first()
            provider_assign_source_2 = provider_assign_source_2.first()
            # create destination 2
            self.action_draft(provider=provider_source_1,
                              client_service_slot=client_service_slot_source_2,
                              type=provider_assign_source_2.type,
                              user=user, action='swap')

            # create destination 1
            self.action_draft(provider=provider_source_2,
                              client_service_slot=client_service_slot_source_1,
                              type=provider_assign_source_1.type,
                              user=user, action='swap')

            # cancel source 1
            self.action_cancel(provider_assign=provider_assign_source_1,
                               user=user, action='cancel_for_swap')
            # cancel source 2
            self.action_cancel(provider_assign=provider_assign_source_2,
                               user=user, action='cancel_for_swap')

    @transaction.atomic
    def action_swap_mobile(self, provider: Provider, client_service_slot: ClientServiceSlot,
                           provider_2: Provider, client_service_slot_2: ClientServiceSlot,
                           user, check_constraint=False) -> list:
        provider_source_1 = provider
        provider_source_2 = provider_2
        client_service_slot_source_1 = client_service_slot
        client_service_slot_source_2 = client_service_slot_2

        provider_assign_source_1 = \
            self.filter(client_service_slot=client_service_slot_source_1,
                        provider_available_slots__provider=provider_source_1) \
                .filter_swapable() \
                .prefetch_related('provider_available_slots', 'provider_available_slots__provider')

        provider_assign_source_2 = \
            self.filter(client_service_slot=client_service_slot_source_2,
                        provider_available_slots__provider=provider_source_2)\
                .filter_swapable()\
                .prefetch_related('provider_available_slots', 'provider_available_slots__provider')

        provider_assign_destination_1 = \
            self.filter(client_service_slot=client_service_slot_source_1,
                        provider_available_slots__provider=provider_source_2) \
                .filter_swapable()

        provider_assign_destination_2 = \
            self.filter(client_service_slot=client_service_slot_source_2,
                        provider_available_slots__provider=provider_source_1) \
                .filter_swapable()

        if provider_assign_source_1 and provider_assign_source_2:
            provider_id_source_1 = provider_assign_source_1.first().provider_available_slots.first().provider.id
            provider_id_source_2 = provider_assign_source_2.first().provider_available_slots.first().provider.id
            if provider_id_source_1 == provider_id_source_2:
                raise serializers.ValidationError("ไม่สามารถสลับเวรของพนักงานคนเดียวกันได้")

        if not (provider_assign_source_1 and provider_assign_source_2):
            raise serializers.ValidationError("ไม่สามารถสลับเวรกับกะเวลาว่างได้")

        # Checking, Are the destination slots available ?
        if provider_assign_destination_1 or provider_assign_destination_2:
            raise serializers.ValidationError("ไม่สามารถสลับเวรได้ เนื่องจากกะปลายทางมีเวรอยู่แล้ว")
        else:
            provider_assign_source_1 = provider_assign_source_1.first()
            provider_assign_source_2 = provider_assign_source_2.first()
            old_provider_assign_status = provider_assign_source_1.status
            # create destination 2
            destination2 = self.action_draft(
                provider=provider_source_1,
                client_service_slot=client_service_slot_source_2,
                type=provider_assign_source_2.type,
                user=user,
                action='swap',
                mobile=True
            )

            # create destination 1
            destination1 = self.action_draft(
                provider=provider_source_2,
                client_service_slot=client_service_slot_source_1,
                type=provider_assign_source_1.type,
                user=user,
                action='swap',
                mobile=True
            )

            # update to old status
            if old_provider_assign_status == ProviderAssign.STATUS.CONFIRMED:
                destination1.action = ProviderAssign.ACTION.CONFIRM
                destination1.user = user
                destination1.save()
                destination2.action = ProviderAssign.ACTION.CONFIRM
                destination2.user = user
                destination2.save()

            # cancel source 1
            self.action_cancel(
                provider_assign=provider_assign_source_1,
                user=user,
                action='cancel_for_swap',
                mobile=True
            )
            # cancel source 2
            self.action_cancel(
                provider_assign=provider_assign_source_2,
                user=user,
                action='cancel_for_swap',
                mobile=True
            )

            # check constraint
            if check_constraint:
                client = client_service_slot_source_1.client
                position = provider.employee.position
                start_date = client_service_slot_source_1.start_date_time
                be_year = start_date.year + 543
                month = start_date.month
                errors = do_service('HRM:hard_or_soft_constraint', client, position, be_year, month)
                errors = do_service('HRM:hard_constraint', errors)
                if errors:
                    error_list = []
                    for error in errors:
                        error_list.append(error['error'])
                    raise serializers.ValidationError(error_list)

    # IsNurse
    def slot_can_offer(self, source_pa, destination_provider: Provider):
        today = datetime.now()
        today_start_sr = do_service('penta.appointment:datetime_to_serial',
                                    today.year + 543, today.month, today.day, 0, 0)

        source_dt = source_pa.client_service_slot.start_date_time
        source_dt = source_dt.replace(year=source_dt.year + 543)
        start_source = source_dt - timedelta(days=30)
        end_source = source_dt + timedelta(days=30)
        source_start_sr = do_service('penta.appointment:datetime_to_serial',
                                     start_source.year, start_source.month, start_source.day, 0, 0)
        end_serial = do_service('penta.appointment:datetime_to_serial',
                                end_source.year, end_source.month, end_source.day, 23, 59)

        if source_start_sr < today_start_sr:
            start_serial = today_start_sr
        else:
            start_serial = source_start_sr

        pa = self \
            .select_related("client_service_slot__client") \
            .prefetch_related("provider_available_slots__provider") \
            .filter(client_service_slot__client=source_pa.client_service_slot.client,
                    client_service_slot__start_slot__gte=start_serial,
                    client_service_slot__start_slot__lte=end_serial,
                    slot_status=ProviderAssign.SLOT_STATUS.RESERVED)

        # source
        source_all_pa = pa \
            .filter(provider_available_slots__provider=source_pa.provider_available_slots.last().provider,
                    status__in=[ProviderAssign.STATUS.DRAFTED, ProviderAssign.STATUS.CONFIRMED])

        result = pa \
            .filter(provider_available_slots__provider=destination_provider,
                    status=ProviderAssign.STATUS.DRAFTED) \
            .exclude(client_service_slot__start_slot__in=source_all_pa.values("client_service_slot__start_slot")) \
            .exclude(client_service_slot__end_slot__in=source_all_pa.values("client_service_slot__end_slot")) \
            .exclude(client_service_slot__start_slot=source_pa.client_service_slot.start_slot) \
            .exclude(client_service_slot__end_slot=source_pa.client_service_slot.end_slot)

        return result


class ProviderAssign(StatableModel):
    class TYPE(LabeledIntEnum):
        NORMAL = 1, 'ปกติ'
        HOLIDAY = 2, 'วันหยุด'
        OT = 3, 'ล่วงเวลา'

    class SLOT_STATUS(LabeledIntEnum):
        RESERVED = 1, 'จอง'
        LEAVE = 2, 'ลา'
        OFF = 3, 'วันหยุด'

    class ACTION(LabeledIntEnum):
        DRAFT = 1
        EDIT = 2
        CONFIRM = 3
        SET_INCHARGE = 4
        SWAP = 5
        OFF = 6
        LEAVE = 7

        CANCEL = 10
        CANCEL_CONFIRM = 11
        CANCEL_FOR_SWAP = 12

    class STATUS(LabeledIntEnum):
        DRAFTED = 1, 'ร่าง'
        CONFIRMED = 2, 'ยืนยัน'
        CANCELED = 10, 'ยกเลิก'

    TRANSITION = [
        (None, ACTION.DRAFT, STATUS.DRAFTED),
        (None, ACTION.SWAP, STATUS.DRAFTED),
        (None, ACTION.OFF, STATUS.DRAFTED),
        (None, ACTION.LEAVE, STATUS.DRAFTED),

        (STATUS.DRAFTED, ACTION.EDIT, STATUS.DRAFTED),
        (STATUS.DRAFTED, ACTION.SET_INCHARGE, STATUS.DRAFTED),
        (STATUS.DRAFTED, ACTION.OFF, STATUS.DRAFTED),
        (STATUS.DRAFTED, ACTION.LEAVE, STATUS.DRAFTED),
        (STATUS.DRAFTED, ACTION.CANCEL, STATUS.CANCELED),
        (STATUS.DRAFTED, ACTION.CANCEL_FOR_SWAP, STATUS.CANCELED),
        (STATUS.DRAFTED, ACTION.CONFIRM, STATUS.CONFIRMED),

        (STATUS.CONFIRMED, ACTION.EDIT, STATUS.CONFIRMED),  # IsNurse : move to new group
        (STATUS.CONFIRMED, ACTION.CONFIRM, STATUS.CONFIRMED),
        (STATUS.CONFIRMED, ACTION.CANCEL_CONFIRM, STATUS.DRAFTED),
        (STATUS.CONFIRMED, ACTION.CANCEL_FOR_SWAP, STATUS.CANCELED),
        (STATUS.CONFIRMED, ACTION.CANCEL, STATUS.CANCELED),

    ]

    provider_available_slots = models.ManyToManyField(ProviderAvailableSlot, related_name='assign_provider_slot')
    client_service_slot = models.ForeignKey(ClientServiceSlot, related_name='assign_client_slot')
    finalize = models.BooleanField(default=False,
                                   help_text='Draft(False) -> Confirm(True) -> Draft(True) -> Confirm(True) \
                                              Draft(False) -> Confirm(True) -> Draft(True) -> Cancel(False)')
    type = EnumField(TYPE, blank=True, null=True)
    incharge = models.BooleanField(default=False, help_text='หัวหน้าเวร(1 กะ มีได้ 1 คน)')
    slot_status = EnumField(SLOT_STATUS, default=SLOT_STATUS.RESERVED)
    service_capacity = models.IntegerField(default=0, verbose_name='สามารถทำนัดหมายได้กี่รายการ',
                                           help_text='0 = ไม่กำหนด')
    source = models.IntegerField(default=0, verbose_name='id DoctorWorkSchedule')

    objects = ProviderAssignQuerySet.as_manager()

    class Meta:
        verbose_name = 'ตารางเวร'

    def __str__(self):
        return '[%s] %s' % (self.status, self.client_service_slot)

    def get_provider(self):
        provider_available_slot = self.provider_available_slots.first()
        if provider_available_slot:
            return provider_available_slot.provider
        return None

    def __provider_available_slots__(self):
        result = []
        for pas in self.provider_available_slots.all():
            result.append('%s provider: %s<br>%s(%s)<br>%s(%s)' % (
                pas.id,
                pas.provider,
                pas.start_date_time.strftime('%d/%m/%y %H:%M'),
                pas.start_slot,
                pas.end_date_time.strftime('%d/%m/%y %H:%M'),
                pas.end_slot))
        return " , ".join(result)

    __provider_available_slots__.allow_tags = True

    def __client_service_slot__(self):
        slot_label = ''
        if self.client_service_slot.slot:
            slot_label = self.client_service_slot.slot.label
        return '%s client: %s<br>%s<br>%s(%s)<br>%s(%s)' % (
            self.client_service_slot.id,
            self.client_service_slot.client,
            slot_label,
            self.client_service_slot.start_date_time.strftime('%d/%m/%y %H:%M'),
            self.client_service_slot.start_slot,
            self.client_service_slot.end_date_time.strftime('%d/%m/%y %H:%M'),
            self.client_service_slot.end_slot)

    __client_service_slot__.allow_tags = True


class ProviderAssignActionLog(BaseActionLog(ProviderAssign)):
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Provider Assign Action Log'


class AppointmentUserTimeslotManager(models.QuerySet):
    def create_timeslot(self, appointment, user, timeslot, timeslot_end, status):
        obj = AppointmentUserTimeslot()
        obj.appointment = appointment
        obj.user = user
        obj.timeslot = timeslot
        obj.timeslot_end = timeslot_end
        obj.status = status
        obj.save()
        return obj


class AppointmentUserTimeslot(models.Model):
    id = models.AutoField(primary_key=True)

    appointment = models.ForeignKey(Appointment, related_name='app_timeslot')
    service_appointment = models.ForeignKey(ServiceAppointment, blank=True, null=True, related_name='sa_timeslot')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)  # Owner + Invite
    timeslot = models.IntegerField(default=0, db_index=True)
    timeslot_end = models.IntegerField(default=0, db_index=True)

    user_available_slot = models.ForeignKey(UserAvailableSlot, null=True, blank=True, default=None)
    provider_available_slot = models.ForeignKey(ProviderAvailableSlot, null=True, blank=True, default=None)
    provider_assigns = models.ManyToManyField(ProviderAssign, blank=True, related_name='app_provider_assign')

    status = models.CharField(max_length=40, null=True, blank=True, default="")
    is_owner = models.BooleanField(default=False)
    is_answer = models.BooleanField(default=False)
    is_ok = models.BooleanField(default=False, db_index=True)  # should not be TRUE if is_answer=FALSE
    is_finalize = models.BooleanField(default=False)
    objects = AppointmentUserTimeslotManager.as_manager()

    class Meta:
        unique_together = ('appointment', 'user', 'timeslot', 'timeslot_end')

    @property
    def start_time(self):
        return do_service('penta.appointment:serial_to_datetime', self.timeslot)

    @property
    def start_time_utc(self):
        return do_service('penta.appointment:serial_to_datetime_utc', self.timeslot)

    @property
    def end_time(self):
        return do_service('penta.appointment:serial_to_datetime', self.timeslot_end)

    @property
    def end_time_utc(self):
        return do_service('penta.appointment:serial_to_datetime_utc', self.timeslot_end)


class SwapShiftBroadcastQuerySet(models.QuerySet):
    def reject_expired_shift(self):
        user = User.objects.get_system_user()

        today = datetime.now()
        start = do_service('penta.appointment:datetime_to_serial', today.year + 543, today.month, today.day, 23, 59)

        # reject SwapShiftBroadcast
        swap_shift_broadcasts = self \
            .filter(source_provider_assign__client_service_slot__start_slot__lte=start,
                    status=SwapShiftBroadcast.STATUS.REQUESTED)
        for ssb in swap_shift_broadcasts:
            ssb.isnurse_reject(user=user, action_log='Expired.')

        # reject SwapShiftRequest
        swap_shift_requests = SwapShiftRequest.objects \
            .filter(destination_assign_slot__client_service_slot__start_slot__lte=start,
                    status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])
        for ssr in swap_shift_requests:
            ssr.isnurse_reject(user=user, action_log="Destination expired.")


class SwapShiftBroadcast(StatableModel):
    class ACTION(LabeledIntEnum):
        REQUEST = 1
        APPROVE = 2

        REJECT = 10
        CANCEL = 11

    class STATUS(LabeledIntEnum):
        REQUESTED = 1, 'Request'
        APPROVED = 3, 'Approve'

        REJECTED = 10, 'Reject'
        CANCELED = 11, 'Cancel'

    TRANSITION = [
        (None, ACTION.REQUEST, STATUS.REQUESTED),
        (STATUS.REQUESTED, ACTION.APPROVE, STATUS.APPROVED),
        (STATUS.REQUESTED, ACTION.REJECT, STATUS.REJECTED),
        (STATUS.REQUESTED, ACTION.CANCEL, STATUS.CANCELED)
    ]

    source_provider_assign = models.ForeignKey(ProviderAssign, related_name='source_pa')

    objects = SwapShiftBroadcastQuerySet.as_manager()

    def __str__(self):
        return '[%s] %s<br>CSS:%s<br>PAS:%s' % (
            self.status.name,
            self.id,
            self.source_provider_assign.client_service_slot.id,
            [i for i in self.source_provider_assign.provider_available_slots.values_list('id', flat=True)])

    def approve(self, user: User):
        self.user = user
        self.action = SwapShiftBroadcast.ACTION.APPROVE
        self.save()

    def isnurse_cancel(self, user, action_log=None):
        # cancel SwapShiftBroadcast
        self.user = user
        self.action = SwapShiftBroadcast.ACTION.CANCEL

        if action_log:
            self.action_log_kwargs = {'note': action_log}

        self.save()

        # reject SwapShiftRequest
        swap_shift_requests = SwapShiftRequest.objects \
            .filter(broadcast=self,
                    status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])
        for ssr in swap_shift_requests:
            ssr.isnurse_reject(user=user, action_log="Cancel broadcast.")

    def isnurse_reject(self, user: User, action_log=None):
        # cancel SwapShiftBroadcast
        self.user = user
        self.action = SwapShiftBroadcast.ACTION.REJECT

        if action_log:
            self.action_log_kwargs = {'note': action_log}

        self.save()

        # reject SwapShiftRequest
        swap_shift_requests = SwapShiftRequest.objects \
            .filter(broadcast=self,
                    status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])
        for ssr in swap_shift_requests:
            ssr.isnurse_reject(user=user, action_log="Cancel broadcast.")


class SwapShiftBroadcastActionLog(BaseActionLog(SwapShiftBroadcast)):
    note = models.TextField(blank=True)


class SwapShiftRequestQuerySet(models.QuerySet):
    def filter_active(self):
        return self.exclude(status=SwapShiftRequest.STATUS.CANCELED)


class SwapShiftRequest(StatableModel):
    class ACTION(LabeledIntEnum):
        REQUEST = 1
        ACCEPT = 2
        APPROVE = 3

        REJECT = 10
        CANCEL = 11
        CANCEL_CONFIRM = 12

    class STATUS(LabeledIntEnum):
        REQUESTED = 1, 'ส่งคำขอ'
        PENDING_APPROVE = 2, 'รอการยืนยัน'
        APPROVED = 3, 'ยืนยัน'

        REJECTED = 10, 'ปฏิเสธ'
        CANCELED = 11, 'ยกเลิก'

    TRANSITION = [
        (None, ACTION.REQUEST, STATUS.REQUESTED),
        (STATUS.REQUESTED, ACTION.ACCEPT, STATUS.PENDING_APPROVE),
        (STATUS.REQUESTED, ACTION.REJECT, STATUS.REJECTED),
        (STATUS.REQUESTED, ACTION.CANCEL, STATUS.CANCELED),
        (STATUS.PENDING_APPROVE, ACTION.APPROVE, STATUS.APPROVED),
        (STATUS.PENDING_APPROVE, ACTION.REJECT, STATUS.REJECTED),
        (STATUS.PENDING_APPROVE, ACTION.CANCEL, STATUS.CANCELED),
    ]

    source_assign_slot = models.ForeignKey(ProviderAssign, related_name='source_swap')
    destination_assign_slot = models.ForeignKey(ProviderAssign, related_name='destination_swap')

    broadcast = models.ForeignKey(SwapShiftBroadcast, blank=True, null=True, related_name='swap_req')

    objects = SwapShiftRequestQuerySet.as_manager()

    class Meta:
        verbose_name = 'รายการขอแลกเวร'

    def __str__(self):
        return '[%s] %s -> %s' % (self.status, self.source_assign_slot, self.destination_assign_slot)

    @property
    def source_provider(self):
        return self.source_assign_slot.get_provider()

    @property
    def destination_provider(self):
        return self.destination_assign_slot.get_provider()

    def send_request_notification(self):
        source_provider_name = self.source_provider.employee.get_full_name()
        destination_user = self.destination_provider.employee.user
        if destination_user:
            fcm_tokens = destination_user.get_fcm_tokens()
            push_service = FCMNotification(api_key=config.HRM_FCM_SERVER_KEY)
            message_title = 'You have new request change shift!'
            message_body = 'request from %s' % source_provider_name
            data_message = {'type': 'SWAP_REQUEST'}
            push_service.notify_multiple_devices(registration_ids=fcm_tokens, message_title=message_title,
                                                 message_body=message_body, data_message=data_message)

    def send_accept_notification(self):
        destination_provider_name = self.destination_provider.employee.get_full_name()
        source_user = self.source_provider.employee.user
        if source_user:
            fcm_tokens = source_user.get_fcm_tokens()
            push_service = FCMNotification(api_key=config.HRM_FCM_SERVER_KEY)
            message_title = 'Your request has been accept!'
            message_body = 'accept from %s' % destination_provider_name
            data_message = {'type': 'SWAP_REQUEST'}
            push_service.notify_multiple_devices(registration_ids=fcm_tokens, message_title=message_title,
                                                 message_body=message_body, data_message=data_message)

    def send_approve_notification(self):
        source_user = self.source_provider.employee.user
        destination_user = self.destination_provider.employee.user

        push_service = FCMNotification(api_key=config.HRM_FCM_SERVER_KEY)
        message_title = 'Your swap shift has been aproved!'
        message_body = ''
        data_message = {'type': 'SWAP_REQUEST'}

        if source_user:
            fcm_tokens = source_user.get_fcm_tokens()
            push_service.notify_multiple_devices(registration_ids=fcm_tokens, message_title=message_title,
                                                 message_body=message_body, data_message=data_message)
        if destination_user:
            fcm_tokens = destination_user.get_fcm_tokens()
            push_service.notify_multiple_devices(registration_ids=fcm_tokens, message_title=message_title,
                                                 message_body=message_body, data_message=data_message)

    def send_reject_notification(self, send_to_destination=False):
        source_user = self.source_provider.employee.user
        destination_user = self.destination_provider.employee.user
        if self.user.employee:
            rejected_name = self.user.employee.get_full_name()
        else:
            rejected_name = self.user.get_full_name()
        push_service = FCMNotification(api_key=config.HRM_FCM_SERVER_KEY)
        message_title = 'Your request has been reject!'
        message_body = 'reject from %s' % rejected_name
        data_message = {'type': 'SWAP_REQUEST'}

        if source_user:
            fcm_tokens = source_user.get_fcm_tokens()
            push_service.notify_multiple_devices(registration_ids=fcm_tokens, message_title=message_title,
                                                 message_body=message_body, data_message=data_message)
        if send_to_destination and destination_user:
            fcm_tokens = destination_user.get_fcm_tokens()
            push_service.notify_multiple_devices(registration_ids=fcm_tokens, message_title=message_title,
                                                 message_body=message_body, data_message=data_message)

    @classmethod
    def common_request(self, source_assign_slot_id, destination_assign_slot_id, user, broadcast=None):
        source_assign_slot = ProviderAssign.objects.filter(pk=source_assign_slot_id).first()
        destination_assign_slot = ProviderAssign.objects.filter(pk=destination_assign_slot_id).first()
        if not (source_assign_slot or destination_assign_slot or user):
            raise serializers.ValidationError({
                'non_field_errors': 'กรุณาระบุ source_assign_slot หรือ destination_assign_slot หรือ user ให้ถูกต้อง'
            })
        swap_shift_request = SwapShiftRequest()
        swap_shift_request.source_assign_slot = source_assign_slot
        swap_shift_request.destination_assign_slot = destination_assign_slot
        swap_shift_request.broadcast = broadcast
        swap_shift_request.action = SwapShiftRequest.ACTION.REQUEST
        swap_shift_request.user = user
        swap_shift_request.save()
        return swap_shift_request

    @classmethod
    def request(self, source_assign_slot_id, destination_assign_slot_id, user):
        swap_shift_request = self.common_request(source_assign_slot_id=source_assign_slot_id,
                                                 destination_assign_slot_id=destination_assign_slot_id,
                                                 user=user)

        swap_shift_request.send_request_notification()

    def common_accept(self, user):
        self.action = SwapShiftRequest.ACTION.ACCEPT
        self.user = user
        self.save()

    def accept(self, user):
        self.common_accept(user=user)

        Messenger.push_to_screen(
            screen='MainHRM',
            source='HRM',
            event='notification_to_screen',
        )
        self.send_accept_notification()

    def isnurse_accept(self, user):
        if self.source_assign_slot.status != ProviderAssign.STATUS.DRAFTED or \
           self.source_assign_slot.slot_status != ProviderAssign.SLOT_STATUS.RESERVED:
            raise serializers.ValidationError({"source_slot": "Invalid status."})
        elif self.destination_assign_slot.status != ProviderAssign.STATUS.DRAFTED or \
                self.destination_assign_slot.slot_status != ProviderAssign.SLOT_STATUS.RESERVED:
            raise serializers.ValidationError({"destination_slot": "Invalid status."})

        # accept
        self.common_accept(user=user)

        # approve
        ProviderAssign.objects.action_swap(
            provider=self.source_assign_slot.provider_available_slots.last().provider,
            client_service_slot=self.source_assign_slot.client_service_slot,
            provider_2=self.destination_assign_slot.provider_available_slots.last().provider,
            client_service_slot_2=self.destination_assign_slot.client_service_slot,
            user=user)

        self.common_approve(user=user)

        broadcast = self.broadcast
        broadcast.approve(user=user)

        # send message
        do_service("MSG:accept_offer", self.request, self)

        # reject offer by broadcast
        swap_shift_requests = SwapShiftRequest.objects \
            .filter(broadcast=self.broadcast,
                    status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])
        for ssr in swap_shift_requests:
            ssr.isnurse_reject(user=user, action_log="User selected other shift.")

        # reject request by using this slot
        swap_shift_requests = SwapShiftRequest.objects.filter(
            Q(source_assign_slot=self.source_assign_slot) |
            Q(destination_assign_slot=self.source_assign_slot) |
            Q(source_assign_slot=self.destination_assign_slot) |
            Q(destination_assign_slot=self.destination_assign_slot))
        swap_shift_requests = swap_shift_requests.filter(
            status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])
        for ssr in swap_shift_requests:
            ssr.isnurse_reject(user=user, action_log="Slot unavailable.")

            # send message
            do_service("MSG:reject_offer", self.request, ssr)

        swap_shift_broadcast = SwapShiftBroadcast.objects.filter(
            Q(source_provider_assign=self.source_assign_slot) | Q(source_provider_assign=self.destination_assign_slot))
        swap_shift_broadcast = swap_shift_broadcast.filter(status=SwapShiftBroadcast.STATUS.REQUESTED)
        for ssb in swap_shift_broadcast:
            ssb.isnurse_reject(user=user, action_log="Slot unavailable.")

        # reject request can not offer
        provider = user.employee.provider.last()
        swap_shift_requests = SwapShiftRequest.objects \
            .filter(source_assign_slot__provider_available_slots__provider=provider,
                    status__in=[SwapShiftRequest.STATUS.REQUESTED, SwapShiftRequest.STATUS.PENDING_APPROVE])
        for ssr in swap_shift_requests:
            if self.destination_assign_slot.client_service_slot.start_slot == \
               ssr.destination_assign_slot.client_service_slot.start_slot:
                ssr.isnurse_reject(user=user, action_log="Can not offer.")

    def common_approve(self, user):
        self.action = SwapShiftRequest.ACTION.APPROVE
        self.user = user
        self.save()

    def approve(self, user):
        source_provider = self.source_assign_slot.provider_available_slots.first().provider
        destination_provider = self.destination_assign_slot.provider_available_slots.first().provider
        source_client_service_slot = self.source_assign_slot.client_service_slot
        destination_client_service_slot = self.destination_assign_slot.client_service_slot
        ProviderAssign.objects.action_swap_mobile(
            source_provider,
            source_client_service_slot,
            destination_provider,
            destination_client_service_slot,
            user,
            True)

        self.common_approve(user=user)

        self.send_approve_notification()

    def common_reject(self, user, action_log=None):
        self.action = SwapShiftRequest.ACTION.REJECT
        self.user = user

        if action_log:
            self.action_log_kwargs = {'note': action_log}

        self.save()

    def reject(self, user):
        self.common_reject(user=user)
        send_to_destination = True if self.status == SwapShiftRequest.STATUS.PENDING_APPROVE else False
        self.send_reject_notification(send_to_destination)

    def isnurse_reject(self, user, action_log=None):
        self.common_reject(user=user, action_log=action_log)

        # send message
        do_service("MSG:reject_offer", self.request, self)

    def cancel(self, user):
        self.action = SwapShiftRequest.ACTION.CANCEL
        self.user = user
        self.save()


class SwapShiftRequestActionLog(BaseActionLog(SwapShiftRequest)):
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Swap Shift Request Action Log'


class RemarkAppointmentManager(models.QuerySet):

    def create_remark(self, key, remark, appointment, service_app=None):
        obj = Remark()
        obj.key = key
        obj.appointment = appointment
        obj.service_appointment = service_app
        obj.remark = remark
        obj.save()

        return obj


class Remark(models.Model):
    key = models.CharField(max_length=40)
    appointment = models.ForeignKey(Appointment, blank=True, null=True, related_name='remark_app')
    service_appointment = models.ForeignKey(ServiceAppointment, blank=True, null=True, related_name='remark_sa')
    remark = models.TextField(null=True, blank=True, default="")
    create_at = models.DateTimeField(auto_now_add=True)
    objects = RemarkAppointmentManager.as_manager()
