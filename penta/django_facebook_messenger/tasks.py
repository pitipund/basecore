from __future__ import absolute_import, unicode_literals

import logging
import importlib

from celery import shared_task

logger = logging.getLogger('django')


@shared_task
def run_webhook_response(page_name, webhook_class, webhook_event):
    try:
        module_name, class_name = webhook_class.rsplit('.', 1)
        module = importlib.import_module(module_name)
        webhook = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.exception(e.message)
        return
    webhook(page_name, webhook_event).response()
