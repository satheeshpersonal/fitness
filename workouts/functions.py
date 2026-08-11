from django.utils import timezone
from lookups.functions import send_template_email
from datetime import datetime
from lookups.firebase_service import send_push_notification


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
    print(gym_access_data)
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
            workout_schedule = {"user":user.id, "gym_id":gym_access_data["gym"]["id"], "gym_access":gym_access_data["id"] }
            serializer = WorkoutScheduleSerializer(data = workout_schedule)
            if serializer.is_valid():
                workout_schedule_data = serializer.save()
                workout_schedule_data.gym_id = gym_access_data["gym"]["id"]
                workout_schedule_data.save(update_fields=["gym_id"])
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

def _send_access_notifications(user_data, gym_data, gym_log_data):
    """
    Fires the check-in email + push notification off the request/response
    cycle. Runs in a background thread — any failure here should never
    affect whether the user's check-in itself succeeded.
    """
    param = {}
    try:
        access_date = datetime.fromisoformat(gym_log_data["access_date"])
	#all email parameters
        param = {
            "gym_name": gym_log_data["gym"]["gym_name"],
            "session_date": access_date.strftime("%d %b %Y %I:%M %p"),
            "gym_address": f'{gym_log_data["gym"]["address"]}, {gym_log_data["gym"]["city"]}, {gym_log_data["gym"]["state"]}',
        }
        if user_data.email:
            emails = {"to_email": [user_data.email]} # to-email and cc-email will add as array
            send_template_email("access_session", emails, param)
    except Exception as e:
        print("The access-session user email error : ", e)
    
    # Send Notification to gym owner
    try:
        if gym_data.owner.fire_base_token:
            send_notification = send_push_notification(
                gym_data.owner.fire_base_token, user_data.first_name,
                "New Fitzz Check-In 💪", "member checked in successfully"
            )
            print("send_notification - ", send_notification)
    except Exception as e:
        print("push notification error : ", e)
    
    #Send email to gym owner
    try:
        if gym_data.owner.email:
            owner_emails = {"to_email": [gym_data.owner.email]}
            owner_param = {**param, "user_name": user_data.first_name}
            send_template_email("access_session_gym_owner", owner_emails, owner_param)
    except Exception as e:
        print("The access-session owner email error : ", e)