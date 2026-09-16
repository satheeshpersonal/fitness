from django.db import models
from cloudinary.models import CloudinaryField

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
    # icon = models.ImageField(upload_to='lookup/gym_feature/', null=True, blank=True, default='/default/feature_icon.png')
    icon = CloudinaryField('image', null=True, blank=True)
    details = models.CharField(max_length=500,  null=True, blank=True)
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Website form submissions (fitzz.in Contact + Partner pages). These are
# public, unauthenticated endpoints — every submission also emails the team.
# ---------------------------------------------------------------------------
class ContactMessage(models.Model):

    CATEGORY_CHOICES = [
        ('general', 'General Inquiry'),
        ('membership', 'Membership Support'),
        ('payment', 'Payment Issue'),
        ('partner', 'Partner With Us'),
        ('technical', 'Technical Support'),
    ]
    STATUS_CHOICES = [
        ('N', 'New'),
        ('P', 'In Progress'),
        ('R', 'Resolved'),
        ('S', 'Spam'),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    message = models.TextField()
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='N')
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.get_category_display()}"


class PartnerLead(models.Model):

    STATUS_CHOICES = [
        ('N', 'New'),
        ('C', 'Contacted'),
        ('Q', 'Qualified'),
        ('O', 'Onboarded'),
        ('X', 'Not a fit'),
    ]

    gym_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=120)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='N')
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.gym_name} — {self.city}"
