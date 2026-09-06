"""Bust the plan cache the instant an admin edits a plan or its bullets."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from FitnessApp.utils import appcache
from .models import SubscriptionPlan, PlanDetails


@receiver([post_save, post_delete], sender=SubscriptionPlan)
@receiver([post_save, post_delete], sender=PlanDetails)
def _invalidate_plan_cache(**kwargs):
    appcache.invalidate_plans()
