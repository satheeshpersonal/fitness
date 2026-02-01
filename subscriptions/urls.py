from django.urls import path
from .views import SubscriptionView, PlanView, RazorpayWebhook, SubscriptionDetailsView, ValidateCoupon

urlpatterns = [
    path('/', SubscriptionView.as_view(), name='subscription-data'),       # GET, POST
    path('/plan-list/', PlanView.as_view(), name='plan-data'),
    path('/validate-coupon/<coupon_code>/', ValidateCoupon.as_view(), name='validate-coupon'),
    path('/razorpay-webhook/', RazorpayWebhook.as_view(), name='razorpay-webhook'),
    path('/<order_id>/', SubscriptionDetailsView.as_view(), name='subscription-detail-data'),       # GET, PATCH
]