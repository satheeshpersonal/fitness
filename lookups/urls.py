
from django.urls import path
from .views import WorkoutTypeView, ExerciseNameView

urlpatterns = [
    path('/workout-type/', WorkoutTypeView.as_view(), name='workout-type'),       # GET
    path('/exercise-name/', ExerciseNameView.as_view(), name='workout-type'),       # GET
    
]