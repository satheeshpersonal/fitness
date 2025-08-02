from django.db import models
from accounts.models import CustomUser
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import uuid
from .functions import update_user_session

# Create your models here.
STATUS_CHOICES = [
        ('A', 'Active'),
        ('I', 'Inactive'),
    ]

CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
    ]

PREMIUM_TYPE_CHOICES = [
        ('B', 'Basic'),
        ('V', 'VIP')
    ]

PAYMENT_STATUS_CHOICES = [
        ('P', 'Pending'),
        ('E', 'Error'),
        ('S', 'Success'),
    ]


class SubscriptionPlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('D', 'Session Based'),
        ('M', 'Monthly'),
        ('Y', 'Yearly'),
    ]
    
    name = models.CharField(max_length=50)
    details = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=2, choices=PLAN_TYPE_CHOICES, default='M')
    session_count = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    duration_in_days = models.IntegerField(null=True, blank=True)  # useful for weekly/monthly/yearly plans
    premim_type = models.CharField(max_length=2, choices=PREMIUM_TYPE_CHOICES, default='B')
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')

    def __str__(self):
        return f"{self.name} - {self.plan_type}"
    

class PlanDetails(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='plan_details')
    details = models.CharField(max_length=500)
    icon = models.ImageField(upload_to='plans/', null=True, blank=True)
    position = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='A')

    def __str__(self):
        return f"{self.details}"
    

class UserSubscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    expire_on = models.DateField()
    sessions_left = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    

class UserSubscriptionHistory(models.Model):
    subscription_id = models.UUIDField(default=uuid.uuid4) #use for QR code
    order_id = models.CharField(max_length=200, blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    per_session_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_session_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    sessions_count = models.IntegerField(null=True, blank=True)
    duration_in_days = models.IntegerField(null=True, blank=True) # useful for weekly/monthly/yearly plans - todal valied days
    expire_on= models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=2, choices=PAYMENT_STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)

    # def save(self, *args, **kwargs):
    #     if not self.order_id:
    #         date_str = timezone.now().strftime('%Y%m%d')
    #         self.order_id = f"{date_str}{self.id:06d}"
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    

@receiver(post_save, sender=UserSubscriptionHistory)
def update_oder_id(sender, instance, created, **kwargs):
    if created and not instance.order_id:
        date_str = timezone.now().strftime('%Y%m%d')
        instance.order_id = f"{date_str}{instance.id:06d}"
        instance.save(update_fields=["order_id"])


@receiver(pre_save, sender=UserSubscriptionHistory) #update user session left in user subscription
def update_oder_id(sender, instance, **kwargs):
    # if created and not instance.order_id:
    #     date_str = timezone.now().strftime('%Y%m%d')
    #     instance.order_id = f"{date_str}{instance.id:06d}"
    #     instance.save(update_fields=["order_id"])
    #     if instance.payment_status == 'S':
    #         update_user_session(instance.user, instance.plan, instance.sessions_count, instance.duration_in_days)
    # else:
        previous_status = sender.objects.filter(pk=instance.pk).first()
        # print(f"status -- {previous_status.payment_status}")
        if (not previous_status and instance.payment_status == 'S') or (previous_status and previous_status.payment_status != 'S' and instance.payment_status == 'S'):
            update_user_session(instance.user, instance.plan, instance.sessions_count, instance.duration_in_days)

