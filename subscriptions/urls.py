from django.urls import path
from .views import SubscriptionView, PlanView, RazorpayWebhook, SubscriptionDetailsView, ValidateCoupon, RedeemFreeSessionView

urlpatterns = [
    path('/', SubscriptionView.as_view(), name='subscription-data'),       # GET, POST
    path('/plan-list/', PlanView.as_view(), name='plan-data'),
    path('/validate-coupon/<coupon_code>/', ValidateCoupon.as_view(), name='validate-coupon'),
    path('/razorpay-webhook/', RazorpayWebhook.as_view(), name='razorpay-webhook'), #Razorpay callback
    path('/redeem-free-session/', RedeemFreeSessionView.as_view(), name='free-session-subscription'), # One Free session for 2 successfull referrals - not using now
    path('/<order_id>/', SubscriptionDetailsView.as_view(), name='subscription-detail-data'),       # GET, PATCH
]