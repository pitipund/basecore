from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
from django.apps import apps, AppConfig
from django.conf import settings
from constance import config

if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')  # pragma: no cover

app = Celery('his')


class CeleryConfig(AppConfig):
    name = 'his.taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        app.config_from_object('django.conf:settings', namespace='CELERY')
        app.conf.timezone = settings.TIME_ZONE
        app.conf.ONCE = {
            'backend': 'celery_once.backends.Redis',
            'settings': {
                'url': settings.REDIS_LOCATION,
                'default_timeout': 60 * 60
            }
        }

        app.conf.beat_schedule = {
            'users_notify_inactivity_session': {
                'task': 'his.users.tasks.notify_inactivity_session',
                'schedule': crontab()  # execute every minute
            },
            'core_create_real_order_and_end_plan_item': {
                'task': 'his.core.tasks.create_real_order_and_end_plan_item',
                'schedule': crontab(minute=0, hour=0)
            }
        }

        if 'ADM' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['ADM_bill_room_items'] = {
                'task': 'his.apps.ADM.tasks.bill_room_items',
                'schedule': crontab(hour=23, minute=55)
            }

        if 'INF' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['inbound_interface_product'] = {
                'task': 'his.apps.INF.tasks.inbound_interface_product',
                'schedule': crontab(minute='*/5')
            }
            app.conf.beat_schedule['inbound_interface_stock'] = {
                'task': 'his.apps.INF.tasks.inbound_interface_stock',
                'schedule': crontab(minute='*/5')
            }
            app.conf.beat_schedule['inbound_interface_movement'] = {
                'task': 'his.apps.INF.tasks.inbound_interface_movement',
                'schedule': crontab(minute='*/5')
            }
            app.conf.beat_schedule['inbound_interface_hr'] = {
                'task': 'his.apps.INF.tasks.inbound_interface_hr',
                'schedule': crontab(minute='*/5')
            }
            app.conf.beat_schedule['outbound_interface_patient_record'] = {
                'task': 'his.apps.INF.tasks.outbound_interface_patient_record',
                'schedule': crontab(hour=1, minute=0)
            }
            app.conf.beat_schedule['outbound_interface_staging'] = {
                'task': 'his.apps.INF.tasks.outbound_interface_staging',
                'schedule': crontab(hour=1, minute=30)
            }
            app.conf.beat_schedule['outbound_interface_drug_dispensing'] = {
                'task': 'his.apps.INF.tasks.outbound_interface_drug_dispensing',
                'schedule': crontab(hour=0, minute=0)
            }
            app.conf.beat_schedule['outbound_interface_drug_transfer'] = {
                'task': 'his.apps.INF.tasks.outbound_interface_drug_transfer',
                'schedule': crontab(hour=23, minute=0)
            }
            app.conf.beat_schedule['outbound_interface_supply_dispensing'] = {
                'task': 'his.apps.INF.tasks.outbound_interface_supply_dispensing',
                'schedule': crontab(hour=0, minute=0)
            }
            app.conf.beat_schedule['generate_send_claim_data'] = {
                'task': 'his.apps.INF.tasks.generate_send_claim_data',
                'schedule': crontab(hour=0, minute=5)
            }

        if 'FLM' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['check_expired_queue_flow_transaction'] = {
                'task': 'his.apps.FLM.tasks.check_expired_queue_flow_transaction',
                'schedule': crontab(hour=0, minute=10)
            }

        if 'HRM' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['HRM_reject_broadcast_and_offer'] = {
                'task': 'his.apps.HRM.tasks.reject_broadcast_and_offer',
                'schedule': crontab(hour=0, minute=0)
            }

        if 'appointment' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['penta_create_provider_available_slot'] = {
                'task': 'his.penta.appointment.tasks.create_provider_available_slot',
                'schedule': crontab(day_of_month=25)
            }

        if 'REG' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['check_certified_death_document'] = {
                'task': 'his.apps.REG.tasks.check_certified_death_document',
                'schedule': crontab(minute='*/30')
            }

        if 'DPO' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['email_notifications'] = {
                'task': 'his.apps.DPO.tasks.email_notifications',
                'schedule': crontab(hour=config.core_EMAIL_NOTIFICATION_TIME, minute=0)
            }

        if 'LAB' in settings.DJANGO_INCLUDE_APPS:
            app.conf.beat_schedule['LAB_send_set_lab_order'] = {
                'task': 'his.apps.LAB.tasks.send_set_lab_order',
                'schedule': crontab()  # execute every minute
            }

        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)

        if hasattr(settings, 'RAVEN_CONFIG'):
            # Celery signal registration
            from raven import Client as RavenClient
            from raven.contrib.celery import register_signal as raven_register_signal
            from raven.contrib.celery import register_logger_signal as raven_register_logger_signal

            raven_client = RavenClient(dsn=settings.RAVEN_CONFIG['DSN'],
                                       release=settings.RAVEN_CONFIG.get('release'),
                                       site=settings.RAVEN_CONFIG.get('site'),
                                       ignore_exceptions=settings.RAVEN_CONFIG.get('ignore_exceptions'))
            raven_register_logger_signal(raven_client)
            raven_register_signal(raven_client)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # pragma: no cover
