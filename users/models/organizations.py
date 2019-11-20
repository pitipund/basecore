import logging

from django.apps import apps
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Max
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from constance import config
from model_utils import FieldTracker

from his.framework.models import EnumField, SelfReferenceForeignKey
from his.framework.utils import LabeledIntEnum, do_service

logger = logging.getLogger(__name__)

__all__ = [
    'Organization', 'Position', 'Employee',
    'Duty', 'AnnualLeave', 'EmployeeInfo'
]


class Organization(models.Model):
    class LEVEL(LabeledIntEnum):
        DEPARTMENT = 1  # DEP
        SECTION = 2  # SEC
        UNIT = 3  # UNIT
        DIVISION = 4  # DIV
        EDUCATION = 5  # E

    class STATUS(LabeledIntEnum):
        ACTIVE = 1  # A
        INACTIVE = 2  # C

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200, blank=True)
    organization_parent = SelfReferenceForeignKey(null=True, blank=True)
    organization_level = EnumField(LEVEL, null=True, blank=True)
    jc_code = models.CharField(max_length=20, blank=True)
    telephone_1 = models.CharField(max_length=20, blank=True)
    telephone_2 = models.CharField(max_length=20, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = EnumField(STATUS)

    def __str__(self):
        return self.name


class Position(models.Model):
    code = models.CharField(max_length=10, default='')
    name = models.CharField(max_length=500, verbose_name='ชื่อตำแหน่งงาน')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class EmployeeQuerySet(models.QuerySet):
    def get_by_username(self, username):
        """Zero-pad username to get Employee code"""
        return self.get(code=username.zfill(config.users_EMPLOYEE_CODE_LENGTH))


class Employee(models.Model):
    class STATUS(LabeledIntEnum):
        ACTIVE = 1  # A
        INACTIVE = 2  # C

    code = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    position = models.ForeignKey(Position)
    licence = models.CharField(max_length=20, blank=True)
    organization = models.ForeignKey(Organization)
    personnel_no = models.CharField(max_length=20, blank=True)
    citizen_no = models.CharField(max_length=20, blank=True)
    job_description = models.CharField(max_length=200, blank=True)
    flag_start_date = models.DateField()
    flag_end_date = models.DateField()
    status = EnumField(STATUS)
    birth_date = models.DateField()

    provider = GenericRelation('appointment.Provider', related_query_name='employees')
    tracker = FieldTracker(fields=['licence'])

    objects = EmployeeQuerySet.as_manager()

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

    def is_expired(self):
        now = timezone.now().date()
        if self.flag_start_date <= now and self.flag_end_date >= now:
            return False
        else:
            return True

    @property
    def user(self):
        return self.user_employee.first()

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    @property
    def formatted_code(self):
        if self.code[:2] == '00' and len(self.code) == 8:
            return self.code[2:]
        else:
            return self.code

    @property
    def main_division(self):
        if self.employee_info:
            return self.employee_info.main_division
        return None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # ส่ง update interface เมื่อมีการเพิ่มข้อมูล employee licence
        changed = self.tracker.changed()
        if ('licence' in changed) and not self.tracker.previous('licence'):
            apps.get_model('core', 'Diagnosis').objects.filter(
                emr__doctor__user__employee__pk=self.pk).update(edited=timezone.now())
            apps.get_model('core', 'Procedure').objects.filter(
                emr__doctor__user__employee__pk=self.pk).update(edited=timezone.now())

        super().save(force_insert, force_update, using, update_fields)


class DutyQuerySet(models.QuerySet):
    def get_duty_by_division_position(self, division, position):
        duty = EmployeeInfo.objects \
            .select_related('main_division', 'duty__position') \
            .filter(main_division=division, duty__position=position, duty__active=True) \
            .values('duty')
        return Duty.objects.filter(id__in=duty.distinct())


class Duty(models.Model):
    """หน้าที่ของพนักงาน เช่น position เป็น พยาบาล จะมี duty เป็น RN, PN, AN"""
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=250)
    active = models.BooleanField(default=True)
    position = models.ForeignKey(Position)
    display_seq = models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')

    objects = DutyQuerySet.as_manager()

    class Meta:
        ordering = ('display_seq', 'id')

    def __str__(self):
        return '[%s] %s' % (self.code, self.name)


class AnnualLeave(models.Model):
    max_experince_year = models.IntegerField(verbose_name='อายุงานไม่เกิน x ปี',
                                             help_text='Example: อายุงานไม่เกิน 6 ปี สามารถลาพักร้อนได้ 6 วัน')
    day_off = models.IntegerField(default=1, verbose_name='จำนวนวันที่ลาพักร้อนได้')

    class Meta:
        verbose_name = 'กำหนดจำนวนวันลาพักร้อน'

    def __str__(self):
        return ' อายุงานไม่เกิน %s ปี สามารถลาพักร้อนได้ %s วัน' % (self.max_experince_year, self.day_off)


class EmployeeInfo(models.Model):
    """รายละเอียดเพิ่มเติมของ Employee"""
    employee = models.OneToOneField(Employee, related_name='employee_info')
    head_staff = models.BooleanField(default=False, help_text='หัวหน้าแผนก')
    incharge = models.BooleanField(default=False, help_text='สามารถเป็นหัวหน้าเวร')
    main_division = models.ForeignKey('core.Division', null=True, blank=True, related_name='ef_main_divisions')
    duty = models.ForeignKey(Duty, null=True, blank=True, related_name='employee_info')

    @property
    def level(self):
        experience_year, experience_month, experience_day = self.get_experience()
        if experience_year <= config.users_MAX_EXPERIENCE_FOR_LEVEL1:
            return 1
        elif experience_year <= config.users_MAX_EXPERIENCE_FOR_LEVEL2:
            return 2
        else:
            return 3

    @property
    def max_annual_leave_day(self):
        experience_year, experience_month, experience_day = self.get_experience()
        if experience_year >= 1:
            annual_leave = AnnualLeave.objects.filter(max_experince_year__gte=experience_year) \
                .order_by('max_experince_year').values('day_off').first()
            if annual_leave:
                return annual_leave['day_off']
            annual_leave = AnnualLeave.objects.aggregate(Max('day_off'))
            return annual_leave['day_off__max']
        return 0

    def left_annual_leave_day(self, be_year, duration):
        max_leave = self.max_annual_leave_day
        start = do_service('penta.appointment:datetime_to_serial', be_year, 1, 1, 0, 0)
        end = do_service('penta.appointment:datetime_to_serial', be_year, 12, 31, 23, 59)

        PersonalAbsent = apps.get_model('HRM', 'PersonalAbsent')
        absents = do_service('HRM:get_personal_absent',
                             self.employee.id, start, end, PersonalAbsent.LEAVE_TYPE.ANNUAL_LEAVE)

        one_day = (60 / duration) * 24  # 60=minutes, 24=hours
        my_leave = absents.count() // one_day
        if max_leave:
            return max_leave - my_leave
        else:
            return 0

    def get_experience(self):
        start_date = self.employee.flag_start_date
        end_date = timezone.now().date()
        diff = relativedelta(end_date, start_date)
        return diff.years, diff.months, diff.days

    def __str__(self):
        return '[%s] %s' % (self.employee, self.main_division)
