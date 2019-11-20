import json
from collections import OrderedDict

from cacheops.signals import cache_invalidated
from django.apps import AppConfig

from his.core.utils import get_his_apps
from django.conf import settings
from django.core.cache import cache
from constance import config


def clear_cache(sender, obj_dict, **kwargs):
    from his.core.models import CitizenWelfare
    # invalidate citizen welfare cache
    if sender in [CitizenWelfare, None]:
        keys = cache.keys(config.core_WELFARE_CATEGORY_CODE_CACHE_KEY + '*')
        cache.delete_many(keys)


class CoreConfig(AppConfig):
    name = 'his.core'

    # Module specific configuration
    # CONFIG_NAME: (default_value, description, type)
    # See supported type from: https://django-constance.readthedocs.io/en/latest/#custom-fields

    config = OrderedDict((
        ('FAVICON_URL', ('/static/images/owl.ico', 'url icon', str)),
        ('REVISIT_TIME', (24, 'เวลา Revisit (ชั่วโมง), ใส่ 0 ถ้าไม่ต้องการตรวจสอบ Revisit', int)),
        ('OPD_ENCOUNTER_EXPIRE', (24, '(ชั่วโมง) อายุสูงสุดของ Encounter OPD', int)),
        ('IPD_ENCOUNTER_EXPIRE', (24, '(ชั่วโมง) อายุสูงสุดของ Encounter IPD, ใส่ 0 จะไม่มีวันหมดอายุ', int)),
        ('DOCTOR_KEY_DISCHARGE_FORM_EXPIRE',
         (12, '(ชั่วโมง) ระยะเวลาที่แพทย์สามารถกรอก Discharge form ได้หลังผู้ป่วยกลับบ้าน', int)),
        ('NURSE_KEY_DISCHARGE_FORM_EXPIRE',
         (24, '(ชั่วโมง) ระยะเวลาที่พยาบาลสามารถกรอก Discharge form ได้หลังผู้ป่วยกลับบ้าน', int)),
        ('OUTSIDE_DOCTOR_CODE', ('ZZZZZZZZZZ', 'code ของแพทย์สำหรับใช้ทำ order ของแพทย์นอกโรงพยาบาล', str)),
        ('CHANGE_PRENAME_AGE', (15, '(ปี) อายุที่เปลี่ยนคำนำหน้าชื่อ', int)),
        ('UNK_CODE', ('UNK', 'Code ของสิทธิ์เงินสด', str)),
        ('GGO_CODE', ('GGO', 'Code ของสิทธิ์ข้าราชการ', str)),
        ('HOSPITAL_NAME', ('โรงพยาบาลรามาธิบดีจักรีนฤบดินทร์', 'ชื่อโรงพยาบาล', str)),
        ('HOSPITAL_NAME_EN', ('RAMADHIBODI CHAKRI NARUEBODINDRA HOSPITAL', 'ชื่อโรงพยาบาลภาษาอังกฤษ', str)),
        ('HOSPITAL_PHONE_NUMBER', ('02-xxx-xxxx', 'เบอร์โรงพยาบาล', str)),
        ('FACULTY_NAME', ('คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี มหาวิทยาลัยมหิดล', 'คณะ', str)),
        ('FACULTY_NAME_EN', ('FACULTY OF MEDICINE RAMADHIBODI HOSPITAL MAHIDOL UNIVERSITY', 'ชื่อคณะภาษาอังกฤษ', str)),
        ('HOSPITAL_ADDRESS', ('ที่อยู่โรงพยาบาล', 'ที่อยู่โรงพยาบาล', str)),
        ('HOSPITAL_FEE_REGULAR', ('N00106', 'Code ของค่าบริการผู้ป่วยนอกคลินิกปกติ', str)),
        ('HOSPITAL_FEE_SPECIAL', ('N00107', 'Code ของค่าบริการผู้ป่วยนอกคลินิกนอกเวลา', str)),
        ('HOSPITAL_FEE_PREMIUM', ('Z00133', 'Code ของค่าบริการผู้ป่วยนอกคลินิกพรีเมี่ยม', str)),
        ('PATIENT_CARD_CODE', ('Z00045', 'Code ของบัตรประจำตัวผู้ป่วย(พิมพ์ใหม่)', str)),
        ('RE_PATIENT_CARD_CODE', ('Z00045', 'Code ของบัตรประจำตัวผู้ป่วย(พิมพ์ซ้ำ)', str)),
        ('PRODUCT_FILTER_GROUP_MISCELLANEOUS', ('MISC', 'Code ของกลุ่มสินค้าและบริการประเภท miscellaneous', str)),
        ('ASSURE_TYPE_UNDEFINED', ('UNDEFINED', 'ไม่ระบุประเภทของสิทธิ', str)),
        ('DISCOUNT_SOCIAL_CODE',
         ('DIS_07,DIS_06,DIS_05,DIS_04,DIS_03', 'กลุ่ม Code ของสิทธิส่วนลดสังคมสงเคราะห์', str)),
        ('WELFARE_CATEGORY_CODE_EXPIRE', (86400, 'อายุของ cache สำหรับ welfare category code (วินาที)', int)),
        ('WELFARE_CATEGORY_CODE_CACHE_KEY', ('users_welfare', 'ชื่อ key สำหรับ cache welfare category code', str)),
        ('USER_TASK_KEY', ('user:%s:tasks', 'ชื่อ key เก็บ task ที่กำลังดำเนินการอยู่ของ user', str)),
        ('USER_TASK_INFO', ('task_id={task_id}, task_name={task_name}', 'format ของ task info', str)),
        ('USER_SUCCEEDED_TASK_KEY', ('user:%s:succeeded_tasks', 'ชื่อ key เก็บ task ของ user ที่สำเร็จ', str)),
        ('USER_FAILED_TASK_KEY', ('user:%s:failed_tasks', 'ชื่อ key เก็บ task ของ user ที่ไม่สำเร็จ', str)),
        ('ENABLE_EPISODE_OF_CARE', (False, 'เปิดใช้งาน Episode of care', bool)),
        ('MAIN_COVERAGE_CODES', (json.dumps(['GGO', 'OSSI', 'ISSI', 'ONHSI', 'INHSI']), 'รายการ Code สิทธิหลัก', str)),
        # ======= Test ==============
        ('TEST_HN', ('C834', 'HN ทดสอบ ที่ไม่ต้องส่ง interface', str)),
        # ======= ORDER PREFIX ==========
        ('PREFIX_DOCTOR_ORDER', ('001', 'prefix order id ของ DoctorOrder', str)),
        ('PREFIX_MISC_ORDER', ('002', 'prefix order id ของ MiscellaneousOrder', str)),
        ('PREFIX_DOCTOR_FEE_ORDER', ('003', 'prefix order id ของ DoctorFeeOrder', str)),
        ('PREFIX_ADMIT_ORDER_ROOM', ('004', 'prefix order id ของ AdmitOrderRoomBill', str)),
        ('PREFIX_ADMIT_ORDER_NURSE', ('005', 'prefix order id ของ AdmitOrderNurseBill', str)),
        ('REQUIRE_DIVISION_COSTCENTER', (False, 'required costcenter of division to create order', bool)),
        ('ICD10_VERSION', (1, 'Version ของ ICD10 ที่จะ active', int)),
        ('ICD9CM_VERSION', (1, 'Version ของ ICD9CM ที่จะ active', int)),
        ('BI_TOOL_URL', ('https://google.com', 'BI Tool url', str)),
        ('PENDING_TASK_EXPIRED', (24, 'เวลาที่แพทย์ต้อง approve ภายใน (hrs)', int)),
        ('EMAIL_NOTIFICATION_TIME', (20, 'เวลาส่ง email แจ้งเตือน ทุกวัน (hrs)', int)),
        ('CAN_VIEW_SECRET_DOCUMENT_CODE', ('CAN_VIEW_SECRET_DOCUMENT', 'สามารถดูเอกสารปกปิด', str)),
        ('SECRET_DEATH_DURATION', (2, 'เวลาปกปิดเอกสาร หลังผู้ป่วยตาย (hrs)', int)),
    ))

    def ready(self):
        """Populate settings.CONSTANCE_CONFIG with collected config from each apps"""
        final_config = OrderedDict()
        fieldsets = {}
        for app in get_his_apps():
            if hasattr(app, 'config'):
                config_keys = []
                for key, value in app.config.items():
                    full_key = '%s_%s' % (app.label, key)
                    final_config[full_key] = value
                    config_keys.append(full_key)
                fieldsets[app.label] = config_keys
        settings.CONSTANCE_CONFIG.update(final_config)
        settings.CONSTANCE_CONFIG_FIELDSETS.update(fieldsets)
        cache_invalidated.connect(clear_cache)
