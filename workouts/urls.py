from django.urls import path
from .views import GymAccessView, ScheduleView

urlpatterns = [
    path('/access-gym/', GymAccessView.as_view(), name='access-gym'),       # GET, POST, PATCH
    path('/schedule/', ScheduleView.as_view(), name='Schedule-workout'),       # GET, POST, PATCH
    path('/schedule/<pk>/', ScheduleView.as_view(), name='Schedule-workout-update'),       # PATCH, DELETE
    # path('/workout-exercise/', WorkoutExerciseView.as_view(), name='workout-exericise'),       # GET, POST, PATCH
]