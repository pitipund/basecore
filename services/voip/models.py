# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from future.builtins import *

import string
import random

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserVOIPRegister(models.Model):
    user = models.OneToOneField(User, models.CASCADE, 'username', related_name='voip_register')
    password = models.CharField(max_length=32, blank=True, default='')

    def generate_new_password(self):
        """generate new password, not save (save it yourself)"""
        self.password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

    def __str__(self):
        return '[%s VOIP register]' % self.user.username

    def __unicode__(self):
        return u'[%s VOIP register]' % self.user.username

    class Meta:
        verbose_name = 'User VOIP Register'
        verbose_name_plural = 'User VOIP Registers'


class VOIPServer(models.Model):
    ip = models.CharField(max_length=15)
    port = models.IntegerField()
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return '[VOIP server (%s): %s]' % (self.ip, self.description)

    def __unicode__(self):
        return u'[VOIP server (%s): %s]' % (self.ip, self.description)

    def get_address(self):
        return '%s:%d' % (self.ip, self.port)

    get_address.short_description = 'Address'

    class Meta:
        verbose_name = 'VOIP Server'
        verbose_name_plural = 'VOIP Servers'

