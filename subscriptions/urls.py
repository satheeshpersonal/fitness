from django.urls import path
from .views import SubscriptionView, PlanView, PlanTiersView, PlanScreenView, RazorpayWebhook, SubscriptionDetailsView, ValidateCoupon, RedeemFreeSessionView, VerifyPaymentView

urlpatterns = [
    path('/', SubscriptionView.as_view(), name='subscription-data'),       # GET, POST
    path('/plan-screen/', PlanScreenView.as_view(), name='plan-screen'),   # GET - tiers + their plans, one call
    path('/plan-list/', PlanView.as_view(), name='plan-data'),
    path('/plan-tiers/', PlanTiersView.as_view(), name='plan-tiers'),      # GET - tier tabs for the Plan page
    path('/validate-coupon/<coupon_code>/', ValidateCoupon.as_view(), name='validate-coupon'),
    path('/verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'), # Razorpay checkout success callback -> server-side signature check
    path('/razorpay-webhook/', RazorpayWebhook.as_view(), name='razorpay-webhook'), #Razorpay callback (backup / reconciliation)
    path('/redeem-free-session/', RedeemFreeSessionView.as_view(), name='free-session-subscription'), # One Free session for 2 successfull referrals - not using now
    path('/<order_id>/', SubscriptionDetailsView.as_view(), name='subscription-detail-data'),       # GET, PATCH
]