from django.urls import path
from .views import SubscriptionView, PlanView

urlpatterns = [
    path('/', SubscriptionView.as_view(), name='subscription-data'),       # GET, POST, PATCH
    path('/plan-list/', PlanView.as_view(), name='plan-data'),
    
]