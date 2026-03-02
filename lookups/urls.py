
from django.urls import path
from .views import WorkoutTypeView, ExerciseNameView, GymFeatureView

urlpatterns = [
    path('/workout-type/', WorkoutTypeView.as_view(), name='workout-type'),       # GET
    path('/exercise-name/', ExerciseNameView.as_view(), name='exercise-name'),       # GET
    path('/gym-features/', GymFeatureView.as_view(), name='gym-features'),       # GET
]