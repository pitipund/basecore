from his.framework.utils import LabeledIntEnum

from ckeditor_uploader.fields import RichTextUploadingField
from django.apps import apps
from django.db import models
from django.utils.safestring import mark_safe
from slugify import slugify

from his.framework.models import EnumField
from his.tools.utils import ui2doc


class Book(models.Model):
    name = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=250, null=True, blank=True)
    url = models.URLField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    consignment_date = models.DateField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class FunctionalArea(models.Model):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=300)
    book = models.ForeignKey(Book, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Phase(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class FlowCategory(models.Model):
    name = models.CharField(max_length=10)
    description = models.CharField(max_length=500, null=True, blank=True)
    due_date = models.DateField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class FlowMatrix(models.Model):
    code = models.CharField(max_length=5)
    description = models.CharField(max_length=500)
    usecases = models.ManyToManyField('Usecase')
    category = models.ForeignKey(FlowCategory, null=True)
    code_complete = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    demo_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ('code',)


class Usecase(models.Model):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=300)
    functional_area = models.ForeignKey(FunctionalArea)
    phase = models.ForeignKey(Phase, null=True, blank=True)
    design_completed = models.BooleanField(default=False, help_text='Completely design this model')
    code_completed = models.BooleanField(default=False, help_text='Finished coding this feature')
    assign_completed = models.BooleanField(default=False, help_text='Finished assigning task in Redmine.')
    description = RichTextUploadingField(blank=True, help_text='Usecase description')
    comment = models.TextField(blank=True)
    progress = models.IntegerField(default=0, editable=False)
    has_ui_test = models.BooleanField(default=False, editable=False)
    has_unit_test = models.BooleanField(default=False, editable=False)
    flowmatrixs = models.ManyToManyField(FlowMatrix, blank=True, through=FlowMatrix.usecases.through)
    page = models.IntegerField(default=0, editable=False, help_text='Page number in Book')
    sub_module = models.ForeignKey('SubModule', null=True, blank=True)

    def __str__(self):
        text = '%s: %s (%s)' % (self.functional_area.book, self.name, self.code)
        if self.phase:
            text += str(self.phase)
        return text

    def ref_url(self):
        return "%s#page=%d" % (self.functional_area.book.url, self.page)

    def rewritten_ref_url(self):
        return '/tools/view_usecase_desc/%d/' % (self.id) if bool(self.description) else None

    def ref(self):
        return mark_safe('<a href="%s">Link to spec</a>' % (self.ref_url()))

    def rewritten_ref(self):
        url = self.rewritten_ref_url()
        return url and mark_safe('<a href="%s">View</a>' % (url))

    def name_link_to_spec(self):
        if self.rewritten_ref_url():
            return mark_safe('<a href="%s">%s *</a>' % (self.rewritten_ref_url(), self.name))
        else:
            return mark_safe('<a href="%s">%s</a>' % (self.ref_url(), self.name))

    class Meta:
        ordering = ('code',)


class App(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Model(models.Model):
    app = models.ForeignKey(App)
    name = models.CharField(max_length=200)

    def __str__(self):
        return '%s.%s' % (self.app.code, self.name)

    def app_code(self):
        return self.app.code


class DesignGroup(models.Model):
    app = models.ForeignKey(App)
    name = models.CharField(max_length=200)
    usecases = models.ManyToManyField(Usecase, blank=True)
    include_related_models = models.BooleanField(default=True,
                                                 help_text='แสดง model ที่เกี่ยวข้องแต่ไม่ได้เลือกใน ER Diagram?')
    order = models.IntegerField(default=0)
    models = models.ManyToManyField(Model, blank=True)  # This field is bad, it shadow `models` variable

    def __str__(self):
        return self.name

    def get_models(self):
        return [apps.get_model(m.app_code(), m.name) for m in self.models.all()]

    def fullname(self):
        return self.name


class RedmineLink(models.Model):
    class STATUS(LabeledIntEnum):
        NEW = 1
        IN_PROGRESS = 2
        RESOLVED = 3
        FEEDBACK = 4
        CLOSED = 5
        REJECTED = 6
        PAUSED = 7
        READ = 8
        DEFER = 10

    issue_no = models.CharField(max_length=5)
    point = models.IntegerField(default=1)
    status = EnumField(STATUS, default=STATUS.NEW)
    usecases = models.ManyToManyField(Usecase)


class DocScreen(models.Model):
    doc_choice = (
        ('SCREEN', 'screen'),
        ('REPORT', 'report')
    )
    type = models.CharField(max_length=50, choices=doc_choice, help_text=u'ประเภทเอกสาร หน้าจอ/รายงาน',
                            default='SCREEN')
    name = models.CharField(max_length=200, help_text=u'ชื่อหน้าจอ')
    qml = models.CharField(max_length=200, blank=True, help_text=u'ชื่อไฟล์ qml เช่น HD/Queue.qml')
    manual_screenshot = models.BooleanField(default=False)
    screenshot = models.FileField(upload_to='screenshots', blank=True,
                                  help_text=u'เลือกไฟล์ screenshot กรณีต้องการ capture ภาพเอง')
    usecases = models.ManyToManyField('Usecase', blank=True, related_name='screens')
    table = models.TextField(default="", blank=True, help_text=u'ตาราง Field Property ที่ gen มาได้')
    alias = models.CharField(max_length=200, blank=True, unique=True)
    index = models.FloatField(default=0, verbose_name="Order")
    approved = models.BooleanField(default=False, verbose_name='user เซ็นยืนยันแบบฟอร์มแล้ว')

    def get_ui2doc(self):
        ui2doc(self)

    @classmethod
    def auto_alias(cls, qml):
        return slugify(qml.replace('.qml', '').replace('/', '-'))

    def save(self, *args, **kwargs):
        if self.alias == "":
            if self.qml:
                self.alias = DocScreen.auto_alias(self.qml)
            elif self.screenshot:
                pass
        if self.type == 'SCREEN' and self.table == "":
            self.get_ui2doc()
        super(DocScreen, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.alias

    def full_name(self):
        if self.qml:
            return self.qml
        return self.name


class AdditionalScreenshot(models.Model):
    screen = models.ForeignKey(DocScreen)
    screenshot = models.FileField(upload_to='screenshots', help_text=u'เลือกภาพเพิ่มเติม เพื่อใส่ต่อจากภาพหลัก')
    index = models.FloatField(default=0)

    class Meta:
        verbose_name = u'รูปหน้าจอเพิ่มเติม'
        verbose_name_plural = verbose_name
        ordering = ('index', 'id')


class SubModule(models.Model):
    name = models.CharField(max_length=100)
    alias = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.alias)
