# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import six
import logging
import importlib

from django.conf import settings
from django.http.response import (HttpResponse, HttpResponseForbidden,
                                  HttpResponseNotFound)
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from his.penta.django_facebook_messenger.api import FacebookMessengerException
from his.penta.django_facebook_messenger.tasks import run_webhook_response

logger = logging.getLogger('django.request')


class FacebookMessengerWebhook(View):

    def post(self, request):
        if six.PY3:
            body = request.body.decode('utf-8')
        else:
            body = request.body
        logger.debug(body)
        data = json.loads(body)
        if data['object'] == 'page':
            for entry in data['entry']:
                if 'messaging' in entry:
                    webhook_event = entry['messaging'][0]
                    recipient_id = webhook_event['recipient']['id']

                    pages = settings.FACEBOOK_PAGE_ACCESS
                    page = next((p for p in pages if p["id"] == recipient_id), None)
                    if page is None:
                        logger.warning('Cannot find page with id %s in settings' % recipient_id)
                    else:
                        page_name = page['name']
                        handler_class = settings.FACEBOOK_MESSENGER_HOOK_CALLBACK.get(page_name)
                        if handler_class is None:
                            logger.warning('Cannot find hook callback names %s' % page_name)
                            continue

                        run_webhook_response.apply_async((page_name, handler_class, webhook_event))

            return HttpResponse('EVENT_RECEIVED')
        return HttpResponseNotFound()

    def get(self, request):
        """
        Handle Verification from Facebook
        """
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        # No challenge? May be, this is not from Facebook
        if challenge is None:
            return HttpResponseForbidden()
        if None not in [mode, token]:
            if mode == 'subscribe' and token == settings.FACEBOOK_HOOK_VERIFICATION:
                logger.info('WEBHOOK_VERIFIED')
                return HttpResponse(challenge)
        # 403 if verify token not match
        return HttpResponseForbidden()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(FacebookMessengerWebhook, self).dispatch(*args, **kwargs)
