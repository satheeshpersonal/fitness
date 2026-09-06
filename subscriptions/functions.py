# your_app/functions.py

from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import Q, Sum
import razorpay
from decouple import config
import json
import threading
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# --- FitPoints -------------------------------------------------------------
# Points a user earns from referrals and can redeem at checkout.
FITPOINTS_PER_RUPEE = 2                       # 2 FitPoints = ₹1
FITPOINTS_MAX_DISCOUNT_PERCENT = Decimal("5") # redeem at most 5% of the
                                             # pre-tax, post-discount amount


def get_fitpoints_earned(user):
    """Total FitPoints the user has ever earned (referral rewards)."""
    from accounts.models import Referral
    total = Referral.objects.filter(
        referrer=user, user_status="C"
    ).aggregate(t=Sum("reward_points"))["t"]
    return int(total or 0)


def get_fitpoints_committed(user, exclude_order_id=None):
    """
    FitPoints already locked into the user's orders — pending ('P') orders
    hold points so a second checkout can't spend the same points, and
    successful ('S') orders have consumed them. Failed orders release them.
    """
    from .models import UserSubscriptionHistory
    qs = UserSubscriptionHistory.objects.filter(
        user=user, payment_status__in=["P", "S"]
    )
    if exclude_order_id:
        qs = qs.exclude(id=exclude_order_id)
    total = qs.aggregate(t=Sum("fitpoints_redeemed"))["t"]
    return int(total or 0)


def get_fitpoints_balance(user, exclude_order_id=None, earned=None):
    """
    Spendable FitPoints = earned − committed (never negative). Pass `earned`
    when the caller has already aggregated the referral reward points, to
    save the repeat query.
    """
    if earned is None:
        earned = get_fitpoints_earned(user)
    return max(0, int(earned or 0) - get_fitpoints_committed(user, exclude_order_id))


def update_user_session(user, plan, sessions_count, duration_in_days): # if status become success
    from .models import UserSubscription

    user_subscription, created = UserSubscription.objects.get_or_create(user = user, plan = plan, defaults = {"start_date":timezone.now(), "expire_on":timezone.now().date()+timedelta(days=duration_in_days), "sessions_left":sessions_count})
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
        user_plan_data["sessions_count"] = request_data.get("sessions_count", plan_data.session_count)
        user_plan_data["total_session_price"] = user_plan_data["sessions_count"]*plan_data.price
        user_plan_data["expire_on"] = timezone.now().date()+timedelta(days=(user_plan_data["sessions_count"]*2)) #double the days based session count
        user_plan_data["duration_in_days"] = user_plan_data["sessions_count"]*2
    else:
        user_plan_data["sessions_count"] = plan_data.session_count
        user_plan_data["total_session_price"] = plan_data.price
        user_plan_data["expire_on"] = timezone.now().date()+timedelta(days=plan_data.duration_in_days)
        user_plan_data["duration_in_days"] = plan_data.duration_in_days

    user_plan_data["per_session_price"] = plan_data.price
    user_plan_data["currency"] = plan_data.currency
    # user_plan_data["duration_in_days"] = plan_data.duration_in_days
    # user_plan_data["expire_on"] = timezone.now().date()+timedelta(days=plan_data.duration_in_days)
    user_plan_data["price_discount"] = plan_data.price_discount #if any default discount
    user_plan_data["discount_percent"] = 0.00
    user_plan_data["discount_amount"] = 0.00
    user_plan_data["coupon_discount_percent"] = 0.00
    user_plan_data["coupon_discount_amount"] = 0.00
    if plan_data.price_discount > 0:
        user_plan_data["discount_percent"] = plan_data.price_discount
        user_plan_data["discount_amount"] = round(
            Decimal(user_plan_data["total_session_price"]) * (Decimal(plan_data.price_discount) / 100), 2
        )
    if request_data.get("coupon_discount_percent", None):
        user_plan_data["coupon"] = request_data.get("coupon", None)
        user_plan_data["coupon_discount_percent"] = Decimal(request_data.get("coupon_discount_percent", 0.00))
        user_plan_data["coupon_discount_amount"] = round(Decimal((user_plan_data["total_session_price"] - Decimal(user_plan_data["discount_amount"]))*(Decimal(user_plan_data["coupon_discount_percent"])/100)), 2)

    # --- FitPoints redemption (applied after plan + coupon, before tax) ---
    # Server is authoritative: the client asks to redeem, we decide how many
    # points actually apply given the live balance and the 5% cap.
    after_discounts = (
        Decimal(user_plan_data["total_session_price"])
        - Decimal(user_plan_data["discount_amount"])
        - Decimal(user_plan_data["coupon_discount_amount"])
    )
    user_plan_data["fitpoints_redeemed"] = 0
    user_plan_data["fitpoints_discount_amount"] = Decimal("0.00")
    if request_data.get("use_fitpoints"):
        balance = get_fitpoints_balance(user_data, exclude_order_id=request_data.get("_exclude_order_id"))
        cap_amount = (after_discounts * FITPOINTS_MAX_DISCOUNT_PERCENT / 100)
        max_points_by_cap = int(cap_amount * FITPOINTS_PER_RUPEE)  # floor to whole points
        redeemed = max(0, min(balance, max_points_by_cap))
        user_plan_data["fitpoints_redeemed"] = redeemed
        user_plan_data["fitpoints_discount_amount"] = (
            Decimal(redeemed) / FITPOINTS_PER_RUPEE
        ).quantize(Decimal("0.01"))

    taxable = after_discounts - Decimal(user_plan_data["fitpoints_discount_amount"])
    user_plan_data["tax_percent"] = Decimal(config('GST_PERCENTAGE'))
    user_plan_data["tax"] = round(taxable * (user_plan_data["tax_percent"] / 100), 2)
    user_plan_data["total_paid"] = round(taxable + Decimal(user_plan_data["tax"]), 2)

    return user_plan_data
        

def get_count_data(user_id):
    from .models import UserSubscription
    from workouts.models import WorkoutSchedule, GymAccessLog
    
    try:
        user_subscription = UserSubscription.objects.filter(user=user_id, is_active=True).values('expire_on', 'sessions_left', 'plan__premim_type').order_by("-id").first()

        if user_subscription:
            user_subscription["access_left"] = user_subscription.pop("sessions_left")
        else:
            user_subscription = {}

        # workout_count = WorkoutSchedule.objects.filter(user=user_id).count()
        # user_subscription["session_count"] = workout_count
        user_subscription["session_count"] = GymAccessLog.objects.filter(user=user_id).count()
        # print(user_subscription)
        return user_subscription
    except Exception as e:
        logger.exception("get_subscription_session_count error")
        return {}

# create order in razer pay
def razorpay_creat_order(order_data):
    client = razorpay.Client(auth=(config('RAZORPAY_API_KEY'), config('RAZORPAY_API_SECRET')))
    # razorpay-python forwards **kwargs straight down to requests.Session —
    # with no timeout, a stalled connection to Razorpay hangs this request
    # (and the checkout page waiting on it) indefinitely instead of failing
    # fast. This was very likely the actual cause behind "sometimes hangs
    # and reaches timeout" on the checkout flow.
    create_params = {
        "amount": int(order_data["total_paid"] * 100),
        "currency": order_data["currency"],
        "payment_capture": 1,
    }
    # Attach our own order id as the Razorpay receipt so the two can be
    # reconciled from the Razorpay dashboard.
    if order_data.get("order_id"):
        create_params["receipt"] = str(order_data["order_id"])

    payment = client.order.create(create_params, timeout=15)


    return payment["id"]


def _razorpay_client():
    return razorpay.Client(auth=(config('RAZORPAY_API_KEY'), config('RAZORPAY_API_SECRET')))


def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verifies the signature Razorpay Checkout returns in its success callback.
    Raises razorpay.errors.SignatureVerificationError on mismatch, returns
    True on success. This is the step that was missing entirely — the app
    used to trust the client callback without any server-side check.
    """
    return _razorpay_client().utility.verify_payment_signature({
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    })


def mark_order_paid(order, payment_id=None, signature=None):
    """
    Idempotently move a UserSubscriptionHistory order to 'S' and activate the
    subscription. Safe to call from BOTH the client-verify endpoint and the
    webhook — whichever gets there first wins, the other is a no-op.

    Returns True if this call performed the P -> S transition (so the caller
    knows to send the confirmation email once), False if it was already paid.
    """
    from .models import UserSubscriptionHistory

    with transaction.atomic():
        locked = (
            UserSubscriptionHistory.objects
            .select_for_update()
            .get(pk=order.pk)
        )
        if locked.payment_status == 'S':
            return False

        locked.payment_status = 'S'
        if payment_id:
            locked.razorpay_payment_id = payment_id
        if signature:
            locked.razorpay_signature = signature
        # Full save() (not update_fields) so the pre_save signal sees the
        # P -> S transition and runs update_user_session() exactly once,
        # inside this same locked transaction.
        locked.save()

    return True


def send_subscription_email(order):
    """
    Fire the 'subscription activated' email off the request/response cycle —
    the webhook (Razorpay times these out) and the verify endpoint (the user
    is waiting on the success screen) both call this.
    """
    try:
        payload = {
            "email": order.user.email,
            "plan_type": order.plan.get_plan_type_display(),
            "session_count": order.sessions_count,
            "amount": str(order.total_paid),
            "expiry_date": order.expire_on.strftime("%d %b %Y") if order.expire_on else "",
        }
    except Exception as e:
        logger.exception("subscription email prep error")
        return

    threading.Thread(target=_send_subscription_email_worker, args=(payload,), daemon=True).start()


def _send_subscription_email_worker(payload):
    from lookups.functions import send_template_email
    try:
        if not payload.get("email"):
            return
        send_template_email(
            "subscription_plan",
            {"to_email": [payload["email"]]},
            {
                "plan_type": payload["plan_type"],
                "session_count": payload["session_count"],
                "amount": payload["amount"],
                "expiry_date": payload["expiry_date"],
            },
        )
    except Exception as e:
        logger.exception("subscription email send error")


def verify_razorpay_event(request):
    # Get the payload and signature
    payload = request.body
    signature = request.headers.get('X-Razorpay-Signature')

    client = razorpay.Client(auth=(config('RAZORPAY_API_KEY'), config('RAZORPAY_API_SECRET')))
    # Verify the webhook signature
    client.utility.verify_webhook_signature(payload.decode('utf-8'), signature, config('RAZORPAY_WEBHOOK_KEY'))
    
    # Parse the event
    # event = request.POST  # Or use json.loads(payload) if JSON
    event = json.loads(payload.decode('utf-8'))
    
    if 'event' in event:
        event_data = {}
        event_data["payment_id"] = event['payload']['payment']['entity']['id']
        event_data["order_id"] = event['payload']['payment']['entity']['order_id']
        event_data["error_code"] = event['payload']['payment']['entity']['error_code']
        event_data["error_description"] = event['payload']['payment']['entity']['error_description']
        event_data["event"] = event["event"]

        return event_data
        
    return None

def redeem_free_session(user_data, request_data):
    from subscriptions.models import SubscriptionPlan
    from subscriptions.serializers import SubscriptionHistorySerializer
    from accounts.models import Referral, FreeSessionRequest

    try:
        referral_count = Referral.objects.filter(referrer = user_data, user_status='C').count()
        request_count = FreeSessionRequest.objects.filter(user=user_data, status='A').count()
        if request_count >0 or referral_count <2:
            return {"status":"error", "message":"Error in referral flow, Please contact admin", "code":"error"}
            
        plan_data = SubscriptionPlan.objects.filter(plan_type = 'D', status='A').first()
        if not plan_data:
            return {"status":"error", "message":"No plans available, Please select valid plan", "code":"not_found"}

        user_plan_data = get_subscription_data(user_data, plan_data, request_data) # get plan data with price calculation
        user_plan_data["per_session_price"] = 0
        user_plan_data["tax"] = 0
        user_plan_data["total_paid"] = 0
        user_plan_data["plan"] = plan_data.id
        user_plan_data["user"] = user_data.id
        user_plan_data["payment_status"] = 'S'

        # razorpay_order_id = razorpay_creat_order(user_plan_data)
        # user_plan_data["razorpay_order_id"] = razorpay_order_id
        
        serializer = SubscriptionHistorySerializer(data=user_plan_data)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return {"status":"success", "message":"success", "code":"success"}
    except Exception as e:
        logger.exception("redeem_free_session error")
        return {"status":"error", "message":"Something went wrong. Please try again.", "code":"error"}
