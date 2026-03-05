
from django.urls import path
from .views import CustomUserView, verifyOTPView, SelectLocationView, GymView, GymListView, DashboardView, ReviewView, ReviewDetailtView, FavoritesGymView, HealthCheckView, ReferralView, ReferralCountView, FreeSessionRequestView, GymCreateView, OwnerGymListView, ExecutiveDashboardView, GymDashboardView, GymNameListView

urlpatterns = [
    path('/', CustomUserView.as_view(), name='user-data'),       # GET, POST & PATCH
    # path('/<int:pk>/', CustomUserView.as_view(), name='user-patch'),  # PATCH
    path('/verify-account/', verifyOTPView.as_view(), name='otp-validation-post'),  # POST
    path('/select-location/', SelectLocationView.as_view(), name='select-location'),  # GET, POST & PATCH #select location from top left corner
    path('/select-location/<id>/', SelectLocationView.as_view(), name='select-location-delete'), # DELETE

    path('/dashboard/', DashboardView.as_view(), name='user-dashboard-get'), # GET
    path('/executive-dashboard/', ExecutiveDashboardView.as_view(), name='executive-dashboard-get'), # GET
    path('/gym-dashboard/', GymDashboardView.as_view(), name='gym-dashboard-get'), # GET

    path('/creat-gym/', GymCreateView.as_view(), name='creat-gym'), # - create or update gym
    path('/gym/', GymListView.as_view(), name='gym-list'), # LIST - POST
    path('/owner-gym/', OwnerGymListView.as_view(), name='owner-gym-list'), # LIST - POST
    path('/gym/<gym_id>/', GymView.as_view(), name='gym-details'), # GET

    path('/review/', ReviewView.as_view(), name='gym-review-list'), #LIST, POST & PATCH
    path('/review-details/<id>/', ReviewDetailtView.as_view(), name='gym-review-details'), # GET

    path('/favorites/', FavoritesGymView.as_view(), name='favorites-gym'), # POST
    path('/health-check', HealthCheckView.as_view(), name='health-check'), # GET - check server hralth
    
    path('/referrals/', ReferralView.as_view(), name='referrals'), # GET
    path('/referral-count/', ReferralCountView.as_view(), name='referrals-coun'), # GET
    path('/free-session-request/', FreeSessionRequestView.as_view(), name='ree-session-request'), # GET

    path('/gym-name-list/', GymNameListView.as_view(), name='gym-list'), # LIST - POST -- for owner & executive pages
]