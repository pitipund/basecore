# -*- coding: utf-8 -*-
from django.core.mail import send_mass_mail, send_mail
from django.core.mail.message import BadHeaderError, EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import loader
from django.template.context import RequestContext
from django.utils import timezone
import os
import base64
from his.penta.curator.models import CuratorChannel, CuratorLink, CuratorPlaylist
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from his.penta.showtime.utils import gen_image_filename, UploadToDir

#User = get_user_model()
from his.penta.curator.models import User

class FacebookUser(models.Model):
    id = models.AutoField(primary_key=True)
    facebook_user_id = models.CharField(max_length=200, blank=True, null=True)
    latest_query_time = models.DateTimeField(blank=True, null=True)


class CuratorSuggestedLink(models.Model):
    channel = models.ForeignKey(CuratorChannel, related_name="suggested_links")
    link = models.ForeignKey(CuratorLink, null=True)
    url = models.URLField(null=False, blank=False)
    suggested_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="suggested_links")
    is_read = models.BooleanField(default=False)
    is_done = models.BooleanField(default=False)
    detail = models.CharField(max_length=2000, blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def _get_link(self):
        return CuratorLink.objects.get_video_link(self.url)

    def create_playlist(self):
        playlist = self.link.create_new_playlist(self.channel, detail=self.detail)
        self.is_done = True
        self.save()
        return playlist

    def save(self, *args, **kwargs):
        if self.link is None:
            self.link = self._get_link()
        super(CuratorSuggestedLink, self).save(*args, **kwargs)

    def read(self):
        self.is_read = True
        self.save()

    def done(self):
        self.is_done = True
        self.save()

    def __unicode__(self):
        return "%s by %s" % (self.channel.name, self.suggested_by.get_full_name())

    class Meta:
        ordering = ['-create_at']


class FeedEmailTemplate(models.Model):
    upload_dir = UploadToDir(settings.EMAIL_TEMPLATE_PATH)
    name = models.CharField(max_length=200)
    mini_preview = models.ImageField(upload_to=upload_dir)
    media_num = models.IntegerField(default=0)
    file = models.FileField(upload_to=upload_dir)

    def __unicode__(self):
        return "%s: %d media" % (self.name, self.media_num)


class FeedEmail(models.Model):
    class STATE:
        draft = 'D'
        ready = 'R'
        sent = 'S'
        old = 'O'
        deleted = 'X'

    STATE_CHOICE = ((STATE.draft, 'Draft'),
                    (STATE.ready, 'Ready'),
                    (STATE.sent, 'Sent'),
                    (STATE.old, 'Old'),
                    (STATE.deleted, 'Deleted'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    subject = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True)
    message = models.TextField(null=True, blank=True)
    channel = models.ForeignKey(CuratorChannel)
    playlist = models.ForeignKey(CuratorPlaylist, null=True)
    template = models.ForeignKey(FeedEmailTemplate, null=True)
    video_position = models.IntegerField(default=0)
    state = models.CharField(max_length=1, choices=STATE_CHOICE, default=STATE.draft)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True)

    def __unicode__(self):
        return "%s: %s" % (self.email, self.subject)

    def send(self, request):
        sender_email = self.email if self.email else self.user.email
        sender = "%s <%s>" % (self.channel.name, sender_email)
        recipient = User.objects.filter(following__curatorChannel=self.channel,
                                       following__subscribed=True).values_list('email', flat=True)
        if self.template:
            file_path = self.template.file.name
        else:
            file_path = FeedEmailTemplate.objects.first().file.name
        template = loader.get_template(file_path)

        images = []
        
        for image in self.images.all():
            currentImage = {'url': image.image.url, 'type': 'image'}
            images.append(currentImage)

        if self.playlist:
            videoImage = {'url': self.playlist.link.real_thumbnail, 'type': 'video'}
            if self.video_position == 0:
                images.insert(0, videoImage)
            elif self.video_position == 1:
                if len(images) == 0:
                    images.append(None)
                images.insert(1, videoImage)
        # print images

        request_context = RequestContext(request, {'c': self.channel, 'images': images, 'mail': self})
        html_message = template.render(request_context)
        unsubscribe_message = u'<br><p style="color:#888;text-align:center;font-size:12px">' \
                              u'คุณได้รับจดหมายฉบับนี้เพราะคุณได้ติดตามรับข่าวสารช่อง ' \
                              u'<a href="%s" style="text-decoration:none">%s</a> ผ่าน ' \
                              u'<a href="www.pentachennel.com/th/" style="text-decoration:none">PentaChannel</a><br>' \
                              u'คุณสามารถยกเลิกรับข่าวสารได้โดยคลิกที่นี่ ' \
                              u'<a href="%s" style="text-decoration:none">ยกเลิกการรับข่าวสาร</a></p>' %\
                              (request.build_absolute_uri(reverse('feed:feed_channel_view', args=(self.channel.id,))) +
                               u'?utm_source=newsletter&utm_medium=email&utm_content=' + str(self.id) +
                               u'&utm_campaign=email_follow',
                               self.channel.name,
                               request.build_absolute_uri(reverse('feed:feed_channel_view', args=(self.channel.id,)) +
                                                          u'?unsubscribe=true&utm_source=newsletter&utm_medium=email&'
                                                          u'utm_content=' + str(self.id) +
                                                          u'&utm_campaign=email_unsubscribe'))
        splited = html_message.split('</body>')
        html_message = ''.join([splited[0], unsubscribe_message, '</body>', splited[1]])
        # print html_message

        mail_subject = "[%s] %s" % (self.channel.name, self.subject)

        try:
            if not recipient:
                raise ValueError("No recipient")
            mail = EmailMultiAlternatives(mail_subject, self.message, sender, [])
            mail.bcc = list(recipient) + [sender]
            mail.attach_alternative(html_message, "text/html")
            ret = mail.send()
        except BadHeaderError as e:
            raise e
        if not ret:
            return False

        self.sent_at = timezone.now()
        self.state = self.STATE.sent
        self.save()
        return True


class FeedEmailImage(models.Model):
    upload_dir = UploadToDir(settings.EMAIL_PATH)

    email = models.ForeignKey(FeedEmail, related_name='images')
    image = models.ImageField(upload_to=upload_dir)
    position = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        try:
            old_image_in_same_position = FeedEmailImage.objects.get(email=self.email, position=self.position)
            old_image_in_same_position.delete()
        except FeedEmailImage.DoesNotExist:
            pass
        super(FeedEmailImage, self).save(*args, **kwargs)

    class Meta:
        ordering = ['id']
