from django.core.exceptions import NON_FIELD_ERRORS
from django.db import models

from his.framework.models import EnumField, ValidationError
from his.framework.utils import LabeledIntEnum
from .utils import SelfReferenceCheckMixIn

__all__ = [
    'Location', 'Device', 'PrintServer',
    'ReportType', 'Printer', 'DevicePrinterMap'
]


class Location(SelfReferenceCheckMixIn, models.Model):
    """สถานที่ภายในโรงพยาบาล"""
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True)

    def __str__(self):
        return self.name


class Device(models.Model):
    computer_name = models.CharField(max_length=20, unique=True)
    ip_address = models.GenericIPAddressField(
        blank=True, null=True,
        help_text='ผู้ใช้ต้องล็อกอินจากเครื่องที่มี Computer Name และ IP Address ที่กำหนด'
                  '(สามารถว่างไว้เพื่อตรวจสอบเฉพาะ Computer Name ได้)')
    division = models.ForeignKey('core.Division')
    location = models.ForeignKey(Location, null=True, blank=True)
    zone = models.ForeignKey('core.Division', related_name='+', null=True, blank=True)

    def __str__(self):
        return self.computer_name

    def save(self, *args, **kwargs):
        # Computer name is not case sensitive so we normalized it here
        # ref: https://msdn.microsoft.com/en-us/library/windows/desktop/ms724220(v=vs.85).aspx
        self.computer_name = self.computer_name.upper()
        super(Device, self).save(*args, **kwargs)


class PrintServer(models.Model):
    class TYPE(LabeledIntEnum):
        JASPER = 1, 'Jasper'
        MSWORD = 2, 'MSWord'

    url = models.URLField(max_length=200, help_text='Example<br/> \
                                                     Jasper : http://192.168.56.150:9080/printserver/print<br/> \
                                                     MSWord : http://192.168.56.154/api/print')
    type = EnumField(TYPE, default=TYPE.JASPER)
    active = models.BooleanField(default=True)

    class Meta(object):
        verbose_name = "Print Server"

    def __str__(self):
        return "[%s] %s" % (self.type.label, self.url)


class ReportType(models.Model):
    name = models.CharField(max_length=200, help_text='Human readable name for administrator')
    page_size = models.CharField(max_length=50, blank=True, help_text='Page sizing of report')
    report_path = models.CharField(max_length=200, unique=True,
                                   help_text='e.g. REG\\rptRegisterForm or list of comma separated path')
    print_server = models.ForeignKey(PrintServer, null=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.page_size)


class PrinterManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Printer(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    objects = PrinterManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class DevicePrinterMap(models.Model):
    """map Device to print to specific Printer (if report is given, map to specific report)"""
    device = models.ForeignKey(Device, related_name='printers')
    printer = models.ForeignKey(Printer)
    report = models.ForeignKey(ReportType, null=True, blank=True, related_name='map_report_type')

    class Meta:
        unique_together = ('device', 'report')

    def validate_unique(self, exclude=None):
        super(DevicePrinterMap, self).validate_unique()

        if not self.id:
            # new item
            if self.report is None:
                if self.__class__.objects.filter(device=self.device, report=None).exists():
                    raise ValidationError(
                        {
                            NON_FIELD_ERRORS: [
                                'Default printer for this device already exists',
                            ],
                        }
                    )
