from django.urls import path
from .views import GymAccessView, ScheduleView, ScheduleListView, GymAccessDetailsView

urlpatterns = [
    path('/access-gym/', GymAccessView.as_view(), name='access-gym'),       # GET, POST, PATCH
    path('/access-gym/<id>/', GymAccessDetailsView.as_view(), name='access-gym-details'), 
    path('/schedule/list/', ScheduleListView.as_view(), name='Schedule-workout'),       # GET(List)
    path('/schedule/<pk>/', ScheduleView.as_view(), name='Schedule-workout-update'),       # GET(Details), PATCH, DELETE
    path('/schedule/', ScheduleView.as_view(), name='Schedule-workout-create'), #POST
    # path('/workout-exercise/', WorkoutExerciseView.as_view(), name='workout-exericise'),       # GET, POST, PATCH
]