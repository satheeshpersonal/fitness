
from django.urls import path
from .views import CustomUserView, verifyOTPView, SelectLocationView, GymView, GymListView, DashboardView, ReviewView, ReviewDetailtView, FavoritesGymView, HealthCheckView

urlpatterns = [
    path('/', CustomUserView.as_view(), name='user-data'),       # GET, POST & PATCH
    # path('/<int:pk>/', CustomUserView.as_view(), name='user-patch'),  # PATCH
    path('/verify-account/', verifyOTPView.as_view(), name='otp-validation-post'),  # POST
    path('/select-location/', SelectLocationView.as_view(), name='otp-validation-post'),  # GET, POST & PATCH #select location from top left corner
    path('/select-location/<id>/', SelectLocationView.as_view(), name='otp-validation-post'), # DELETE

    path('/dashboard/', DashboardView.as_view(), name='user-dashboard-get'), # GET

    path('/gym/', GymListView.as_view(), name='otp-validation-post'), # LIST - POST
    path('/gym/<gym_id>/', GymView.as_view(), name='otp-validation-post'), # GET

    path('/review/', ReviewView.as_view(), name='user-dashboard-get'), #LIST, POST & PATCH
    path('/review-details/<id>/', ReviewDetailtView.as_view(), name='user-dashboard-get'), # GET

    path('/favorites', FavoritesGymView.as_view(), name='favorites-gym'), # POST
    path('/health-check', HealthCheckView.as_view(), name='health-check'), # GET - check server hralth
]