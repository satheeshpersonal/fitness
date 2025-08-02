from django.db import models

# Create your models here.
STATUS_CHOICES = [
        ('A', 'Active'),
        ('I', 'Inactive'),
    ]

# WORKOUT_TYPE_CHOICES = [
#         ('Cardio', 'Cardio'),
#         ('Chest', 'Chest'),
#         ('Triceps', 'Triceps'),
#         ('Back', 'Back'),
#         ('Biceps', 'Biceps'),
#         ('Legs', 'Legs'),
#         ('Shoulders', 'Shoulders')
#     ]

class WorkoutType(models.Model):

    name = models.CharField(max_length=500)
    details = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')

    def __str__(self):
        return self.name
    

class ExerciseName(models.Model):

    name = models.CharField(max_length=500)
    workout_type = models.ForeignKey(WorkoutType, on_delete=models.CASCADE, null=True, blank=True)
    details = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.name


class GymFeature(models.Model):

    name = models.CharField(max_length=500)
    icon = models.ImageField(upload_to='lookup/gym_feature/', null=True, blank=True, default='/default/feature_icon.png')
    details = models.CharField(max_length=500,  null=True, blank=True)
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')

    class Meta:
        ordering = ['position']
        
    def __str__(self):
        return self.name
