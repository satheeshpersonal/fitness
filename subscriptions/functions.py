# your_app/functions.py

from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import razorpay
from decouple import config
import json
from decimal import Decimal


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
        print(request_data.get("sessions_count"))
        user_plan_data["sessions_count"] = request_data.get("sessions_count", plan_data.session_count)
        user_plan_data["total_session_price"] = user_plan_data["sessions_count"]*plan_data.price
    else:
        user_plan_data["sessions_count"] = plan_data.session_count
        user_plan_data["total_session_price"] = plan_data.price

    user_plan_data["per_session_price"] = plan_data.price
    user_plan_data["currency"] = plan_data.currency
    user_plan_data["duration_in_days"] = plan_data.duration_in_days
    user_plan_data["expire_on"] = timezone.now().date()+timedelta(days=plan_data.duration_in_days)
    user_plan_data["price_discount"] = plan_data.price_discount #if any default discount
    user_plan_data["discount_percent"] = 0.00
    user_plan_data["discount_amount"] = 0.00
    user_plan_data["coupon_discount_percent"] = 0.00
    user_plan_data["coupon_discount_amount"] = 0.00
    if plan_data.price_discount >0:
        user_plan_data["discount_amount"] = Decimal(user_plan_data["total_session_price"]*(plan_data.price_discount/100))
    if request_data.get("coupon_discount_percent", None):
        user_plan_data["coupon"] = request_data.get("coupon", None)
        user_plan_data["coupon_discount_percent"] = Decimal(request_data.get("coupon_discount_percent", 0.00))
        user_plan_data["coupon_discount_amount"] = round(Decimal((user_plan_data["total_session_price"] - Decimal(user_plan_data["discount_amount"]))*(Decimal(user_plan_data["coupon_discount_percent"])/100)), 2)
    user_plan_data["tax_percent"] = Decimal(config('GST_PERCENTAGE'))
    user_plan_data["tax"] = round((Decimal(user_plan_data["total_session_price"]) - Decimal(user_plan_data["discount_amount"])-Decimal(user_plan_data["coupon_discount_amount"]))*(Decimal((user_plan_data["tax_percent"]/100))), 2)
    user_plan_data["total_paid"] = round(Decimal(user_plan_data["total_session_price"])-Decimal(user_plan_data["discount_amount"])-Decimal(user_plan_data["coupon_discount_amount"])+Decimal(user_plan_data["tax"]), 2)

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

# create order in razer pay 
def razorpay_creat_order(order_data):
    client = razorpay.Client(auth=(config('RAZORPAY_API_KEY'), config('RAZORPAY_API_SECRET')))
    payment = client.order.create({
            "amount": int(order_data["total_paid"]* 100),
            "currency": order_data["currency"],
            "payment_capture": 0
        })
    
    print(payment)
    
    return payment["id"]

def verify_razorpay_event(request):
    # Get the payload and signature
    payload = request.body
    signature = request.headers.get('X-Razorpay-Signature')
    print(payload)

    client = razorpay.Client(auth=(config('RAZORPAY_API_KEY'), config('RAZORPAY_API_SECRET')))
    # Verify the webhook signature
    client.utility.verify_webhook_signature(payload.decode('utf-8'), signature, config('RAZORPAY_WEBHOOK_KEY'))
    
    # Parse the event
    # event = request.POST  # Or use json.loads(payload) if JSON
    event = json.loads(payload.decode('utf-8'))
    print("event -----> ", event)
    
    if 'event' in event:
        event_data = {}
        event_data["payment_id"] = event['payload']['payment']['entity']['id']
        event_data["order_id"] = event['payload']['payment']['entity']['order_id']
        event_data["error_code"] = event['payload']['payment']['entity']['error_code']
        event_data["error_description"] = event['payload']['payment']['entity']['error_description']
        event_data["event"] = event["event"]

        return event_data
        
    return None