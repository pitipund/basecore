from celery import shared_task
from .backends import SessionManager


@shared_task
def notify_inactivity_session():
    manager = SessionManager()
    manager.notify_inactivity_session()
