from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from FitnessApp.utils.response import success_response, error_response
from django.utils import timezone
from datetime import timedelta
from decouple import config
from .models import SubscriptionPlan, UserSubscriptionHistory, DicountCoupon, UserSubscription, PlanDetails, PREMIUM_TYPE_CHOICES
from .serializers import SubscriptionHistorySerializer, SubscriptionPlanSerializer
from .functions import (
    get_subscription_data,
    razorpay_creat_order,
    redeem_free_session,
    verify_payment_signature,
    mark_order_paid,
    send_subscription_email,
    get_fitpoints_balance,
)
import json
import razorpay
from .plan_screen import tier_copy
from lookups.functions import send_template_email
from FitnessApp.utils import appcache
from django.db.models import Prefetch
import logging

logger = logging.getLogger(__name__)
# from django.views.decorators.csrf import csrf_exempt
# Create your views here.



def _build_plans(premim_type=None):
    """Serialized active plans, optionally for one tier, ordered by position."""
    filters = {"status": "A"}
    if premim_type:
        filters["premim_type"] = premim_type
    qs = (
        SubscriptionPlan.objects
        .filter(**filters)
        .order_by("position")
        .prefetch_related(
            Prefetch("plan_details", queryset=PlanDetails.objects.filter(status="A"))
        )
    )
    return SubscriptionPlanSerializer(qs, many=True).data


def _build_tiers():
    """Tier tabs — one per premium_type that has at least one active plan."""
    tier_labels = dict(PREMIUM_TYPE_CHOICES)
    active_codes = set(
        SubscriptionPlan.objects.filter(status="A").values_list("premim_type", flat=True)
    )
    ordered_codes = [code for code, _ in PREMIUM_TYPE_CHOICES if code in active_codes]
    tiers = []
    for index, code in enumerate(ordered_codes):
        copy = tier_copy(code)
        tiers.append({
            "code": code,
            "label": tier_labels.get(code, code),
            "description": copy["description"],
            "show_gym_link": copy["show_gym_link"],
            "gym_link_label": copy["gym_link_label"],
            "gym_link_url": copy["gym_link_url"],
            "is_default": index == 0,
        })
    return tiers


class PlanView(APIView):
    """Active plans, optionally filtered by ?premim_type=. Read-through cached."""

    def get(self, request):
        premim_type = request.query_params.get("premim_type", None)
        key = appcache.PLAN_LIST_KEY.format(code=premim_type or "all")
        data = appcache.get_or_set(key, lambda: _build_plans(premim_type), appcache.PLAN_TTL)
        return Response(success_response(message="success", code="success", data=data), status=200)


class PlanTiersView(APIView):
    """Tier tabs for the ChoosePlan screen. Read-through cached."""

    def get(self, request):
        data = appcache.get_or_set(appcache.PLAN_TIERS_KEY, _build_tiers, appcache.PLAN_TTL)
        return Response(success_response(message="success", code="success", data=data), status=200)


class PlanScreenView(APIView):
    """
    One call for the whole ChoosePlan screen — tier tabs plus every tier's
    plans nested — so the app stops firing `plan-tiers` then `plan-list` and
    switching tabs needs no further request. Fully cached.
    """

    def get(self, request):
        def build():
            tiers = _build_tiers()
            plans_all = _build_plans()  # every active plan, one query
            by_tier = {}
            for p in plans_all:
                by_tier.setdefault(p.get("premim_type"), []).append(p)
            for t in tiers:
                t["plans"] = by_tier.get(t["code"], [])
            return {"tiers": tiers}

        data = appcache.get_or_set(appcache.PLAN_SCREEN_KEY, build, appcache.PLAN_TTL)
        return Response(success_response(message="success", code="success", data=data), status=200)


class ValidateCoupon(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, coupon_code):
        coupon_data = DicountCoupon.objects.filter(coupon_code=coupon_code).first()
        if coupon_data:
            # print(coupon_data.coupon_code)
            success_data =  success_response(message=f"success", code="success", data={"coupon_code": coupon_data.coupon_code, "percentage": coupon_data.percentage})
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="Invalid coupon code", code="not_found", data={})
            return Response(error_data, status=200) 
        

class SubscriptionView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        page_type = self.request.query_params.get('page', 'L') # L - List, P - Profile (can send only 2)
        # SubscriptionHistorySerializer.to_representation() reads
        # instance.plan 5 times per row — without select_related that's an
        # extra query per row (the Profile page's payment-history widget and
        # the full payment-history list both hit this).
        if page_type == 'P':
            # was payment_status__in='S' — a bare string happens to work
            # with __in (Python iterates its characters) only because 'S'
            # is a single character; written as a real list to not rely on
            # that.
            subscription_history = UserSubscriptionHistory.objects.select_related("plan").filter(user = request.user, payment_status__in = ['S']).order_by("-created_at")[0:2]
        else:
            subscription_history = UserSubscriptionHistory.objects.select_related("plan").filter(user = request.user, payment_status__in = ['S', 'F']).order_by("-created_at")
        subscription_history_data = SubscriptionHistorySerializer(subscription_history, many=True).data
        success_data =  success_response(message=f"success", code="success", data=subscription_history_data)
        return Response(success_data, status=200)
        
    def post(self, request): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user

        user_current_plan = UserSubscription.objects.select_related("plan").filter(user=user_data.id, is_active=True).order_by("-id").first()

        plan_data = SubscriptionPlan.objects.filter(id = request_data["plan"], status='A').first()
        if not plan_data:
            error_data =  error_response(message="No plans available, Please select valid plan", code="not_found", data={})
            return Response(error_data, status=200)
        
        if user_current_plan and user_current_plan.plan.premim_type != plan_data.premim_type:
            error_data =  error_response(message="You have active sessions under a different membership type. Please complete them before switching plans or contact support.", code="not_found", data={})
            return Response(error_data, status=200)
        # if plan_data.plan_type == "D":
        #     user_plan_data["sessions_count"] = request_data.get("sessions_count", 2)
        # else:
        #     user_plan_data["sessions_count"] = plan_data.session_count

        # user_plan_data = {}
        # user_plan_data["plan"] = plan_data
        # user_plan_data["per_session_price"] = plan_data.price
        # user_plan_data["currency"] = plan_data.currency
        # user_plan_data["duration_in_days"] = plan_data.duration_in_days
        # user_plan_data["expire_on"] = timezone.now().date()+timedelta(days=plan_data.duration_in_days)
        # user_plan_data["total_session_price"] = user_plan_data["sessions_count"]*plan_data.price
        # user_plan_data["discount_amount"] = 0
        # user_plan_data["tax"] = 0
        # user_plan_data["total_paid"] = user_plan_data["total_session_price"]+user_plan_data["discount_amount"]+user_plan_data["tax"]

        # user_plan_data["user"] = user_data

        user_plan_data = get_subscription_data(user_data, plan_data, request_data) # get plan data with price calculation
        
        user_plan_data["plan"] = plan_data.id
        user_plan_data["user"] = user_data.id
        
        # razorpay_order_id = razorpay_creat_order(user_plan_data)
        # user_plan_data["razorpay_order_id"] = razorpay_order_id
        serializer = SubscriptionHistorySerializer(data=user_plan_data)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            success_data =  success_response(message=f"Enrollment initiated successfully.", code="success", data=response_data)
            return Response(success_data, status=200) 

        error_data =  error_response(message=serializer.errors, code="error", data={})
        return Response(error_data, status=200)
    

class SubscriptionDetailsView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        subscription_history = UserSubscriptionHistory.objects.select_related("plan").filter(user = request.user, order_id=order_id).first()
        # Was serializing None into {} and still returning code="success", so
        # a bad/foreign order_id gave the app a "successful" empty payload it
        # then rendered as ₹undefined everywhere. Match patch()'s behaviour.
        if not subscription_history:
            error_data =  error_response(message="No orders available, Please select valid order", code="not_found", data={})
            return Response(error_data, status=200)
        subscription_history_data = SubscriptionHistorySerializer(subscription_history).data
        # FitPoints this order can still redeem (balance not counting the
        # points this same order is already holding).
        subscription_history_data["fitpoints_available"] = get_fitpoints_balance(
            request.user, exclude_order_id=subscription_history.id
        )
        success_data =  success_response(message=f"success", code="success", data=subscription_history_data)
        return Response(success_data, status=200)
        
    def patch(self, request, order_id): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user

        subscription_history = UserSubscriptionHistory.objects.filter(user = request.user, order_id=order_id).first()
        if not subscription_history:
            error_data =  error_response(message="No orders available, Please select valid order", code="not_found", data={})
            return Response(error_data, status=200) 

        plan_data = SubscriptionPlan.objects.filter(id = subscription_history.plan.id, status='A').first()
        if not plan_data:
            error_data =  error_response(message="No plans available, Please select valid plan", code="not_found", data={})
            return Response(error_data, status=200) 

        if request_data.get("coupon", None):
            coupon_data = DicountCoupon.objects.filter(coupon_code=request_data["coupon"]).first()
            if coupon_data:
                request_data["coupon"] = coupon_data.coupon_code
                request_data["coupon_discount_percent"] = coupon_data.percentage
        else:
            request_data["coupon"] = None

        # Don't count the points THIS order is currently holding against its
        # own balance while we recompute the redemption.
        request_data["_exclude_order_id"] = subscription_history.id

        user_plan_data = get_subscription_data(user_data, plan_data, request_data) # get plan data with price calculation

        user_plan_data["plan"] = plan_data.id
        user_plan_data["user"] = user_data.id
        user_plan_data["order_id"] = subscription_history.order_id  # used as the Razorpay receipt

        # An unreachable/slow Razorpay used to bubble up as an unhandled 500
        # (or, before the client timeout was added, hang) — the "Proceed to
        # Pay" tap just failed silently for the user. Return a clean error
        # they can retry instead.
        try:
            razorpay_order_id = razorpay_creat_order(user_plan_data)
        except Exception as e:
            logger.exception("razorpay_creat_order error")
            error_data =  error_response(message="Couldn't reach the payment gateway. Please try again.", code="gateway_error", data={})
            return Response(error_data, status=200)
        user_plan_data["razorpay_order_id"] = razorpay_order_id
        serializer = SubscriptionHistorySerializer(subscription_history, data=user_plan_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            response_data["razorpay_key"] = config('RAZORPAY_API_KEY')
            # The exact integer paise the Razorpay order was created with —
            # the client must pass this through verbatim rather than
            # recomputing `amount * 100` in JS (float drift => checkout
            # rejected).
            response_data["amount_paise"] = int(user_plan_data["total_paid"] * 100)
            response_data["fitpoints_available"] = get_fitpoints_balance(
                user_data, exclude_order_id=subscription_history.id
            )
            success_data =  success_response(message=f"Enrollment updated successfully.", code="success", data=response_data)
            return Response(success_data, status=200)

        error_data =  error_response(message=serializer.errors, code="error", data={})
        return Response(error_data, status=200)
    
    
class VerifyPaymentView(APIView):
    """
    Called by the app straight from the Razorpay Checkout success callback
    with razorpay_order_id / razorpay_payment_id / razorpay_signature. This
    is the primary confirmation path — the signature is checked server-side,
    the order is marked paid and the subscription activated before the
    success screen is shown. The webhook stays as a backup for the case
    where the app never gets to call this (network drop, app killed).
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        rzp_order_id = data.get("razorpay_order_id")
        rzp_payment_id = data.get("razorpay_payment_id")
        rzp_signature = data.get("razorpay_signature")

        if not (rzp_order_id and rzp_payment_id and rzp_signature):
            return Response(error_response(message="Missing payment details", code="error", data={}), status=200)

        order = UserSubscriptionHistory.objects.filter(
            razorpay_order_id=rzp_order_id, user=request.user
        ).first()
        if not order:
            return Response(error_response(message="Order not found", code="not_found", data={}), status=200)

        try:
            verify_payment_signature(rzp_order_id, rzp_payment_id, rzp_signature)
        except Exception as e:
            logger.exception("verify_payment_signature failed")
            # Don't mark the order failed here — a webhook may still confirm a
            # genuinely captured payment. Just refuse to activate on this
            # unverified callback.
            return Response(error_response(
                message="We couldn't verify this payment. If money was deducted it will be auto-refunded, or contact support.",
                code="verification_failed", data={},
            ), status=200)

        newly_paid = mark_order_paid(order, payment_id=rzp_payment_id, signature=rzp_signature)
        if newly_paid:
            send_subscription_email(order)

        order.refresh_from_db()
        return Response(success_response(
            message="Payment verified", code="success",
            data=SubscriptionHistorySerializer(order).data,
        ), status=200)


class RazorpayWebhook(APIView):
    """
    Backup / reconciliation path. Razorpay retries this on any non-2xx, so a
    signature failure returns 400 (surfaces in the Razorpay dashboard and
    gets retried) and a real event returns 200. Activation goes through the
    same idempotent mark_order_paid() as VerifyPaymentView, so the two can
    race without double-crediting sessions.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        signature = request.headers.get('X-Razorpay-Signature')
        body = request.body.decode('utf-8')

        try:
            client = razorpay.Client(auth=(config('RAZORPAY_API_KEY'), config('RAZORPAY_API_SECRET')))
            client.utility.verify_webhook_signature(body, signature, config('RAZORPAY_WEBHOOK_KEY'))
        except Exception as e:
            logger.exception("Razorpay webhook signature verification failed")
            return Response({"status": "invalid signature"}, status=400)

        try:
            event = json.loads(body)
        except Exception:
            return Response({"status": "bad payload"}, status=400)

        event_type = event.get("event")
        payment_entity = ((event.get("payload") or {}).get("payment") or {}).get("entity") or {}
        rzp_order_id = payment_entity.get("order_id")

        if event_type in ("payment.captured", "payment.failed") and rzp_order_id:
            order = UserSubscriptionHistory.objects.filter(razorpay_order_id=rzp_order_id).first()
            if order:
                if event_type == "payment.captured":
                    newly_paid = mark_order_paid(order, payment_id=payment_entity.get("id"))
                    if newly_paid:
                        order.refresh_from_db()
                        send_subscription_email(order)
                elif order.payment_status != 'S':  # payment.failed, and not already succeeded another way
                    order.payment_status = 'F'
                    order.razorpay_payment_id = payment_entity.get("id")
                    order.error_code = payment_entity.get("error_code")
                    order.error_description = payment_entity.get("error_description")
                    order.save(update_fields=["payment_status", "razorpay_payment_id", "error_code", "error_description"])

        return Response({"status": "ok"}, status=200)
        

class RedeemFreeSessionView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user
        redeem_data = redeem_free_session(user_data, request_data)

        if redeem_data["status"] == "success":
            success_data =  success_response(message=redeem_data["message"], code=redeem_data["code"], data={})
            return Response(success_data, status=200) 
        else:
            error_data =  error_response(message=redeem_data["message"], code=redeem_data["code"], data={})
            return Response(error_data, status=200) 
        

        # plan_data = SubscriptionPlan.objects.filter(plan_type = 'D', status='A').first()
        # if not plan_data:
        #     error_data =  error_response(message="No plans available, Please select valid plan", code="not_found", data={})
        #     return Response(error_data, status=200) 

        # user_plan_data = get_subscription_data(user_data, plan_data, request_data) # get plan data with price calculation
        # user_plan_data["per_session_price"] = 0
        # user_plan_data["tax"] = 0
        # user_plan_data["total_paid"] = 0
        # user_plan_data["plan"] = plan_data.id
        # user_plan_data["user"] = user_data.id
        # user_plan_data["payment_status"] = 'S'

        # # razorpay_order_id = razorpay_creat_order(user_plan_data)
        # # user_plan_data["razorpay_order_id"] = razorpay_order_id
        
        # serializer = SubscriptionHistorySerializer(data=user_plan_data)
        # if serializer.is_valid():
        #     serializer.save()
        #     response_data = serializer.data
        #     success_data =  success_response(message=f"Enrollment initiated successfully.", code="success", data=response_data)
        #     return Response(success_data, status=200) 

        # error_data =  error_response(message=serializer.errors, code="error", data={})
        # return Response(error_data, status=200)
