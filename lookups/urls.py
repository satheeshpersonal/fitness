
from django.urls import path
from .views import (
    WorkoutTypeView,
    ExerciseNameView,
    GymFeatureView,
    AppVersionView,
    ContactMessageView,
    PartnerLeadView,
)

urlpatterns = [
    path('/workout-type/', WorkoutTypeView.as_view(), name='workout-type'),       # GET
    path('/exercise-name/', ExerciseNameView.as_view(), name='exercise-name'),       # GET
    path('/gym-features/', GymFeatureView.as_view(), name='gym-features'),       # GET
    path('/app-version/', AppVersionView.as_view(), name='app-version'),       # GET - min supported mobile app version
    path('/contact/', ContactMessageView.as_view(), name='contact-message'),       # POST - website contact form
    path('/partner-lead/', PartnerLeadView.as_view(), name='partner-lead'),       # POST - website partner form
]