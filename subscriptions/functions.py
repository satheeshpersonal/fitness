# your_app/functions.py

from django.utils import timezone
from datetime import timedelta
from django.db.models import Q


def update_user_session(user, plan, sessions_count, duration_in_days): # if status become success
    from .models import UserSubscription

    print("--- called update_user_session function ----")
    user_subscription, created = UserSubscription.objects.get_or_create(user = user, plan = plan, defaults = {"start_date":timezone.now(), "expire_on":timezone.now().date()+timedelta(days=duration_in_days), "sessions_left":sessions_count})
    print("date --", user_subscription)
    previous_plan = UserSubscription.objects.filter(~Q(pk=user_subscription.id), is_active = True, user = user).first()
    if not created:
        if user_subscription.expire_on >= timezone.now().date() and user_subscription.is_active == True: # if existing plan not expired - like renival
            user_subscription.sessions_left = user_subscription.sessions_left+sessions_count
        else:
            user_subscription.sessions_left = sessions_count
            user_subscription.is_active = True
        
        user_subscription.expire_on = timezone.now().date()+timedelta(days=duration_in_days)
        user_subscription.save(update_fields=["sessions_left", "is_active", "expire_on"])

    if previous_plan and  previous_plan.expire_on >= timezone.now().date():
        user_subscription.sessions_left = user_subscription.sessions_left+previous_plan.sessions_left # get previous plan session add to current plan 
        user_subscription.save(update_fields=["sessions_left"])
        previous_plan.is_active = False
        previous_plan.save(update_fields=["is_active"])


def get_subscription_data(user_data, plan_data, request_data):
    user_plan_data = {}
    if plan_data.plan_type == "D":
        user_plan_data["sessions_count"] = request_data.get("sessions_count", 2)
    else:
        user_plan_data["sessions_count"] = plan_data.session_count

    user_plan_data["per_session_price"] = plan_data.price
    user_plan_data["currency"] = plan_data.currency
    user_plan_data["duration_in_days"] = plan_data.duration_in_days
    user_plan_data["expire_on"] = timezone.now().date()+timedelta(days=plan_data.duration_in_days)
    user_plan_data["total_session_price"] = user_plan_data["sessions_count"]*plan_data.price
    user_plan_data["discount_amount"] = 0
    user_plan_data["tax"] = 0
    user_plan_data["total_paid"] = user_plan_data["total_session_price"]+user_plan_data["discount_amount"]+user_plan_data["tax"]

    return user_plan_data
        

def get_count_data(user_id):
    from .models import UserSubscription
    from workouts.models import WorkoutSchedule
    
    try:
        user_subscription = UserSubscription.objects.filter(user=user_id, is_active=True).values('expire_on', 'sessions_left').first()

        if user_subscription:
            user_subscription["access_left"] = user_subscription.pop("sessions_left")
        else:
            user_subscription = {}

        workout_count = WorkoutSchedule.objects.filter(user=user_id).count()
        user_subscription["session_count"] = workout_count
        # print(user_subscription)
        return user_subscription
    except Exception as e:
        print("get_subscription_session_count: ",e)
        return {}
    
