from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils import timezone
from datetime import timedelta
from lookups.models import GymFeature

# Create your models here.
STATUS_CHOICES = [
        ('P', 'Pending'),
        ('A', 'Active'),
        ('I', 'Inactive'),
        ('D', 'Deleted'),
    ]

CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
    ]

PREMIUM_TYPE_CHOICES = [
        ('B', 'Basic'),
        ('V', 'VIP')
    ]

USER_TYPE_CHOICES = [
        ('U', 'User'),
        ('G', 'Gym')
    ]

LOGIN_TYPE_CHOICES = [
        ('M', 'Mobile Number'),
        ('E', 'Email')
    ]

NEW_TYPE_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No')
    ]

DAYS_CHOICES = [
        ('MF', 'Monday - Friday'),
        ('MS', 'Monday - Saturday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday')
    ]


class CustomUser(AbstractUser):
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=50, null=True, blank=True)
    ip_country = models.CharField(max_length=100, null=True, blank=True)
    ip_state = models.CharField(max_length=100, null=True, blank=True)
    ip_city = models.CharField(max_length=100, null=True, blank=True)
    profile_icon = models.ImageField(upload_to='gym_images/', null=True, blank=True, default='/default/profile.png')
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    new_to_gym = models.CharField(max_length=2, choices=NEW_TYPE_CHOICES, default='N')
    profile_completed = models.BooleanField(default=False)
    login_type = models.CharField(max_length=2, choices=LOGIN_TYPE_CHOICES, default='M')
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='P')
    user_type = models.CharField(max_length=2, choices=USER_TYPE_CHOICES, default='U')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class UserOTP(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=10)
    # otp_type = models.CharField(max_length=2, choices=LOGIN_TYPE_CHOICES, default='M')
    expire_on = models.DateTimeField(default=timezone.now() + timedelta(minutes=5))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.otp


class Gym(models.Model):
    gym_id = models.UUIDField(default=uuid.uuid4) #use for QR code
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='gyms')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_icon = models.ImageField(upload_to='gym_images/', null=True, blank=True, default='/default/gym_profile.png')
    per_session_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3,  choices=CURRENCY_CHOICES, default='INR')
    premium_type = models.CharField(max_length=2, choices=PREMIUM_TYPE_CHOICES, default='B')
    feature = models.ManyToManyField(GymFeature, null=True, blank=True) 
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')
    verified_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='verified_by')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class GymMedia(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    media = models.ImageField(upload_to='gym_images/', null=True, blank=True)
    position = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GymTiming(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=DAYS_CHOICES)
    morning_start = models.TimeField(null=True, blank=True)
    morning_end = models.TimeField(null=True, blank=True)
    evening_start = models.TimeField(null=True, blank=True)
    evening_end = models.TimeField(null=True, blank=True)
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')


    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"{self.get_day_display()} - {self.gym.name}"
    

class GymEquipment(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    icon = models.ImageField(upload_to='gym_images/equipment', null=True, blank=True, default='/default/gym_equipment.png')
    category = models.CharField(max_length=500, null=True, blank=True)
    description = models.TextField(null=True, blank=True)  # e.g., "20+ Latest Treadmills & Bikes"
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.category


class GymFavorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorite_gyms')
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='favorited_users')
    created_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     unique_together = ('user', 'gym')  # Prevent duplicates

    def __str__(self):
        return f"{self.user.username} - {self.gym.name}"   


class GymReview(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(null=True, blank=True)
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.user} - {self.gym.name} - {self.rating}"
    


class UserSelectLocation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=500, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=500, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')
    created_at = models.DateTimeField(auto_now_add=True)