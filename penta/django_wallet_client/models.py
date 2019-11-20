# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from future.builtins import *

from hashlib import sha1
from django.db import models
from six import string_types

User = get_user_model()


class BaseUserWallet(models.Model):

    user = models.OneToOneField(User, models.CASCADE)
    default_wallet_hash = models.CharField(max_length=40, null=True, blank=True,
                                           help_text='SHA-1 hash of default wallet')

    def get_default_wallet_from_list(self, wallet_id_list):
        """
        given list of wallet id, this function will return id of wallet that match
        :param wallet_id_list:
        :return: a wallet_id that match the hash
        """
        if isinstance(wallet_id_list, string_types):
            wallet_id_list = [wallet_id_list]

        for id in wallet_id_list:
            hash = sha1(id).hexdigest()
            if self.default_wallet_hash == hash:
                return wallet_id_list
        return None

    class Meta:
        abstract = True
