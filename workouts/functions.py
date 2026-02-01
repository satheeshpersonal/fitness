from django.utils import timezone


def update_user_session_log(user):
    from subscriptions.models import UserSubscription

    print("--- called update_user_session_log function ----")
    user_current_plan = UserSubscription.objects.filter(user=user, expire_on__gte=timezone.now().date(), is_active=True).first()
    user_current_plan.sessions_left = user_current_plan.sessions_left-1
    user_current_plan.save(update_fields=["sessions_left"])


def create_workout(user, workout_data, gym_access_data):
    from .serializers import WorkoutScheduleSerializer
    from .models import WorkoutSchedule, WorkoutExercise
    print("--- called create_workout function ----")
    if workout_data:
        # WorkoutScheduleSerializer(workout_schedule_data, )
        pass
    elif gym_access_data:
        workout_schedule_data = WorkoutSchedule.objects.filter(user = user, gym_access_id = gym_access_data["id"]).order_by("scheduled_at").first()
        if not workout_schedule_data:
            workout_schedule_data = WorkoutSchedule.objects.filter(user = user, scheduled_at__date = timezone.now().date(), gym_access_id__isnull = True).order_by("scheduled_at").first()
        if workout_schedule_data:
            workout_schedule_data.gym_id = gym_access_data["gym"]["id"]
            workout_schedule_data.gym_access_id = gym_access_data["id"]
            workout_schedule_data.save(update_fields=["gym_id", "gym_access_id"])
            return workout_schedule_data.id
        else:
            workout_schedule = {"user":user.id, "gym":gym_access_data["gym"]["id"], "gym_access":gym_access_data["id"] }
            serializer = WorkoutScheduleSerializer(data = workout_schedule)
            if serializer.is_valid():
                workout_schedule_data = serializer.save()
                # print("workout_schedule_data -", workout_schedule_data.id)
                return workout_schedule_data.id
            else:
                print("Error in create_workout is", serializer.errors)
            
        
def get_last_activity(user_id):
    from .models import WorkoutSchedule
    from .serializers import WorkoutScheduleSerializer
    workout_schedule = WorkoutSchedule.objects.filter(user_id = user_id).order_by("-scheduled_at").first()
    if workout_schedule:
        workout_schedule_data = WorkoutScheduleSerializer(workout_schedule).data
        return workout_schedule_data
    else:
        return {}