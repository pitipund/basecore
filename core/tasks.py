from celery import shared_task
from his.core.models import PlanItem


@shared_task
def create_real_order_and_end_plan_item():
    PlanItem.objects.create_real_order_and_end_plan_item()
