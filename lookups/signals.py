"""Bust the lookup caches when an admin edits workout types / gym features."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from FitnessApp.utils import appcache
from .models import WorkoutType, GymFeature


@receiver([post_save, post_delete], sender=WorkoutType)
def _invalidate_workout_types(**kwargs):
    appcache.invalidate_workout_types()


@receiver([post_save, post_delete], sender=GymFeature)
def _invalidate_gym_features(**kwargs):
    appcache.invalidate_gym_features()
    # gym features also appear in plan bullets on the ChoosePlan screen
    appcache.invalidate_plans()
