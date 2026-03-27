from django.urls import path
from .views import GymAccessView, ScheduleView, ScheduleListView, GymAccessDetailsView, GymSessionView, SetGoalView

urlpatterns = [
    path('/access-gym/', GymAccessView.as_view(), name='access-gym'),       # GET, POST, PATCH 
    path('/gym-session/', GymSessionView.as_view(), name='gym-session'),       # GET
    path('/access-gym/<id>/', GymAccessDetailsView.as_view(), name='access-gym-details'), 
    path('/schedule/list/', ScheduleListView.as_view(), name='schedule-workout'),       # GET(List)
    path('/schedule/<pk>/', ScheduleView.as_view(), name='schedule-workout-update'),       # GET(Details), PATCH, DELETE
    path('/schedule/', ScheduleView.as_view(), name='schedule-workout-create'), #POST
    path('/set-goal/', SetGoalView.as_view(), name='set-goal'), #POST
    path('/set-goal/<pk>/', SetGoalView.as_view(), name='update-set-goal'), #PATCH
    # path('/workout-exercise/', WorkoutExerciseView.as_view(), name='workout-exericise'),       # GET, POST, PATCH
]