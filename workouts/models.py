from django.db import models
from accounts.models import CustomUser, Gym
from lookups.models import WorkoutType
import uuid
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .functions import update_user_session_log

# Create your models here.
STATUS_CHOICES = [
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('D', 'Deleted'),
    ]


class GymAccessLog(models.Model):
    gym_access_id = models.UUIDField(default=uuid.uuid4) #access refrence number
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=100, null=True, blank=True) #mobile uniqe id (for refrence)
    access_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    

    def __str__(self):
        return self.gym.name


@receiver(post_save, sender=GymAccessLog)
def update_user_session_signal(sender, instance, created, **kwargs):
    if created:
        update_user_session_log(instance.user) # reduce session left in user subcription



class WorkoutSchedule(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, null=True, blank=True)
    gym_access = models.ForeignKey(GymAccessLog, on_delete=models.CASCADE, null=True, blank=True)
    workout_type = models.ManyToManyField(WorkoutType, related_name='users', null=True, blank=True)
    body_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) 
    duration_minutes = models.IntegerField(null=True, blank=True)  # for total session
    burned_calories = models.IntegerField(null=True, blank=True)  # for full session
    heart_rate = models.IntegerField(null=True, blank=True)  # for full session - Maimum
    scheduled_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    reminder = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return f"{self.user.username}"
    

class WorkoutExercise(models.Model):
    workout_schedule = models.ForeignKey(WorkoutSchedule, on_delete=models.CASCADE)
    exercise_name = models.CharField(max_length=100, null=True, blank=True)
    reps = models.IntegerField(null=True, blank=True)
    sets = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # for strength training
    duration_minutes = models.IntegerField(null=True, blank=True)  # for cardio etc.
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.exercise_name
    
