from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from FitnessApp.utils.response import success_response, error_response
from django.utils import timezone
from datetime import timedelta, date, datetime
from .models import GymAccessLog, WorkoutSchedule, WorkoutExercise, SetGoal
from .serializers import GymAccessLogSerializer, SetGoalSerializer
from accounts.models import Gym
from .functions import create_workout, _send_access_notifications
from subscriptions.models import UserSubscription
from .serializers import WorkoutScheduleSerializer, WorkoutExerciseSerializer
import uuid
from django.db.models import Sum, Prefetch
from lookups.functions import send_template_email
from lookups.firebase_service import send_push_notification
import threading
import logging

logger = logging.getLogger(__name__)
# Create your views here.


class GymAccessView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        offset = request.query_params.get('offset', None)
        limit = request.query_params.get('limit', None)

        # Newest visit first — this is a chronological log, but the ordering
        # had been commented out, so rows came back in arbitrary DB order.
        # Only "gym" is joined: user_details is context-gated off for this
        # endpoint and the review field serializes as a bare id.
        gym_access = (
            GymAccessLog.objects
            .filter(user=request.user)
            .select_related("gym")
            .order_by("-access_date")
        )

        # DB-level pagination (LIMIT/OFFSET) — the app pages this in as the
        # user scrolls instead of pulling every visit at once.
        if offset is not None and limit is not None:
            offset = int(offset)
            limit = int(limit)
            gym_access = gym_access[offset:offset + limit]

        gym_accessa_data = GymAccessLogSerializer(gym_access, many=True).data
        # Always a success response, even when empty — a page past the end is
        # a valid "no more rows", not an error, so infinite scroll can stop.
        success_data = success_response(message="Success", code="success", data=gym_accessa_data)
        return Response(success_data, status=200)

        
    def post(self, request): #Register User

        request_data = request.data
        user_data = request.user

        if 'device_id' not in request_data:
            error_data =  error_response(message="Device information is missing", code="not_found", data={})
            return Response(error_data, status=200) 
        
        gym_access = GymAccessLog.objects.filter(user = user_data, access_date__date=timezone.now().date()).order_by("-access_date").first()
        if gym_access:
            if gym_access.access_date >= timezone.now()-timedelta(minutes=30): # cehck request lessthen 30mins
                if gym_access.device_id == request_data["device_id"] and gym_access.gym.gym_id  == uuid.UUID(request_data["gym_id"]):  # if user try with same gym with in 30 minutes and same device- we are showing seccess message
                    gym_accessa_data = GymAccessLogSerializer(gym_access).data
                    workout_schedule_id = create_workout(user_data, None, gym_accessa_data)
                    gym_accessa_data["workout_schedule_id"] = workout_schedule_id                      
                    success_data =  success_response(message="Successfully accessed", code="success", data=gym_accessa_data)
                    return Response(success_data, status=200) 
                else: # if user try with diffrent gym or same gym with diffent device with in 30 minutes or diffrent device 
                    error_data =  error_response(message="Your session for today has already been used at the same time from another gym or device. Please contact support for further assistance.", code="not_found", data={})
                    return Response(error_data, status=200)
            elif not request_data.get("second_session", False): #send confirmation popup message if same day second section 
                error_data =  error_response(message="You've already used today's session. Would you like to take one more?", code="confirmation", data=request_data)
                return Response(error_data, status=200)
        
        if not gym_access or request_data["second_session"]:
            # select_related("plan") avoids a second query the moment
            # sessions_left_value.plan.premim_type is accessed below
            sessions_left_value = UserSubscription.objects.select_related("plan").filter(
                user=user_data, expire_on__gte=timezone.now().date(), is_active=True
            ).first()
            if (sessions_left_value and sessions_left_value.sessions_left<=0) or not sessions_left_value: 
                error_data =  error_response(message="Please enroll in a plan to continue your workout", code="no_session", data={})
                return Response(error_data, status=200) 
            
            # select_related("owner") avoids a second query later when
            # gym_data.owner.fire_base_token / .email are accessed
            gym_data = Gym.objects.select_related("owner").filter(gym_id=request_data["gym_id"], status='A').first()
            if not gym_data:
                error_data =  error_response(message="Gym is not valid, Please try again sometime", code="not_found", data={})
                return Response(error_data, status=200)
            
            if (sessions_left_value.plan.premim_type == "B" and gym_data.premium_type in ["V", "E"]) or (sessions_left_value.plan.premim_type == "V" and gym_data.premium_type == "E"):
                error_data =  error_response(message="Your current plan doesn't include access to this gym. Please upgrade your plan to continue.", code="plan_upgrade_required", data={})
                return Response(error_data, status=200)

            request_data["gym"] = gym_data.id
            request_data["amount"] = gym_data.per_session_cost
            request_data["user"] = user_data.id
            
            serializer = GymAccessLogSerializer(data=request_data)
            if serializer.is_valid():
                gym_instance = serializer.save()
                # We already fetched this exact gym above (with select_related
                # owner) — assigning it here means the serializer's
                # to_representation doesn't re-query it from scratch.
                gym_instance.gym = gym_data
                gym_log_data = serializer.data

                try:
                    #if create or update WorkoutSchedule while acccess gym
                    workout_schedule_id = create_workout(user_data, None, gym_log_data)
                    gym_log_data["workout_schedule_id"] = workout_schedule_id
                except Exception as e:
                    logger.exception("create_workout error")
                
                # Email + push notification are external network calls — don't
                # make the person scanning the QR code wait on them. This was
                # very likely the main source of the 2+ second response time.
                threading.Thread(
                    target=_send_access_notifications,
                    args=(user_data, gym_data, gym_log_data),
                    daemon=True,
                ).start()

                success_data =  success_response(message="Successfully accessed", code="success", data=gym_log_data)
                return Response(success_data, status=200) 
            else:
                error_data =  error_response(message=serializer.errors, code="serializer", data={})
                return Response(error_data, status=200) 
        
        error_data =  error_response(message="No plans available, Please select valid plan", code="not_found", data={})
        return Response(error_data, status=200)


class GymSessionView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # print(request.data)
        page_type = self.request.query_params.get('page', None)
        gym_id = self.request.query_params.get('gym_id', None)
        extra_data = {}

        user_data = request.user
        # select_related here matters: GymAccessLogSerializer reads
        # instance.gym for every row, and with with_user=True it also reads
        # instance.user — without this that was two extra queries per row.
        if gym_id:
            gym_access = GymAccessLog.objects.select_related("gym", "user").filter(gym__owner = user_data, gym__gym_id = gym_id).order_by("-access_date")
        else:
            gym_access = GymAccessLog.objects.select_related("gym", "user").filter(gym__owner = user_data).order_by("-access_date")

        pending_payout = gym_access.exclude(settled_status='PR').aggregate(total=Sum('amount'))['total'] or "0.00"
        extra_data["pending_payout"] = pending_payout

        if page_type == "D":
            gym_access = gym_access[0:3]
        if gym_access:
            gym_accessa_data = GymAccessLogSerializer(gym_access, many=True, context={"with_user": True}).data
            success_data =  success_response(message="Success", code="success", data=gym_accessa_data, extra_data = extra_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No data found", code="not_found", data={})
            return Response(error_data, status=200) 


class GymAccessDetailsView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        # print(request.data)
        user_data = request.user
        # GymAccessLogSerializer.to_representation() reads instance.gym and
        # instance.user (nested UserDetailsSerializer) — without
        # select_related this ran 2 extra queries on top of the row fetch.
        gym_access = GymAccessLog.objects.select_related("gym", "user").filter(user = user_data, gym_access_id=id).first()
        if gym_access:
            gym_accessa_data = GymAccessLogSerializer(gym_access).data
            success_data =  success_response(message="Success", code="success", data=gym_accessa_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No data found", code="not_found", data={})
            return Response(error_data, status=200) 

class ScheduleListView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # print(request.data)
        session_type = request.query_params.get('type', 'u')  # u- upcoming , p- past 
        # user_data = request.user
        # if sessio_type == 'p': # Past session based on scheduled_at
        #     workout_schedule = WorkoutSchedule.objects.filter(user = user_data, scheduled_at__lt=date.today()).order_by("-scheduled_at")
        # else:
        #     workout_schedule = WorkoutSchedule.objects.filter(user = user_data, scheduled_at__gte=date.today()).order_by("-scheduled_at")
        filters = {
            "user": request.user
        }
        if session_type == "p":
            filters["scheduled_at__lt"] = date.today()
        else:
            filters["scheduled_at__gte"] = date.today()
        workout_schedule = (
            WorkoutSchedule.objects
            .filter(**filters)
            .select_related("gym")
            .prefetch_related(
                "workout_type",
                Prefetch(
                    "exercises",
                    queryset=WorkoutExercise.objects.filter(status="A")
                )
            )
            .order_by("-scheduled_at")
        )

        if workout_schedule:
            workout_schedule_data = WorkoutScheduleSerializer(workout_schedule, many=True).data
            success_data =  success_response(message="Success", code="success", data=workout_schedule_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No data found", code="not_found", data={})
            return Response(error_data, status=200)
        

class ScheduleView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
        
    def get(self, request, pk):
        # print(request.data)
        user_data = request.user
        workout_data = WorkoutSchedule.objects.filter(pk=pk, user=user_data).first()
        
        if workout_data:
            serializer = WorkoutScheduleSerializer(workout_data)
            workout_schedule_data = serializer.data
            
            #get all exercise
            exercise_data_all = WorkoutExercise.objects.filter(workout_schedule=workout_data.id, status = 'A').order_by("created_at")
            workout_schedule_data['exercise'] = WorkoutExerciseSerializer(exercise_data_all, many=True).data
            success_data =  success_response(message="Successfully updated", code="success", data=workout_schedule_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="WorkoutSchedule not found.", code="serializer", data={})
            return Response(error_data, status=200)

        
    def post(self, request): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user

        if 'scheduled_at' not in request_data:
            error_data =  error_response(message="Scheduled data is missing", code="missing_value", data={})
            return Response(error_data, status=200) 
        
        exercise_all = request_data.pop("exercise", [])
        request_data["user"] = user_data.id
        serializer = WorkoutScheduleSerializer(data = request_data)
        if serializer.is_valid():
            instance = serializer.save()
            workout_schedule_data = serializer.data

            # Validate every row first (no DB writes yet), then insert them
            # all in a single query. The previous version called .save() per
            # row inside the loop — one INSERT round trip per exercise, which
            # is what made saving a workout with several exercises slow.
            new_exercises = []
            for exercise in exercise_all:
                exercise["workout_schedule"] = instance.id
                exercise_serializer = WorkoutExerciseSerializer(data=exercise)
                if not exercise_serializer.is_valid():
                    error_data =  error_response(message=exercise_serializer.errors, code="serializer", data={})
                    return Response(error_data, status=200)
                new_exercises.append(WorkoutExercise(**exercise_serializer.validated_data))

            if new_exercises:
                WorkoutExercise.objects.bulk_create(new_exercises)

            exercise_data_all = WorkoutExercise.objects.filter(workout_schedule=instance.id, status = 'A').order_by("created_at")
            workout_schedule_data['exercise'] = WorkoutExerciseSerializer(exercise_data_all, many=True).data

            success_data =  success_response(message="Successfully scheduled workout", code="success", data=workout_schedule_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message=serializer.errors, code="serializer", data={})
            return Response(error_data, status=200)

    def patch(self, request, pk):
        user_data = request.user
        request_data = request.data
        exercise_all = request_data.pop("exercise", [])
        gym = request_data.pop("gym", None)
        workout_data = WorkoutSchedule.objects.filter(pk=pk, user=user_data).first()
        serializer = WorkoutScheduleSerializer(workout_data, data=request_data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            workout_schedule_data = serializer.data

            # One query to load every existing exercise row for this
            # schedule, instead of a SELECT per row just to check whether it
            # already exists — that per-row existence check (plus its own
            # write) was doubling the query count on every edit.
            existing_by_id = {
                e.id: e for e in WorkoutExercise.objects.filter(workout_schedule=instance.id)
            }
            delete_ids = []

            for exercise in exercise_all: # add or update exercise data
                ex_id = exercise.get('id', None)
                if ex_id:
                    exercise_data = existing_by_id.get(ex_id)
                    if not exercise_data:
                        continue  # not found / doesn't belong to this schedule

                    if exercise.get('delete', False):
                        delete_ids.append(ex_id)
                    else:
                        exercise_serializer = WorkoutExerciseSerializer(exercise_data, data=exercise, partial=True)
                        if exercise_serializer.is_valid():
                            exercise_serializer.save()
                else:
                    exercise["workout_schedule"] = instance.id
                    exercise_serializer = WorkoutExerciseSerializer(data=exercise)
                    if exercise_serializer.is_valid():
                        exercise_serializer.save()
                    else:
                        # print("serializer errors ----- ", exercise_serializer.errors)
                        error_data =  error_response(message=exercise_serializer.errors, code="serializer", data={})
                        return Response(error_data, status=200)

            if delete_ids:
                WorkoutExercise.objects.filter(id__in=delete_ids).delete()

            #get all exercise
            exercise_data_all = WorkoutExercise.objects.filter(workout_schedule=instance.id, status = 'A').order_by("created_at")
            workout_schedule_data['exercise'] = WorkoutExerciseSerializer(exercise_data_all, many=True).data
            success_data =  success_response(message="Successfully updated", code="success", data=workout_schedule_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message=serializer.errors, code="serializer", data={})
            return Response(error_data, status=200)

    def delete(self, request, pk):
        user_data = request.user
        workout = WorkoutSchedule.objects.filter(pk=pk, user=user_data).first()
        if workout:
            workout.delete()
            success_data =  success_response(message="Deleted successfully.", code="success", data={})
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="WorkoutSchedule not found.", code="serializer", data={})
            return Response(error_data, status=200)
              

class SetGoalView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
        
    def get(self, request):
        # print(request.data)
        user_data = request.user
        goal_data = SetGoal.objects.filter(user=user_data).first()
        
        if goal_data:
            serializer = SetGoalSerializer(goal_data)
            set_goal_data = serializer.data
            success_data =  success_response(message="Success", code="success", data=set_goal_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="Goal data not found.", code="serializer", data={})
            return Response(error_data, status=200)

        
    def post(self, request): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user
        request_data["user"] = user_data.id
        serializer = SetGoalSerializer(data = request_data)
        if serializer.is_valid():
            instance = serializer.save()
            goal_data = serializer.data
            success_data =  success_response(message="Success", code="success", data=goal_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message=serializer.errors, code="serializer", data={})
            return Response(error_data, status=200) 
        
    
    def patch(self, request, pk):
        user_data = request.user
        request_data = request.data
    
        goal_data = SetGoal.objects.filter(pk=pk, user=user_data).first()
        if goal_data:
            serializer = SetGoalSerializer(goal_data, data=request_data, partial=True)
            if serializer.is_valid():
                instance = serializer.save()
                set_goal_data = serializer.data
                success_data =  success_response(message="Success", code="success", data=set_goal_data)
                return Response(success_data, status=200)
            else:
                error_data =  error_response(message=serializer.errors, code="serializer", data={})
                return Response(error_data, status=200) 
        else:
            error_data =  error_response(message="Goal data not found.", code="serializer", data={})
            return Response(error_data, status=200)