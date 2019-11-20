import json
import logging
import operator
import os
import re
import time as import_time
import traceback
from abc import abstractmethod
from contextlib import contextmanager
from datetime import datetime, date, timedelta, time
from functools import reduce
from typing import Union, List, Tuple, Optional

import requests
from constance import config
from dateutil import relativedelta
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db.utils import ProgrammingError, OperationalError
from django.db import models
from django.db import transaction
from django.db.models import Q, F, Max
from django.db.models.deletion import get_candidate_relations_to_delete, DO_NOTHING
from django.db.models.functions import Concat
from django.dispatch import Signal
from django.utils import timezone
from django.utils.safestring import mark_safe
from jsonfield import JSONField
from model_utils import FieldTracker
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from six import BytesIO

from his.core import utils
from his.core.exceptions import RecordLockedException, RecordNotLockedException
from his.core.services import Messenger
from his.core.utils import damm_encode, week_number, ad_to_be, be_to_ad, sort_by_id, convert_to_date, format_date, \
    ImageTransition
from his.core.variants import HNGenerator
from his.framework import barcode
from his.framework.models import EditableModel, AbstractCheckerModelMixin, StatableModel, BaseActionLog, EnumField
from his.framework.models.fields import SelfReferenceForeignKey
from his.framework.models.functions import Replace
from his.framework.utils import validate_english, LabeledIntEnum, do_service, _, get_context_language, get_language
from his.users.models import User, Location

logger = logging.getLogger(__name__)

LANGUAGE_TH = 'TH'
LANGUAGE_EN = 'EN'
LANGUAGE_CHOICES = (
    (LANGUAGE_TH, 'Thai'),
    (LANGUAGE_EN, 'English'),
)

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
)

PREFIX_BARCODE_HN = 'A00'
PREFIX_BARCODE_ENCOUNTER = 'A01'
PREFIX_BARCODE_ENCOUNTER_OPD_NUMBER = 'A02'
PREFIX_BARCODE_ENCOUNTER_IPD_NUMBER = 'A03'
PREFIX_BARCODE_ENCOUNTER_SSS_NUMBER = 'A04'
PREFIX_BARCODE_DIVISION = 'D00'


class PRICE_TYPE(LabeledIntEnum):
    RGL = 1, 'ราคาในเวลาราชการ'
    SPC = 2, 'ราคาคลินิกพิเศษ'
    PRV = 3, 'ราคา รพ.เอกชน'
    PRM = 4, 'ราคา พรีเมี่ยม'
    RPX = 5, 'ราคาโครงการ RPX'
    NRS = 6, 'ราคาชาวต่างชาติ'


class ELIGIBILITY_TYPE(LabeledIntEnum):
    TREATMENT = 1, 'เพื่อการรักษา'
    BEAUTY = 2, 'เพื่อเสริมสวย'
    PATIENT_PAY = 3, 'ผู้ป่วยแสดงความจำนงชำระเงินเอง'
    NOT_INDICATOR = 4, 'ใช้ไม่ตรงข้อบ่งชี้'
    SELF_REIMB = 5, 'ผู้ป่วยนำไปเบิกเอง'
    # (ELIGIBILITY_NO_REIMB_CODE, 'ทะเบียนที่ รพ.ห้ามใช้สิทธิเบิก'),
    # (ELIGIBILITY_HOSPITAL_REIMB_CODE, 'ทะเบียนที่รพ.รองรับค่าใช้จ่าย'),
    # (ELIGIBILITY_INCLUDE_OPERATIVE_CODE, 'เหมารวมในหัตถการ'),


class OPERATING_ROLES(LabeledIntEnum):
    CHIEF_SURGEON = 1, 'Chief Surgeon'
    ASSISTANT_SURGEON = 2, 'Assistant Surgeon'
    SCRUB_NURSE = 3, 'Scrub Nurse'
    CIRCULATION_NURSE = 4, 'Circulation Nurse'
    ANESTHESIOLOGIST = 5, 'Anesthesiologist'
    ANESTHETIST = 6, 'Anesthetist'


# ====================================================================== FRAMEWORK MODEL ===============================


class ChoiceModel(models.Model):
    """Base object for create the combobox choices
    Just extend this class and implement Meta verbose_name method
    """
    name = models.CharField(max_length=500, verbose_name='ชื่อของตัวเลือก')
    display_seq = models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')
    is_active = models.BooleanField(default=True)

    @classmethod
    def get_choices(cls):
        return cls.objects.filter(is_active=True).order_by('display_seq', 'name')

    class Meta:
        abstract = True
        ordering = ('-is_active', 'display_seq')

    def __str__(self):
        if self.is_active:
            return '[%s] %s ✔' % (self.display_seq, self.name)
        else:
            return '[%s] %s ✖' % (self.display_seq, self.name)


class BillableModel(AbstractCheckerModelMixin, models.Model):
    """ an ancestor model for every model which is able to charge a medical fee """

    @abstractmethod
    def get_product(self) -> 'Product':
        """ a product which is ordered and will be used in receipt detail """
        pass

    @abstractmethod
    def get_quantity(self) -> int:
        """ a quantity of product or service used for price calculation (only when pricing structure is not provided)"""
        pass

    @abstractmethod
    def get_encounter(self) -> 'Encounter':
        """ an encounter which is related to this order. """
        pass

    @abstractmethod
    def get_requesting_division(self) -> 'Division':
        """ a division which requested this order. eg. "คลินิกผู้สูงอายุ, คลินิกเด็ก, ห้องผู้ป่วยฉุกเฉิน" """
        pass

    @abstractmethod
    def get_performing_division(self) -> 'Division':
        """ a division which performed this order. eg. "ห้องยา1, ห้องเวชภัณฑ์2, ห้องผ่าตัด" """
        pass

    @abstractmethod
    def get_perform_datetime(self) -> Union[datetime, None]:
        """ if a related service has been performed, return a perform datetime, else return None """
        pass

    def get_alternative_products(self) -> List['Product']:
        """ list of available products in coupon when this billable is pledged """
        return [self.get_product()]

    def get_order(self) -> 'BaseDoctorOrder':
        """
        :return: BaseDoctorOrder which related to this model.
        """
        return self

    def get_bill_display_name(self) -> str:
        """ a name of ordering type. eg. "รายการสั่งยา, รายการสั่งเวชภัณฑ์, รายการสั่งผ่าตัด". """
        return BillDisplayName.get_display_name(self.get_order())

    def get_bill_mode(self):
        """ overide this function to force setting bill_mode to invoice item """
        return None

    def get_unit_price(self):
        """ override this function to force bill not using price from Pricing
        and you need to override get_bill_mode when override this function"""
        return None

    def get_order_sequence(self):
        order = self.get_order()
        items = sort_by_id(order.get_staging_items())
        seq = 0
        for item in items:
            seq += 1
            if item.pk == self.pk:
                break
        return seq

    def get_order_perform_user(self):
        order = self.get_order()
        if order and isinstance(order, BaseDoctorOrder):
            return order.order_perform_by
        return None

    def get_order_user(self):
        order = self.get_order()
        if order and isinstance(order, BaseDoctorOrder):
            return order.order_by.user
        return None

    def get_business_date(self):
        return None

    @classmethod
    def get_descendants(cls):
        children = []
        subclasses = cls.__subclasses__().copy()
        while subclasses:
            subclass = subclasses.pop()
            subclasses.extend(subclass.__subclasses__().copy())
            if not subclass._meta.abstract:
                children.append(subclass)

        return children

    def _check_no_cost_center(self):
        no_cost_center = []

        requesting_division = self.get_requesting_division()
        if requesting_division and not requesting_division.cost_center:
            no_cost_center.append(str(requesting_division))

        performing_division = self.get_performing_division()
        if performing_division and not performing_division.cost_center:
            no_cost_center.append(str(performing_division))

        if no_cost_center:
            raise ValidationError(
                _('ไม่สามารถบันทึกได้ เนื่องจากยังไม่ได้ตั้งค่ารหัสหน่วยต้นทุน ของ {}').format(
                    ', '.join(no_cost_center)
                )
            )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if config.core_REQUIRE_DIVISION_COSTCENTER:
            self._check_no_cost_center()

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True


class RunningNumberManager(models.Manager):
    MAX_RETRIES = 5

    def get_next_number(self, type: models.Model, prefix='', reset=None):
        type = ContentType.objects.get_for_model(type)
        num = self.filter(type=type, prefix=prefix).first()
        if num:
            for retry in range(RunningNumberManager.MAX_RETRIES):
                date_diff = (timezone.now().date() - num.reset_date.date()).days
                reset_date = timezone.now()
                if reset == RunningNumber.RESET_DAILY and date_diff >= 1:
                    number = 1
                elif reset == RunningNumber.RESET_WEEKLY and date_diff >= 7:
                    number = 1
                else:
                    reset_date = num.reset_date
                    number = num.number

                row_affected = (self.filter(type=type, number=num.number, prefix=prefix)
                                .update(number=number + 1, reset_date=reset_date))
                if row_affected == 1:
                    return number
                elif row_affected == 0:
                    # we failed to optimistic update this row
                    num = self.filter(type=type, prefix=prefix).first()
                else:
                    logger.error('Many row with same type found!!!')
            raise Exception('Maximum retry exceeded')
        else:
            self.create(type=type, prefix=prefix, number=2, reset_date=timezone.now())
            return 1

    def get_next_number_with_formatted_prefix(self, type: models.Model, prefix='', pattern='%s%s'):
        if re.compile('.*%.*%.*').match(pattern) is None:
            raise ValueError('pattern must contains two %')
        return pattern % (prefix, self.get_next_number(type, prefix))

    def get_current_number(self, type: models.Model, prefix=''):
        """Return current counting number of given model"""
        type = ContentType.objects.get_for_model(type)
        num = self.filter(type=type, prefix=prefix).first()

        if num:
            return num.number - 1
        else:
            return 0


class RunningNumber(models.Model):
    """This table store running number for each (type, prefix)

    it store next available number to use"""
    RESET_DAILY = 1
    RESET_WEEKLY = 2

    type = models.ForeignKey(ContentType)
    prefix = models.CharField(max_length=16)
    number = models.IntegerField(default=1)
    reset_date = models.DateTimeField()
    objects = RunningNumberManager()

    class Meta:
        unique_together = ('type', 'prefix')


# ================================================================== PRESET MASTER DATA ================================

class Prename(ChoiceModel):
    """คำนำหน้าชื่อ"""
    PRENAME_GENDER_CHOICES = GENDER_CHOICES + (
        ('U', 'ไม่ระบุ'),
    )
    name = models.CharField(max_length=20, help_text="คำนำหน้าชื่อ")
    language = models.CharField(max_length=2, default='TH', choices=LANGUAGE_CHOICES)
    gender = models.CharField(max_length=1, default='M', choices=PRENAME_GENDER_CHOICES, verbose_name="เพศ")

    class Meta:
        ordering = ['display_seq']

    def __str__(self):
        return self.name


class ContactChannel(models.Model):
    code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=20)

    class Meta:
        managed = True

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)


class HomeType(ChoiceModel):
    code = models.CharField(max_length=4, unique=True)

    class Meta:
        managed = True

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)


class City(ChoiceModel):
    code = models.CharField(max_length=10, unique=True)
    name_en = models.CharField(max_length=40)
    area = models.ForeignKey('District', related_name='city_district', blank=True, null=True)
    zipcode = models.CharField(max_length=10)

    class Meta:
        managed = True

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)


class District(ChoiceModel):
    name_en = models.CharField(max_length=50)
    area = models.ForeignKey('Province', related_name='district_province', blank=True, null=True)

    class Meta:
        managed = True

    def __str__(self):
        return "%s" % self.name


class Province(ChoiceModel):
    name_en = models.CharField(max_length=50)
    zone = models.CharField(max_length=30)
    area = models.ForeignKey('Country', related_name='province_country', blank=True, null=True)

    class Meta:
        managed = True

    def __str__(self):
        return "%s" % self.name


class Country(ChoiceModel):
    iso = models.CharField(max_length=2, unique=True)
    iso3 = models.CharField(max_length=30)
    name_en = models.CharField(max_length=50)
    name_en_big = models.CharField(max_length=50)
    num_code = models.CharField(max_length=50)
    phone_code = models.CharField(max_length=10)

    class Meta:
        managed = True
        ordering = ['display_seq']

    def __str__(self):
        if self.name:
            return "%s (%s)" % (self.name, self.iso)
        else:
            return "%s (%s)" % (self.name_en, self.iso)

    def get_full_name(self):
        if self.name:
            full_name = "%s - %s (*%s)" % (self.name_en, self.name, self.iso)
        else:
            full_name = "%s (*%s)" % (self.name_en, self.iso)
        return full_name


class Nationality(ChoiceModel):
    name_en = models.CharField(max_length=50)
    language = models.CharField(max_length=2, default='TH', choices=LANGUAGE_CHOICES)

    class Meta:
        managed = True
        ordering = ['display_seq']

    def __str__(self):
        if self.name:
            return "%s - %s" % (self.name, self.name_en)
        else:
            return "%s" % (self.name_en)


class Gender(ChoiceModel):
    name_en = models.CharField(max_length=50)
    language = models.CharField(max_length=2, default='TH', choices=LANGUAGE_CHOICES)

    class Meta:
        ordering = ['display_seq']

    def __str__(self):
        if self.name:
            return "%s - %s" % (self.name, self.name_en)
        else:
            return self.name_en


class Religion(ChoiceModel):
    name_en = models.CharField(max_length=30)

    class Meta:
        managed = True
        ordering = ['display_seq']

    def __str__(self):
        return "%s - %s" % (self.name, self.name_en)


class Education(ChoiceModel):
    code = models.CharField(max_length=4, unique=True)

    class Meta:
        managed = True
        ordering = ['display_seq']

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)


class Career(ChoiceModel):
    code = models.CharField(max_length=4, unique=True)

    class Meta:
        managed = True
        ordering = ['display_seq']

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)


class MaritalStatus(ChoiceModel):
    code = models.CharField(max_length=4, unique=True)

    class Meta:
        managed = True
        ordering = ['display_seq']

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)


class Specialty(ChoiceModel):
    name_en = models.CharField(max_length=500, blank=True, null=True, default='', verbose_name='ชื่อของตัวเลือก en')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'สาขาเฉพาะทางของแพทย์'
        verbose_name_plural = verbose_name


class CleaningChoice(ChoiceModel):
    value = models.IntegerField(help_text="จำนวนชั่วโมงที่ทำความสะอาด")

    class Meta:
        verbose_name = 'ตัวเลือกประเภทเวลาในการทำความสะอาด หลังจากผู้ป่วยออกจากห้อง'

    def __str__(self):
        return '{s.name} ({s.value} ชม.)'.format(s=self)


class ExaminationTypeChoice(ChoiceModel):
    class Meta:
        verbose_name = 'ประเภทการรักษา'
        verbose_name_plural = verbose_name


class ClinicalTermSet(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    def __str__(self):
        return '[%s] %s' % (self.code, self.name)


class ClinicalTermQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True).order_by('seq', 'id')


class ClinicalTerm(models.Model):
    TYPE_DISCHARGE_STATUS = 'I'
    TYPE_DISCHARGE_CONDITION = 'H'
    TYPE_CHIEF_COMPLAINT = 'A'
    TYPE_CONTRAST_MEDIA = 'CM'

    type = models.ForeignKey(ClinicalTermSet, verbose_name='ประเภท Clinical Term')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    require_flag = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False, verbose_name='default สำหรับตัวเลือกในหน้าจอ')
    has_description = models.BooleanField(default=False, verbose_name='ตัวเลือกนี้มีรายละเอียดเพิ่มเติมหรือไม่')
    seq = models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')
    active = models.BooleanField(default=True)

    objects = ClinicalTermQuerySet.as_manager()

    def __str__(self):
        return '%s - [%s] %s' % (self.type, self.code, self.name)


class Icd10Version(models.Model):
    """Keep tracking version of ICD10 in database. The Icd10 objects will refer to this class"""
    version = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')

    def __str__(self):
        return str(self.version)

    class Meta:
        verbose_name = 'รุ่นของ ICD10'


class Icd10VersionManager(models.Manager):
    """Override manager which return the ICD based on the veresion specific in constance config"""

    def get_queryset(self):
        try:
            version = cache.get('icd10_version', None)
            if not version:
                version = Icd10Version.objects.filter(version=config.core_ICD10_VERSION).first()
                if version:
                    cache.set('icd10_version', version.pk, 1800)
        except ProgrammingError:
            return super().get_queryset()
        except OperationalError:
            return super().get_queryset()

        if version is not None:
            return super().get_queryset().filter(version=version)
        else:
            # Version not found return default queryset (all versions)
            return super().get_queryset()


class Icd10(models.Model):
    """
    Master table to store the ICD10 code. This table should be up-to-date with ICD10 standard.
    """
    E_CODES = ('V', 'W', 'X', 'Y')

    version = models.ForeignKey(Icd10Version)
    code = models.CharField(max_length=100, blank=False)
    term = models.CharField(max_length=1000, blank=False)
    term_detail = models.CharField(max_length=1000, blank=True)
    term_sub_detail = models.CharField(max_length=1000, blank=True)
    has_sublevel = models.BooleanField(default=False)  # True if need more sublevel
    is_principal_opd = models.BooleanField(default=False)
    is_principal_ipd = models.BooleanField(default=False)
    start_age = models.IntegerField(default=-1)
    end_age = models.IntegerField(default=-1)
    male = models.BooleanField(default=False)
    female = models.BooleanField(default=False)

    all_objects = models.Manager()  # default django manager
    objects = Icd10VersionManager()  # Custom manager with version controlled

    def __str__(self):
        return self.code + ' ' + self.term

    class Meta:
        verbose_name = 'รหัส ICD10'


class Icd10MedicalTermVersionManager(models.Manager):
    """Override manager which return the ICD based on the veresion specific in constance config"""

    def get_queryset(self):
        try:
            version = cache.get('icd10_version', None)
            if not version:
                version = Icd10Version.objects.filter(version=config.core_ICD10_VERSION).first()
                if version:
                    cache.set('icd10_version', version.pk, 1800)
        except ProgrammingError:
            return super().get_queryset()
        except OperationalError:
            return super().get_queryset()

        if version is not None:
            return super().get_queryset().filter(icd10__version=version)
        else:
            # Version not found return default queryset (all versions)
            return super().get_queryset()


class Icd10MedicalTerm(models.Model):
    """
    Describe medical term which matched to the ICD10 code in database
    """
    icd10 = models.ForeignKey(Icd10)
    term = models.CharField(max_length=255, blank=True)
    seq = models.IntegerField(default=255)  # Sequence to display medical term on screen

    all_objects = models.Manager()  # default django manager
    objects = Icd10MedicalTermVersionManager()  # Custom manager with version controlled

    def __str__(self):
        return self.term + ' : ' + self.icd10.code

    class Meta:
        verbose_name = 'ชื่อเรียก ICD10 ที่แพทย์เข้าใจ'


class Icd9cmVersion(models.Model):
    """Keep tracking version of ICD9 in database. The Icd9 objects will refer to this class"""
    version = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.version)

    class Meta:
        verbose_name = 'รุ่นของ ICD9CM'


class Icd9cmVersionManager(models.Manager):
    """Override manager which return the ICD based on the veresion specific in constance config"""

    def get_queryset(self):
        try:
            version = cache.get('icd9cm_version', None)
            if not version:
                version = Icd9cmVersion.objects.filter(version=config.core_ICD9CM_VERSION).first()
                if version:
                    cache.set('icd9cm_version', version.pk, 1800)
        except ProgrammingError:
            return super().get_queryset()
        except OperationalError:
            return super().get_queryset()

        if version is not None:
            return super().get_queryset().filter(version=version)
        else:
            # Version not found return default queryset (all versions)
            return super().get_queryset()


class Icd9cm(models.Model):
    """
    Master table to store the ICD9 code. This table should be up-to-date with ICD9 standard.
    """
    version = models.ForeignKey(Icd9cmVersion)
    code = models.CharField(max_length=100, blank=False)
    term = models.CharField(max_length=1000, blank=False)
    term_detail = models.CharField(max_length=1000, blank=True)
    term_sub_detail = models.TextField(blank=True)
    has_sublevel = models.BooleanField(default=False)  # True if need more sublevel
    is_principal_opd = models.BooleanField(default=False)
    is_principal_ipd = models.BooleanField(default=False)
    start_age = models.IntegerField(default=-1)
    end_age = models.IntegerField(default=-1)
    male = models.BooleanField(default=False)
    female = models.BooleanField(default=False)

    all_objects = models.Manager()  # default django manager
    objects = Icd9cmVersionManager()  # Custom manager with version controlled

    def __str__(self):
        return self.code + ' ' + self.term

    @property
    def staging_code(self):
        return self.code.replace('.0', '')

    class Meta:
        verbose_name = 'รหัส ICD9CM'


class Icd9cmMedicalTermVersionManager(models.Manager):
    """Override manager which return the ICD based on the veresion specific in constance config"""

    def get_queryset(self):
        try:
            version = cache.get('icd9cm_version', None)
            if not version:
                version = Icd9cmVersion.objects.filter(version=config.core_ICD9CM_VERSION).first()
                if version:
                    cache.set('icd9cm_version', version.pk, 1800)
        except ProgrammingError:
            return super().get_queryset()
        except OperationalError:
            return super().get_queryset()

        if version is not None:
            return super().get_queryset().filter(icd9cm__version=version)
        else:
            # Version not found return default queryset (all versions)
            return super().get_queryset()


class Icd9cmMedicalTerm(models.Model):
    """
    Describe medical term which matched to the ICD10 code in database
    """
    icd9cm = models.ForeignKey(Icd9cm)
    term = models.CharField(max_length=255, blank=True)
    seq = models.IntegerField(default=255)  # Sequence to display medical term on screen

    all_objects = models.Manager()  # default django manager
    objects = Icd9cmMedicalTermVersionManager()  # Custom manager with version controlled

    def __str__(self):
        return self.term + ' : ' + str(self.seq) + ' : ' + self.icd9cm.code

    class Meta:
        verbose_name = 'ชื่อเรียก ICD9CM ที่แพทย์เข้าใจ'


# ================================================================ BUSINESS MASTER DATA ================================


class CostCenter(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=250)

    def __str__(self):
        return "[%s] %s" % (self.code, self.name)


class Department(models.Model):
    code = models.CharField(max_length=5)
    name = models.CharField(max_length=250)
    logo = models.ImageField(null=True, blank=True, upload_to='core/department/logo/')
    color = models.CharField(max_length=50, blank=True)
    url = models.CharField(max_length=250, blank=True, help_text='thai url')
    url_en = models.CharField(max_length=250, blank=True, help_text='english url')
    url_zh = models.CharField(max_length=250, blank=True, help_text='chinese url')

    def __str__(self):
        return "[%s] %s" % (self.code, self.name)


class DivisionQuerySet(models.QuerySet):
    def filter_clinic(self):
        return self.filter(type__in=[Division.TYPE.CLINIC,
                                     Division.TYPE.PREMIUM_CLINIC])

    def for_opd_encounter(self):
        """Return Divisions that allowed to use in OPD encounter"""
        return self.filter(type__in=[Division.TYPE.CLINIC,
                                     Division.TYPE.PREMIUM_CLINIC,
                                     Division.TYPE.SHORTSTAY,
                                     Division.TYPE.SPECIMEN_COLLECTOR])

    def for_ipd_encounter(self):
        """Division allowed for Admission"""
        return self.filter(type__in=[Division.TYPE.WARD, Division.TYPE.SHORTSTAY])

    def for_ss_encounter(self):
        """Division allowed for short stay service (patient can shortstay at both Ward & OPD Clinic)"""
        return self.filter(type__in=[Division.TYPE.WARD,
                                     Division.TYPE.CLINIC,
                                     Division.TYPE.SHORTSTAY,
                                     Division.TYPE.PREMIUM_CLINIC])


class Area(ChoiceModel):
    alias = models.CharField(max_length=5, unique=True)


class Division(ChoiceModel):
    """หน่วยงาน/หน่วยตรวจ/คลินิก"""
    BARCODE_PREFIX = 'DIV01'
    BARCODE_LENGTH = 10

    class TYPE(LabeledIntEnum):
        GENERAL = 1, 'ทั่วไป'
        BILLING = 2, 'การเงิน'
        DRUG = 3, 'ห้องยา'
        SUPPLY = 4, 'ห้องเวชภัณฑ์'
        SPECIMEN_COLLECTOR = 6, 'แผนกเก็บ Specimen'
        CLINIC = 7, 'หน่วยตรวจ'
        PREMIUM_CLINIC = 8, 'คลินิกพรีเมี่ยม'
        WARD = 9, 'หอผู้ป่วย'
        ZONE = 10, 'หน่วยย่อย'
        SHORTSTAY = 11, 'short stay'
        WARD_PREMIUM = 12, 'หอผู้ป่วยพรีเมี่ยม'

    code = models.CharField(max_length=10, unique=True)
    name_en = models.CharField(max_length=500, blank=True, verbose_name='ชื่อหน่วยงานภาษาอังกฤษ')
    parent = SelfReferenceForeignKey(null=True, blank=True, related_name='children')
    short_name = models.CharField(max_length=500, default='', blank=True)
    type = EnumField(TYPE, default=TYPE.GENERAL, verbose_name='ประเภทหน่วยงาน')
    billing_div = models.ForeignKey('self', null=True, blank=True, related_name='+',
                                    help_text='การเงินที่ผูกกับหน่วยตรวจ')
    drug_div = models.ForeignKey('self', null=True, blank=True, related_name='+',
                                 help_text='ห้องยาที่ผูกกับหน่วยตรวจ')
    supply_div = models.ForeignKey('self', null=True, blank=True, related_name='+',
                                   help_text='ห้องเวชภัณฑ์ที่ผูกกับหน่วยตรวจ')
    cost_center = models.ForeignKey(CostCenter, null=True, blank=True, related_name='divisions',
                                    verbose_name='หน่วยต้นทุนที่ผูกกับหน่วยงานนี้')
    department = models.ForeignKey(Department, null=True, blank=True, related_name='divisions',
                                   verbose_name='ภาควิชาที่หน่วยงานนี้สังกัด')
    storage = models.ForeignKey('Storage', null=True, blank=True, related_name='divisions',
                                verbose_name='คลังที่ผูกกับหน่วยงานนี้')
    area = models.ForeignKey(Area, null=True, blank=True, related_name='divisions',
                             verbose_name='ที่ตั้งของหน่วยงาน')
    location = models.TextField(blank=True, verbose_name='ชื่อสถานที่')

    client = GenericRelation('appointment.Client', related_query_name='divisions')
    objects = DivisionQuerySet.as_manager()

    def __str__(self):
        return "[%s] %s" % (self.code, self.name)

    @property
    def code_name_hl7(self):
        return '%s^%s' % (self.code, self.name)

    @property
    def is_patient_division(self):
        return self.type not in [self.TYPE.GENERAL,
                                 self.TYPE.BILLING,
                                 self.TYPE.ZONE]

    def get_name(self, language=None):
        language = get_language(language)
        if language == LANGUAGE_EN:
            return self.name_en or self.name
        else:
            return self.name or self.name_en

    def get_short_name(self):
        return self.short_name or self.name

    def get_location_name(self):
        """try to get location name from DivisionLocation.
        if not found, using location field from self.
        if location field is empty, return __str__"""
        division_location = DivisionLocation.objects.filter(
            division=self,
            active=True,
        ).first()
        if division_location:
            return division_location.location.name
        if self.location != '':
            return self.location
        return str(self)


class ZoneLog(models.Model):
    encounter = models.ForeignKey('Encounter', related_name='zone_log')
    zone = models.ForeignKey('Division', related_name='zone_log')
    check_in_time = models.DateTimeField(null=True)
    check_out_time = models.DateTimeField(null=True)
    check_in_user = models.ForeignKey(User, related_name='+', null=True, blank=True)
    check_out_user = models.ForeignKey(User, related_name='+', null=True, blank=True)
    create_user = models.ForeignKey(User, related_name='+')
    tracker = FieldTracker(fields=['zone', 'check_in_time', 'check_out_time', 'create_user'])

    def notify_current_division(self):
        Messenger.push_to_location(self.zone.parent.code,
                                   source='core',
                                   event='update_encounter_queue',
                                   encounter_id=self.encounter.pk)

    def edit_zone(self, zone, user):
        self.zone = zone
        self.create_user = user
        self.save()

    def check_out(self, user):
        self.check_out_time = datetime.now()
        self.check_out_user = user
        self.save()

    def check_in(self, user):
        self.check_in_time = datetime.now()
        self.check_in_user = user
        self.save()

    def delete(self, using=None, keep_parents=False):
        self.notify_current_division()
        return super().delete(using, keep_parents)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # Division type validation
        if self.zone.type is not Division.TYPE.ZONE:
            raise ValidationError('Division จะต้องเป็น Zone')

        # Zone parent validation
        if not self.zone.parent:
            raise ValidationError('Zone จะต้องมี parent')

        # Prevent to change zone when already checked-in
        changed = self.tracker.changed()
        if ('zone' in changed) and (self.tracker.previous('check_in_time') is not None):
            raise ValidationError('ไม่สามารถแก้ไข Zone ได้เนื่องจาก check-in แล้ว')

        # Prevent check-out when not check-in yet
        if ('check_out_time' in changed) and (self.check_in_time is None):
            raise ValidationError('ไม่สามารถ check-out ได้ เนื่องจากยังไม่ได้ check-in')

        # Prevent duplicate non check-out ZoneLog
        if self.encounter.zone_log.filter(check_out_time__isnull=True).exclude(id=self.id):
            raise ValidationError('ไม่สามารถสร้างใหม่ได้เนื่องจากยังมี ZoneLog ที่ยังไม่ check-out')

        # Ignore re check-in
        if ('check_in_time' in changed) and self.tracker.previous('check_in_time'):
            return

        # Ignore re check-out
        if ('check_out_time' in changed) and self.tracker.previous('check_out_time'):
            return

        # Must record user when check in
        if ('check_in_time' in changed) and not self.check_in_user:
            raise ValidationError('ต้องระบุ check_in_user เมื่อ check_in')

        # Must record user when check out
        if ('check_out_time' in changed) and not self.check_out_user:
            raise ValidationError('ต้องระบุ check_out_user เมื่อ check_out')

        # create_user cannot change if zone not change
        if 'zone' not in changed:
            self.create_user_id = self.tracker.previous('create_user')

        self.notify_current_division()

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return '%s - (%s, %s)' % (self.zone.name, self.check_in_time, self.check_out_time)


class WeekDayWeekNumberQuerySet(models.QuerySet):
    """Base queryset allow you to filter model with field by providing date:
        work_on_monday, work_on_tuesday, ...
        work_on_week_1, work_on_week_2
    """
    WEEKDAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')

    def for_date(self, date=None):
        """ return a queryset of all DoctorWorkSchedule for the date """
        if date is None:
            date = datetime.today()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')  # same as django format (YYYY-MM-DD)

        return self.filter(Q(end_date__gte=date) | Q(end_date__isnull=True)) \
            .filter(start_date__lte=date) \
            .filter_weekday(self.weekday_string_from_date(date)) \
            .filter_week_number(week_number(date))

    def weekday_string_from_date(self, date: datetime) -> str:
        """Convert python datetime object to weekday string, e.g. 'monday' """
        return self.WEEKDAYS[date.weekday()]

    def filter_weekday(self, weekday: str):
        if weekday in self.WEEKDAYS:
            return self.filter(**{'work_on_%s' % weekday: True})
        raise ValueError('weekday should be a string (monday to friday)')

    def filter_week_number(self, week_number: int):
        if week_number >= 1 and week_number <= 6:
            return self.filter(**{'work_on_week_%d' % week_number: True})
        raise ValueError('week number should be an integer (1-6)')


class DivisionWorkScheduleQuerySet(WeekDayWeekNumberQuerySet):
    def is_available(self, division, date_time: datetime = None) -> bool:
        """return True if the division will stop working on the date at start_time - end_time"""
        if not date_time:
            date_time = datetime.now()
        return self.filter(active=True,
                           division=division,
                           start_date__lte=date_time,
                           start_time__lte=date_time.time()) \
            .filter_weekday(self.weekday_string_from_date(date_time)) \
            .filter_week_number(week_number(date_time)) \
            .filter(Q(end_date__gte=date_time) | Q(end_date__isnull=True)) \
            .filter(Q(end_time__gte=date_time.time()) | Q(end_time__isnull=True)) \
            .exists()


class DivisionWorkSchedule(models.Model):
    """เก็บข้อมูลตารางการเปิดให้บริการของหน่วยงาน"""
    division = models.ForeignKey(Division, verbose_name='หน่วยงาน', help_text='หน่วยงาน')
    start_date = models.DateField(verbose_name='วันเริ่มต้น', help_text='วันที่เริ่มต้น')
    end_date = models.DateField(null=True, blank=True, verbose_name='วันสิ้นสุด', help_text='วันที่สิ้นสุดการ')
    start_time = models.TimeField(verbose_name='เวลาเริ่มต้น', help_text='เวลาที่เริ่มต้น')
    end_time = models.TimeField(null=True, blank=True, verbose_name='เวลาสิ้นสุด', help_text='เวลาที่สิ้นสุด')
    work_on_monday = models.BooleanField(default=True, verbose_name='เปิดให้บริการวันจันทร์',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_tuesday = models.BooleanField(default=True, verbose_name='เปิดให้บริการวันอังคาร',
                                          help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_wednesday = models.BooleanField(default=True, verbose_name='เปิดให้บริการวันพุธ',
                                            help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_thursday = models.BooleanField(default=True, verbose_name='เปิดให้บริการวันพฤหัส',
                                           help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_friday = models.BooleanField(default=True, verbose_name='เปิดให้บริการวันศุกร์',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_saturday = models.BooleanField(default=True, verbose_name='เปิดให้บริการวันเสาร์',
                                           help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_sunday = models.BooleanField(default=True, verbose_name='เปิดให้บริการวันอาทิตย์',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_week_1 = models.BooleanField(default=True, verbose_name='เปิดให้บริการสัปดาห์ที่ 1',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_week_2 = models.BooleanField(default=True, verbose_name='เปิดให้บริการสัปดาห์ที่ 2',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_week_3 = models.BooleanField(default=True, verbose_name='เปิดให้บริการสัปดาห์ที่ 3',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_week_4 = models.BooleanField(default=True, verbose_name='เปิดให้บริการสัปดาห์ที่ 4',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_week_5 = models.BooleanField(default=True, verbose_name='เปิดให้บริการสัปดาห์ที่ 5',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    work_on_week_6 = models.BooleanField(default=True, verbose_name='เปิดให้บริการสัปดาห์ที่ 6',
                                         help_text='True = เปิดให้บริการ, False = ไม่เปิดให้บริการ')
    active = models.BooleanField(default=True, verbose_name='active flag',
                                 help_text='True = active, False = not active')

    objects = DivisionWorkScheduleQuerySet.as_manager()

    def __str__(self):
        return '%s - %s - %s' % (self.division.name, self.start_date, self.division)

    class Meta:
        verbose_name = 'ตารางการเปิดให้บริการของหน่วยงาน'
        verbose_name_plural = verbose_name


class DivisionStopWorkScheduleManager(models.Manager):
    def stop_on(self, division, date_time=None) -> bool:
        """return True if the division will stop working on the date at start_time - end_time"""
        if not date_time:
            date_time = datetime.now()
        qs = self.get_queryset()
        return qs.filter(active=True,
                         division=division,
                         start_date__lte=date_time,
                         start_time__lte=date_time.time(),
                         end_time__gte=date_time.time()) \
            .filter(Q(end_date__gte=date_time) | Q(end_date__isnull=True)) \
            .exists()


class DivisionStopWorkSchedule(EditableModel):
    """เก็บข้อมูลตารางงดเปิดให้บริการของหน่วยงาน"""
    division = models.ForeignKey(Division, verbose_name='หน่วยงาน')
    start_date = models.DateField(verbose_name='วันเริ่มต้น', help_text='วันที่เริ่มต้นหยุดให้บริการ')
    end_date = models.DateField(null=True, blank=True, verbose_name='วันสิ้นสุด',
                                help_text='วันที่สิ้นสุดการหยุดให้บริการ')
    start_time = models.TimeField(verbose_name='เวลาเริ่มต้น', help_text='เวลาที่เริ่มต้นการหยุดให้บริการ')
    end_time = models.TimeField(verbose_name='เวลาสิ้นสุด', help_text='เวลาที่สิ้นสุดการหยุดให้บริการ')
    active = models.BooleanField(default=True, verbose_name='active flag',
                                 help_text='True = active, False = not active')

    objects = DivisionStopWorkScheduleManager()

    class Meta:
        verbose_name = 'ตารางงดเปิดให้บริการของหน่วยงาน'
        verbose_name_plural = verbose_name


class PayerGroup(EditableModel):
    payer_group_id = models.CharField(max_length=2)
    name = models.CharField(max_length=255, verbose_name='ชื่อกลุ่ม Payer')

    def __str__(self):
        return '%s - %s' % (self.payer_group_id, self.name)

    class Meta:
        verbose_name = 'กลุ่ม Payer'
        verbose_name_plural = verbose_name


class Payer(EditableModel):
    payer_group = models.ForeignKey(PayerGroup, null=True, blank=True, verbose_name='กลุ่ม Payer')
    payer_id = models.CharField(max_length=10, verbose_name='รหัส Payer')
    name = models.CharField(max_length=255, verbose_name='ชื่อ Payer')
    short_name = models.CharField(max_length=255, default='', blank=True, verbose_name='ชื่อ Payer แบบสั้น')
    province = models.ForeignKey(Province, null=True, blank=True, verbose_name='จังหวัด')

    def __str__(self):
        return '[%s] %s' % (self.payer_id, self.name)


class CoverageManager(models.Manager):
    def get_unk_coverage(self):
        """Return UNK (cash only) coverage"""
        cov, _ = self.get_or_create(code=config.core_UNK_CODE,
                                    defaults=dict(name='เงินสด', name_en='',
                                                  start_date=date.today(),
                                                  type=Coverage.COVERAGE_TYPE.COVERAGE))
        return cov

    def get_ggo_coverage(self):
        """Return GGO (ข้าราชการ) coverage"""
        return self.get(code=config.core_GGO_CODE)


class Coverage(EditableModel):
    """สิทธิ์ต่างๆ (ข้าราชการ, ประกันสังคมในเขต, ประกันสังคมนอกเขต, ประกันสุขภาพ, AR)"""

    class COVERAGE_TYPE(LabeledIntEnum):
        COVERAGE = 1, 'สิทธิการรักษาพยาบาล'
        DISCOUNT_POLICY = 2, 'สิทธิส่วนลดตามนโยบาย'
        DISCOUNT_CARD = 3, 'สิทธิส่วนลดตามหน้าบัตร'
        PACKAGE = 4, 'แพ็กเกจ'
        INVOICE_DISCOUNT = 5, 'ส่วนลดท้ายใบเสร็จ'

    code = models.CharField(max_length=8, unique=True, verbose_name='รหัสสิทธิหลัก')
    name = models.CharField(max_length=200, verbose_name='ชื่อสิทธิ (ภาษาไทย)')
    name_en = models.CharField(max_length=200, blank=True, verbose_name='ชื่อสิทธิ (ภาษาอังกฤษ)')
    type = EnumField(COVERAGE_TYPE, default=COVERAGE_TYPE.COVERAGE, verbose_name='ประเภทสิทธิ์')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    payers = models.ManyToManyField(Payer, blank=True, verbose_name='Payer List',
                                    help_text='Payer ที่สามารถใช้งานกับสิทธิ์นี้ได้(ไม่ระบุ = สามารถใช้ได้ทุก Payer)')
    group_number = models.CharField(max_length=4, blank=True, help_text='เลขกลุ่มสิทธิ์ เพื่อใช้ป้องกันเลือกสิทธิ์ซ้ำ\n'
                                                                        'เว้นว่างไว้ถ้าไม่ต้องการ lock')
    staging_code = models.CharField(max_length=6, blank=True, help_text='รหัสสิทธิสำหรับส่ง staging')

    objects = CoverageManager()

    def __str__(self):
        return '[%s] %s' % (self.code, self.name)

    def get_name(self, language=LANGUAGE_TH):
        if language == LANGUAGE_EN:
            if self.name_en:
                return self.name_en
        return self.name

    def is_payer_allowed(self, payer_id):
        """Check if this payer is allowed to use with this coverage"""
        if self.payers.exists():
            # If there is any payer specified, only those in the list is allowed
            return self.payers.filter(id=payer_id).exists()
        return True

    def edit_discount(self):
        if self.type == Coverage.COVERAGE_TYPE.DISCOUNT_POLICY:
            URL = '/BIL/CardDiscountSetting.qml?type=policy&id=%d' % self.pk
            return mark_safe('<a href="%s">Edit Discount</a>' % URL)
        else:
            return ''

    def get_staging_code(self):
        return self.staging_code or self.code


class CoverageDocument(models.Model):
    """Document required by each coverage"""

    class ACTION_TYPE(LabeledIntEnum):
        SCAN = 1, 'เอกสาร scan จากผู้ป่วย'
        PRINT = 2, 'เอกสาร print ให้ผู้ป่วย'

    type = EnumField(ACTION_TYPE, help_text='ประเภทของเอกสาร')
    coverage = models.ForeignKey('Coverage')
    document_type = models.ForeignKey('DocumentType')
    prefix = models.CharField(max_length=8)
    title = models.CharField(max_length=255, blank=True)


class CoveragePayerSettings(models.Model):
    coverage = models.ForeignKey(Coverage, null=True, blank=True)
    payer = models.ForeignKey(Payer, null=True, blank=True)
    approval_code_required = models.BooleanField()


class Project(EditableModel):
    """สิทธิโครงการ เช่น โครงการผู้ป่วยโรคไตเรื้อรัง ส่วนต่อขยายจากสิทธิหลัก"""
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    def __str__(self):
        return '[%s] %s' % (self.code, self.name)

    class Meta:
        verbose_name = 'สิทธิโครงการ'


class Referer(ChoiceModel):
    code = models.CharField(max_length=50, null=True, blank=True, verbose_name='รหัสโรงพยาบาลต้นสังกัด')

    def __str__(self):
        return '[%s] %s' % (self.code, self.name)

    class Meta:
        verbose_name = 'โรงพยาบาลต้นสังกัดกรณีผู้ป่วย Refer-in'


class DocumentCategoryQuerySet(models.QuerySet):
    def get_or_create_undefined_category(self):
        return self.get_or_create(
            code='UNDEFINED',
            defaults={
                'name': 'ไม่ระบุ'
            }
        )


class DocumentCategory(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, blank=True)
    parent = SelfReferenceForeignKey(null=True, blank=True, help_text='กรณีเป็นหมวดรอง field นี้คือหมวดที่เป็น parent')
    active = models.BooleanField(default=True)
    display_seq = models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')

    objects = DocumentCategoryQuerySet.as_manager()

    class Meta:
        verbose_name = 'Document Category'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '[%s] %s' % (self.code, self.name)


class DocumentType(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(DocumentCategory)
    code = models.CharField(max_length=20, blank=True)
    division = models.ManyToManyField(Division, blank=True,
                                      help_text='ระบุ Division ที่ใช้เอกสารชนิดนี้ (เว้นว่าง = ใช้ได้ทุก Division)')
    print_api = models.CharField(max_length=500, blank=True,
                                 verbose_name="url of document print api")  # "/apis/core/encounter/print/"
    jasper_path = models.CharField(max_length=255, blank=True, verbose_name="Path ไปยังไฟล์ jasper")
    jasper_module = models.CharField(max_length=255, blank=True, verbose_name="Module ของไฟล์ jasper")
    version = models.IntegerField()
    active = models.BooleanField(default=True)
    display_seq = models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')

    def __str__(self):
        return "%s (v.%s)" % (self.name, self.version)

    class Meta:
        ordering = ('display_seq',)


class BillDisplayName(models.Model):
    model_name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)

    @classmethod
    def get_display_name(cls, obj):
        model_name = obj.__class__.__name__
        order_name = BillDisplayName.objects.filter(model_name=model_name).first()
        if order_name:
            return order_name.display_name
        else:
            return model_name


# ======================================================================== PRODUCT DATA ================================


class Unit(models.Model):
    """Master data of "unit of measure" used to count products.
    Adding is allowed. Deleting is not allowed. Editing is not allowed unless the meaning is not change.
    """
    code = models.CharField(unique=True, max_length=100, help_text='an abbreviation of the unit of measure')
    name = models.CharField(max_length=255, help_text='a name of the unit of measure')
    name_en = models.CharField(max_length=255, blank=True, help_text='a name of the unit of measure')
    display_seq = models.IntegerField(default=999, verbose_name='ลำดับการแสดงผลบนหน้าจอ')
    image = models.ImageField(max_length=150, upload_to='core/medication/icons/', blank=True, null=True)

    @property
    def text(self):
        if get_context_language() == LANGUAGE_EN:
            return self.name_en
        else:
            return self.name

    def __str__(self):
        return '%s : %s' % (self.code, self.name_en or self.name)

    class Meta:
        ordering = ('code',)
        verbose_name = 'unit of measure for product'
        verbose_name_plural = 'units of measure for product'


class UnitConversion(models.Model):
    from_unit = models.ForeignKey(Unit, related_name='+')
    to_unit = models.ForeignKey(Unit, related_name='+')
    factor = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('from_unit', 'to_unit')


class ProductType(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, null=True, blank=True)
    observation_type = models.CharField(max_length=20, null=True, verbose_name="ประเภทการให้บริการ")
    allow_cancel_receipt_when_performed = models.BooleanField(default=True,
                                                              help_text='อนุญาตให้ยกเลิกใบเสร็จ ถ้า perform รายการแล้ว')

    def __str__(self):
        return self.code + ' : ' + self.name

    class Meta:
        verbose_name = 'ประเภทค่าใช้จ่าย'


class Product(models.Model):
    """
    code = SAP Code เช่น N00107
    service_code = รหัสบริการของรามา Z102
    """

    class AVAILABILITY(LabeledIntEnum):
        INACTIVE = 5, 'ไม่พร้อมจำหน่าย'
        ACTIVE = 1, 'มีจำหน่าย'
        INSUFFICIENT = 2, 'ใกล้ขาดคราว'
        UNAVAILABLE = 3, 'ขาดคราว'
        TERMINATED = 4, 'เลิกจำหน่าย'

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default='')
    unit = models.ForeignKey('Unit', null=True, help_text='หน่วยขาย')
    p_type = models.ForeignKey(ProductType, null=True)
    service_code = models.CharField(max_length=20, blank=True)
    active_flag = EnumField(AVAILABILITY, default=AVAILABILITY.ACTIVE)

    def __str__(self):
        return "[%s] %s" % (self.code, self.name)

    def get_subclass_product(self):
        for subclass in self._meta.model.__subclasses__():
            sub_product = getattr(self, subclass.__name__.lower(), None)
            if sub_product:
                return sub_product
        return self

    def is_deletable_with_keep_parents(self):
        subclass_product = self.get_subclass_product()
        if not subclass_product:
            return False
        exists_list = []
        parents = self._meta.parents
        for rel in get_candidate_relations_to_delete(subclass_product._meta):
            if rel.model in parents:
                continue
            if rel.field.remote_field.on_delete == DO_NOTHING:
                continue
            related_model = rel.related_model
            related = related_model.objects.filter(**{rel.field.name: subclass_product})
            if related.exists():
                exists_list.append('%s: %s' % (related_model.__name__, related.count()))
        if exists_list:
            return False, exists_list
        return True, None

    def get_name(self, language=LANGUAGE_TH):
        if language == LANGUAGE_EN:
            if self.name_en != '':
                return self.name_en
        return self.name

    @property
    def price(self):
        return self.pricing[0].price if getattr(self, 'pricing', None) else None

    @classmethod
    def exclude_price_zero(cls, query, encounter):
        from his.apps.BIL.models import Pricing
        price_type = Pricing.get_price_type(encounter)
        now = date.today()
        query = query.filter(**{'full_pricings__%s__gt' % price_type: 0},
                             full_pricings__start_date__lte=now,
                             full_pricings__end_date__gte=now)
        return query


class Storage(models.Model):
    code = models.CharField(unique=True, max_length=10)
    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    sap_code = models.CharField(max_length=10, blank=True)

    @property
    def text(self):
        if get_context_language() == LANGUAGE_EN:
            return self.name_en
        else:
            return self.name

    def __str__(self):
        return "[%s] %s" % (self.code, self.name)


class Stock(models.Model):
    class MOVEMENT_TYPE(LabeledIntEnum):
        INITIAL = 1
        DISPENSE_PERFORM = 2
        DISPENSE_CANCEL = 3
        RETURN_PERFORM = 4
        RETURN_CANCEL = 5
        TRANSFER_PERFORM = 6
        TRANSFER_CANCEL = 7
        MOVEMENT_PERFORM = 8
        MOVEMENT_CANCEL = 9

    product = models.ForeignKey(Product, related_name='+')
    storage = models.ForeignKey(Storage, related_name='+')
    quantity = models.IntegerField(default=0)
    counting_datetime = models.DateTimeField(editable=False, null=True)
    bin_location = models.CharField(max_length=20)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "[%s][%s] %s" % (self.storage.code, self.product.code, self.product.name)

    @staticmethod
    def get_balance(storage, product):
        stock = Stock.objects.filter(storage=storage, product=product).first() or \
                Stock()

        return stock.quantity

    @staticmethod
    @transaction.atomic()
    def update_balance(storage, product, different):
        stock = Stock.objects.filter(storage=storage, product=product).first() or \
                Stock(storage=storage, product=product)

        stock.quantity = stock.quantity + different
        stock.save()
        return stock

    @staticmethod
    @transaction.atomic()
    def transact(storage, product, different, movement_type, related_issue):
        stock = Stock.update_balance(storage, product, different)

        StockLog.objects.create(
            stock=stock,
            type=movement_type,
            datetime=datetime.now(),
            quantity=different,
            balance=stock.quantity,
            related_issue=related_issue,
        )

    class Meta:
        unique_together = ('product', 'storage',)


class StockLog(models.Model):
    stock = models.ForeignKey(Stock, related_name='logs')
    type = EnumField(Stock.MOVEMENT_TYPE)
    datetime = models.DateTimeField()
    quantity = models.IntegerField()
    balance = models.IntegerField()
    related_issue_type = models.ForeignKey(ContentType, null=True, blank=True)
    related_issue_id = models.PositiveIntegerField(null=True, blank=True)
    related_issue = GenericForeignKey('related_issue_type', 'related_issue_id')

    def __str__(self):
        return '[{}][{}] {}: {} ({})'.format(
            self.stock.storage.sap_code,
            self.stock.product.code,
            self.type.name,
            self.quantity,
            self.related_issue or '',
        )


class SpecialEquipment(Product):
    division = models.ForeignKey(Division)
    active = models.BooleanField(default=True)


class Miscellaneous(Product):
    pass


class ProductFilterGroup(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    products = models.ManyToManyField(Product)


class Package(Product):
    coverage = models.ForeignKey(Coverage)
    duration = models.PositiveIntegerField(default=1, help_text='อายุของ package (วัน)')
    can_discount = models.BooleanField(default=False)
    remark = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'แพ็กเกจ'
        permissions = (
            ("can_view_package", "Can view Package"),
            ("can_action_package", "Can create, update Package"),
        )


# ======================================================================= PATIENT DATA =================================
class Doctor(EditableModel):
    class TYPE(LabeledIntEnum):
        TYPE_NORMAL = 1, 'แพทย์'
        TYPE_SYSTEM = 2, 'แพทย์กลาง'

    code = models.CharField(max_length=10, help_text="รหัสแพทย์", unique=True)
    pre_name = models.ForeignKey(Prename, related_name='+', null=True, blank=True)
    pre_name_en = models.ForeignKey(Prename, related_name='+', null=True, blank=True)
    first_name = models.CharField(max_length=80, verbose_name="ชื่อ")
    first_name_en = models.CharField(max_length=80, blank=True, default='', verbose_name="ชื่อภาษาอังกฤษ")
    middle_name = models.CharField(max_length=80, blank=True, verbose_name="ชื่อกลาง")
    middle_name_en = models.CharField(max_length=80, blank=True, default='', verbose_name="ชื่อกลางภาษาอังกฤษ")
    last_name = models.CharField(max_length=80, verbose_name="นามสกุล")
    last_name_en = models.CharField(max_length=80, blank=True, default='', verbose_name="นามสกุลภาษาอังกฤษ")
    certificate_no = models.CharField(max_length=50, verbose_name='เลขที่ใบประกอบวิชาชีพเวชกรรม', null=True, blank=True)
    specialty = models.ManyToManyField(Specialty, blank=True)
    user = models.OneToOneField(User, blank=True, null=True)
    type = EnumField(TYPE, default=TYPE.TYPE_NORMAL, verbose_name='ประเภทของแพทย์')
    is_active = models.BooleanField(default=True)
    image = models.ImageField(verbose_name=_('doctor image file'), upload_to='doctors/images/', null=True)
    image_url = models.URLField(verbose_name=_('doctor image url'), max_length=200, null=True,
                                help_text=_('this will override image field'))
    common = models.BooleanField(default=False, verbose_name='เป็นแพทย์กลางหรือไม่')

    def __str__(self):
        return '[%s] %s %s' % (
            self.code, self.first_name, self.last_name)

    def get_first_specialty(self):
        return self.specialty.first()

    def get_name_code(self, language=LANGUAGE_TH):
        return '%s (%s)' % (self.get_full_name(language), self.code)

    def get_full_name(self, language=None):
        language = get_language(language)
        if language == LANGUAGE_EN:
            return self.fullname_en() or self.fullname()
        else:
            return self.fullname() or self.fullname_en()

    def fullname(self):
        name = []
        if self.pre_name:
            name.append(self.pre_name.name + self.first_name)
        else:
            name.append(self.first_name)
        if self.middle_name:
            name.append(self.middle_name)
        name.append(self.last_name)
        return ' '.join(name)

    def fullname_en(self):
        if self.first_name_en != '' and self.last_name_en != '':
            if self.middle_name_en != '':
                return '%s %s %s M.D.' % (self.first_name_en, self.middle_name_en, self.last_name_en)
            return '%s %s M.D.' % (self.first_name_en, self.last_name_en)
        return ''

    def get_full_name_for_hl7(self):
        code = self.code
        last_name = self.last_name
        first_name = self.first_name
        middle_name = self.middle_name
        prefix_name = getattr(self.pre_name, 'name', '')
        return '%s^%s^%s^%s^%s' % (code, last_name, first_name, middle_name, prefix_name)

    def get_full_name_for_short_hl7(self):
        return '%s^%s' % (self.code, self.fullname())

    def get_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return None

    def save_image_from_url(self, url, transition: ImageTransition = None):
        result = requests.get(url)
        buffer = BytesIO(result.content)
        if transition:
            buffer = transition.apply_transition(buffer)
        self.image.save(
            os.path.basename(url),
            File(buffer)
        )
        self.save()

    @property
    def full_name(self):
        return self.fullname()

    def translate_pre_name(self):
        return self.pre_name.name if self.pre_name else ''

    def translate_pre_name_en(self):
        return self.pre_name_en.name if self.pre_name_en else ''

    @property
    def full_name_en(self):
        prename_en = getattr(self.pre_name_en, 'name', '')
        if self.first_name_en != '' and self.last_name_en != '':
            if self.middle_name_en != '':
                return '%s %s %s %s' % (prename_en, self.first_name_en, self.middle_name_en, self.last_name_en)
            return '%s %s %s' % (prename_en, self.first_name_en, self.last_name_en)
        return ''

    @property
    def specialties(self):
        return self.specialty.values_list('name', flat=True)

    @property
    def specialties_en(self):
        return self.specialty.values_list('name_en', flat=True)

    @property
    def education_list(self):
        return self.educations.all()

    @property
    def board_list(self):
        return self.boards.all()

    @property
    def certification_list(self):
        return self.certifications.all()


class DoctorGroup(models.Model):
    name = models.CharField(max_length=255, verbose_name='ชื่อกลุ่ม', unique=True)
    doctors = models.ManyToManyField(Doctor, verbose_name='แพทย์ในกลุ่ม')

    class Meta:
        verbose_name = 'กลุ่มแพทย์'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Address(EditableModel):
    owner_name = models.CharField(max_length=200, blank=True, null=True, default='', verbose_name=u'ชื่อ-สกุล')
    relative = models.CharField(max_length=200, blank=True, null=True, default='', verbose_name=u'ความสัมพันธ์')
    receive_documents = models.BooleanField(default=False, verbose_name='ต้องการรับเอกสาร')

    no = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=50, blank=True, default='')
    type = models.ForeignKey('HomeType', related_name='address_type', blank=True, null=True)
    town = models.CharField(max_length=50, blank=True, default='')
    street = models.CharField(max_length=100, blank=True, default='')
    road = models.CharField(max_length=100, blank=True)
    city = models.ForeignKey('City', related_name='address_city', blank=True, null=True)
    district = models.ForeignKey('District', related_name='address_district', blank=True, null=True)
    province = models.ForeignKey('Province', related_name='address_province', blank=True, null=True)
    country = models.ForeignKey('Country', related_name='address_country', blank=True, null=True)

    tel_home = models.CharField(max_length=12, blank=True, default='')
    tel_home_suffix = models.CharField(max_length=6, blank=True, default='')
    tel_office = models.CharField(max_length=12, blank=True, default='')
    tel_office_suffix = models.CharField(max_length=6, blank=True, default='')
    tel_mobile = models.CharField(max_length=12, blank=True, default='')
    email = models.EmailField(max_length=50, blank=True, default='')
    note = models.CharField(max_length=200, blank=True, default='')
    channel = models.CharField(max_length=100, blank=True, null=True, default='')

    # channel = models.ForeignKey('ContactChannel', related_name='address_contact_channel', blank=True, null=True)

    @property
    def tel_home_full(self):
        if self.tel_home_suffix in (None, ''):
            return self.tel_home
        return '%s %s' % (self.tel_home, self.tel_home_suffix)

    @property
    def tel_office_full(self):
        if self.tel_office_suffix in (None, ''):
            return self.tel_office
        return '%s %s' % (self.tel_office, self.tel_office_suffix)

    def get_full_address(self, language=LANGUAGE_TH, FULL_ADDRESS_FIELD=None):
        if not FULL_ADDRESS_FIELD:
            FULL_ADDRESS_FIELD = ['no',
                                  'name',
                                  'town',
                                  'street',
                                  'road',
                                  'city',
                                  'district',
                                  'province',
                                  'country']
        result = ''
        for key in FULL_ADDRESS_FIELD:
            field = getattr(self, key, None)
            if field:
                if isinstance(field, ChoiceModel):
                    if language == LANGUAGE_EN:
                        result += field.name_en + ' '
                    else:
                        result += field.name + ' '
                else:
                    result += field + ' '
        return result.strip()

    def get_full_address_en(self):
        return self.get_full_address(language=LANGUAGE_EN)

    def get_full_address_for_hl7(self):
        FULL_ADDRESS_FIELD = ['no', 'name', 'town', 'street', 'road', 'city']
        address = self.get_full_address(language=LANGUAGE_TH, FULL_ADDRESS_FIELD=FULL_ADDRESS_FIELD)
        city = self.district.name if self.district else ''
        province = self.province.name if self.province else ''
        zipcode = self.city.zipcode if self.city else ''
        return '%s^%s^%s^%s' % (address, city, province, zipcode)

    def get_full_address_th(self, language=LANGUAGE_TH, FULL_ADDRESS_FIELD=None):
        if not FULL_ADDRESS_FIELD:
            FULL_ADDRESS_FIELD = ['no',
                                  'name',
                                  'town',
                                  'street',
                                  'road',
                                  'city',
                                  'district',
                                  'province',
                                  'country']
        result = ''
        for key in FULL_ADDRESS_FIELD:
            if key == 'no':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'เลขที่ ' + field.name + ' '
                    else:
                        result += 'เลขที่ ' + field + ' '
            elif key == 'name':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'หมู่บ้าน ' + field.name + ' '
                    else:
                        result += 'หมู่บ้าน ' + field + ' '
            elif key == 'town':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'หมู่ ' + field.name + ' '
                    else:
                        result += 'หมู่ ' + field + ' '
            elif key == 'street':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'ซอย ' + field.name + ' '
                    else:
                        result += 'ซอย ' + field + ' '
            elif key == 'road':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'ถนน ' + field.name + ' '
                    else:
                        result += 'ถนน ' + field + ' '
            elif key == 'city':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'แขวง/ตำบล ' + field.name + ' '
                    else:
                        result += 'แขวง/ตำบล ' + field + ' '
            elif key == 'district':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'เขต/อำเภอ ' + field.name + ' '
                    else:
                        result += 'เขต/อำเภอ ' + field + ' '
            elif key == 'province':
                field = getattr(self, key, None)
                if field:
                    if isinstance(field, ChoiceModel):
                        if language == LANGUAGE_EN:
                            result += field.name_en + ' '
                        else:
                            result += 'จังหวัด ' + field.name + ' '
                    else:
                        result += 'จังหวัด ' + field + ' '
        return result.strip()

    def get_full_address_th_with_zipcode(self):
        address = self.get_full_address_th()
        zipcode = self.city.zipcode if self.city else ''
        return '%s %s' % (address, zipcode)

    def get_premise(self):
        ADDRESS_FIELD = ['no',
                         'name',
                         'town',
                         'street',
                         'road',
                         'city']
        result = ''
        for key in ADDRESS_FIELD:
            field = getattr(self, key, None)
            if field:
                if isinstance(field, ChoiceModel):
                    result += field.name + ' '
                else:
                    result += field + ' '
        return result.strip()

    def __str__(self):
        return str(self.id)


class PatientQuerySet(models.QuerySet):
    def check_name_duplication(self, full_name: str):
        queryset = self.annotate(
            full_name_th=Replace(Concat(
                models.F('first_name_th'),
                models.F('middle_name_th'),
                models.F('last_name_th'),
            ), ' ', ''),
            full_name_en=Replace(Concat(
                models.F('first_name_en'),
                models.F('middle_name_en'),
                models.F('last_name_en'),
            ), ' ', ''),
        )

        full_name = re.sub('\s*', '', full_name)
        queryset = queryset.filter(full_name_th=full_name) | queryset.filter(full_name_en=full_name)
        return queryset.first()


class Patient(EditableModel):
    PATIENT_GENDER_CHOICES = GENDER_CHOICES + (
        ('U', 'Undetermined'),
        ('PM', 'Male(Not Approved)'),  # ทารกเพศหญิงที่ยังไม่ได้รับการยืนยันเพศ
        ('PF', 'Female(Not Appoved)')  # ทารกเพศชายที่ยังไม่ได้รับการยืนยันเพศ
    )
    MARRIAGE_CHOICES = (
        ('S', 'Single'),
        ('M', 'Married'),
        ('E', 'Engaged'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
        ('A', 'Separated'),
    )
    PREFIX_NON_IDENTITY = 'NI'
    PREFIX_HN = 'C'
    NOT_KNOWN_LAST_NAME = 'ไม่ทราบนามสกุล'

    class TYPE(LabeledIntEnum):
        NORMAL = 1, 'ผู้ป่วยทั่วไป'
        TEMP = 2, 'ผู้มาติดต่อเพื่อซื้อสินค้า'

    type = EnumField(TYPE, default=TYPE.NORMAL)
    hn = models.CharField(max_length=200, unique=True, null=True, blank=True, verbose_name="หมายเลข HN")
    pre_name = models.ForeignKey(Prename, related_name='+', null=True, blank=True, verbose_name="คำนำหน้าชื่อ")
    first_name = models.CharField(max_length=200, blank=True, verbose_name="ชื่อ")
    middle_name = models.CharField(max_length=80, blank=True, verbose_name="ชื่อกลาง")
    last_name = models.CharField(max_length=200, blank=True, verbose_name="นามสกุล")

    pre_name_th = models.ForeignKey(Prename, related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
                                    verbose_name="คำนำหน้าชื่อภาษาไทย")
    first_name_th = models.CharField(max_length=200, blank=True, verbose_name="ชื่อภาษาไทย")
    middle_name_th = models.CharField(max_length=80, blank=True, verbose_name="ชื่อกลางภาษาไทย")
    last_name_th = models.CharField(max_length=200, blank=True, verbose_name="นามสกุลภาษาไทย")

    pre_name_en = models.ForeignKey(Prename, related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
                                    verbose_name="คำนำหน้าชื่อภาษาอังกฤษ")
    first_name_en = models.CharField(max_length=80, blank=True, verbose_name="ชื่อภาษาอังกฤษ",
                                     validators=[validate_english])
    middle_name_en = models.CharField(max_length=80, blank=True, verbose_name="ชื่อกลางภาษาอังกฤษ",
                                      validators=[validate_english])
    last_name_en = models.CharField(max_length=80, blank=True, verbose_name="นามสกุลภาษาอังกฤษ",
                                    validators=[validate_english])

    sequence = models.CharField(max_length=80, default='')
    gender = models.CharField(max_length=2, default='M', choices=PATIENT_GENDER_CHOICES, verbose_name="เพศ", blank=True)
    marriage = models.CharField(max_length=1, default='S', choices=MARRIAGE_CHOICES, verbose_name="สถานภาพ", blank=True)
    birthdate = models.DateField(null=True, blank=True, verbose_name="วันเกิด")
    birthdate_year_only = models.BooleanField(default=False, verbose_name='ทราบวันเกิดแค่ปี')
    deathdate = models.DateTimeField(null=True, blank=True, verbose_name="วันและเวลาตาย")
    location = models.ForeignKey(Location, null=True, blank=True, help_text='สถานที่ล่าสุดที่ให้บริการผู้ป่วย')
    natural_mother = SelfReferenceForeignKey(null=True, blank=True,
                                             help_text='มารดาผู้ให้กำเนิด กรณีเป็นเด็กเกิดใหม่ที่โรงพยาบาล')
    student_no = models.CharField(max_length=15, null=True, blank=True, verbose_name='รหัสนักศึกษา')
    employee_no = models.CharField(max_length=15, null=True, blank=True, verbose_name='รหัสพนักงาน')

    race = models.ForeignKey('ClinicalTerm', blank=True, null=True, verbose_name='เชื้อชาติ')
    belief = models.TextField(blank=True, null=True, verbose_name='ความเชื่อ')
    objects = PatientQuerySet.as_manager()

    def __str__(self):
        return "[%s] %s %s" % (self.hn, self.first_name, self.last_name)

    def gen_hn(self):
        self.hn = HNGenerator.generate_hn(self, RunningNumber)

    def save(self, *args, **kwargs):
        is_skip_duplicate = kwargs.pop('is_skip_duplicate', False)
        super(Patient, self).save(*args, **kwargs)

        proxy_patient = None
        if 'PRX' in settings.DJANGO_INCLUDE_APPS:
            try:
                proxy_patient = self.proxypatient
            except ObjectDoesNotExist:
                pass

        if not self.hn and proxy_patient is None:
            self.gen_hn()
            super(Patient, self).save()

        if not is_skip_duplicate:
            # Add sequence if duplicate name
            # Check on both new & old patient (patient which change their name)
            same_name_patients = Patient.objects.filter(
                first_name=self.first_name,
                last_name=self.last_name,
            ).exclude(last_name=Patient.NOT_KNOWN_LAST_NAME)
            index = same_name_patients.count() - 1  # Minus 1 for self patient object
            if index > 0:
                # Found duplicate name
                self.update_patient_sequence(index)
            elif index == 0:
                # Check if this is last patient with sequence
                # (Patient may change the duplicate name to new name)
                p = same_name_patients[0]
                if p.sequence != '':
                    p.sequence = ''
                    p.save(is_skip_duplicate=True)

    def update_patient_sequence(self, index):
        """
        Add sequence to this patient and search for the other patient which has no sequence
        then update them too
        :return:
        """
        # Update self sequence
        self.sequence = str(index + 1)
        super(Patient, self).save()

        # Search for root duplicate patient and add sequence 1 to that patient
        p_list = Patient.objects.filter(
            first_name=self.first_name,
            last_name=self.last_name,
            sequence=''
        )
        p_list_size = p_list.count()
        if p_list_size == 1:
            root_patient = p_list[0]
            root_patient.sequence = '1'
            root_patient.save(is_skip_duplicate=True)
        elif p_list_size > 1:
            # Should not be here
            # It means we found 2 patient with duplicate name with no sequence number
            # Program has been bugged!!!!
            logger.error('Found patient with duplicate name %s, last %s with no sequence number on IDs %s',
                         self.first_name, self.last_name, str(p_list))

    def update_location(self, location):
        """
        Update patient location
        :param location: location to update
        :type location: Location
        :return:
        """
        self.location = location
        self.save()

    def get_all_encounter(self):
        if self.id is None:
            return None
        return [x['id'] for x in list(Encounter.objects.filter(patient=self.id).values('id'))]

    def get_last_encounter(self):
        return Encounter.objects.filter(patient=self).filter_active().last()

    def get_full_hn(self):
        return '%s-%s-%s' % (self.hn[0:4], self.hn[4:6], self.hn[6:8])

    def get_full_name(self):
        full_name = ""
        if self.pre_name:
            full_name = self.pre_name.name
        if self.middle_name and self.middle_name != '':
            full_name = "%s %s %s %s" % (full_name, self.first_name, self.middle_name, self.last_name)
        else:
            full_name = "%s %s %s" % (full_name, self.first_name, self.last_name)
        if full_name.strip() and self.sequence != '':
            full_name = "%s (%s)" % (full_name, self.sequence)
        return full_name

    def get_real_name(self, language=None):
        language = get_language(language)

        if language == LANGUAGE_EN:
            return self.get_real_name_en() or self.get_real_name_th()
        else:
            return self.get_real_name_th() or self.get_real_name_en()

    def get_real_name_th(self):
        name = []
        if self.pre_name_th:
            name.append(self.pre_name_th.name + self.first_name_th)
        else:
            name.append(self.first_name_th)
        if self.middle_name_th:
            name.append(self.middle_name_th)
        name.append(self.last_name_th)
        return ' '.join(name).strip()

    def get_real_name_en(self):
        name = []
        if self.pre_name_en:
            name.append(self.pre_name_en.name + self.first_name_en)
        else:
            name.append(self.first_name_en)
        if self.middle_name_en:
            name.append(self.middle_name_en)
        name.append(self.last_name_en)
        return ' '.join(name).strip()

    def get_name_code(self):
        return '%s (%s)' % (self.get_full_name(), self.hn)

    def get_full_age(self, language=None):
        language = get_language(language)

        if not self.birthdate:
            return ""

        if language == LANGUAGE_EN:
            age_en = self.get_full_age_en()
            return age_en

        today = date.today()
        delta = relativedelta.relativedelta(today, self.birthdate)
        year = delta.years
        if self.birthdate_year_only:
            return '%d ปี' % year

        month = delta.months
        day = delta.days
        return "%s ปี %s เดือน %s วัน" % (year, month, day)

    def get_full_age_en(self):
        if not self.birthdate:
            return ""

        today = date.today()
        delta = relativedelta.relativedelta(today, self.birthdate)
        year = delta.years
        if self.birthdate_year_only:
            return '%d years' % year

        month = delta.months
        day = delta.days
        return "%s years %s months %s days" % (year, month, day)

    def get_age(self) -> Union[None, int]:
        """
        :return: age in year (calculate by day/month/year in birthdate)
                 or None if no birthday specified
        """
        # suggested by: https://stackoverflow.com/a/9754466
        today = date.today()
        if not self.birthdate:
            return None

        year = today.year - self.birthdate.year
        pass_birth_date = (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
        return year - pass_birth_date

    def is_teenage(self):
        """
        :return: True if age >= 15
        """
        return (self.get_age() or 0) >= config.core_CHANGE_PRENAME_AGE

    def get_birthdate(self) -> str:
        """
        :return: birthdate string in พ.ศ.
        """
        if self.birthdate_year_only and self.birthdate:
            return "00/00/%d" % (self.birthdate.year + 543)
        return utils.ad_to_be(self.birthdate)

    def get_telephone_no(self):
        """
        :return: a default telephone no for patient (require REG)
        """
        if hasattr(self, 'patientdetail'):
            detail = self.patientdetail
            numbers = list()
            if detail.present_address is not None:
                numbers.append(detail.present_address.tel_mobile)
                numbers.append(detail.present_address.tel_home_full)
                numbers.append(detail.present_address.tel_office_full)
            if detail.relative_address is not None:
                numbers.append(detail.relative_address.tel_mobile)
                numbers.append(detail.relative_address.tel_home_full)
                numbers.append(detail.relative_address.tel_office_full)

            for number in numbers:
                if number not in (None, ''):
                    return number

    def get_gender_name(self):
        return dict(Patient.PATIENT_GENDER_CHOICES).get(self.gender)

    # def set_hn(self, hn: str):
    #     from his.apps.PRX import crypto
    #     self.hn = crypto.encode(hn)
    #
    # def get_hn(self):
    #     from his.apps.PRX import crypto
    #     return crypto.decode(self.hn) if self.hn else ''


class PatientCoverageQuerySet(models.QuerySet):
    def filter_actives(self, date=None):
        date = date or timezone.now()
        return (self.filter(start_date__lte=date, active=True)
                .filter(Q(stop_date__gte=date) | Q(stop_date__isnull=True)))

    def filter_active_coverages(self, date=None):
        """Get coverage by active, within date specified range"""
        return self.filter_actives(date).filter(coverage__type=Coverage.COVERAGE_TYPE.COVERAGE)

    def filter_active_discounts(self, date=None):
        """Get coverage by active, within date specified range"""
        return self.filter_actives(date).filter(coverage__type__in=[Coverage.COVERAGE_TYPE.DISCOUNT_POLICY,
                                                                    Coverage.COVERAGE_TYPE.DISCOUNT_CARD])

    def filter_active_packages(self):
        return self.filter_actives().filter(coverage__type=Coverage.COVERAGE_TYPE.PACKAGE)

    def create_or_update_coverage_both_type(self, patient, coverage, payer, start_date, stop_date):
        kwargs = {
            'patient': patient,
            'coverage': coverage,
            'payer': payer,
            'start_date': start_date,
            'stop_date': stop_date,
        }
        self.create_or_update_coverage(service_type=PatientCoverage.TYPE_OPD, **kwargs)
        self.create_or_update_coverage(service_type=PatientCoverage.TYPE_IPD, **kwargs)

    def create_or_update_coverage(self, patient, coverage, service_type, payer, start_date, stop_date,
                                  force_create=False):
        """
        if {patient, coverage, service_type} doesn't match any rows in PatientCoverage
            create a new one with {patient, coverage, service_type, payer, start_date, stop_date}
        if {patient, coverage, service_type} exists
            update an existing row with {payer, start_date, stop_date}
        :param patient: for query
        :param coverage: for query
        :param service_type: for query
        :param payer: use as updating field
        :param start_date:
        :param stop_date:
        :param force_create:
        :return:
        """
        if not force_create:
            patient_coverage, created = self.get_or_create(
                patient=patient,
                coverage=coverage,
                service_type=service_type,
                assure_type=AssureType.objects.get_undefined(),
                defaults={'payer': payer, 'start_date': start_date, 'stop_date': stop_date}
            )
            if not created:
                patient_coverage.payer = payer
                patient_coverage.start_date = start_date
                patient_coverage.stop_date = stop_date
                patient_coverage.save()
        else:
            patient_coverage = PatientCoverage()
            patient_coverage.patient = patient
            patient_coverage.coverage = coverage
            patient_coverage.payer = payer
            patient_coverage.start_date = start_date
            patient_coverage.stop_date = stop_date
            patient_coverage.assure_type = AssureType.objects.get_undefined()
            patient_coverage.service_type = service_type
            patient_coverage.save()
        return patient_coverage

    def activate_coverage_both_type(self, patient, coverage):
        if coverage:
            self.activate_coverage(patient=patient, coverage=coverage, service_type=PatientCoverage.TYPE_OPD)
            self.activate_coverage(patient=patient, coverage=coverage, service_type=PatientCoverage.TYPE_IPD)

    def activate_coverage(self, patient, coverage, service_type):
        patient_coverage, created = self.get_or_create(
            patient=patient,
            coverage=coverage,
            service_type=service_type,
            assure_type=AssureType.objects.get_undefined(),
            defaults={'start_date': date.today()}
        )
        # Check on start/stop date and change to match active conditions
        if (not created) and (not patient_coverage.active):
            patient_coverage.active = True
            if date.today() < patient_coverage.start_date:
                patient_coverage.start_date = date.today()
            if patient_coverage.stop_date and date.today() > patient_coverage.stop_date:
                patient_coverage.stop_date = None
            patient_coverage.save()
        return patient_coverage

    def deactivate_coverage(self, patient, coverage):
        patient_coverages = self.filter(patient=patient, coverage=coverage, active=True)
        for patient_coverage in patient_coverages:
            patient_coverage.active = False
            patient_coverage.save()

    def for_division(self, division: Division):
        return self.filter(Q(service_point=None) | Q(service_point=division))

    def order_by_priority(self):
        return self.order_by('priority', '-id')

    def for_encounter_type(self, encounter_type):
        if encounter_type == Encounter.TYPE_OPD:
            return self.filter(service_type=PatientCoverage.TYPE_OPD)
        elif encounter_type == Encounter.TYPE_IPD:
            return self.filter(service_type=PatientCoverage.TYPE_IPD)
        logger.warning('Not supported encounter_type = %s' % encounter_type)
        return self

    def has_overlapped_effective_date(self, patient, coverage, start_date, stop_date):
        queryset = self.filter(coverage__type=Coverage.COVERAGE_TYPE.PACKAGE)
        queryset = queryset.filter(patient=patient, coverage=coverage)
        queryset = queryset.filter(
            Q(start_date__range=(start_date, stop_date)) |
            Q(stop_date__range=(start_date, stop_date)) |
            (Q(start_date__lte=start_date) & Q(stop_date__gte=stop_date)) |
            (Q(start_date__gte=start_date) & Q(stop_date__lte=stop_date))
        )
        return queryset.exists()


class AssureTypeManager(models.Manager):
    def get_undefined(self):
        """Return UNK (cash only) coverage"""
        assure_type, _ = self.get_or_create(code=config.core_ASSURE_TYPE_UNDEFINED, name='ไม่ระบุ')
        return assure_type


class AssureType(ChoiceModel):
    code = models.CharField(max_length=20, unique=True)
    objects = AssureTypeManager()

    def __str__(self):
        return "[%s] %s" % (self.code, self.name)


class CommonCoverage(EditableModel):
    coverage = models.ForeignKey(Coverage, verbose_name='สิทธิผู้ป่วย')
    payer = models.ForeignKey(Payer, null=True, blank=True, verbose_name='ผู้จ่ายเงิน')
    project = models.ForeignKey(Project, null=True, blank=True, verbose_name='โครงการ')
    start_date = models.DateField(verbose_name='วันที่เริ่มต้นคุ้มครอง')
    stop_date = models.DateField(null=True, blank=True, verbose_name='วันที่สิ้นสุดการคุ้มครอง')
    referer = models.ForeignKey(Referer, null=True, blank=True, help_text='โรงพยาบาลต้นสังกัดกรณีผู้ป่วย Refer-in')
    refer_date = models.DateField(null=True, blank=True)
    refer_no = models.CharField(null=True, blank=True, max_length=255,
                                help_text='เลขรหัสหนังสือส่งตัว')
    assure_type = models.ForeignKey(AssureType, verbose_name='ประเภทการรับรองสิทธิ์')
    priority = models.IntegerField(default=99, verbose_name='ลำดับการเลือกใช้สิทธิ์')

    class Meta:
        abstract = True

    def get_settings(self):
        return CoveragePayerSettings.objects.filter(
            Q(Q(coverage=self.coverage) | Q(coverage=None)),
            Q(Q(payer=self.payer) | Q(payer=None)),
        ).first()


class PatientCoverage(CommonCoverage):
    """สิทธิ์ที่ผู้ป่วยมี (จะโดนคัดลอกไปใส่ใน EncounterCoverage)"""
    TYPE_OPD = 'O'
    TYPE_IPD = 'I'
    SERVICE_TYPES = (
        (TYPE_OPD, 'ผู้ป่วยนอก'),
        (TYPE_IPD, 'ผู้ป่วยใน'),
    )

    patient = models.ForeignKey(Patient)
    service_type = models.CharField(max_length=2, choices=SERVICE_TYPES, help_text="ประเภทบริการ",
                                    verbose_name='ประเภทบริการ')
    claim_code = models.CharField(max_length=50, blank=True)
    claim_code_request_date = models.DateField(verbose_name='วันที่ขอเลข e-claim', null=True, blank=True)
    claim_code_request_time = models.TimeField(verbose_name='เวลาที่ขอเลข e-claim', null=True, blank=True)
    claim_code_expiry_date = models.DateField(verbose_name='วันที่หมดอายุเลข e-claim', null=True, blank=True)
    claim_code_expiry_time = models.TimeField(verbose_name='เวลาที่หมดอายุเลข e-claim', null=True, blank=True)
    active = models.BooleanField(default=True, help_text="ใช้สิทธิ์ หรือระงับสิทธิ์")
    service_point = models.ManyToManyField(Division, blank=True, verbose_name='หน่วยงาน',
                                           help_text='จุดบริการ')

    objects = PatientCoverageQuerySet.as_manager()

    def __str__(self):
        return "id:%s coverage:%s ช่วงวันที่ %s - %s" % (self.id, self.coverage, self.start_date, self.stop_date)


class PatientCount(models.Model):
    created = models.DateField(auto_now_add=True, verbose_name='วันที่')
    patient_count = models.IntegerField(verbose_name='จำนวนผู้ป่วยในวัน')

    def __str__(self):
        return '%s %s' % (self.created, self.patient_count)


class PatientRelationQuerySet(models.QuerySet):
    def filter_relation_husband_wife(self, patient: Patient):
        return self.filter(
            (Q(base_patient=patient) | Q(related_patient=patient)) &
            (Q(forward_relation=PatientRelation.RELATION.HUSBAND) |
             Q(backward_relation=PatientRelation.RELATION.HUSBAND) |
             Q(forward_relation=PatientRelation.RELATION.WIFE) |
             Q(backward_relation=PatientRelation.RELATION.WIFE))
        )

    def filter_by_patient(self, patient: Patient):
        return self.filter(
            Q(base_patient=patient) | Q(related_patient=patient)
        ).select_related('related_patient', 'base_patient')

    def get_related_patients(self, patient: Patient):
        query1 = self.filter(base_patient=patient)
        query1 = query1.values_list('related_patient', flat=True)

        query2 = self.filter(related_patient=patient)
        query2 = query2.values_list('base_patient', flat=True)

        patients = set(list(query1) + list(query2))
        patients = Patient.objects.filter(id__in=patients)
        return patients


class PatientRelation(models.Model):
    """
    Describe relation between 2 patient.
    The relation will be forward and backward (mother and child or husband and wife)
    """

    class RELATION(LabeledIntEnum):
        UNKNOWN = 0, 'ไม่ทราบ'
        HUSBAND = 1, 'สามี'
        WIFE = 2, 'ภรรยา'
        CHILD = 3, 'ลูก'
        MOTHER = 4, 'แม่'
        FATHER = 5, 'พ่อ'
        BROTHER = 6, 'พี่-น้องชาย'
        SISTER = 7, 'พี่-น้องสาว'
        GRAND_CHILD = 8, 'หลาน'
        GRAND_MOTHER = 9, 'ย่า-ยาย'
        GRAND_FATHER = 10, 'ปู่-ตา'
        COUSIN = 11, 'ญาติ'
        DONOR = 12, 'ผู้บริจาค'
        RECEPTOR = 13, 'ผู้รับบริจาค'
        SURROGATE_MOM = 14, 'แม่อุ้มบุญ'
        BIOLOGICAL_PARENT = 15, 'ครอบครัว'

    base_patient = models.ForeignKey(Patient, related_name='relation_base_patient')
    related_patient = models.ForeignKey(Patient, related_name='relation_related_patient')
    forward_relation = EnumField(RELATION,
                                 verbose_name='ความสัมพันธ์ระหว่าง base ไปยัง related patient '
                                              'เช่น base(ญ) มี related(ช) เป็น สามี')
    backward_relation = EnumField(RELATION,
                                  verbose_name='ความสัมพันธ์ระหว่าง related ไปยัง base patient '
                                               'เช่น related(ช) มี base(ญ) เป็น ภรรยา')
    is_active = models.BooleanField(default=True)
    objects = PatientRelationQuerySet.as_manager()

    def get_related_patient(self, patient_id) -> Patient:
        # Get Patient object of given patient id
        if str(patient_id) == str(self.base_patient.id):
            return self.related_patient
        elif str(patient_id) == str(self.related_patient.id):
            return self.base_patient
        else:
            return None

    def get_relation(self, patient_id) -> RELATION:
        if str(patient_id) == str(self.base_patient.id):
            return self.forward_relation
        elif str(patient_id) == str(self.related_patient.id):
            return self.backward_relation
        else:
            return None


class Triage(EditableModel):
    PATIENT_WALK_IN = 'WLK'
    PATIENT_APPOINTMENT = 'APP'
    PATIENT_REFER_IN = 'REF'
    PATIENT_CONSULT = 'CON'
    PATIENT_TRANSFER = 'TRF'
    PATIENT_TYPE_CHOICES = (
        (PATIENT_WALK_IN, 'Walk-in'),
        (PATIENT_APPOINTMENT, 'นัดหมาย'),
        (PATIENT_REFER_IN, 'Refer-in'),
        (PATIENT_CONSULT, 'Consult'),
        (PATIENT_TRANSFER, 'ถูกส่งมาจากหน่วยงานอื่น'),
    )

    LEVEL_LIFE_THREATENING = '1'
    LEVEL_EMERGENCY = '2'
    LEVEL_URGENCY = '3'
    LEVEL_SEMI_URGENCY = '4'
    LEVEL_GENERAL = '5'
    TRIAGE_LEVEL_CHOICES = (
        (LEVEL_LIFE_THREATENING, 'Life Threatening'),
        (LEVEL_EMERGENCY, 'Emergency'),
        (LEVEL_URGENCY, 'Urgency'),
        (LEVEL_SEMI_URGENCY, 'Semi-Urgency'),
        (LEVEL_GENERAL, 'ทั่วไป'),
    )

    division = models.ForeignKey(Division, blank=True, null=True)
    chief_complaint = models.CharField(max_length=255)
    arrive_status = models.ForeignKey(ClinicalTerm, related_name='triage_arrive_status', verbose_name='สถานะการมา')
    case = models.ForeignKey(ClinicalTerm, related_name='triage_case', verbose_name='ประเภท case ผู้ป่วย')
    patient_type = models.CharField(max_length=3, default=PATIENT_WALK_IN, choices=PATIENT_TYPE_CHOICES,
                                    verbose_name='ประเภทผู้ป่วย')
    referer = models.CharField(max_length=255, blank=True, verbose_name='ผู้นำส่ง')
    triage_level = models.CharField(max_length=3, default=LEVEL_GENERAL, choices=TRIAGE_LEVEL_CHOICES,
                                    verbose_name='ระดับการคัดกรอง')

    def encounters(self):
        return [x[0] for x in self.encounter_set.all().values_list('id')]


class Episode(EditableModel):
    """Episode of care
    Episode of care is the managed care provided by a health care facility or provider for
    a specific medical problem or condition or specific illness during a set of time period.
    It contains group of encounter use for curing disease of patient.
    In case of chronic disease the episode may contains multiple encounters both IPD and OPD,
    but in acute case the episode field will not be used (e.g. common cold).
    NOTE : Currently in RAMA all illness is acute case. We may use this field in the future.
           However in case of Jetanin, Episode will be used with ART cycle.
    TODO : Add more illness or disease information of each episode. Need to discuss the further
           concept before we can decide which information to add on this model.
    """
    patient = models.ForeignKey(Patient, verbose_name='ผู้ป่วยที่เกี่ยวข้อง')
    name = models.CharField(max_length=255, verbose_name='ชื่อ Episode of care')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    start_date = models.DateTimeField(auto_now_add=True, verbose_name='วันเริ่มต้น Episode')
    end_date = models.DateTimeField(null=True, blank=True, verbose_name='วันสิ้นสุด Episode')
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Episode of care'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s - %s' % (self.patient, self.name)


class EncounterQuerySet(models.QuerySet):
    def filter_unexpired(self):
        return self.filter_unexpired_opd() | self.filter_unexpired_ipd() | self.filter_unexpired_oth()

    def filter_unexpired_admit(self):
        queryset = self.filter(type__in=Encounter.ADMIT_TYPES)
        if config.core_IPD_ENCOUNTER_EXPIRE:
            expire_date = datetime.now() - timedelta(hours=config.core_IPD_ENCOUNTER_EXPIRE)
            return queryset.filter(Q(ended__gte=expire_date) | Q(ended=None) | Q(type=Encounter.TYPE_SS))
        else:
            return queryset

    def filter_unexpired_ipd(self):
        queryset = self.filter(type__in=Encounter.IPD_TYPES)
        if config.core_IPD_ENCOUNTER_EXPIRE:
            expire_date = datetime.now() - timedelta(hours=config.core_IPD_ENCOUNTER_EXPIRE)
            return queryset.filter(Q(ended__gte=expire_date) | Q(ended=None))
        else:
            return queryset

    def filter_unexpired_opd(self):
        """
        You should use .filter_active_opd instead. This function does not exclude encounter that is discharged
        """
        queryset = self.filter(type__in=Encounter.OPD_TYPES)
        yesterday = datetime.now() - timedelta(hours=config.core_OPD_ENCOUNTER_EXPIRE)
        return queryset.filter(created__gte=yesterday)

    def filter_unexpired_oth(self):
        queryset = self.filter(type=Encounter.TYPE_OTH)
        yesterday = datetime.now() - timedelta(hours=config.core_OPD_ENCOUNTER_EXPIRE)
        return queryset.filter(created__gte=yesterday)

    def exclude_finish(self):
        return self.exclude(status__in=[
            Encounter.STATUS.DISCHARGED,
            Encounter.STATUS.FINISHED,
            Encounter.STATUS.WAIT_DISPENSE,
            Encounter.STATUS.CANCELED
        ]).filter_unexpired_opd()

    def filter_active(self):
        return self.filter_unexpired().exclude_discharged()

    def filter_active_ipd(self):
        return self.filter_unexpired_ipd().exclude_discharged()

    def filter_active_opd(self):
        return self.filter_unexpired_opd().exclude_discharged()

    def filter_active_oth(self):
        return self.filter_unexpired_oth().exclude_discharged()

    def exclude_discharged(self):
        return self.exclude(status__in=[
            Encounter.STATUS.FINISHED,
            Encounter.STATUS.DISCHARGED,
            Encounter.STATUS.CANCELED,
        ])

    def filter_general_type(self, general_type):
        if general_type == Encounter.TYPE_OPD:
            return self.filter(type__in=[Encounter.TYPE_OPD, Encounter.TYPE_ER, Encounter.TYPE_OTH, Encounter.TYPE_SS])
        elif general_type == Encounter.TYPE_IPD:
            return self.filter(type__in=[Encounter.TYPE_IPD])
        else:
            raise Exception('invalid Encounter.general_type')

    def filter_diagnosed(self):
        """List of today diagnosed encounter in today"""
        queryset = self.filter(created__date=datetime.today())
        return queryset.filter(status__in=[Encounter.STATUS.WAIT_RESULT, Encounter.STATUS.RECEIVE_RESULT,
                                           Encounter.STATUS.CHECKED_OUT, Encounter.STATUS.WAIT_PAY,
                                           Encounter.STATUS.WAIT_DISPENSE, Encounter.STATUS.DISCHARGED])

    def filter_wait_diagnosis(self):
        """List of today encounter wait for diagnose with doctor"""
        queryset = self.filter(created__date=datetime.today())
        return queryset.filter(status__in=[Encounter.STATUS.WAIT_TRIAGE, Encounter.STATUS.ARRIVING,
                                           Encounter.STATUS.ARRIVED, Encounter.STATUS.SCREENED,
                                           Encounter.STATUS.IN_QUEUE])

    def get_active_or_create_other(self, patient: Patient, user: User, division: Division):
        encounter = Encounter.objects.filter_active().filter(patient=patient).last()

        if not encounter:
            encounter = Encounter.objects.create(
                type=Encounter.TYPE_OTH,
                action=Encounter.ACTION.OTH_NEW,
                hospital_fee_charged=True,
                patient=patient,
                user=user,
                division=division,
            )

        return encounter

    def get_or_create_other_active(self, patient: Patient, user: User, division: Division):
        """
        Filer active encounter with type OTH or create new encounter with type OTH
        Unlike get_active_or_create_other which only create OTH but it may query normal Encounter to user
        """
        encounter = Encounter.objects.filter_active().filter(patient=patient, type=Encounter.TYPE_OTH).last()

        if not encounter:
            encounter = Encounter.objects.create(
                type=Encounter.TYPE_OTH,
                action=Encounter.ACTION.OTH_NEW,
                hospital_fee_charged=True,
                patient=patient,
                user=user,
                division=division,
            )

        return encounter


class Encounter(StatableModel):
    """Queue"""
    MORNING_WALKIN_HOUR = 11
    AFTERNOON_WALKIN_HOUR = 15
    WALKIN_MINUTE = 31
    START_MORNING_TIME = time(hour=0, minute=0, second=0, microsecond=0)
    END_MORNING_TIME = time(hour=11, minute=59, second=59, microsecond=59)
    START_AFTERNOON_TIME = time(hour=12, minute=0, second=0, microsecond=0)
    END_AFTERNOON_TIME = time(hour=23, minute=59, second=59, microsecond=59)

    """Visit (VN), PatientAdmission (AN)"""
    TYPE_OPD = 'OPD'
    TYPE_IPD = 'IPD'
    TYPE_SS = 'SS'
    TYPE_ER = 'ER'
    TYPE_OTH = 'OTH'
    TYPES = (
        (TYPE_OPD, 'OPD'),
        (TYPE_IPD, 'IPD'),
        (TYPE_SS, 'Short Stay'),
        (TYPE_ER, 'ER'),
        (TYPE_OTH, 'OTH'),
    )

    GENERAL_TYPES = (
        (TYPE_OPD, TYPE_OPD),
        (TYPE_IPD, TYPE_IPD),
    )
    IPD_TYPES = [TYPE_IPD]
    OPD_TYPES = [TYPE_OPD, TYPE_ER, TYPE_SS]
    ADMIT_TYPES = [TYPE_IPD, TYPE_SS]

    CLINIC_TYPE_REGULAR = 'RGL'
    CLINIC_TYPE_SPECIAL = 'SPC'
    CLINIC_TYPE_PREMIUM = 'PRM'
    CLINIC_TYPES = (
        (CLINIC_TYPE_REGULAR, 'Regular (ปกติ)'),
        (CLINIC_TYPE_SPECIAL, 'Special (นอกเวลา)'),
        (CLINIC_TYPE_PREMIUM, 'Premium')
    )

    # only numbers are allowed to calculate checksum (DAMM's algorithm)
    PREFIX_OPD = '901'
    PREFIX_IPD = '902'
    PREFIX_SS = '903'
    PREFIX_ER = '904'

    class ACTION(LabeledIntEnum):
        OPD_NEW = 1, 'บันทึก Encounter ใหม่'
        OPD_TRIAGE = 2, 'บันทึกคัดกรอง'
        OPD_ARRIVE = 3, 'รับเข้า'
        OPD_SCREEN = 4, 'ประเมินแรกรับ'
        OPD_QUEUE_EXAM = 5, 'ส่งเข้าคิวรอตรวจ'
        OPD_CHECK_IN = 6
        OPD_CHECK_OUT = 7, 'Check Out'
        OPD_DISCHARGE = 8, 'Discharge'
        OPD_PAID = 9
        OPD_DISPENSE = 10
        OPD_SEND_LAB = 11
        OPD_SEND_TREATMENT = 12
        OPD_EDIT = 13, 'แก้ไข Encounter'
        OPD_FINISH_LAB = 15
        OPD_FINISH_TREATMENT = 16
        OPD_UNDISCHARGE = 17
        OPD_CANCEL = 18
        OPD_DISCHARGE_BILLING = 19
        OPD_CANCEL_CHECK_IN = 20
        OPD_CANCEL_QUEUE_EXAM = 21, 'ยกเลิกส่งเข้าคิวรอตรวจ'

        # ---- IPD action ----
        ADMISSION_ADMIT = 101
        ADMIT = 102
        IPD_CHECK_OUT = 103,
        IPD_CASHIER_REQUEST = 104,
        IPD_CASHIER_DISCHARGE = 105
        IPD_DISCHARGE = 106
        IPD_CANCEL_CASHIER_REQUEST = 108
        IPD_CANCEL_CHECK_OUT = 109
        IPD_CANCEL_ROOM_PAYMENT = 110
        IPD_CANCEL_ADMIT = 111

        # ---- other ----
        OTH_NEW = 14

    class STATUS(LabeledIntEnum):
        # ---- OPD status ----
        WAIT_TRIAGE = 1, 'รอคัดกรอง'
        ARRIVING = 2, 'กําลังมาถึง'
        ARRIVED = 3, 'มาถึง ณ หน่วยตรวจ'
        SCREENED = 4, 'ซักประวัติแล้ว'
        IN_QUEUE = 5, 'รอพบแพทย์'
        IN_EXAM = 6, 'กำลังพบแพทย์'
        WAIT_RESULT = 15, 'รอผลตรวจ'
        RECEIVE_RESULT = 16, 'ได้รับผลตรวจ'
        CHECKED_OUT = 10, 'ออกจากห้องตรวจ'
        WAIT_PAY = 11, 'รอชำระเงินห้องการเงิน'
        WAIT_DISPENSE = 12, 'รอรับบริการ'
        DISCHARGED = 13, 'จำหน่ายผู้ป่วยกลับบ้าน'

        ISSARA_DISCHARGED = 201, 'DISCHARGED FOR DBMS'  # this status can pass encounter expired exception

        # ---- IPD status ----
        ADMISSION_ADMITED = 101, 'Admit'
        ADMITTED = 102, 'Ward Admitted'
        IPD_CHECKED_OUT = 103, 'หมอมีคำสั่งให้ Discharge'
        IPD_CASHIER_REQUESTED = 104, 'Cashier Request'
        IPD_CASHIER_DISCHARGED = 105, 'Cashier Discharged'
        FINISHED = 106, 'กลับบ้าน'
        CANCELED = 107, 'ยกเลิก'

        @property
        def type(self):
            """ Define type
            status number > 100 is 'IPD'
            status number < 100 is 'OPD'

            :Example:
            >>> Encounter.STATUS.WAIT_PAY.type
            """
            return 'OPD' if (self < 100) else 'IPD'

    TRANSITION = [
        (None, ACTION.OTH_NEW, STATUS.WAIT_PAY),
        # สำหรับ รับยาขาดคราว / เติมยา / รับเวชภัณฑ์ขาดคราว / รับเวชภัณฑ์สั่งทำ

        (None, ACTION.OPD_NEW, STATUS.WAIT_TRIAGE),
        (STATUS.WAIT_TRIAGE, ACTION.OPD_TRIAGE, STATUS.ARRIVING),
        (STATUS.WAIT_TRIAGE, ACTION.OPD_EDIT, STATUS.WAIT_TRIAGE),
        (STATUS.WAIT_TRIAGE, ACTION.OPD_CANCEL, STATUS.CANCELED),
        (STATUS.WAIT_TRIAGE, ACTION.OPD_CHECK_IN, STATUS.IN_EXAM),
        (STATUS.ARRIVING, ACTION.OPD_ARRIVE, STATUS.ARRIVED),
        (STATUS.ARRIVING, ACTION.OPD_EDIT, STATUS.ARRIVING),
        (STATUS.ARRIVING, ACTION.OPD_SCREEN, STATUS.SCREENED),
        (STATUS.ARRIVING, ACTION.OPD_DISCHARGE, STATUS.WAIT_PAY),
        (STATUS.ARRIVING, ACTION.OPD_CANCEL, STATUS.CANCELED),
        (STATUS.ARRIVING, ACTION.OPD_CHECK_IN, STATUS.IN_EXAM),
        (STATUS.SCREENED, ACTION.OPD_EDIT, STATUS.SCREENED),
        (STATUS.SCREENED, ACTION.OPD_CHECK_IN, STATUS.IN_EXAM),
        (STATUS.WAIT_TRIAGE, ACTION.OPD_SCREEN, STATUS.SCREENED),
        (STATUS.ARRIVED, ACTION.OPD_ARRIVE, STATUS.ARRIVED),
        (STATUS.ARRIVED, ACTION.OPD_SCREEN, STATUS.SCREENED),
        (STATUS.ARRIVED, ACTION.OPD_DISCHARGE, STATUS.WAIT_PAY),
        (STATUS.ARRIVED, ACTION.OPD_CHECK_IN, STATUS.IN_EXAM),
        (STATUS.SCREENED, ACTION.OPD_QUEUE_EXAM, STATUS.IN_QUEUE),
        (STATUS.IN_QUEUE, ACTION.OPD_CHECK_IN, STATUS.IN_EXAM),
        (STATUS.IN_QUEUE, ACTION.OPD_ARRIVE, STATUS.IN_QUEUE),
        (STATUS.IN_QUEUE, ACTION.OPD_EDIT, STATUS.IN_QUEUE),
        (STATUS.IN_QUEUE, ACTION.OPD_CANCEL_QUEUE_EXAM, STATUS.SCREENED),

        (STATUS.IN_EXAM, ACTION.OPD_EDIT, STATUS.IN_EXAM),
        (STATUS.IN_EXAM, ACTION.OPD_SEND_LAB, STATUS.WAIT_RESULT),
        (STATUS.IN_EXAM, ACTION.OPD_SEND_TREATMENT, STATUS.WAIT_RESULT),
        (STATUS.IN_EXAM, ACTION.OPD_CANCEL_CHECK_IN, STATUS.IN_QUEUE),
        (STATUS.WAIT_RESULT, ACTION.OPD_SEND_TREATMENT, STATUS.WAIT_RESULT),
        (STATUS.WAIT_RESULT, ACTION.OPD_SEND_LAB, STATUS.WAIT_RESULT),
        (STATUS.WAIT_RESULT, ACTION.OPD_FINISH_LAB, STATUS.RECEIVE_RESULT),
        (STATUS.WAIT_RESULT, ACTION.OPD_FINISH_TREATMENT, STATUS.RECEIVE_RESULT),
        (STATUS.WAIT_RESULT, ACTION.OPD_ARRIVE, STATUS.WAIT_RESULT),
        (STATUS.WAIT_RESULT, ACTION.OPD_QUEUE_EXAM, STATUS.IN_QUEUE),
        (STATUS.WAIT_RESULT, ACTION.OPD_CHECK_OUT, STATUS.CHECKED_OUT),
        (STATUS.WAIT_RESULT, ACTION.OPD_DISCHARGE, STATUS.WAIT_PAY),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_ARRIVE, STATUS.RECEIVE_RESULT),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_QUEUE_EXAM, STATUS.IN_QUEUE),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_CHECK_OUT, STATUS.CHECKED_OUT),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_DISCHARGE, STATUS.WAIT_PAY),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_FINISH_TREATMENT, STATUS.RECEIVE_RESULT),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_FINISH_LAB, STATUS.RECEIVE_RESULT),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_EDIT, STATUS.RECEIVE_RESULT),
        (STATUS.IN_EXAM, ACTION.OPD_CHECK_OUT, STATUS.CHECKED_OUT),
        (STATUS.CHECKED_OUT, ACTION.OPD_CHECK_OUT, STATUS.CHECKED_OUT),
        (STATUS.CHECKED_OUT, ACTION.OPD_ARRIVE, STATUS.CHECKED_OUT),
        (STATUS.CHECKED_OUT, ACTION.OPD_DISCHARGE, STATUS.WAIT_PAY),
        (STATUS.CHECKED_OUT, ACTION.OPD_QUEUE_EXAM, STATUS.IN_QUEUE),
        (STATUS.WAIT_PAY, ACTION.OPD_PAID, STATUS.WAIT_DISPENSE),
        (STATUS.WAIT_DISPENSE, ACTION.OPD_ARRIVE, STATUS.WAIT_DISPENSE),
        (STATUS.WAIT_DISPENSE, ACTION.OPD_DISCHARGE, STATUS.DISCHARGED),
        (STATUS.DISCHARGED, ACTION.OPD_UNDISCHARGE, STATUS.WAIT_PAY),
        (STATUS.WAIT_PAY, ACTION.OPD_UNDISCHARGE, STATUS.CHECKED_OUT),

        # Encounter which open for doing lab or treatment from appointment
        (STATUS.WAIT_TRIAGE, ACTION.OPD_FINISH_LAB, STATUS.RECEIVE_RESULT),
        (STATUS.WAIT_TRIAGE, ACTION.OPD_FINISH_TREATMENT, STATUS.RECEIVE_RESULT),
        (STATUS.ARRIVED, ACTION.OPD_FINISH_LAB, STATUS.RECEIVE_RESULT),
        (STATUS.ARRIVING, ACTION.OPD_FINISH_LAB, STATUS.RECEIVE_RESULT),
        (STATUS.ARRIVING, ACTION.OPD_FINISH_TREATMENT, STATUS.RECEIVE_RESULT),
        (STATUS.IN_EXAM, ACTION.OPD_FINISH_LAB, STATUS.IN_EXAM),
        (STATUS.IN_EXAM, ACTION.OPD_FINISH_TREATMENT, STATUS.IN_EXAM),
        (STATUS.CHECKED_OUT, ACTION.OPD_FINISH_LAB, STATUS.CHECKED_OUT),
        (STATUS.CHECKED_OUT, ACTION.OPD_FINISH_TREATMENT, STATUS.CHECKED_OUT),
        (STATUS.WAIT_PAY, ACTION.OPD_FINISH_LAB, STATUS.WAIT_PAY),
        (STATUS.WAIT_DISPENSE, ACTION.OPD_FINISH_LAB, STATUS.WAIT_DISPENSE),
        (STATUS.DISCHARGED, ACTION.OPD_FINISH_LAB, STATUS.DISCHARGED),
        (STATUS.IN_QUEUE, ACTION.OPD_FINISH_LAB, STATUS.IN_QUEUE),
        (STATUS.SCREENED, ACTION.OPD_FINISH_LAB, STATUS.SCREENED),
        (STATUS.RECEIVE_RESULT, ACTION.OPD_SEND_TREATMENT, STATUS.RECEIVE_RESULT),

        # For ORM
        (STATUS.WAIT_TRIAGE, ACTION.OPD_ARRIVE, STATUS.ARRIVED),
        (STATUS.ARRIVED, ACTION.OPD_DISCHARGE_BILLING, STATUS.WAIT_PAY),

        # IPD BEFORE ADMIT
        # Allow discharge without meeting with doctor. (For Lab & Treatment only, or patient run away)
        (STATUS.SCREENED, ACTION.OPD_DISCHARGE, STATUS.DISCHARGED),  # the day patient come to admit
        # (STATUS.SCREENED, ACTION.OPD_DISCHARGE, STATUS.WAIT_PAY),  # the day patient come to admit
        (None, ACTION.ADMISSION_ADMIT, STATUS.ADMISSION_ADMITED),
        (STATUS.ADMISSION_ADMITED, ACTION.ADMISSION_ADMIT, STATUS.ADMISSION_ADMITED),
        (STATUS.ADMISSION_ADMITED, ACTION.ADMIT, STATUS.ADMITTED),
        (STATUS.ADMISSION_ADMITED, ACTION.IPD_CANCEL_ADMIT, STATUS.CANCELED),
        # IPD AFTER ADMIT
        (STATUS.ADMITTED, ACTION.IPD_CANCEL_ADMIT, STATUS.CANCELED),
        (STATUS.ADMITTED, ACTION.IPD_CHECK_OUT, STATUS.IPD_CHECKED_OUT),
        (STATUS.ADMITTED, ACTION.ADMIT, STATUS.ADMITTED),
        (STATUS.IPD_CHECKED_OUT, ACTION.IPD_CASHIER_REQUEST, STATUS.IPD_CASHIER_REQUESTED),
        (STATUS.IPD_CHECKED_OUT, ACTION.IPD_CANCEL_CHECK_OUT, STATUS.ADMITTED),
        (STATUS.IPD_CASHIER_REQUESTED, ACTION.IPD_CASHIER_DISCHARGE, STATUS.IPD_CASHIER_DISCHARGED),
        (STATUS.IPD_CASHIER_REQUESTED, ACTION.IPD_CANCEL_CASHIER_REQUEST, STATUS.IPD_CHECKED_OUT),
        (STATUS.IPD_CASHIER_DISCHARGED, ACTION.IPD_CANCEL_ROOM_PAYMENT, STATUS.IPD_CASHIER_REQUESTED),
        (STATUS.IPD_CASHIER_DISCHARGED, ACTION.IPD_DISCHARGE, STATUS.FINISHED),
    ]

    BIL_STATUS = [
        STATUS.WAIT_PAY,
        STATUS.WAIT_DISPENSE,
    ]

    episode = models.ForeignKey(Episode, null=True, blank=True, verbose_name='Episode of care')
    number = models.CharField(max_length=12, default='')
    type = models.CharField(max_length=4, choices=TYPES)
    patient = models.ForeignKey(Patient)
    division = models.ForeignKey(Division, null=True, blank=True)
    doctor = models.ForeignKey(Doctor, null=True, blank=True)
    remark = models.CharField(max_length=255, blank=True, help_text="จุดสังเกต")
    note = models.CharField(max_length=255, blank=True, help_text="หมายเหตุ")
    drug_allergy = models.CharField(max_length=255, blank=True, null=True, help_text="แพ้ยา")
    other_allergy = models.CharField(max_length=255, blank=True, null=True, help_text="แพ้อื่น ๆ")
    underlying_disease = models.CharField(max_length=255, blank=True, help_text="โรคประจำตัว")
    started = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(null=True, blank=True)
    triage = models.ForeignKey('Triage', null=True, blank=True)
    triage_level = models.CharField(max_length=3, verbose_name='ระดับการคัดกรอง', blank=True)
    chief_complaints = models.CharField(max_length=255, blank=True, help_text="อาการเบื่องต้น")
    objects = EncounterQuerySet.as_manager()
    predischarge_condition = models.ForeignKey(ClinicalTerm, blank=True, null=True, related_name='+',
                                               help_text="สภาพผู้ป่วยก่อนจำหน่าย")
    discharge_status = models.ForeignKey(ClinicalTerm, blank=True, null=True, related_name='+',
                                         help_text="Discharge Status")
    discharge_note = models.CharField(max_length=255, blank=True, help_text="รายละเอียดการ Discharge")
    is_appointment = models.BooleanField(default=False, help_text="encounter ที่เปิดจากการนัดหมาย")
    queue_date = models.DateField(auto_now_add=True, help_text="ใช้สำหรับจัดเรียงคิว")
    queue_time = models.TimeField(null=True, blank=True, help_text="หากเป็นนัดหมายจะเป็นเวลาที่นัดหมาย \
                                               หากไม่ใช่จะเป็น 11.30 สำหรับ walk-in เช้า \
                                               และ 15.30 สำหรับ walk-in บ่าย")

    hospital_fee_charged = models.BooleanField(default=False, help_text='คิดค่าเหยียบโรงบาลแล้ว?')
    tracker = FieldTracker(fields=['division', 'status'])
    clinic_type = models.CharField(max_length=3, choices=CLINIC_TYPES, default=CLINIC_TYPE_REGULAR)
    cleaning = models.ForeignKey(CleaningChoice, blank=True, null=True, help_text='ประเภทเวลาในการทำความสะอาด')
    examination_type = models.ForeignKey(ExaminationTypeChoice, blank=True, null=True)

    def __str__(self):
        return '[%d - %s] %s' % (self.id, self.number, self.patient.get_full_name())

    def gen_vn(self):
        number = str(
            RunningNumber.objects.get_next_number(Encounter, Encounter.PREFIX_OPD, reset=RunningNumber.RESET_WEEKLY))
        number = number + str(damm_encode(Encounter.PREFIX_OPD + number))
        self.number = number

    def gen_an(self):
        number = str(RunningNumber.objects.get_next_number(Encounter, Encounter.PREFIX_IPD))
        number = number + str(damm_encode(Encounter.PREFIX_IPD + number))
        self.number = number

    def gen_ss(self):
        number = str(RunningNumber.objects.get_next_number(Encounter, Encounter.PREFIX_SS))
        number = number + str(damm_encode(Encounter.PREFIX_SS + number))
        self.number = number

    def generate_encounter_number(self):
        if self.number == '' and self.type == Encounter.TYPE_OTH:
            self.gen_vn()

        if self.number == '' and self.type == Encounter.TYPE_OPD:
            self.gen_vn()

        if self.number == '' and self.type == Encounter.TYPE_ER:
            self.gen_vn()

        if self.number == '' and self.type == Encounter.TYPE_IPD:
            self.gen_an()

        if self.number == '' and self.type == Encounter.TYPE_SS:
            self.gen_ss()

    def get_type_an_vn_ss(self):
        if self.type == Encounter.TYPE_OTH:
            return 'VN'
        elif self.type == Encounter.TYPE_OPD:
            return 'VN'
        elif self.type == Encounter.TYPE_ER:
            return 'VN'
        elif self.type == Encounter.TYPE_IPD:
            return 'AN'
        elif self.type == Encounter.TYPE_SS:
            return 'SS'

    def pre_oth_new(self):
        assert self.type == Encounter.TYPE_OTH

    @property
    def latest_zone_log(self):
        return self.zone_log.last()

    @transaction.atomic
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.generate_encounter_number()
        newly_create = not self.pk
        # Newly created encounter, set queue no appointment
        if not self.pk and self.is_appointment is False:
            queue_time = datetime.now().time()
            if Encounter.START_MORNING_TIME <= queue_time <= Encounter.END_MORNING_TIME:
                queue_time = queue_time.replace(hour=Encounter.MORNING_WALKIN_HOUR,
                                                minute=Encounter.WALKIN_MINUTE,
                                                second=0,
                                                microsecond=0)
            elif Encounter.START_AFTERNOON_TIME <= queue_time <= Encounter.END_AFTERNOON_TIME:
                queue_time = queue_time.replace(hour=Encounter.AFTERNOON_WALKIN_HOUR,
                                                minute=Encounter.WALKIN_MINUTE,
                                                second=0,
                                                microsecond=0)
            self.queue_time = queue_time

        clinic_type_changed = self.set_clinic_type()
        super().save(force_insert, force_update, using, update_fields)
        if clinic_type_changed and self.type in Encounter.OPD_TYPES:
            # Only re-calculate for the OPD
            do_service('BIL:recalculate_for_encounter', self)

        self.create_or_update_encounter_coverage(detect_division_change=True, newly_create=newly_create)

        self.check_hospital_fee()
        self.update_hospital_fee()
        self.create_or_update_hospital_fee()
        self.check_division_ward_premium()

        self.update_payment_status(self.user, notify=False)
        self.update_dispense_status(self.user, notify=False)
        self.notify_encounter_change()
        self.notify_current_division()
        self.transfer_invoice_items_if_possible(user=self.user)

    def check_division_ward_premium(self):
        if not self.division:
            pass
        elif self.division.type == Division.TYPE.WARD_PREMIUM:
            self.clinic_type = Encounter.CLINIC_TYPE_PREMIUM

    def notify_current_division(self):
        if not self.division:
            pass

        elif self.tracker.has_changed('status') or self.tracker.has_changed('division'):
            Messenger.push_to_location(self.division.code,
                                       source='core',
                                       event='update_encounter_queue',
                                       encounter_id=self.pk)

    def notify_encounter_change(self):
        Messenger.push_to_encounter(self,
                                    source='core',
                                    event='update_encounter_queue',
                                    encounter_id=self.pk)
        self.notify_billing_division()

    def notify_billing_division(self):
        if not self.division:
            pass

        elif self.status in self.BIL_STATUS + [self.STATUS.DISCHARGED]:
            if self.division.billing_div:
                Messenger.push_to_location(self.division.billing_div.code,
                                           source='core',
                                           event='update_encounter_queue',
                                           encounter_id=self.pk)
            else:
                logger.error('Division [%s] don\'t have billing division' % self.division.code)

    def set_clinic_type(self):
        if self.division and self.tracker.has_changed('division'):
            if self.division.type == Division.TYPE.PREMIUM_CLINIC:
                new_clinic_type = Encounter.CLINIC_TYPE_PREMIUM
            else:
                if self.type in (Encounter.TYPE_IPD, Encounter.TYPE_SS):
                    new_clinic_type = Encounter.CLINIC_TYPE_REGULAR
                else:
                    is_office_time = (DivisionWorkSchedule.objects.is_available(self.division) and
                                      not DivisionStopWorkSchedule.objects.stop_on(self.division))
                    if is_office_time:
                        new_clinic_type = Encounter.CLINIC_TYPE_REGULAR
                    else:
                        new_clinic_type = Encounter.CLINIC_TYPE_PREMIUM
            if self.clinic_type != new_clinic_type:
                if self.id and do_service('BIL:has_encounter_paid', self):
                    raise serializers.ValidationError('มีรายการชำระเงินแล้ว ไม่สามารถเปลี่ยนเป็นแผนก %s ได้ '
                                                      'เนื่องจากทำให้ clinic type เปลี่ยน' % self.division.name)
                else:
                    self.clinic_type = new_clinic_type
                    return True
        return False

    def create_or_update_encounter_coverage(self, detect_division_change=False, newly_create=False,
                                            patient_coverage_changed=False):
        if detect_division_change and self.tracker.has_changed('division') is False and not newly_create:
            return

        if self.type == Encounter.TYPE_IPD and not newly_create and not patient_coverage_changed:
            return

        qa_claim = do_service('CLM:allow_change_encounter_coverage', encounter=self)
        is_allow = do_service('BIL:allow_change_encounter_coverage', encounter=self)
        if qa_claim is False or is_allow is False:
            return

        # clone PatientCoverage -> EncounterCoverage (type COVERAGE)
        created_date = self.created
        encounter_coverages = EncounterCoverage.objects.filter(encounter=self,
                                                               coverage__type=Coverage.COVERAGE_TYPE.COVERAGE)
        patient_coverages = (PatientCoverage.objects.filter(patient=self.patient)
                             .for_encounter_type(self.general_type)
                             .filter_active_coverages(created_date).for_division(self.division)
                             .order_by_priority())
        patient_coverages_list = patient_coverages.values_list('coverage')
        EncounterCoverage.objects.filter(encounter=self, coverage__type=Coverage.COVERAGE_TYPE.COVERAGE
                                         ).exclude(coverage__in=patient_coverages_list).delete()
        if len(patient_coverages) > 0:
            for patient_coverage in patient_coverages:
                ec = encounter_coverages.filter(coverage=patient_coverage.coverage).first()
                if ec:
                    ec.update_from_patient_coverage(patient_coverage)
                    ec.save()
                else:
                    EncounterCoverage.objects.create_from_patient_coverage(self, patient_coverage)
        else:
            EncounterCoverage.objects.create_unk_coverage(self)

        # clone PatientCoverage -> EncounterCoverage (type DISCOUNTS)
        encounter_coverage_discounts = EncounterCoverage.objects.filter(encounter=self, coverage__type__in=[
            Coverage.COVERAGE_TYPE.DISCOUNT_CARD,
            Coverage.COVERAGE_TYPE.DISCOUNT_POLICY])

        discount_coverages = (PatientCoverage.objects.filter(patient=self.patient)
                              .filter_active_discounts(created_date))
        discount_coverages_list = discount_coverages.values_list('coverage')
        for discount in discount_coverages:
            ec = encounter_coverage_discounts.filter(coverage=discount.coverage).first()
            if ec:
                ec.update_from_patient_coverage(discount)
                ec.save()
            else:
                EncounterCoverage.objects.create_from_patient_coverage(self, discount)

        EncounterCoverage.objects.filter(encounter=self, coverage__type__in=[
            Coverage.COVERAGE_TYPE.DISCOUNT_CARD,
            Coverage.COVERAGE_TYPE.DISCOUNT_POLICY]).exclude(coverage__in=discount_coverages_list).delete()

        # clone PatientCoverage -> EncounterCoverage (type PACKAGE)
        encounter_coverage_packages = EncounterCoverage.objects.filter(encounter=self,
                                                                       coverage__type=Coverage.COVERAGE_TYPE.PACKAGE)
        package_coverages = PatientCoverage.objects.filter(patient=self.patient).filter_active_packages()
        package_coverages_list = package_coverages.values_list('coverage')
        for package in package_coverages:
            ec = encounter_coverage_packages.filter(coverage=package.coverage).first()
            if ec:
                ec.update_from_patient_coverage(package)
                ec.save()
            else:
                EncounterCoverage.objects.create_from_patient_coverage(self, package)

        if package_coverages:
            EncounterCoverage.objects.get_unk_encounter_coverages(self).delete()

        EncounterCoverage.objects.filter(encounter=self, coverage__type=Coverage.COVERAGE_TYPE.PACKAGE).exclude(
            coverage__in=package_coverages_list).delete()

        do_service('BIL:recalculate_for_encounter', self)

    @transaction.atomic
    def create_or_update_hospital_fee(self):
        if self.tracker.has_changed('division') and self.type in Encounter.OPD_TYPES:
            self.create_hospital_fee(self.division)

    @transaction.atomic
    def bill_hospital_fee(self, code, division):
        hospital_fee = Product.objects.filter(code=code).first()
        if hospital_fee:
            hospital_fee_order = MiscellaneousOrder.objects.create(
                product=hospital_fee,
                quantity=1,
                encounter=self,
                requesting_division=division,
                performing_division=division,
                perform_datetime=datetime.now(),
                active=True
            )
            do_service('BIL:bill', [hospital_fee_order])
            self.hospital_fee_charged = True
        else:
            self.hospital_fee_charged = False
        self.save_for_test()

    def check_hospital_fee(self):
        hospital_fee = HospitalFee.objects.filter(patient=self.patient).filter_active().first()
        if hospital_fee and hospital_fee.encounters.exclude_finish().exists() is False:
            hospital_fee.status = HospitalFee.STATUS.CLOSED
            hospital_fee.save()

    def update_hospital_fee(self):
        if self.type not in Encounter.OPD_TYPES:
            return
        # hospital_fee = HospitalFee.objects.filter(patient=self.patient, status=HospitalFee.STATUS.ACTIVE).first()
        hospital_fee = self.hospital_fee.first()
        if hospital_fee:
            if hospital_fee.encounters.exclude_finish().exists():
                hospital_fee.status = HospitalFee.STATUS.ACTIVE
            else:
                hospital_fee.status = HospitalFee.STATUS.CLOSED
            hospital_fee.save()
        else:
            hospital_fee = HospitalFee.objects.filter(patient=self.patient).filter_active().first()
            if hospital_fee is None:
                hospital_fee = HospitalFee.objects.create(
                    patient=self.patient
                )
            if not hospital_fee.encounters.filter(pk=self.pk):
                hospital_fee.encounters.add(self)

    def create_expensive_clinic_type(self, encounters, old_encounter, old_hospital_fee_orders):
        # create hospital fee by clinic_type priority (premium > special > regular)
        premium_encounter = encounters.filter(clinic_type=Encounter.CLINIC_TYPE_PREMIUM).exclude(division=None).first()
        special_encounter = encounters.filter(clinic_type=Encounter.CLINIC_TYPE_SPECIAL).exclude(division=None).first()
        regular_encounter = encounters.filter(clinic_type=Encounter.CLINIC_TYPE_REGULAR).exclude(division=None).first()
        target_encounter = None
        code_list = None
        if premium_encounter and premium_encounter.division:
            target_encounter = premium_encounter
            code_list = [config.core_HOSPITAL_FEE_PREMIUM, config.core_HOSPITAL_FEE_SPECIAL]
        elif special_encounter and special_encounter.division:
            target_encounter = special_encounter
            code_list = [config.core_HOSPITAL_FEE_SPECIAL]
        elif regular_encounter and regular_encounter.division:
            target_encounter = regular_encounter
            code_list = [config.core_HOSPITAL_FEE_REGULAR]

        old_code_list = list(old_hospital_fee_orders.values_list('product__code', flat=True))
        # check is old hospital fee is same as expensive hospital fee
        if set(old_code_list) != set(code_list):
            # remove old hospital fee
            do_service('BIL:unbill', old_hospital_fee_orders)
            old_hospital_fee_orders.update(active=False)
            old_encounter.hospital_fee_charged = False
            old_encounter.save_for_test()
            if target_encounter.status == Encounter.STATUS.DISCHARGED:
                bill_encounter = encounters.exclude_finish().first()
            else:
                bill_encounter = target_encounter
            for code in code_list:
                bill_encounter.bill_hospital_fee(code, bill_encounter.division)

    @transaction.atomic
    def create_hospital_fee(self, division):
        """
        This method create hospital fee if no hospital fee charged in the last 24 hours

        If clinic type change, it unbill and rebill the correct hospital fee that match with clinic_type
        """
        if division is None or self.type not in Encounter.OPD_TYPES:
            return

        # bill hospital fee if patient first visit
        hospital_fee = self.hospital_fee.first() or HospitalFee.objects.filter(
            patient=self.patient).filter_active().first()
        if hospital_fee.is_closed:
            return

        encounter_has_fee_charge = hospital_fee.encounters.filter(
            hospital_fee_charged=True
        ).exclude(
            status=Encounter.STATUS.CANCELED).first()
        if encounter_has_fee_charge:
            HOSPITAL_FEE_LIST = MiscellaneousOrder.get_hospital_fee_list()
            hospital_fee_orders = MiscellaneousOrder.objects.filter(encounter=encounter_has_fee_charge,
                                                                    product__code__in=HOSPITAL_FEE_LIST, active=True)
            is_paid = all(do_service('BIL:is_paid', list(hospital_fee_orders)))
            if is_paid is False:
                # create hospital fee by clinic_type priority (premium > special > regular)
                unexpired_encounter = hospital_fee.encounters.exclude(status=Encounter.STATUS.CANCELED)
                self.create_expensive_clinic_type(unexpired_encounter, encounter_has_fee_charge, hospital_fee_orders)
        else:
            if self.clinic_type == Encounter.CLINIC_TYPE_REGULAR:
                code = config.core_HOSPITAL_FEE_REGULAR
            elif self.clinic_type == Encounter.CLINIC_TYPE_SPECIAL:
                code = config.core_HOSPITAL_FEE_SPECIAL
            elif self.clinic_type == Encounter.CLINIC_TYPE_PREMIUM:
                code = config.core_HOSPITAL_FEE_PREMIUM
                # premium clinic have 2 hospital fee charged include HOSPITAL_FEE_SPECIAL
                self.bill_hospital_fee(config.core_HOSPITAL_FEE_SPECIAL, division)
            self.bill_hospital_fee(code, division)

    def set_triage_if_exists(self):
        unexpired_encounter = Encounter.objects.filter_active_opd().filter(
            patient=self.patient
        ).exclude(
            triage=None
        ).last()

        if unexpired_encounter:
            triage = unexpired_encounter.triage
            self.triage = triage
            self.action = Encounter.ACTION.OPD_TRIAGE
            self.triage_level = triage.triage_level
            self.chief_complaints = triage.chief_complaint
            self.user = self.user or self.edit_user
            self.save()

    def update_patient_location(self, device):
        """
        Check action then update patient status
        :param device: Device of user in request
        :type device: Device
        :return:
        """
        if not device:
            logger.warning('No Device found. Skipping update patient location')
            return
        elif not device.location:
            logger.warning('No location found for Device %s. Skipping update patient location' %
                           device)
            return
        elif not isinstance(device.location, Location):
            logger.warning('device.location is not Location instance %s. Skipping update patient location' %
                           device.location)
            return

        # CHANGING_LOCATION_ACTION = [
        #     Encounter.ACTION.OPD_TRIAGE,
        #     Encounter.ACTION.OPD_NEW,
        #     Encounter.ACTION.OPD_ARRIVE,
        #     Encounter.ACTION.OPD_SCREEN,
        #     Encounter.ACTION.OPD_QUEUE_EXAM,
        #     Encounter.ACTION.OPD_CHECK_IN,
        #     Encounter.ACTION.OPD_SEND_LAB,
        #     Encounter.ACTION.OPD_SEND_TREATMENT
        # ]
        self.patient.update_location(device.location)
        self.notify_encounter_change()
        self.notify_current_division()

    def get_medical_record(self):
        # TODO : filter only doctor's medical record (exclude doctor's student)
        return self.emrs.filter(active=True).last()

    def doctor_orders(self):
        return DoctorOrder.objects.filter(progression_cycle=None, emr=None, encounter=self)

    def update_payment_status(self, user: User, notify=True):
        if self.status != Encounter.STATUS.WAIT_PAY:
            return
        if self.action == Encounter.ACTION.OTH_NEW:
            return
        if self.action == Encounter.ACTION.OPD_UNDISCHARGE:
            return
        if not do_service('BIL:has_payment', patient=self.patient):
            self.action = Encounter.ACTION.OPD_PAID
            self.user = user
            super().save()

        if notify:
            self.notify_encounter_change()

    def update_dispense_status(self, user: User, notify=True):
        if self.status != Encounter.STATUS.WAIT_DISPENSE:
            return
        if self.action == Encounter.ACTION.OTH_NEW:
            return

        orders = DoctorOrder.objects.filter(encounter=self).filter_wait_perform().exclude_admit_order()
        if not orders.exists():
            self.action = Encounter.ACTION.OPD_DISCHARGE
            self.user = user
            super().save()

        if notify:
            self.notify_encounter_change()

    def transfer_invoice_items_if_possible(self, user: User):
        if self.action == Encounter.ACTION.OPD_UNDISCHARGE:
            return
        ipd_encounter = do_service('ADM:get_ipd_encounter', self)
        if ipd_encounter and ipd_encounter.status == Encounter.STATUS.ADMISSION_ADMITED \
                and self.status in [Encounter.STATUS.WAIT_PAY, Encounter.STATUS.DISCHARGED]:
            do_service('BIL:transfer_to_ipd', ipd_encounter, user)

    def create_or_update_emr(self, old_doctor=None):
        """
        the emr will be created if the following requirements are met.
            1. There are not any active emrs in this encounter.
            2. This encounter has a doctor who is not a common doctor.
        the emr will be updated if the following requirements are met.
            1. There is an active emr in this encounter.
            2. This encounter has a doctor who is not a common doctor
            3. The doctor in this encounter has been changed
        """
        emr = self.get_medical_record()
        doctor_is_not_common = self.doctor and not self.doctor.common
        has_changed = old_doctor != self.doctor

        if not emr:
            if doctor_is_not_common:
                emr = MedicalRecord()
                emr.encounter = self
                emr.doctor = self.doctor
                emr.edit_user = self.edit_user
                emr.save()
        else:
            if has_changed and doctor_is_not_common:
                if self.status == Encounter.STATUS.IN_EXAM:
                    raise serializers.ValidationError({'doctor': [
                        'ไม่สามารถแก้ไขแพทย์ได้ เนื่องจาก Encounter อยู่ในสถานะ %s' % Encounter.STATUS.IN_EXAM.label]})

                emr.doctor = self.doctor
                emr.edit_user = self.edit_user
                emr.save()

                for progression_cycle in emr.progression_cycles.filter(checkout_time=None, active=True):
                    progression_cycle.creator = self.doctor
                    progression_cycle.edit_user = self.edit_user
                    progression_cycle.save()

            elif has_changed and not self.doctor:
                raise serializers.ValidationError({'doctor': [
                    'ไม่สามารถนำแพทย์ออกจาก Encounter ได้ เนื่องจากมี Medical Record']})

    @property
    def has_doctor_fee(self):
        if self.clinic_type == Encounter.CLINIC_TYPE_PREMIUM or self.clinic_type == Encounter.CLINIC_TYPE_SPECIAL:
            return True
        # elif self.clinic_type == Encounter.CLINIC_TYPE_REGULAR:
        #     # For demo only
        #     return True
        else:
            return False

    @property
    def is_expired(self):
        if self.type == self.TYPE_IPD:
            if self.status == Encounter.STATUS.FINISHED:
                yesterday = datetime.now() - timedelta(hours=config.core_IPD_ENCOUNTER_EXPIRE)
                return self.ended < yesterday
            return False
        yesterday = datetime.now() - timedelta(hours=config.core_OPD_ENCOUNTER_EXPIRE)
        return self.created < yesterday

    @property
    def is_doctor_key_discharge_form_expired(self):
        if self.type == self.TYPE_IPD:
            if self.status == Encounter.STATUS.FINISHED:
                yesterday = datetime.now() - timedelta(hours=config.core_DOCTOR_KEY_DISCHARGE_FORM_EXPIRE)
                return self.ended < yesterday
        return False

    @property
    def is_nurse_key_discharge_form_expired(self):
        if self.type == self.TYPE_IPD:
            if self.status == Encounter.STATUS.FINISHED:
                yesterday = datetime.now() - timedelta(hours=config.core_NURSE_KEY_DISCHARGE_FORM_EXPIRE)
                return self.ended < yesterday
        return False

    @property
    def is_active(self):
        return (not self.is_expired) and self.status not in [Encounter.STATUS.DISCHARGED]

    @property
    def status_name(self):
        if self.discharge_status:
            if self.status == self.STATUS.DISCHARGED and self.discharge_status.code == 'ADM':
                return 'จำหน่ายไปหอผู้ป่วยใน'
        return self.status.label

    @property
    def general_type(self):
        if self.type in [self.TYPE_OPD, self.TYPE_ER, self.TYPE_OTH, self.TYPE_SS]:
            return self.TYPE_OPD
        elif self.type in [self.TYPE_IPD]:
            return self.TYPE_IPD
        else:
            raise ValueError('invalid encounter_type: ' + self.type)

    def get_encounter_coverage(self) -> Optional['EncounterCoverage']:
        """Get EncounterCoverage for this encounter, excluding DISCOUNT Coverage"""
        return self.encountercoverage_set.filter(coverage__type=Coverage.COVERAGE_TYPE.COVERAGE
                                                 ).order_by('priority').first()

    def get_all_encounter_coverages(self):
        return self.encountercoverage_set.filter(
            coverage__type=Coverage.COVERAGE_TYPE.COVERAGE
        ).order_by('priority')

    def change_zone(self, zone, user):
        zone_log = self.latest_zone_log

        if zone_log:
            if not zone and not zone_log.check_in_time:  # Change zone to no zone
                zone_log.delete()
            elif zone and zone_log.zone.id == zone.id and not zone_log.check_out_time:  # Already inside zone
                return
            elif zone_log.check_in_time:  # Already check in to another zone
                zone_log.check_out(user)
                if zone:
                    ZoneLog.objects.create(encounter=self, zone=zone, create_user=user)
            else:  # Not check in to other zone yet
                zone_log.edit_zone(zone, user)
        elif zone:
            ZoneLog.objects.create(encounter=self, zone=zone, create_user=user)

    def check_in_to_zone(self, zone, user):
        self.change_zone(zone, user)

        zone_log = self.latest_zone_log
        zone_log.check_in(user)

    @transaction.atomic()
    def cancel(self, user, note, division):
        if not note:
            raise serializers.ValidationError(
                {'note': [_('กรุณาระบุสาเหตุที่ต้องการยกเลิก')]}
            )
        if self.division != division:
            raise serializers.ValidationError(
                {'division': [_('ไม่สามารถยกเลิกได้เนื่องจาก device มี division ไม่ตรงกับของ encounter')]}
            )
        if self.get_action(Encounter.ACTION.OPD_SCREEN):
            raise serializers.ValidationError(
                {'status': [_('ไม่สามารถยกเลิกได้เนื่องจากซักประวัติแล้ว')]}
            )
        if do_service('BIL:has_payment_except_hospital_fee', self):
            raise serializers.ValidationError(
                {'payment': [_('ไม่สามารถยกเลิกได้เนื่องจากมีค่าใช้จ่าย')]}
            )

        # cancel hospital fee or move it to another encounter
        if self.hospital_fee_charged:
            do_service('BIL:remove_hospital_fee_of_encounter', self)
            encounters = Encounter.objects.filter_unexpired_opd()
            encounters = encounters.filter(patient=self.patient)
            encounters = encounters.exclude(
                Q(id=self.id) | Q(status__in=[Encounter.STATUS.WAIT_DISPENSE, Encounter.STATUS.DISCHARGED])
            )
            encounter = encounters.first()
            if encounter:
                encounter.create_hospital_fee(encounter.division)

        self.refresh_from_db()
        self.action = Encounter.ACTION.OPD_CANCEL
        self.user = user
        self.action_log_kwargs = {'note': str(note)}
        self.save()

    @property
    def admitted(self):
        return self.get_action(Encounter.ACTION.ADMIT)

    @property
    def discharged(self):
        return self.get_action(Encounter.ACTION.IPD_DISCHARGE)

    def get_coverages(self):
        encounter_coverages = EncounterCoverage.objects.filter(encounter=self)
        return [enc.coverage for enc in encounter_coverages]

    @property
    def allow_discharge_weight_null(self):
        coverages = self.get_coverages()
        try:
            main_coverage_codes = json.loads(config.core_MAIN_COVERAGE_CODES)
            for coverage in coverages:
                if coverage.code in main_coverage_codes:
                    return False
        except Exception as e:
            logger.error(e)
            logger.error('error to parse config.core_MAIN_COVERAGE_CODES, allow_discharge_weight_null return False')
            return False
        return True

    def has_ggo_coverage(self):
        return EncounterCoverage.objects.filter(
            encounter=self, coverage__code=config.core_GGO_CODE
        ).exists()


class EncounterActionLog(BaseActionLog(Encounter)):
    note = models.TextField(blank=True, default='')


class HospitalFeeQuerySet(models.QuerySet):
    def filter_active(self):
        return self.filter(status=HospitalFee.STATUS.ACTIVE)


class HospitalFee(EditableModel):
    class STATUS(LabeledIntEnum):
        ACTIVE = 1
        CLOSED = 9

    status = EnumField(STATUS, default=STATUS.ACTIVE)
    patient = models.ForeignKey(Patient)
    encounters = models.ManyToManyField(Encounter, blank=True, related_name='hospital_fee')
    objects = HospitalFeeQuerySet.as_manager()

    @property
    def is_closed(self):
        return self.status == HospitalFee.STATUS.CLOSED


class EncounterCoverageManager(models.Manager):
    def create_from_patient_coverage(self, encounter: Encounter, patient_coverage: PatientCoverage):
        ec = EncounterCoverage(encounter=encounter)
        ec.update_from_patient_coverage(patient_coverage)
        ec.save()
        return ec

    def create_unk_coverage(self, encounter: Encounter):
        ec = EncounterCoverage(encounter=encounter)
        ec.set_as_unk_coverage()
        ec.save()
        return ec

    def get_unk_encounter_coverages(self, encounter):
        return EncounterCoverage.objects.filter(
            encounter=encounter,
            coverage=Coverage.objects.get_unk_coverage(),
            payer=None,
            project=None,
            assure_type=AssureType.objects.get_undefined(),
        )


class EncounterCoverage(CommonCoverage):
    encounter = models.ForeignKey(Encounter)
    patient_coverage = models.ForeignKey(PatientCoverage, null=True, blank=True,
                                         help_text='reference PatientCoverage that create this EncounterCoverage.')
    objects = EncounterCoverageManager()

    class Meta:
        unique_together = ('encounter', 'coverage')

    def __str__(self):
        return '%s:%s' % (self.id, self.coverage)

    def update_from_patient_coverage(self, patient_coverage: PatientCoverage):
        self.coverage = patient_coverage.coverage
        self.payer = patient_coverage.payer
        self.project = patient_coverage.project
        self.assure_type = patient_coverage.assure_type
        self.start_date = patient_coverage.start_date
        self.stop_date = patient_coverage.stop_date
        self.referer = patient_coverage.referer
        self.refer_date = patient_coverage.refer_date
        self.refer_no = patient_coverage.refer_no
        self.priority = patient_coverage.priority
        self.patient_coverage = patient_coverage

    def set_as_unk_coverage(self):
        self.coverage = Coverage.objects.get_unk_coverage()
        self.payer = None
        self.project = None
        self.assure_type = AssureType.objects.get_undefined()
        self.start_date = timezone.now()


class MedicalRecordQuerySet(models.QuerySet):
    def filter_checkout(self):
        return self.exclude(checkout_time=None)


class MedicalRecord(EditableModel):
    """Main table for OPD EMR
    It contains clinical data of patient on each encounter.
    The diagnosis, treatment operation, and orders will refer back to this table.
    """

    class CHECKOUT_CAUSE(LabeledIntEnum):
        BY_APPROVAL = 1, 'By approval'  # AP
        ADMIT = 2, 'Admit'  # AD
        ER = 3, 'ER'  # ER
        REFER_OUT = 4, 'Refer Out'  # RO
        REJECT = 5, 'Reject'  # RJ
        DEAD = 6, 'Dead'  # DD
        DISAPPEAR = 7, 'Disappear'
        WAIT_RESULT = 8, 'Wait Result'

    DRG_CHECKOUT_CAUSE_MAP = {
        CHECKOUT_CAUSE.BY_APPROVAL: 'APPROVAL',
        CHECKOUT_CAUSE.REJECT: 'AGAINST_ADVICE',
        CHECKOUT_CAUSE.DISAPPEAR: 'ESCAPE',
        CHECKOUT_CAUSE.REFER_OUT: 'TRANSFER',
        CHECKOUT_CAUSE.DEAD: 'DEAD',
        CHECKOUT_CAUSE.ADMIT: 'OTHER',
        CHECKOUT_CAUSE.ER: 'OTHER',
    }

    encounter = models.ForeignKey(Encounter, related_name='emrs')
    doctor = models.ForeignKey(Doctor, verbose_name='แพทย์ผู้ตรวจ')
    active = models.BooleanField(default=True)
    checkout_time = models.DateTimeField(null=True, blank=True)
    checkout_cause = EnumField(CHECKOUT_CAUSE, verbose_name='สาเหตุการสิ้นสุดการรักษา', null=True, blank=True)
    objects = MedicalRecordQuerySet.as_manager()

    class Meta:
        verbose_name = 'เวชระเบียนทางการแพทย์ของผู้ป่วย'

    def __str__(self):
        return "[EMR %s] %s" % (self.id, self.encounter)

    def checkout(self, user: User, checkout_cause: CHECKOUT_CAUSE, ipd=False):
        # Allow multiple checkout in case nurse re-send the patient back into the queue
        # assert not self.is_checkout, 'already checkout.'
        self.edit_user = user
        self.checkout_cause = checkout_cause
        self.checkout_time = datetime.now()
        self.save()

        if not ipd:
            ProgressionCycle.objects.filter(emr=self, checkout_time=None).update(checkout_time=datetime.now(),
                                                                                 edit_user=user)
        DoctorOrder.objects.filter(emr=self).checkout(user, ipd)

    @property
    def is_checkout(self):
        return bool(self.checkout_time)

    def doctor_orders(self):
        return DoctorOrder.objects.filter(progression_cycle=None, emr=self)

    def principal_diagnosis(self) -> Union[None, "his.core.models.Diagnosis"]:
        if not hasattr(self, 'core_diagnosis'):
            return None
        queryset = self.core_diagnosis.filter(type=Diagnosis.TYPE.PRIMARY)
        queryset = queryset.filter(active=True)
        queryset = queryset.exclude(source=Diagnosis.SOURCE.ORM)
        return queryset

    def secondary_diagnosis(self):
        if not hasattr(self, 'core_diagnosis'):
            return []
        queryset = self.core_diagnosis.filter(type__in=Diagnosis.SECONDARY_TYPE)
        queryset = queryset.filter(active=True)
        queryset = queryset.exclude(source=Diagnosis.SOURCE.ORM)
        return queryset

    def principal_procedure(self) -> Union[None, "his.core.models.Procedure"]:
        if not hasattr(self, 'core_procedure'):
            return None
        queryset = self.core_procedure.filter(type=Procedure.TYPE.PRIMARY)
        queryset = queryset.filter(active=True)
        return queryset

    def secondary_procedure(self):
        if not hasattr(self, 'core_procedure'):
            return []
        queryset = self.core_procedure.filter(type=Procedure.TYPE.SECONDARY)
        queryset = queryset.filter(active=True)
        return queryset

    def provisional_diagnosis(self) -> Union[None, "his.core.models.Diagnosis"]:
        if not hasattr(self, 'core_diagnosis'):
            return None
        queryset = self.core_diagnosis.filter(type=Diagnosis.TYPE.PROVISIONAL_PRIMARY)
        queryset = queryset.filter(active=True)
        return queryset

    def provisional_secon_diagnosis(self):
        if not hasattr(self, 'core_diagnosis'):
            return []
        queryset = self.core_diagnosis.filter(type__in=Diagnosis.PROVISIONAL_SECONDARY_TYPE)
        queryset = queryset.filter(active=True)
        return queryset

    def external_cause_diagnosis(self) -> Union[None, "his.core.models.Diagnosis"]:
        if not hasattr(self, 'core_diagnosis'):
            return None
        queryset = self.core_diagnosis.filter(type=Diagnosis.TYPE.EXTERNAL_CAUSE)
        queryset = queryset.exclude(source=Diagnosis.SOURCE.ORM)
        queryset = queryset.filter(active=True)
        return queryset

    def get_encounter_type(self):
        return self.encounter.type

    @property
    def get_diagnosis_summary(self):
        result = ''
        if self:
            for index, diagnosis in enumerate(
                list(self.principal_diagnosis()) + list(self.secondary_diagnosis()) or []
            ):
                if diagnosis.icd10:
                    result += '%s. %s-%s (%s)  ' % (
                        index + 1, diagnosis.icd10.code, diagnosis.icd10.term, diagnosis.medical_description)
                else:
                    result += '%s. %s  ' % (index + 1, diagnosis.medical_description)
        return result

    def is_doctor_examined(self):
        return (self.physicalexamination_set.exists() or
                self.physicalexaminationother_set.exists() or
                self.patientillness_set.exists() or
                self.core_diagnosis.exists())

    def clone_diagnosis(self, prototype_emr):
        for diagnosis in prototype_emr.principal_diagnosis() | prototype_emr.secondary_diagnosis():
            diagnosis.id = None
            diagnosis.emr = self
            diagnosis.save()


class ProgressionCycleQuerySet(models.QuerySet):
    def filter_checkout(self):
        return self.exclude(checkout_time=None)


class ProgressionCycle(EditableModel):
    """Progression cycle of patient meeting with doctor in each encounter
    Progression cycle consist of orders from PRX, LAB, etc. and progression note.
    This table only store the progression_note and other orders will refer to this table
    There can be multiple instance of ProgressionCycle in one encounter.
    Please sort this cycle with "created" field.
    """
    creator = models.ForeignKey(Doctor, help_text='Ordered doctor')
    emr = models.ForeignKey(MedicalRecord, related_name='progression_cycles')
    progression_note = models.TextField(blank=True)
    checkout_time = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    objects = ProgressionCycleQuerySet.as_manager()

    def checkout(self, user: User):
        if self.is_checkout:
            # Already checkout
            raise ValidationError('Already checked out')

        self.edit_user = user
        self.checkout_time = datetime.now()
        self.save()

        DoctorOrder.objects.filter(progression_cycle=self).checkout(user)

    @property
    def is_checkout(self):
        return self.checkout_time

    @property
    def is_rejected(self):
        for order in self.doctor_orders():
            if order.specific.is_rejected():
                return True
        return False

    def doctor_orders(self):
        return DoctorOrder.objects.filter(progression_cycle=self)

    def __str__(self):
        return 'Progression Cycle: ' + str(self.emr)


class ScannedDocument(EditableModel):
    document_type = models.ForeignKey(DocumentType, verbose_name='ประเภทเอกสาร')
    document_no = models.CharField(max_length=50, blank=True, verbose_name='')
    document_code = models.CharField(max_length=50, blank=True, verbose_name='รหัสเอกสาร')
    document_image = models.ImageField(upload_to="patient/scanned_document/", verbose_name='ภาพสแกนเอกสาร')
    scan_user = models.ForeignKey(User, related_name='+', null=True, verbose_name='ผู้สแกนเอกสาร')
    scan_division = models.ForeignKey(Division, related_name='+', null=True, verbose_name='แผนกที่สแกนเอกสาร')
    owner_division = models.ForeignKey(Division, related_name='+', null=True, verbose_name='แผนกเจ้าของเอกสาร')
    page = models.IntegerField(default=1, verbose_name='เลขหน้าเอกสาร')
    version = models.IntegerField(default=1, verbose_name='version เอกสาร')

    scan_date = models.DateTimeField(verbose_name='วันที่สแกนเอกสาร', auto_now_add=True)
    document_date = models.DateField(verbose_name='วันที่ของเอกสาร', default=date.today)
    expiry_date = models.DateField(verbose_name='วันหมดอายุ', null=True)

    patient = models.ForeignKey(Patient)
    encounter = models.ForeignKey(Encounter, null=True, blank=True)
    is_secret = models.BooleanField(default=False, verbose_name='เอกสารปกปิด')
    active = models.BooleanField(default=True)
    remark = models.TextField(blank=True)
    cancel_note = models.TextField(blank=True, verbose_name='หมายเหตุการยกเลิก')

    class Meta:
        permissions = (
            ('can_edit_scanned_document', 'Can edit ScannedDocument'),
            ('can_cancel_scanned_document', 'Can cancel ScannedDocument'),
        )
        verbose_name = 'ภาพสแกนเอกสารผู้ป่วย'


class PrintLogQuerySet(models.QuerySet):
    def filter_ref_model(self, ref_model):
        content_type = ContentType.objects.get_for_model(ref_model)
        return self.filter(content_type=content_type, object_id=ref_model.pk)

    def is_printed(self, ref_model):
        return self.filter_ref_model(ref_model).exists()


class PrintLog(models.Model):
    user = models.ForeignKey(User, verbose_name='ผู้สั่งพิมพ์')
    created = models.DateTimeField(auto_now_add=True, verbose_name='วันเวลาที่พิมพ์')
    division = models.ForeignKey(Division, verbose_name='แผนกที่สั่งพิมพ์')
    report_name = models.CharField(max_length=255, verbose_name='เอกสารที่สั่งพิมพ์')
    hn = models.CharField(max_length=10, blank=True, default='', verbose_name="หมายเลข HN")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    ref_model = GenericForeignKey('content_type', 'object_id')

    objects = PrintLogQuerySet.as_manager()

    @property
    def original(self):
        """This return true if document was printed for the first time
        if no ref_model provided, it will also return True"""
        if self.object_id:
            original = PrintLog.objects.filter_ref_model(self.ref_model).order_by('created').first()
            return original.pk == self.pk
        return True

    class Meta:
        verbose_name = 'ประวัติการพิมพ์เอกสาร'


class FormPrintingCountManager(models.Manager):
    def get_count(self, form_name, key) -> int:
        try:
            return self.get(form_name=form_name, key=key).count
        except FormPrintingCount.DoesNotExist:
            return 0

    def get_for_print(self, form_name, key) -> int:
        """will increase the count for each call and return the value"""
        printing_count, _ = self.get_or_create(form_name=form_name, key=key)
        return printing_count.increase()


class FormPrintingCount(models.Model):
    form_name = models.CharField(max_length=255, verbose_name='ชื่อไฟล์ jasper')
    key = models.CharField(max_length=255, help_text='สิ่งที่ใช้ระบุเอกสารนั้นๆ เช่น pk, วันที่')
    count = models.PositiveIntegerField(default=0, verbose_name='จำนวนครั้งที่พิมพ์')

    objects = FormPrintingCountManager()

    class Meta:
        unique_together = ('form_name', 'key')

    def __str__(self):
        return '{s.form_name}/{s.key}'.format(s=self)

    def increase(self):
        self.count = F('count') + 1
        self.save()
        self.refresh_from_db()
        return self.count


class WelfareCategory(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return '{code}: {name}'.format(
            code=self.code,
            name=self.name,
        )


class CitizenWelfareQuerySet(models.QuerySet):
    def get_coverage_for_patient(self, patient):
        citizen_welfare = self.filter(citizen_no=patient.patientdetail.citizen_no).first()
        if citizen_welfare:
            return citizen_welfare.coverage
        else:
            return None


class CitizenWelfare(models.Model):
    class STATUS(LabeledIntEnum):
        ACTIVE = 1
        TERMINATED = 2

    citizen_no = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(WelfareCategory)
    coverage = models.ForeignKey(Coverage, null=True)

    employee_no = models.CharField(max_length=100, blank=True)
    employee_type = models.CharField(max_length=100, blank=True)
    year_of_work = models.CharField(max_length=100, blank=True)
    record_date = models.DateTimeField()
    record_by = models.CharField(max_length=100, blank=True)
    status = EnumField(STATUS)
    objects = CitizenWelfareQuerySet.as_manager()
    tracker = FieldTracker(fields=['coverage', 'status'])

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        patient = Patient.objects.filter(patientdetail__citizen_no=self.citizen_no).first()
        changed = self.tracker.changed()
        if patient:
            if 'coverage' in changed:
                if self.tracker.previous('coverage') is not None:
                    PatientCoverage.objects.deactivate_coverage(patient, self.tracker.previous('coverage'))

                if self.coverage and (self.status == self.STATUS.ACTIVE):
                    PatientCoverage.objects.activate_coverage_both_type(patient=patient, coverage=self.coverage)

            if ('status' in changed) and (self.status == self.STATUS.ACTIVE):
                PatientCoverage.objects.activate_coverage_both_type(patient=patient, coverage=self.coverage)
            elif ('status' in changed) and (self.status == self.STATUS.TERMINATED):
                PatientCoverage.objects.deactivate_coverage(patient, self.coverage)

        super().save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        patient = Patient.objects.filter(patientdetail__citizen_no=self.citizen_no).first()
        if patient and self.coverage:
            PatientCoverage.objects.deactivate_coverage(patient, self.coverage)
        return super().delete(using, keep_parents)


# ======================================================================= DOCTOR ORDER =================================

class DoctorOrderQuerySet(models.QuerySet):
    def exclude_admit_order(self):
        return self.exclude(
            specific_type__model='admitorder'
        )

    def filter_unacknowledged_by_encounter(self, encounter: Encounter):
        return self.filter(encounter=encounter,
                           order_ack_by=None,
                           order_ack_time=None,
                           order_ack_div=None,
                           specific_type__model__in=DoctorOrder.ORDER_SUMMARY_MODEL) \
            .exclude(order_status=DoctorOrder.ORDER_STATUS.CANCEL)

    def filter_wait_pay(self):
        return self.filter(
            order_payment_status__in=[
                DoctorOrder.PAYMENT_STATUS.PENDING,
                DoctorOrder.PAYMENT_STATUS.READY,
            ],
            order_status__in=[
                DoctorOrder.ORDER_STATUS.DRAFT,
                DoctorOrder.ORDER_STATUS.PENDING,
                DoctorOrder.ORDER_STATUS.PERFORMED,
            ]
        )

    def filter_wait_perform(self):
        return self.filter(
            order_status__in=[
                DoctorOrder.ORDER_STATUS.DRAFT,
                DoctorOrder.ORDER_STATUS.PENDING,
            ]
        )

    def filter_payment_not_ready(self):
        return self.filter(
            order_payment_status__in=[
                DoctorOrder.PAYMENT_STATUS.PENDING,
            ],
            order_status__in=[
                DoctorOrder.ORDER_STATUS.DRAFT,
                DoctorOrder.ORDER_STATUS.PENDING,
                DoctorOrder.ORDER_STATUS.PERFORMED,
            ]
        )

    def checkout(self, user, ipd=False):
        if ipd:
            orders = self.all()
        else:
            orders = self.filter(order_status=DoctorOrder.ORDER_STATUS.DRAFT)

        messages_data = list(
            orders.values(
                'order_perform_div__code',
                'specific_type__model',
                'encounter__patient__pk'
            ).distinct()
        )

        with transaction.atomic():
            for order in orders:
                order.specific and order.specific.do_checkout(user)
            if not ipd:
                orders.update(order_status=DoctorOrder.ORDER_STATUS.PENDING)

        for data in messages_data:
            if not all([
                data['order_perform_div__code'],
                data['specific_type__model'],
                data['encounter__patient__pk']
            ]):
                continue

            Messenger.push_to_location(data['order_perform_div__code'],
                                       source='core',
                                       event='update_doctor_order',
                                       type=data['specific_type__model'],
                                       patient_id=data['encounter__patient__pk'])

    def get_active_order_by_encounter(self, encounter: Encounter):
        inactive_admit_status = do_service('ADM:inactive_admit_status', default=[])
        inactive_centrallab_status = do_service('LAB:inactive_central_lab_status', default=[])
        inactive_cytopathology_status = do_service('PTH:inactive_cyto_status', default=[])
        inactive_dr_consult_status = do_service('DPO:inactive_dr_consult_status', default=[])
        inactive_dr_note_status = do_service('DPO:inactive_dr_note_status', default=[])
        inactive_drug_status = do_service('TPD:inactive_drug_status', default=[])
        inactive_frozen_section_status = do_service('PTH:inactive_frozen_status', default=[])
        inactive_imaging_status = do_service('IME:inactive_imaging_status', default=[])
        inactive_operating_status = do_service('ORM:inactive_operating_status', default=[])
        inactive_parenteral_nutrition_status = do_service('TPD:inactive_parenteral_nutrition_status', default=[])
        inactive_supply_status = do_service('MSD:inactive_supply_status', default=[])
        inactive_surgical_pathology_status = do_service('PTH:inactive_patho_status', default=[])
        inactive_treatment_status = do_service('TRT:inactive_treatment_status', default=[])
        return DoctorOrder.objects \
            .filter(Q(encounter=encounter) |
                    Q(doctorconsultorder__order_encounter=encounter) |
                    Q(admitorder__encounter_opd=encounter)) \
            .exclude(Q(order_status=DoctorOrder.ORDER_STATUS.CANCEL)) \
            .exclude(Q(admitorder__status__in=inactive_admit_status) |
                     Q(centrallaborder__status__in=inactive_centrallab_status) |
                     Q(cytopathologyorder__status__in=inactive_cytopathology_status) |
                     Q(doctorconsultorder__status__in=inactive_dr_consult_status) |
                     Q(doctornoteorder__status__in=inactive_dr_note_status) |
                     Q(drugorder__status__in=inactive_drug_status) |
                     Q(frozensectionorder__status__in=inactive_frozen_section_status) |
                     Q(imagingorder__status__in=inactive_imaging_status) |
                     Q(operatingorder__status__in=inactive_operating_status) |
                     Q(parenteralnutritionorder__status__in=inactive_parenteral_nutrition_status) |
                     Q(supplyorder__status__in=inactive_supply_status) |
                     Q(surgicalpathologyorder__status__in=inactive_surgical_pathology_status) |
                     Q(treatmentorder__status__in=inactive_treatment_status))


class DoctorOrder(models.Model):
    """ A model which collected all doctor order in system. To create new Order,
    please extend BaseDoctorOrder to get a property of statable and abstractmethod.
    """

    class ORDER_STATUS(LabeledIntEnum):
        APPOINTMENT = 1, 'เป็นคำสั่งล่วงหน้า'
        PENDING = 2, 'กำลังทำคำสั่ง'
        PERFORMED = 3, 'ทำคำสั่งเรียบร้อยแล้ว'
        CANCEL = 4, 'คำสั่งถูกยกเลิก'
        DRAFT = 5, 'คำสั่ง DRAFT'
        PLANNING = 6, 'คำสั่งแบบต่อเนื่อง'
        OFF = 7, 'หยุดทำคำสั่งแบบต่อเนื่อง'

    class ORDER_TYPE(LabeledIntEnum):
        DIRECT = 1, 'คำสั่งจากแพทย์โดยตรง'
        VERBAL = 2, 'คำสั่งโดยวาจา'
        TELEPHONE = 3, 'คำสั่งทางโทรศัพท์'

    class PAYMENT_STATUS(LabeledIntEnum):
        PENDING = 1, 'รอดำเนินการ'
        READY = 2, 'พร้อมชำระเงิน'
        PAID = 3, 'ชำระเงินแล้ว'

    # CardOrderSummary ในตอนนี้ support เท่านี้ก่อน
    ORDER_SUMMARY_MODEL = ['drugstatorder',
                           'drugonedoseorder',
                           'drugonedayorder',
                           'drugresuscitationorder',
                           'drugipdhomeorder',
                           'doctornoteorder',
                           'centrallaborder',
                           'treatmentorder',
                           'parenteralnutritionorder',
                           'operatingorder']

    ADMIT_ORDER = 'ADMIT_ORDER'
    DRUG_ORDER = 'DRUG_ORDER'
    DRUG_ORDER_HOME_OPD = 'DRUG_ORDER_HOME_OPD'
    DRUG_ORDER_SELLING = 'DRUG_ORDER_SELLING'
    DRUG_ORDER_STAT = 'DRUG_ORDER_STAT'
    DRUG_ORDER_STAT__OPD = 'DRUG_ORDER_STAT__OPD'
    DRUG_ORDER_STAT__IPD = 'DRUG_ORDER_STAT__IPD'
    DRUG_ORDER_ONE_DOSE = 'DRUG_ORDER_ONE_DOSE'
    DRUG_ORDER_ONE_DOSE__OPD = 'DRUG_ORDER_ONE_DOSE__OPD'
    DRUG_ORDER_ONE_DOSE__IPD = 'DRUG_ORDER_ONE_DOSE__IPD'
    DRUG_ORDER_HOME_IPD = 'DRUG_ORDER_HOME_IPD'
    DRUG_ORDER_CONTINUE_PLAN = 'DRUG_ORDER_CONTINUE_PLAN'
    DRUG_ORDER_ONE_DAY = 'DRUG_ORDER_ONE_DAY'
    LAB_ORDER = 'LAB_ORDER'
    TREATMENT_ORDER = 'TREATMENT_ORDER'
    OR_ORDER = 'OR_ORDER'

    DRUG_ORDER_OPD_LIST = [
        (DRUG_ORDER_HOME_OPD, 'OPD HOME รายการสั่งยากลับบ้านผู้ป่วยนอก'),
        # (DRUG_ORDER_SELLING, 'SELLING รายการขายยาผู้ป่วยนอกตามใบสั่งแพทย์'),
        (DRUG_ORDER_STAT__OPD, 'STAT รายการสั่งยาเร่งด่วนผู้ป่วยนอก'),
        (DRUG_ORDER_ONE_DOSE__OPD, 'ONE DOSE รายการสั่งยาใช้ในโรงพยาบาลผู้ป่วยนอก')
    ]
    DRUG_ORDER_IPD_LIST = [
        (DRUG_ORDER_HOME_IPD, 'IPD HOME รายการสั่งยากลับบ้านผู้ป่วยใน'),
        # (DRUG_ORDER_CONTINUE_PLAN, 'แผนการจ่ายยาต่อเนื่องสำหรับผู้ป่วยใน'),
        (DRUG_ORDER_ONE_DAY, 'ONE DAY รายการสั่งยาใช้ภายในวันผู้ป่วยใน'),
        (DRUG_ORDER_STAT__IPD, 'STAT รายการสั่งยาเร่งด่วนผู้ป่วยใน'),
        (DRUG_ORDER_ONE_DOSE__IPD, 'ONE DOSE รายการสั่งยาใช้ในโรงพยาบาลผู้ป่วยใน')
    ]

    SPECIFIC_TYPE_MAPPING = {
        ADMIT_ORDER: {
            'type_label': 'Admit',
            'app_label': 'ADM',
            'model': 'admitorder'
        },
        DRUG_ORDER: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugorder'
        },
        DRUG_ORDER_HOME_OPD: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugopdhomeorder'
        },
        DRUG_ORDER_SELLING: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugsellingorder'
        },
        DRUG_ORDER_STAT: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugstatorder'
        },
        DRUG_ORDER_ONE_DOSE: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugonedoseorder'
        },
        DRUG_ORDER_HOME_IPD: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugipdhomeorder'
        },
        DRUG_ORDER_CONTINUE_PLAN: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugcontinueplan'
        },
        DRUG_ORDER_ONE_DAY: {
            'type_label': 'ยา',
            'app_label': 'TPD',
            'model': 'drugonedayorder'
        },
        LAB_ORDER: {
            'type_label': 'Lab',
            'app_label': 'LAB',
            'model': 'centrallaborder'
        },
        TREATMENT_ORDER: {
            'type_label': 'Treatment',
            'app_label': 'TRT',
            'model': 'treatmentorder'
        },
        OR_ORDER: {
            'type_label': 'ผ่าตัด',
            'app_label': 'ORM',
            'model': 'operatingorder'
        }
    }

    ORDER_MODEL_TYPE_MAPPING = {
        'admitorder': ADMIT_ORDER,
        'drugopdhomeorder': DRUG_ORDER_HOME_OPD,
        'drugsellingorder': DRUG_ORDER_SELLING,
        'drugstatorder': DRUG_ORDER_STAT,
        'drugonedoseorder': DRUG_ORDER_ONE_DOSE,
        'drugipdhomeorder': DRUG_ORDER_HOME_IPD,
        'drugcontinueplan': DRUG_ORDER_CONTINUE_PLAN,
        'drugonedayorder': DRUG_ORDER_ONE_DAY,
        'centrallaborder': LAB_ORDER,
        'treatmentorder': TREATMENT_ORDER,
        'operatingorder': OR_ORDER,
    }

    NURSE_ACKNOWLEDGE = 'รับทราบแล้ว'
    NURSE_CANCEL = 'ยกเลิก'
    NURSE_WAIT = 'รอรับคำสั่ง'

    specific_type = models.ForeignKey(ContentType, editable=False, null=True, help_text='specific type of order')
    specific = GenericForeignKey('specific_type', 'id')

    edited_doctor = models.ForeignKey(Doctor, blank=True, null=True, verbose_name='แพทย์ผู้แก้ไข', related_name='+')
    doctor_edit_time = models.DateTimeField(null=True, blank=True, verbose_name='วันเวลาที่แพทย์แก้ไข')

    order_status = EnumField(ORDER_STATUS, default=ORDER_STATUS.DRAFT, verbose_name='สถานะของคำสั่ง')
    order_payment_status = EnumField(PAYMENT_STATUS, default=PAYMENT_STATUS.PENDING, verbose_name='สถานะการชำระเงิน')
    order_type = EnumField(ORDER_TYPE, default=ORDER_TYPE.DIRECT, verbose_name='ชนิดคำสั่ง')
    order_by = models.ForeignKey(Doctor, verbose_name='แพทย์ผู้สั่ง')
    order_div = models.ForeignKey(Division, related_name='+', verbose_name='แผนกที่สั่ง')
    order_time = models.DateTimeField(auto_now_add=True, verbose_name='วันเวลาที่สั่ง')
    # order_receive_by and order_receive_time and order_approve_time are used only when order by phone or verbal.
    order_receive_by = models.ForeignKey(User, related_name='+', null=True, blank=True, verbose_name="ผู้รับคำสั่งแทน")
    order_receive_time = models.DateTimeField(null=True, blank=True, verbose_name='วันเวลาที่รับคำสั่งแทน')
    order_approve_time = models.DateTimeField(null=True, blank=True, verbose_name='วันเวลาที่ยืนยันคำสั่งแทน')
    # order_perform_div and order_perform_by and order_perform_time are used only when order is performed
    order_perform_div = models.ForeignKey(Division, related_name='+', verbose_name='แผนกที่ทำ', null=True, blank=True)
    order_perform_by = models.ForeignKey(User, related_name='+', null=True, blank=True, verbose_name="ผู้ปฏิบัติคำสั่ง")
    order_perform_time = models.DateTimeField(verbose_name='เวลาเริ่มทำ', null=True, blank=True)
    # order_ack_div and order_ack_by and order_ack_time are used only when order is acknowledged
    order_ack_by = models.ForeignKey(User, related_name='+', null=True, blank=True, verbose_name="ผู้รับทราบคำสั่ง")
    order_ack_time = models.DateTimeField(verbose_name='เวลารับทราบคำสั่ง', null=True, blank=True)
    order_ack_div = models.ForeignKey(Division, related_name='+', verbose_name='แผนกที่รับทราบคำสั่ง', null=True,
                                      blank=True)

    is_advance = models.BooleanField(default=False, verbose_name='คำสั่งล่วงหน้า')

    # Associated progression_cycle or encounter. If this order is appointment order,
    # the encounter will be encounter which patient coming to hospital for doing as ordered.
    progression_cycle = models.ForeignKey(ProgressionCycle, null=True, blank=True)
    emr = models.ForeignKey(MedicalRecord, null=True, blank=True)
    encounter = models.ForeignKey(Encounter)

    objects = DoctorOrderQuerySet.as_manager()
    tracker = FieldTracker(fields=['order_perform_time'])
    post_perform = Signal(providing_args=['instance'])
    post_unperform = Signal(providing_args=['instance'])

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        newly_create = not self.pk
        if self.progression_cycle:
            self.emr = self.progression_cycle.emr
        if self.emr:
            self.encounter = self.emr.encounter
        if self.__class__ is not DoctorOrder:
            self.specific_type = ContentType.objects.get_for_model(self, for_concrete_model=False)
        super().save(force_insert=False, force_update=False, using=None, update_fields=None)
        changed = self.tracker.changed()
        if 'order_perform_time' in changed:
            old_order_perform_time = self.tracker.previous('order_perform_time')
            if old_order_perform_time is None and self.order_perform_time:
                self.post_perform.send(sender=DoctorOrder, instance=self)
            if old_order_perform_time and self.order_perform_time is None:
                self.post_unperform.send(sender=DoctorOrder, instance=self)

        if self.order_perform_div and self.specific_type:
            Messenger.push_to_location(self.order_perform_div.code,
                                       source='core',
                                       event='update_doctor_order',
                                       type=self.specific_type.model,
                                       patient_id=self.encounter.patient.pk)

        if newly_create and self.encounter.type in Encounter.ADMIT_TYPES:
            unacknowledged = self.order_ack_by is None
            unacknowledged = unacknowledged and self.order_ack_time is None
            unacknowledged = unacknowledged and self.order_ack_div is None
            if unacknowledged:
                Messenger.push_to_encounter(self.encounter,
                                            source='core',
                                            event='update_ward_queue',
                                            encounter_id=self.encounter.id)

    @property
    def document_no(self):
        return config.core_PREFIX_DOCTOR_ORDER + str(self.id)

    @property
    def obs_id(self):
        return self.id

    @property
    def active_prototype_order_binder(self):
        return self.prototype_order_binders.filter(active=True).first()

    def get_type_display(self):
        Appointment = apps.get_model('APP.Appointment')
        if self.specific_type.model == Appointment.APPOINTMENT_TYPE_DOCTOR:
            return 'พบแพทย์'
        elif self.specific_type.model == Appointment.APPOINTMENT_TYPE_TREATMENT:
            return 'หัตถการ'
        elif self.specific_type.model == Appointment.APPOINTMENT_TYPE_CONSULT:
            return 'Consult แพทย์'
        elif self.specific_type.model == Appointment.APPOINTMENT_TYPE_CENTRAL_LAB:
            return 'Central Lab'
        elif self.specific_type.model == Appointment.APPOINTMENT_TYPE_XRAY:
            return 'Xray'
        elif self.specific_type.model == Appointment.APPOINTMENT_TYPE_SPECIAL_LAB:
            return 'Special Lab'
        elif self.specific_type.model == Appointment.APPOINTMENT_TYPE_CHECKUP:
            return 'Checkup'
        elif self.specific_type.model == Appointment.APPOINTMENT_TYPE_ADMIT:
            return 'Admit'
        return ''

    @property
    def order_specific_type(self):
        model_name = self.specific_type.model
        order_specific_type = DoctorOrder.ORDER_MODEL_TYPE_MAPPING.get(model_name, '')
        # if order_specific_type can be OPD or IPD, it's required to check encounter
        # and change to type follow encounter
        if order_specific_type in [DoctorOrder.DRUG_ORDER_STAT, DoctorOrder.DRUG_ORDER_ONE_DOSE]:
            order_specific_type = '%s__%s' % (order_specific_type, self.encounter.general_type,)
        return order_specific_type

    @property
    def order_specific_label(self):
        model_name = self.specific_type.model
        order_specific_type = DoctorOrder.ORDER_MODEL_TYPE_MAPPING.get(model_name, '')
        order_specific_name = DoctorOrder.SPECIFIC_TYPE_MAPPING.get(order_specific_type, None)
        if not order_specific_name:
            return ''
        return order_specific_name['type_label']

    @property
    def nurse_status(self):
        if self.order_ack_by and self.order_ack_time:
            return DoctorOrder.NURSE_ACKNOWLEDGE
        elif self.order_status is DoctorOrder.ORDER_STATUS.CANCEL:
            return DoctorOrder.NURSE_CANCEL
        else:
            return DoctorOrder.NURSE_WAIT

    class Meta:
        verbose_name = 'คำสั่งแพทย์'

    def __str__(self):
        return "[%s] %s" % (self.specific_type, self.encounter.patient)


class BaseDoctorOrder(AbstractCheckerModelMixin, StatableModel, DoctorOrder):
    """Base class for every doctor's order
    Only doctor can create, cancel these orders.
    However other staff can also order but need remarks and approval from doctor.
    Some order may be able to edit/modify by nurse or laboratory's staff.
    The doctor order can has reference to progression_cycle or encounter directly.
    """

    class MESSAGE_PRIORITY(LabeledIntEnum):
        LOW = 1  # แสดงเฉพาะตัวแรกที่เจอ
        NORMAL = 2  # แสดงเฉพาะตัวแรกที่เจอและทับ LOW ที่มีอยู่ทั้งหมด
        HIGH = 3  # แสดงทุกตัวที่เจอ และทับ NORMAL กับ LOW ที่มีอยู่ทั้งหมด
        URGENT = 4  # แสดงทุกตัวที่เจอร่วมกับ HIGH และแจ้งเตือนผ่านเสียงหรืออื่นๆ

    @classmethod
    def get_descendants(cls):
        children = []
        subclasses = cls.__subclasses__().copy()
        while subclasses:
            subclass = subclasses.pop()
            subclasses.extend(subclass.__subclasses__().copy())
            if not subclass._meta.abstract and subclass.__module__ != 'his.core.tests.models':
                children.append(subclass)

        return children

    @abstractmethod
    def get_order_summary_detail(self) -> str:
        """Summary detail of the order to be display to user"""
        raise NotImplementedError()

    @abstractmethod
    def get_order_detail(self) -> str:
        """ตอนนี้ใช้สำหรับ CardOrderSummary ของ IPD"""
        raise NotImplementedError()

    def get_reject_detail(self) -> str:
        """Reject detail of the order to be display to user

        return '' mean this order is ok"""
        return ''

    @abstractmethod
    def is_editable(self) -> bool:
        """Implement when this order is able to edit"""
        raise NotImplementedError()

    def is_cancellable(self) -> bool:
        return self.is_editable()

    def is_rejected(self) -> bool:
        return False

    def get_queue_message(self) -> Tuple[str, MESSAGE_PRIORITY]:
        return self.__class__.__name__, BaseDoctorOrder.MESSAGE_PRIORITY.LOW

    @abstractmethod
    def get_billable_list(self) -> List[BillableModel]:
        """
        :return: List of BillableModel which is contained in this order.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_staging_items(self) -> List[BillableModel]:
        """
        :return: List of all items in this order (self.items.all())
        """
        raise NotImplementedError()

    def get_encounter(self) -> 'Encounter':
        return self.encounter

    def cancel(self, user, division):
        """ this method will be called when order is canceled """
        if not self.is_editable():
            raise serializers.ValidationError('ไม่สามารถยกเลิก %s ได้' % str(self))

        billable_list = self.get_billable_list()
        is_bill = do_service('BIL:is_billed', billable_list)
        is_paid = do_service('BIL:is_paid', billable_list)

        if all(is_bill) and any(is_bill):
            if not all(is_paid) and any(is_paid):
                raise Exception('Some billable items are not paid!')
            if any(is_paid):
                raise serializers.ValidationError({'order': ['ไม่สามารถยกเลิกได้ เนื่องจากบางรายการจ่ายเงินแล้ว']})
            if not all(is_paid):
                do_service('BIL:unbill', billable_list)
        if not all(is_bill) and any(is_bill):
            raise Exception('Some billable items are not billed!')

        if not hasattr(self.ACTION, 'CANCEL'):
            raise Exception('Action "CANCEL" does not exist in "%s"' % self._meta.model.__name__)

        self.action = self.ACTION.CANCEL
        if self.order_status != self.ORDER_STATUS.APPOINTMENT:
            # Don't change order_status of the appointment
            self.order_status = self.ORDER_STATUS.CANCEL
        self.user = user
        self.save()

    def to_real_from_planning(self, user: User):
        """This method will be called on planning doctor order (doctor order which has order_status=PLANNING)
        to create another doctor order
        :param user:
        :return:
        """
        raise NotImplementedError()

    def renew_from_planning(self, user: User) -> DoctorOrder:
        """ This method will be called on planning doctor order (doctor order which has order_status=PLANNING)
        to create a new cloned planning doctor order
        :param user:
        :return: planning doctor order
        """
        raise NotImplemented()

    def change_from_planning(self, user: User, division: Division, note: str = ''):
        """ This method will be called when plan item is changed
        :param user:
        :param division:
        :param note:
        :return:
        """
        pass

    def to_real_from_appointment(self, ref_appointment_order_binder, encounter, emr, progression_cycle):
        """Called when patient comeback and open Encounter then want to create new appointment
        from the appointed one.
        """
        raise NotImplementedError()

    def get_type_display_name(self) -> str:
        """
        :return: String to describe this object order. For dynamically generated display type
        """
        raise NotImplementedError()

    def do_checkout(self, user: User):
        """Method will be called when this order is being checked out"""
        pass

    def do_nurse_note(self, user: User, division: Division, date_time: datetime):
        """Method will be called when this order is being noted by nurse"""
        pass

    def save_doctor_order(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self.doctororder_ptr, key, value)
            setattr(self, key, value)

        self.doctororder_ptr.save()

    def get_appointment_order_summary_detail(self, language=LANGUAGE_TH) -> str:
        return ''

    def renew_order(self, user):
        print('renew_order')

    def off_order(self, user):
        print('off_order')

    def hold_order(self, user):
        print('hold_order')

    def resume_order(self, user):
        print('resume_order')

    class Meta:
        abstract = True


class PlanItemQuerySet(models.QuerySet):
    def _check_plan_active_from_take_skip(self, target_date, start_date, day_take, day_skip):
        # ex. start_date=01/01/2560, day_take=2, day_skip=3,
        #     target_date=07/01/2560
        #
        # delta=7,  the number of dates between start_date and target_date
        # take=[True, True], skip=[False, False, False]
        # condition=[True, True, False, False, False]
        #
        # -------------------- the first interval --------------  ---- the second interval --
        # 01/01/2560 02/01/2560 03/01/2560 04/01/2560 05/01/2560     06/01/2560 07/01/2560   ...
        #    TAKE       TAKE       SKIP       SKIP       SKIP            take     take       ...
        #
        # delta=7, interval=5
        # (delta % interval)     = 2, the position of target_date in the first interval
        # (delta % interval) - 1 = 1, the index of target_date in condition
        # index=1
        # condition[1] = True
        delta = (target_date - start_date).days + 1
        take = [True] * day_take
        skip = [False] * day_skip
        condition = take + skip
        interval = len(condition)
        index = (delta % interval) - 1
        return condition[index]

    def _get_occurence_from_take_skip(self, target_date, start_date, day_take, day_skip):
        delta = (target_date - start_date).days + 1
        take = list(range(1, day_take + 1))
        skip = [0] * day_skip
        days = take + skip
        interval = len(days)
        index = (delta % interval) - 1
        occurrence = (int(delta / interval) * day_take) + days[index]
        return occurrence

    def _get_occurrence_from_weekdays(self, target_date, start_date, week_days):
        delta = (target_date - start_date).days + 1
        do_per_week = len(week_days)

        # days can be -- [Mon, Tue, Wed, Thu, Fri, Sat, Sun] -> [1, 2, 3, 4, 5, 6, 7]
        #             -- [Mon, Tue, Fri] -> [1, 2, 0, 0, 3, 0, 0]
        #             -- [Fri] -> [0, 0, 0, 0, 0, 0, 1]
        #             -- etc.
        # if week_days is [Mon, Tue, Fri] and target_day is 'Fri' it means 3 plans have done this week
        # if week_days is [Fri] and target_day is 'Fri' it means 1 plan has done this week
        days = [0] * len(PlanItem.ALLOW_WEEK_DAYS)
        for i, day in enumerate(week_days):
            if day in PlanItem.ALLOW_WEEK_DAYS:
                index = PlanItem.ALLOW_WEEK_DAYS.index(day)
                days[index] = i + 1

        index = target_date.weekday()  # date.weekday return index of day (starting at Mon->0, Fri -> 4)
        # The number of weeks before this week
        week_pass = int(delta / 7)
        return (week_pass * do_per_week) + days[index]

    def get_plan_item(self, medical_record: MedicalRecord, target_date: date, show_inactive=False):
        latest_logs = PlanItemActionLog.objects.filter(datetime__date__lte=target_date)
        latest_logs = latest_logs.values('statable_id').annotate(latest=Max('id')).values('latest')
        latest_logs = list(PlanItemActionLog.objects.filter(
            id__in=latest_logs,
            action__in=[PlanItem.ACTION.EDIT, PlanItem.ACTION.REQUEST, PlanItem.ACTION.RESUME],
        ).values_list('statable_id', flat=True))

        if show_inactive:
            inactive_logs = list(PlanItemActionLog.objects.filter(
                datetime__date=target_date, action__in=[
                    PlanItem.ACTION.OFF,
                    PlanItem.ACTION.HOLD,
                ]
            ).values_list('statable_id', flat=True))
            latest_logs = latest_logs + inactive_logs

        result = []
        plan_items = (self.filter(
            (
                (Q(start_date__lte=target_date) & Q(end_date=None)) |
                (Q(start_date__lte=target_date) & Q(end_date__gte=target_date)) |
                (Q(dates__icontains=ad_to_be(target_date)))
            ) &
            (
                Q(week_days=[]) |
                Q(week_days__icontains=PlanItem.ALLOW_WEEK_DAYS[target_date.weekday()])
            ) &
            (
                Q(pk__in=latest_logs)
            )
        ))
        if medical_record:
            plan_items = plan_items.filter(Q(plan_order__emr=medical_record))

        for plan_item in plan_items:
            delta = 0
            if plan_item.start_date:
                delta = (target_date - plan_item.start_date).days + 1
            if delta > 0:
                if plan_item.day_take and plan_item.day_skip:
                    plan_active = self._check_plan_active_from_take_skip(
                        target_date=target_date,
                        start_date=plan_item.start_date,
                        day_take=plan_item.day_take,
                        day_skip=plan_item.day_skip,
                    )
                    occurrence = self._get_occurence_from_take_skip(
                        target_date=target_date,
                        start_date=plan_item.start_date,
                        day_take=plan_item.day_take,
                        day_skip=plan_item.day_skip,
                    )
                    if not plan_active:
                        continue
                    if plan_item.occurrence and occurrence > plan_item.occurrence:
                        continue
                elif plan_item.week_days:
                    occurrence = self._get_occurrence_from_weekdays(
                        target_date=target_date,
                        start_date=plan_item.start_date,
                        week_days=plan_item.week_days
                    )
                    if plan_item.occurrence and occurrence > plan_item.occurrence:
                        continue

                elif plan_item.occurrence:
                    if delta > plan_item.occurrence:
                        continue
            result.append(plan_item)
        return result

    def get_expired_plan_items(self, medical_record: MedicalRecord, target_date: date, include_ended=False):
        """
        :param medical_record:
        :param target_date:
        :param include_ended: if True, return all expired plan items including ones that have status ENDED
        :return: plan items which are expired before target date
        """
        result = []
        # get plan_items which have start_date with end_date or occurrence,
        # or plan items which have dates
        plan_items = self.filter(
            (
                (
                    ~Q(start_date=None) &
                    ~(Q(end_date=None) & Q(occurrence=None)) &
                    Q(dates=[])
                ) |
                (
                    ~Q(dates=[]) &
                    Q(start_date=None)
                )
            ) &
            Q(status__in=[PlanItem.STATUS.ACTIVE, PlanItem.STATUS.HELD])
        )
        if medical_record:
            plan_items = plan_items.filter(Q(plan_order__emr=medical_record))
        if not include_ended:
            plan_items = plan_items.exclude(status=PlanItem.STATUS.ENDED)

        for plan_item in plan_items:
            expired = False

            if plan_item.dates:
                plan_dates = sorted(plan_item.dates, key=lambda _date: be_to_ad(_date))
                last_date = be_to_ad(plan_dates[-1])
                delta = (target_date - last_date).days
                expired = True if delta > 0 else False

            elif plan_item.start_date and plan_item.end_date:
                delta = (target_date - plan_item.end_date).days
                expired = True if delta > 0 else False

            elif plan_item.start_date and plan_item.occurrence:

                if plan_item.day_take and plan_item.day_skip:
                    occurrence = self._get_occurence_from_take_skip(
                        target_date=target_date,
                        start_date=plan_item.start_date,
                        day_take=plan_item.day_take,
                        day_skip=plan_item.day_skip,
                    )
                    expired = True if occurrence > plan_item.occurrence else False

                elif plan_item.week_days:
                    occurrence = self._get_occurrence_from_weekdays(
                        target_date=target_date,
                        start_date=plan_item.start_date,
                        week_days=plan_item.week_days
                    )
                    expired = True if occurrence > plan_item.occurrence else False

                else:
                    delta = (target_date - plan_item.start_date).days + 1
                    expired = True if delta > plan_item.occurrence else False

            if expired:
                result.append(plan_item)

        return result

    def create_real_order_and_end_plan_item(self):
        today = timezone.now().date()

        items_planned = list(
            PlanItem.objects.filter(realize_every_time=False).get_plan_item(medical_record=None, target_date=today)
        )
        items_always = list(
            PlanItem.objects.filter(realize_every_time=True, status=PlanItem.STATUS.ACTIVE)
        )

        for item in items_planned + items_always:
            try:
                item.plan_order.specific.to_real_from_planning(user=item.plan_order.order_by.user)
            except:
                logger.error(traceback.format_exc())

        items = PlanItem.objects.get_expired_plan_items(medical_record=None, target_date=today)
        for item in items:
            item.user = User.objects.get_system_user()
            item.action = PlanItem.ACTION.END
            item.save()

    def terminate_all_plan_item(self, encounter, user):
        plan_items = PlanItem.objects.filter(
            plan_order__encounter=encounter,
            status__in=(
                PlanItem.STATUS.ACTIVE,
                PlanItem.STATUS.HELD,
            )
        )
        for plan_item in plan_items:
            plan_item.action = PlanItem.ACTION.OFF
            plan_item.user = user
            plan_item.save()

    def get_active_plan_items_between_date(self, from_date, to_date):
        date_matching = (
            Q(dates__icontains=format_date(target_date))
            for target_date in
            (from_date + timedelta(i) for i in range((to_date - from_date).days + 1))
        )

        return self.filter(
            Q(start_date__lte=to_date) | reduce(operator.or_, date_matching, Q()),
        ).exclude(
            pk__in=PlanItemActionLog.objects.filter(
                action__in=[PlanItem.ACTION.OFF, PlanItem.ACTION.END],
                datetime__date__lt=from_date
            ).values('statable')
        ).exclude(
            end_date__lt=from_date,
        )


class PlanItem(StatableModel):
    class ACTION(LabeledIntEnum):
        EDIT = 1
        REQUEST = 2
        HOLD = 3
        RESUME = 4
        OFF = 5
        END = 6
        RENEW = 8

    class STATUS(LabeledIntEnum):
        ACTIVE = 1, 'Active'
        HELD = 2, 'Hold'
        OFF = 3, 'Off'
        ENDED = 4, 'End'
        CANCELED = 5, 'Cancel'
        RENEWED = 6, 'Renew'

    TRANSITION = [
        (None, ACTION.REQUEST, STATUS.ACTIVE),
        (STATUS.ACTIVE, ACTION.EDIT, STATUS.ACTIVE),
        (STATUS.ACTIVE, ACTION.END, STATUS.ENDED),
        (STATUS.ACTIVE, ACTION.HOLD, STATUS.HELD),
        (STATUS.ACTIVE, ACTION.OFF, STATUS.OFF),
        (STATUS.HELD, ACTION.RESUME, STATUS.ACTIVE),
        (STATUS.HELD, ACTION.OFF, STATUS.OFF),
        (STATUS.HELD, ACTION.END, STATUS.ENDED),
        (STATUS.OFF, ACTION.RENEW, STATUS.RENEWED),
        (STATUS.ENDED, ACTION.RENEW, STATUS.RENEWED),
    ]

    ACTION_REQUIRE_NOTE = (
        ACTION.EDIT,
        ACTION.HOLD,
        ACTION.RESUME,
        ACTION.OFF,
    )

    start_date = models.DateField(verbose_name='วันที่เริ่มต้น', null=True, blank=True)
    end_date = models.DateField(verbose_name='วันที่สิ้นสุด', null=True, blank=True)
    week_days = JSONField(verbose_name='วันในสัปดาห์', default=list, blank=True)
    day_take = models.PositiveIntegerField(verbose_name='จำนวนวันที่ทำ', null=True, blank=True)
    day_skip = models.PositiveIntegerField(verbose_name='จำนวนวันที่ไม่ทำ', null=True, blank=True)
    occurrence = models.PositiveIntegerField(verbose_name='จำนวนครั้งที่ทำ', null=True, blank=True)
    dates = JSONField(verbose_name='วันที่จะทำ (กำหนดได้หลายวัน)', help_text='วันที่/เดือน/ปี ที่จะทำ (พ.ศ.)',
                      default=list, blank=True)
    times = JSONField(verbose_name='เวลาที่จะทำ (กำหนดได้หลายเวลา)', default=list, blank=True)
    plan_summary = models.TextField(verbose_name='สรุปข้อมูลของ DoctorOrder',
                                    help_text='เมื่อมีการ บันทึก/แก้ไข DoctorOrder จะต้อง update plan_summary')
    plan_order = models.OneToOneField(DoctorOrder,
                                      verbose_name='รายการต้นแบบที่จะถูกสร้างเมื่อถึงเวลา',
                                      related_name='plan_item')
    actual_orders = models.ManyToManyField(DoctorOrder, blank=True,
                                           verbose_name='รายการที่ถูกสร้างแล้ว',
                                           related_name='created_from_plan_items',
                                           help_text='PlanItem ที่ ผูกกับ DoctorOrder ที่ถูก Clone')
    realize_every_time = models.BooleanField(default=False)

    MUTUALLY_EXCLUSIVE = (
        ('end_date', 'occurrence', _('end_date ไม่สามารถเลือกพร้อมกับ occurrence ได้')),
        ('week_days', 'day_take', _('week_days ไม่สามารถเลือกพร้อมกับ day_take ได้')),
        ('week_days', 'day_skip', _('week_days ไม่สามารถเลือกพร้อมกับ day_skip ได้')),
        ('dates', 'start_date', _('dates ไม่สามารถเลือกพร้อมกับ start_date ได้')),
        ('dates', 'end_date', _('dates ไม่สามารถเลือกพร้อมกับ end_date ได้')),
        ('dates', 'week_days', _('dates ไม่สามารถเลือกพร้อมกับ week_days ได้')),
        ('dates', 'day_take', _('dates ไม่สามารถเลือกพร้อมกับ day_take ได้')),
        ('dates', 'day_skip', _('dates ไม่สามารถเลือกพร้อมกับ day_skip ได้')),
        ('dates', 'occurrence', _('dates ไม่สามารถเลือกพร้อมกับ occurrence ได้')),
    )

    ALLOW_WEEK_DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
    THAI_WEEK_DAYS = (_('จันทร์'), _('อังคาร'), _('พุธ'), _('พฤหัสบดี'), _('ศุกร์'), _('เสาร์'), _('อาทิตย์'))
    ALLOW_DATE_PATTERN = '^(\d{1,2})/(\d{1,2})/(\d{4})$'

    objects = PlanItemQuerySet.as_manager()

    def get_date_time_summary(self) -> str:
        """Date/Time summary of the plan item to be displayed to user"""
        summary = []
        if self.has_validation_errors():
            return _('ระบุวันที่หรือเวลาไม่ถูกต้อง')
        if self.start_date:
            summary.append(_('เริ่ม %s, ' % ad_to_be(self.start_date)))
        if self.week_days:
            summary.append(_('ทำทุกวัน '))
            for week_day in sorted(self.week_days, key=self.ALLOW_WEEK_DAYS.index):
                summary.append('%s, ' % self.THAI_WEEK_DAYS[self.ALLOW_WEEK_DAYS.index(week_day)])
        if self.day_take:
            if self.day_skip:
                summary.append(_('ทำซ้ำ %d วัน เว้น %d วัน, ' % (self.day_take, self.day_skip)))
            else:
                summary.append(_('ทำซ้ำ %d วัน, ' % self.day_take))
        if self.occurrence:
            summary.append(_('%d วัน, ' % self.occurrence))
        if self.end_date:
            summary.append(_('สิ้นสุด %s, ' % ad_to_be(self.end_date)))
        if self.dates:
            summary.append(_('ทำในวันที่ '))
            for _date in sorted(self.dates, key=lambda _date: be_to_ad(_date)):
                summary.append('%s, ' % _date)
        if self.times:
            summary.append(_('เวลา '))
            times = sorted((import_time.strptime(_time, "%H:%M") for _time in self.times))
            for _time in times:
                summary.append('%s น., ' % import_time.strftime("%H:%M", _time))

        summary = ''.join(map(str, summary))
        return summary[0:-2]

    def _check_allow_week_days(self):
        errors = []
        if self.week_days is None:
            return errors
        if type(self.week_days) != list:
            errors.append('week_days ต้องระบุเป็น list')
            return errors
        for day in self.week_days:
            if day not in self.ALLOW_WEEK_DAYS:
                errors.append('ระบุค่า week_days ไม่ถูกต้อง')
                break
        return errors

    def _check_allow_dates(self):
        errors = []
        if self.dates is None:
            return errors
        if type(self.dates) != list:
            errors.append(_('dates ต้องระบุเป็น list'))
            return errors
        for _date in self.dates:
            if not re.match(self.ALLOW_DATE_PATTERN, _date):
                errors.append(_('ระบุค่า dates ไม่ถูกต้อง'))
                break
        return errors

    def _check_allow_times(self):
        errors = []
        if self.times is None:
            return errors
        if type(self.times) != list:
            errors.append(_('times ต้องระบุเป็น list'))
            return errors
        for _time in self.times:
            try:
                import_time.strptime(_time, '%H:%M')
                continue
            except ValueError:
                errors.append(_('ระบุค่า times ไม่ถูกต้อง'))
                break
        return errors

    def _check_day_skip_without_day_take(self):
        errors = []
        if self.day_skip is None:
            return errors
        if self.day_skip and self.day_take is None:
            errors.append(_('เมื่อระบุ day_skip จำเป็นต้องระบุ day_take'))
        return errors

    def _check_should_has_start_date_or_dates(self):
        if not self.start_date and not self.dates:
            return [_('ต้องระบุ start_date หรือ dates')]
        return []

    def _check_mutually_exclusive(self):
        errors = []
        for items in self.MUTUALLY_EXCLUSIVE:
            if bool(getattr(self, items[0], None)) and bool(getattr(self, items[1], None)):
                errors.append(items[2])
        return errors

    def has_validation_errors(self, raise_exception=False):
        errors = []
        errors += self._check_allow_week_days()
        errors += self._check_allow_dates()
        errors += self._check_allow_times()
        errors += self._check_day_skip_without_day_take()
        errors += self._check_should_has_start_date_or_dates()
        errors += self._check_mutually_exclusive()
        if raise_exception and errors:
            raise ValidationError(errors)
        return errors

    def pre_request(self):
        if self.plan_order.order_status != DoctorOrder.ORDER_STATUS.PLANNING:
            raise Exception('order_status of plan_order must be "PLANNING"')

    def pre_edit(self):
        if not self.plan_order.specific.is_editable():
            raise ValidationError({'ACTION': [_('ไม่สามารถแก้ไขได้ เนื่องจากไม่สามารถแก่ไข Plan Order')]})

    def pre_off(self):
        ref_plan_order = DoctorOrder.objects.get(pk=self.plan_order.pk)
        ref_plan_order.order_status = DoctorOrder.ORDER_STATUS.OFF
        ref_plan_order.save()

        do_service('DPO:create_doctor_note_order_from_plan', **dict(
            user=self.user,
            emr=ref_plan_order.emr,
            doctor=ref_plan_order.order_by,
            division=ref_plan_order.order_div,
            detail=ref_plan_order.specific.get_order_detail(),
            plan_action='OFF',
        ))

    def do_off(self):
        self.plan_order.specific.off_order(user=self.user)

    def pre_end(self):
        self.pre_off()

    def pre_renew(self):
        new_plan_order = self.plan_order.specific.renew_from_planning(user=self.user)
        if not new_plan_order:
            raise Exception('renew_from_planning() should return a new planning doctor order')

        new_plan_item = PlanItem.objects.get(pk=self.pk)
        new_plan_item.id = None
        new_plan_item.status = None
        new_plan_item.plan_order = new_plan_order
        new_plan_item.action = self.ACTION.REQUEST
        new_plan_item.user = self.user
        new_plan_item.save()

    def do_renew(self):
        self.plan_order.specific.renew_order(user=self.user)

    def pre_hold(self):
        ref_plan_order = DoctorOrder.objects.get(pk=self.plan_order.pk)
        do_service('DPO:create_doctor_note_order_from_plan', **dict(
            user=self.user,
            emr=ref_plan_order.emr,
            doctor=ref_plan_order.order_by,
            division=ref_plan_order.order_div,
            detail=ref_plan_order.specific.get_order_detail(),
            plan_action='HOLD',
        ))

    def do_hold(self):
        self.plan_order.specific.hold_order(user=self.user)

    def pre_resume(self):
        ref_plan_order = DoctorOrder.objects.get(pk=self.plan_order.pk)
        do_service('DPO:create_doctor_note_order_from_plan', **dict(
            user=self.user,
            emr=ref_plan_order.emr,
            doctor=ref_plan_order.order_by,
            division=ref_plan_order.order_div,
            detail=ref_plan_order.specific.get_order_detail(),
            plan_action='RESUME',
        ))

    def do_resume(self):
        self.plan_order.specific.resume_order(user=self.user)

    def update_plan_summary(self, plan_summary):
        assert type(plan_summary) == str, 'plan_summary should be string'
        self.plan_summary = plan_summary
        self.save_for_test()

    def cancel(self, user):
        self.action = self.ACTION.OFF
        self.user = user
        self.save()

    def get_date_list(self, from_date: date, to_date: date):
        from_date = convert_to_date(from_date)
        to_date = convert_to_date(to_date)
        assert from_date <= to_date

        if self.dates:
            return [
                a_date
                for a_date in (convert_to_date(a_date) for a_date in self.dates)
                if from_date <= a_date <= to_date
            ]

        if self.start_date:
            from_date = max(from_date, self.start_date)

        if self.end_date:
            to_date = min(to_date, self.end_date)

        if self.occurrence:
            result = [self.start_date + timedelta(i) for i in range((to_date - self.start_date).days + 1)]

        else:
            result = [from_date + timedelta(i) for i in range((to_date - from_date).days + 1)]

        if self.week_days:
            result = [
                a_date
                for a_date in result
                if PlanItem.ALLOW_WEEK_DAYS[a_date.weekday()] in self.week_days
            ]

        elif self.day_take and self.day_skip:
            result = [
                a_date
                for a_date in result
                if (a_date - self.start_date).days % (self.day_take + self.day_skip) < self.day_take
            ]

        if self.occurrence:
            return [
                a_date
                for a_date in result[: self.occurrence]
                if from_date <= a_date <= to_date
            ]

        return result

    def get_allowed_action(self):
        ret = super().get_allowed_action()

        current_action = self.actions.all().last()
        if current_action:
            current_action = current_action.action.text

        if self.plan_order_id:
            order = DoctorOrder.objects.get(id=self.plan_order_id)
            acknowledged = order.order_ack_by and order.order_ack_time

            if current_action == 'REQUEST' and not acknowledged:
                ret = [self.ACTION.EDIT, self.ACTION.OFF]

            elif current_action == 'REQUEST' and acknowledged:
                ret = [self.ACTION.HOLD, self.ACTION.OFF]

            if current_action == 'RESUME' and not acknowledged:
                ret = [self.ACTION.EDIT, self.ACTION.OFF]

            elif current_action == 'RESUME' and acknowledged:
                ret = [self.ACTION.HOLD, self.ACTION.OFF]

            if self.plan_order.specific_type.model == "doctornoteorder":
                block_actions = [PlanItem.ACTION.HOLD, PlanItem.ACTION.RENEW]
                ret = [action for action in ret if action not in block_actions]

        if current_action == 'HOLD':
            ret = [self.ACTION.RESUME, self.ACTION.OFF]

        if self.ACTION.EDIT in ret and hasattr(self.plan_order.specific, 'is_editable'):
            if not self.plan_order.specific.is_editable():
                ret.remove(self.ACTION.EDIT)
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.has_validation_errors(raise_exception=True)
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta:
        verbose_name = 'ตารางวางแผนการทำรายการแบบต่อเนื่อง'


class PlanItemActionLog(BaseActionLog(PlanItem)):
    note = models.TextField(blank=True)


class StandardAdministrationTime(ChoiceModel):
    omission_time = models.IntegerField(default=60, help_text='จำนวนนาทีสูงสุดที่สามารถให้ยาคลาดเคลื่อนได้')

    def __str__(self):
        return '%s' % self.name


class StandardAdministrationTimeItem(models.Model):
    standard_admin_time = models.ForeignKey(StandardAdministrationTime, related_name='items')
    time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return '%s %s' % (self.standard_admin_time, self.time)

    @staticmethod
    def get_common_time(time_str):
        hour, minute = time_str.split(':')

        std = StandardAdministrationTime.objects.get_or_create(
            name='COMMON', defaults=dict(is_active=False)
        )[0]

        return StandardAdministrationTimeItem.objects.get_or_create(
            standard_admin_time=std,
            time=time(int(hour), int(minute)),
        )[0]


class Diagnosis(EditableModel):
    """Diagnosis of the patient
    Each encounter must include at least one principal diagnosis.
    The patient may contains multiple diagnosis on each encounter.
    """

    class TYPE(LabeledIntEnum):
        PRIMARY = 1, 'Primary Diagnosis'  # Or Principal in OPD it's the same
        SECONDARY = 2, 'Secondary Diagnosis'  # For OPD

        PROVISIONAL_PRIMARY = 3, 'Provisional Primary Diagnosis'
        PROVISIONAL_SECONDARY_COMORBID = 4, 'Provisional Secondary Comorbid Diagnosis'
        PROVISIONAL_SECONDARY_COMPLICATION = 5, 'Provisional Secondary Complication Diagnosis'
        PROVISIONAL_SECONDARY_OTHER = 6, 'Provisional Secondary Other Diagnosis'

        SECONDARY_COMORBID = 7, 'Secondary Comorbid Diagnosis'
        SECONDARY_COMPLICATION = 8, 'Secondary Complication Diagnosis'
        SECONDARY_OTHER = 9, 'Secondary Other Diagnosis'

        EXTERNAL_CAUSE = 10, 'External Cause Diagnosis'

        # PREOPERATIVE_PRIMARY = 11, 'Preoperative Primary Diagnosis'
        # PREOPERATIVE_SECONDARY = 12, 'Preoperative Secondary Diagnosis'

    PROVISIONAL_SECONDARY_TYPE = [
        TYPE.PROVISIONAL_SECONDARY_COMORBID,
        TYPE.PROVISIONAL_SECONDARY_COMPLICATION,
        TYPE.PROVISIONAL_SECONDARY_OTHER,
    ]

    # PREOPERATIVE_TYPE = [
    #     TYPE.PREOPERATIVE_PRIMARY,
    #     TYPE.PREOPERATIVE_SECONDARY
    # ]

    PROVISIONAL_TYPE = [TYPE.PROVISIONAL_PRIMARY] + PROVISIONAL_SECONDARY_TYPE

    SECONDARY_TYPE = [
        TYPE.SECONDARY,
        TYPE.SECONDARY_COMORBID,
        TYPE.SECONDARY_COMPLICATION,
        TYPE.SECONDARY_OTHER,
    ]

    class SOURCE(LabeledIntEnum):
        OPD = 1, 'OPD'
        IPD = 2, 'IPD'
        ORM = 3, 'ORM'

    emr = models.ForeignKey(MedicalRecord, related_name='core_diagnosis', verbose_name='Electronic Medical Record')
    type = EnumField(TYPE, verbose_name='ชนิดของ Diagnosis')
    source = EnumField(SOURCE, default=SOURCE.OPD, verbose_name='ชนิดของ Diagnosis')
    medical_description = models.TextField(null=True, blank=True)
    icd10 = models.ForeignKey(Icd10, related_name='core_diagnosis', null=True, blank=True)
    icd10_med_term = models.ForeignKey(Icd10MedicalTerm, related_name='core_diagnosis', null=True, blank=True)
    detail = models.CharField(null=True, blank=True, max_length=255, verbose_name='สาเหตุเพิ่มเติม')
    active = models.BooleanField(default=True)

    def __str__(self):
        return '[%s] %s (%s)' % (self.icd10_med_term, self.icd10, self.medical_description)

    class Meta:
        verbose_name = 'ผลวิเคราะห์อาการป่วย'


class DiagnosisTemplate(models.Model):
    """Frequently used diagnosis.
    The diagnosis template will be linked into this model.
    This template will be use depend on division.
    """
    name = models.CharField(max_length=255, verbose_name='ชื่อ Template โรค')
    division = models.ManyToManyField(Division, related_name='core_diag_template')

    def __str__(self):
        return self.name + ' : ' + ','.join([d.code for d in self.division.all()])

    class Meta:
        verbose_name = 'ชื่อ Template ของ Diagnosis'


class DiagnosisTemplateDetail(models.Model):
    """
    It links diagnosis with given ICD10
    """
    diag_template = models.ForeignKey('DiagnosisTemplate', related_name='core_diag_template_detail')
    type = EnumField(Diagnosis.TYPE, verbose_name='ชนิดของ Diagnosis')
    icd10 = models.ForeignKey(Icd10, related_name='core_diag_template_detail')
    icd10_med_term = models.ForeignKey(Icd10MedicalTerm,
                                       related_name='core_diag_template_detail', null=True, blank=True)

    class Meta:
        verbose_name = 'รายละเอียด Template ของ Diagnosis'


class ProcedureQuerySet(models.QuerySet):
    def filter_active(self):
        return self.filter(active=True)

    def filter_treatment(self):
        return self.filter(source=Procedure.SOURCE.TREATMENT)

    def filter_ipd_discharge(self):
        return self.filter(source=Procedure.SOURCE.IPD_DISCHARGE)


class Procedure(EditableModel):
    class TYPE(LabeledIntEnum):
        PRIMARY = 1, 'Primary Procedure'
        SECONDARY = 2, 'Secondary Procedure'

    class SOURCE(LabeledIntEnum):
        UNKNOWN = 1, 'Unknown'
        TREATMENT = 2, 'Treatment'
        IPD_DISCHARGE = 3, 'IPD Discharge Summary'
        PRE_OP = 4, 'Pre-Operation'
        POST_OP = 5, 'Post-Operation'

    emr = models.ForeignKey(MedicalRecord, related_name='core_procedure', verbose_name='Electronic Medical Record')
    order = models.ForeignKey(DoctorOrder, null=True, blank=True,
                              related_name='core_procedure', verbose_name='Doctor Order')
    type = EnumField(TYPE, verbose_name='ชนิดของ Procedure')
    source = EnumField(SOURCE, default=SOURCE.UNKNOWN, verbose_name='แหล่งที่มาของ Procedure')
    medical_description = models.TextField(default='', blank=True)
    icd9cm = models.ForeignKey(Icd9cm, related_name='core_procedure', null=True, blank=True)
    icd9cm_med_term = models.ForeignKey(Icd9cmMedicalTerm, related_name='core_procedure', null=True, blank=True)
    active = models.BooleanField(default=True)
    objects = ProcedureQuerySet.as_manager()

    def __str__(self):
        return '[%s] %s (%s)' % (self.icd9cm_med_term, self.icd9cm, self.medical_description)

    class Meta:
        verbose_name = 'การทำหัตถการ'


class ProcedureTemplate(models.Model):
    """Frequently used procedure.
    The procedure template will be linked into this model.
    This template will be use depend on division.
    """
    name = models.CharField(max_length=255, verbose_name='ชื่อ Template หัตถการ')
    division = models.ManyToManyField(Division, related_name='core_procedure_template')

    def __str__(self):
        return self.name + ' : ' + ','.join([d.code for d in self.division.all()])

    class Meta:
        verbose_name = 'ชื่อ Template ของ Procedure'


class ProcedureTemplateDetail(models.Model):
    """
    It links procedure with given ICD10
    """
    procedure_template = models.ForeignKey('ProcedureTemplate', related_name='core_procedure_template_detail')
    type = EnumField(Procedure.TYPE, verbose_name='ชนิดของ Procedure')
    icd9cm = models.ForeignKey(Icd9cm, related_name='core_procedure_template_detail')
    icd9cm_med_term = models.ForeignKey(Icd9cmMedicalTerm,
                                        related_name='core_procedure_template_detail', null=True, blank=True)

    class Meta:
        verbose_name = 'รายละเอียด Template ของ Procedure'


class MiscellaneousOrder(BillableModel, EditableModel):
    """Transactional data of "a miscellaneous order" used for a medical fee creation of a product.
    which have no workflow or its workflow is not yet available. a pricing is retrieved from a product code.
    """
    product = models.ForeignKey(Product, related_name='+', help_text='a product to be charged')
    quantity = models.DecimalField(decimal_places=2, max_digits=10, help_text='a quantity of product to be charged')
    encounter = models.ForeignKey(Encounter, help_text='an encounter of the patient whose to be charged',
                                  related_name='miscellaneous_orders')
    requesting_division = models.ForeignKey(Division, related_name='+', help_text='a division requested the order')
    performing_division = models.ForeignKey(Division, related_name='+', help_text='a division performed the order')
    perform_datetime = models.DateTimeField(help_text='a date and time when order was performed.')
    active = models.BooleanField(default=True, help_text='is the order active?')
    note = models.TextField(blank=True)
    eligibility_type = EnumField(ELIGIBILITY_TYPE, default=ELIGIBILITY_TYPE.TREATMENT)
    charges_date = models.DateField(default=date.today, help_text='วันที่ของค่าใช้จ่าย จะแสดงใบใบรายละเอียดใบเสร็จ')

    def get_business_date(self):
        return self.charges_date

    def get_product(self):
        return self.product

    def get_quantity(self):
        return self.quantity

    def get_encounter(self):
        return self.encounter

    def get_requesting_division(self):
        return self.requesting_division

    def get_performing_division(self):
        return self.performing_division

    def get_perform_datetime(self):
        return self.perform_datetime

    def get_bill_display_name(self):
        return self.product.name

    def get_staging_items(self):
        return [self]

    @property
    def order_status(self):
        return DoctorOrder.ORDER_STATUS.PERFORMED if self.perform_datetime is not None else ''

    @property
    def document_no(self):
        return config.core_PREFIX_MISC_ORDER + str(self.id)

    @property
    def obs_id(self):
        return self.id

    @staticmethod
    def get_hospital_fee_list():
        return [config.core_HOSPITAL_FEE_REGULAR, config.core_HOSPITAL_FEE_SPECIAL, config.core_HOSPITAL_FEE_PREMIUM]


class ActiveEncounterManager(models.Manager):
    def __init__(self, types: list):
        super().__init__()
        self.types = types

    def get_queryset(self):
        return EncounterQuerySet(self.model).filter_unexpired().filter(type__in=self.types)


class EncounterNumberOPD(Encounter):
    objects = ActiveEncounterManager([
        Encounter.TYPE_OPD,
        Encounter.TYPE_ER,
        Encounter.TYPE_OTH
    ])

    class Meta:
        proxy = True


class EncounterNumberIPD(Encounter):
    objects = ActiveEncounterManager([
        Encounter.TYPE_IPD,
    ])

    class Meta:
        proxy = True


class EncounterNumberSSS(Encounter):
    objects = ActiveEncounterManager([
        Encounter.TYPE_SS,
    ])

    class Meta:
        proxy = True


class CoveragePayerMap(models.Model):
    coverage = models.ForeignKey(Coverage, verbose_name='สิทธิผู้ป่วย', related_name='coverage_payer')
    payer_id = models.CharField(max_length=50, verbose_name='รหัสผู้จ่ายเงิน')
    map_to_coverage = models.ForeignKey(Coverage, verbose_name='สิทธิผู้ป่วยที่เลือกให้',
                                        related_name='coverage_payer_map')

    class Meta:
        unique_together = ('coverage', 'payer_id')

    def __str__(self):
        return "%s. %s - %s = %s" % (self.id, self.coverage.name, self.payer_id, self.map_to_coverage.name)


class BankTransferScheduleManager(models.Manager):
    def open_on(self, date) -> bool:
        qs = self.get_queryset()
        return qs.filter(active=True,
                         day_of_week=date.weekday(),
                         start_time__lte=date.time(),
                         end_time__gte=date.time()
                         ).exists()

    def is_work_day(self, date) -> bool:
        qs = self.get_queryset()
        return qs.filter(active=True,
                         day_of_week=date.weekday()
                         ).exists()

    def is_before_open_time(self, date) -> bool:
        qs = self.get_queryset()
        return qs.filter(active=True,
                         day_of_week=date.weekday(),
                         start_time__gt=date.time()
                         ).exists()


class BankTransferSchedule(EditableModel):
    """เก็บข้อมูลตารางเปิดทำการของธนาคาร"""
    DAY_CHOICES = (
        ('0', 'จันทร์'),
        ('1', 'อังคาร'),
        ('2', 'พุธ'),
        ('3', 'พฤหัส'),
        ('4', 'ศุกร์'),
        ('5', 'เสาร์'),
        ('6', 'อาทิตย์'),
    )
    day_of_week = models.CharField(max_length=1, default='0', choices=DAY_CHOICES, verbose_name="วัน")
    start_time = models.TimeField(verbose_name='เวลาเปิดทำการ', help_text='เวลาเปิดทำการ')
    end_time = models.TimeField(verbose_name='เวลาปิดทำการ', help_text='เวลาปิดทำการ')
    active = models.BooleanField(default=True, verbose_name='active flag',
                                 help_text='True = active, False = not active')

    objects = BankTransferScheduleManager()

    class Meta:
        verbose_name = 'ตารางเวลาเปิดทำการของธนาคาร'
        verbose_name_plural = verbose_name


class BankTransferStopScheduleManager(models.Manager):
    def is_stop(self, date) -> bool:
        qs = self.get_queryset()
        return qs.filter(active=True, date=date).exists()


class BankTransferStopSchedule(EditableModel):
    """เก็บข้อมูลตารางวันหยุดของธนาคาร"""
    date = models.DateField(verbose_name='วันหยุดตามประเพณี')
    active = models.BooleanField(default=True)

    objects = BankTransferStopScheduleManager()

    class Meta:
        verbose_name = 'ตารางวันหยุดของธนาคาร'
        verbose_name_plural = verbose_name


class PackageOrder(EditableModel, BillableModel):
    patient_coverage = models.ForeignKey(PatientCoverage, related_name='+', blank=True, null=True)
    package = models.ForeignKey(Package, related_name='+')
    quantity = models.PositiveIntegerField(default=1)
    encounter = models.ForeignKey(Encounter, related_name='package_orders')
    requesting_division = models.ForeignKey(Division, related_name='+', help_text='a division requested the order')
    performing_division = models.ForeignKey(Division, related_name='+', help_text='a division performed the order')
    perform_datetime = models.DateTimeField(help_text='a date and time when order was performed.')
    active = models.BooleanField(default=True, help_text='is the order active?')

    def get_product(self):
        return self.package

    def get_quantity(self):
        return self.quantity

    def get_encounter(self):
        return self.encounter

    def get_requesting_division(self):
        return self.requesting_division

    def get_performing_division(self):
        return self.performing_division

    def get_perform_datetime(self):
        return self.perform_datetime

    def get_bill_display_name(self):
        return self.package.name


class RecordLocker(models.Model):
    target_type = models.ForeignKey(ContentType)
    target_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_type', 'target_id')

    def __str__(self):
        return '{} {}'.format(self.target_type, self.target_id)

    class Meta:
        unique_together = ['target_type', 'target_id']

    @staticmethod
    @contextmanager
    def atomic(targets):
        targets = list(targets)
        try:
            yield RecordLocker.lock(targets)
        except:
            raise
        finally:
            RecordLocker.unlock(targets)

    @staticmethod
    @transaction.atomic()
    def lock(targets):
        errors = []
        locked_targets = []
        for target in targets:
            locker, is_created = RecordLocker.objects.get_or_create(
                target_type=ContentType.objects.get_for_model(target),
                target_id=target.pk,
            )

            if not is_created:
                errors.append('{} is locked'.format(str(target)))
            else:
                # print('LOCKING', locker)
                locked_targets.append(locker.target)

        if errors:
            raise RecordLockedException(errors)

        return locked_targets

    @staticmethod
    @transaction.atomic()
    def unlock(targets):
        errors = []
        for target in targets:
            locker = RecordLocker.objects.filter(
                target_type=ContentType.objects.get_for_model(target),
                target_id=target.pk,
            ).first()

            if not locker:
                errors.append('{} is not locked by'.format(str(target)))
            else:
                # print('UNLOCKING', locker)
                locker.delete()

        if errors:
            raise RecordNotLockedException(errors)

    def is_locked(target):
        return RecordLocker.objects.filter(
            target_type=ContentType.objects.get_for_model(target),
            target_id=target.pk,
        ).exists()


class Language(EditableModel):
    code = models.CharField(max_length=4, unique=True)
    name_th = models.CharField(max_length=40)
    name_en = models.CharField(max_length=40)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "%s: %s (%s) " % (self.code, self.name_en, self.name_th)


class DivisionLocation(models.Model):
    division = models.ForeignKey(Division)
    location = models.ForeignKey(Location)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'สถานที่ตั้งหน่วยงาน'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s - %s' % (self.division, self.location)


class UnitActionQuerySet(models.QuerySet):
    pass


class UnitAction(models.Model):
    model_type = models.ForeignKey(ContentType, null=True, blank=True)
    action_class_name = models.CharField(max_length=255, blank=True, default='ACTION', help_text='action class name')
    code = models.CharField(max_length=20, help_text='if import from LabelIntEnum this field = value')
    name = models.CharField(max_length=255, help_text='if import from LabelIntEnum this field = name')
    active = models.BooleanField(default=True)

    objects = UnitActionQuerySet.as_manager()

    class Meta:
        unique_together = ('model_type', 'action_class_name', 'code',)
        verbose_name = 'Unit Action'
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.model_type:
            source = '[%s.%s]' % (self.model_type, self.action_class_name)
        else:
            source = '[%s]' % (self.action_class_name,)
        return '%s %s = %s' % (source, self.name, self.code)


class UnitStatusQuerySet(models.QuerySet):
    def get_initial_status(self):
        unit_status, created = self.get_or_create(
            model_type=None,
            status_class_name='',
            code='0',
            name='INITIAL',
        )
        return unit_status


class UnitStatus(models.Model):
    model_type = models.ForeignKey(ContentType, null=True, blank=True)
    status_class_name = models.CharField(max_length=255, blank=True, default='STATUS', help_text='status class name')
    code = models.CharField(max_length=20, help_text='if import from LabelIntEnum this field = value')
    name = models.CharField(max_length=255, help_text='if import from LabelIntEnum this field = name')
    active = models.BooleanField(default=True)

    objects = UnitStatusQuerySet.as_manager()

    class Meta:
        unique_together = ('model_type', 'status_class_name', 'code',)
        verbose_name = 'Unit Status'
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.model_type:
            source = '[%s.%s]' % (self.model_type, self.status_class_name)
        else:
            source = '[%s]' % (self.status_class_name,)
        return '%s %s = %s' % (source, self.name, self.code)


class UnitStatusTransitionQuerySet(models.QuerySet):
    def get_from_status_and_action(self, unit_status: UnitStatus, unit_action: UnitAction):
        unit_status_transitions = self.filter(
            from_unit_status=unit_status,
            unit_action=unit_action,
            active=True
        )
        if unit_status_transitions.count() > 1:
            raise Exception('UnitStatusTransition contains duplicate data from_unit_status %s action %s' % (
                unit_status, unit_action
            ))
        elif unit_status_transitions.count() == 0:
            raise Exception('UnitStatusTransition not found data from_unit_status %s action %s' % (
                unit_status, unit_action
            ))
        return unit_status_transitions.first()


class UnitStatusTransition(models.Model):
    unit_action = models.ForeignKey(UnitAction)
    from_unit_status = models.ForeignKey(UnitStatus, related_name='+')
    to_unit_status = models.ForeignKey(UnitStatus, related_name='+')
    create_unit_slot = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    objects = UnitStatusTransitionQuerySet.as_manager()

    class Meta:
        unique_together = ('unit_action', 'from_unit_status',)
        verbose_name = 'Unit Status Transition'
        verbose_name_plural = verbose_name

    def __str__(self):
        return 'from %s action %s to %s' % (self.from_unit_status, self.unit_action, self.to_unit_status)

    @classmethod
    def get_allowed_actions(cls, unit_status: UnitStatus):
        unit_status_transitions = cls.objects.filter(
            from_unit_status=unit_status,
            active=True
        )
        return [unit_status_transition.unit_action for unit_status_transition in unit_status_transitions]


class UnitSlotQuerySet(models.QuerySet):

    def filter_active(self):
        return self.filter(active=True)

    def filter_specific_datetime(self, specific_datetime=None):
        if specific_datetime is None:
            specific_datetime = datetime.now()
        q_range = Q(start_datetime__lte=specific_datetime, end_datetime__gte=specific_datetime)
        q_end_none = Q(start_datetime__lte=specific_datetime, end_datetime=None)
        return self.filter_active().filter(q_range | q_end_none)

    def filter_unit(self, unit):
        return self.filter_active().filter(
            unit_type=ContentType.objects.get_for_model(unit),
            unit_id=unit.id
        )

    def create_initial_unit_slot(self, unit, specific_datetime, user):
        unit_slot = UnitSlot()
        unit_slot.unit = unit
        unit_slot.start_datetime = specific_datetime
        unit_slot.unit_status = UnitStatus.objects.get_initial_status()
        unit_slot.created_by = user
        unit_slot.save()
        return unit_slot


class UnitSlot(models.Model):
    unit_type = models.ForeignKey(ContentType, related_name='+')
    unit_id = models.PositiveIntegerField()
    unit = GenericForeignKey('unit_type', 'unit_id')
    owner_type = models.ForeignKey(ContentType, null=True, blank=True, related_name='+')
    owner_id = models.PositiveIntegerField(null=True, blank=True)
    owner = GenericForeignKey('owner_type', 'owner_id')
    allowed_actions = models.ManyToManyField(UnitAction, blank=True, verbose_name='Action ที่สามารถทำได้',
                                             help_text='derived from UnitStatusAllowedAction')
    start_datetime = models.DateTimeField(verbose_name='วันเวลาเริ่มต้น')
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name='วันเวลาสิ้นสุด')
    unit_status = models.ForeignKey(UnitStatus, verbose_name='สถานะของ Unit')
    change_status_action = models.ForeignKey(UnitAction, null=True, blank=True, related_name='+',
                                             verbose_name='UnitAction ที่ทำให้ Unit เปลี่ยนสถานะ')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, related_name='+')
    edited_at = models.DateTimeField(auto_now=True)
    edited_by = models.ForeignKey(User, null=True, blank=True, related_name='+')

    objects = UnitSlotQuerySet.as_manager()

    class Meta:
        verbose_name = 'Unit Slot'
        verbose_name_plural = verbose_name

    @classmethod
    def import_master_data_from_statable_model(cls, model_class: StatableModel):
        if not issubclass(model_class, StatableModel):
            raise Exception('model class is not StatableModel')

        initial_unit_status = UnitStatus.objects.get_initial_status()
        action_class = model_class.ACTION
        status_class = model_class.STATUS
        transition_list = model_class.TRANSITION
        model_type = ContentType.objects.get_for_model(model_class)
        print('======= Action')
        for action in action_class:
            unit_action, created = UnitAction.objects.get_or_create(
                model_type=model_type,
                action_class_name='ACTION',
                code=action.value,
                name=action.name
            )
            if created:
                print('create: %s' % (unit_action,))
            else:
                print('skip: %s' % (unit_action,))

        print('======= Status')
        for status in status_class:
            unit_status, created = UnitStatus.objects.get_or_create(
                model_type=model_type,
                status_class_name='STATUS',
                code=status.value,
                name=status.name
            )
            if created:
                print('create: %s' % (unit_status,))
            else:
                print('skip: %s' % (unit_status,))

        for transition in transition_list:
            unit_action = UnitAction.objects.get(
                model_type=model_type,
                action_class_name='ACTION',
                code=transition[1].value,
                name=transition[1].name
            )
            if transition[0] is not None:
                from_unit_status = UnitStatus.objects.get(
                    model_type=model_type,
                    status_class_name='STATUS',
                    code=transition[0].value,
                    name=transition[0].name
                )
            else:
                from_unit_status = initial_unit_status

            to_unit_status = UnitStatus.objects.get(
                model_type=model_type,
                status_class_name='STATUS',
                code=transition[2].value,
                name=transition[2].name
            )
            unit_status_transition, created = UnitStatusTransition.objects.get_or_create(
                unit_action=unit_action,
                from_unit_status=from_unit_status,
                to_unit_status=to_unit_status,
            )
            if created:
                print('create: %s' % (unit_status_transition,))
            else:
                print('skip: %s' % (unit_status_transition,))

    def __str__(self):
        return '[%s] %s (%s)' % (self.id, self.unit, self.unit_status.code)

    @classmethod
    def take_action(cls, unit, owner, unit_action: UnitAction, user: User,
                    specific_datetime=None, ignore_allowed_actions=False):
        if specific_datetime is None:
            specific_datetime = datetime.now()
        unit_slot = UnitSlot.objects.filter_unit(unit).filter_specific_datetime(
            specific_datetime=specific_datetime).last()
        if unit_slot is None:
            # create initial state of unit_slot
            unit_slot = UnitSlot.objects.create_initial_unit_slot(unit, specific_datetime, user)

        initial_status = UnitStatus.objects.get_initial_status()
        if not ignore_allowed_actions:
            if unit_slot.unit_status != initial_status:
                if unit_action not in unit_slot.allowed_actions.all():
                    raise Exception('action %s is not allowed for status %s' % (
                        unit_action, unit_slot.unit_status
                    ))

        unit_status_transition = UnitStatusTransition.objects.get_from_status_and_action(
            unit_slot.unit_status, unit_action
        )

        # ignore if this action doesn't need to create/update unit slot (e.g. view)
        if not unit_status_transition.create_unit_slot:
            return unit_slot

        next_status = unit_status_transition.to_unit_status
        # set existed unit_slot end_datetime
        unit_slot.end_datetime = specific_datetime
        unit_slot.change_status_action = unit_action
        unit_slot.edited_by = user
        unit_slot.save()

        # create new unit_slot
        new_unit_slot = UnitSlot()
        new_unit_slot.unit = unit
        new_unit_slot.owner = owner
        new_unit_slot.unit_status = next_status
        new_unit_slot.start_datetime = specific_datetime
        new_unit_slot.created_by = user
        new_unit_slot.save()
        for allowed_action in UnitStatusTransition.get_allowed_actions(next_status):
            new_unit_slot.allowed_actions.add(allowed_action)
        return new_unit_slot

    @classmethod
    def change_status(cls, unit, owner, unit_status: UnitStatus, user: User,
                      specific_datetime=None, use_same_owner=True):
        if specific_datetime is None:
            specific_datetime = datetime.now()
        unit_slot = UnitSlot.objects.filter_unit(unit).filter_specific_datetime(
            specific_datetime=specific_datetime).last()
        if unit_slot is None:
            # create initial state of unit_slot
            unit_slot = UnitSlot.objects.create_initial_unit_slot(unit, specific_datetime, user)

        # check unit status. if same status, ignore.
        if unit_slot.unit_status == unit_status:
            raise Exception('unit had already in status %s.' % (unit_status.name,))

        unit_slot.end_datetime = specific_datetime
        unit_slot.change_status_action = None  # because
        unit_slot.edited_by = user
        unit_slot.save()

        # create new unit_slot
        new_unit_slot = UnitSlot()
        new_unit_slot.unit = unit
        if use_same_owner:
            new_unit_slot.owner = unit_slot.owner
        else:
            new_unit_slot.owner = owner
        new_unit_slot.unit_status = unit_status
        new_unit_slot.start_datetime = specific_datetime
        new_unit_slot.created_by = user
        new_unit_slot.save()
        for allowed_action in UnitStatusTransition.get_allowed_actions(unit_status):
            new_unit_slot.allowed_actions.add(allowed_action)
        return new_unit_slot


class DoctorEducation(models.Model):
    doctor = models.ForeignKey(Doctor, related_name='educations')
    type = models.CharField(max_length=255, blank=True)
    type_en = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)
    name_en = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    country_en = models.CharField(max_length=255, blank=True)
    graduated_from = models.CharField(max_length=255, blank=True)
    graduated_from_en = models.CharField(max_length=255, blank=True)
    graduated_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True)
    flag_status = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.doctor)

    # class Meta:
    #     unique_together = ('type', 'name', 'country', 'graduated_from', 'graduated_date', 'doctor')


class DoctorBoard(models.Model):
    doctor = models.ForeignKey(Doctor, related_name='boards')
    type = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    subject_en = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    country_en = models.CharField(max_length=255, blank=True)
    university = models.CharField(max_length=255, blank=True)
    university_en = models.CharField(max_length=255, blank=True)
    institute = models.CharField(max_length=255, blank=True)
    institute_en = models.CharField(max_length=255, blank=True)
    recieve_date = models.DateField(blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    verify_status = models.CharField(max_length=255)
    flag_status = models.CharField(max_length=255)

    def __str__(self):
        return '%s - %s (%s)' % (self.subject, self.university, self.doctor)

    # class Meta:
    #     unique_together = ('doctor', 'type', 'subject', 'country', 'university', 'institute', 'recieve_date',
    #                        'expiration_date')


class DoctorCertification(models.Model):
    doctor = models.ForeignKey(Doctor, related_name='certifications')
    type = models.CharField(max_length=255, blank=True)
    type_en = models.CharField(max_length=255, blank=True)
    institute = models.CharField(max_length=255, blank=True)
    institute_en = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)
    name_en = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    expired_date = models.DateField(blank=True, null=True)
    verified_status = models.CharField(max_length=255, blank=True)
    training_flag = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.doctor)

    # class Meta:
    #     unique_together = ('doctor', 'type', 'institute', 'name', 'start_date', 'end_date')


barcode.register(PREFIX_BARCODE_HN, Patient, 'hn')
barcode.register(PREFIX_BARCODE_ENCOUNTER, Encounter, 'id', 'Encounter ID')
barcode.register(PREFIX_BARCODE_ENCOUNTER_OPD_NUMBER, EncounterNumberOPD, 'number', 'Encounter OPD')
barcode.register(PREFIX_BARCODE_ENCOUNTER_IPD_NUMBER, EncounterNumberIPD, 'number', 'Encounter IPD')
barcode.register(PREFIX_BARCODE_ENCOUNTER_SSS_NUMBER, EncounterNumberSSS, 'number', 'Encounter SSS')
barcode.register(PREFIX_BARCODE_DIVISION, Division, 'id')
