from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from FitnessApp.utils.response import success_response, error_response
from django.utils import timezone
from datetime import timedelta, date
from .models import GymAccessLog, WorkoutSchedule, WorkoutExercise
from .serializers import GymAccessLogSerializer
from accounts.models import Gym
from .functions import create_workout
from subscriptions.models import UserSubscription
from .serializers import WorkoutScheduleSerializer, WorkoutExerciseSerializer
import uuid
# Create your views here.


class GymAccessView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # print(request.data)
        user_data = request.user
        gym_access = GymAccessLog.objects.filter(user = user_data).order_by("-access_date")
        if gym_access:
            gym_accessa_data = GymAccessLogSerializer(gym_access, many=True).data
            success_data =  success_response(message="Success", code="success", data=gym_accessa_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No data found", code="not_found", data={})
            return Response(error_data, status=200) 

        
    def post(self, request): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user

        if 'device_id' not in request_data:
            error_data =  error_response(message="Device infromation is missing", code="not_found", data={})
            return Response(error_data, status=200) 
        
        gym_access = GymAccessLog.objects.filter(user = user_data, access_date__date=timezone.now().date()).order_by("-access_date").first()
        if gym_access:
            if gym_access.access_date >= timezone.now()-timedelta(minutes=30): # cehck request lessthen 30mins
                # print(gym_access.gym.gym_id == uuid.UUID(request_data["gym_id"]))
                if gym_access.device_id == request_data["device_id"] and gym_access.gym.gym_id  == uuid.UUID(request_data["gym_id"]):  # if user try with same gym with in 30 minutes and same device- we are showing seccess message
                    gym_accessa_data = GymAccessLogSerializer(gym_access).data
                    success_data =  success_response(message="Successfully accessed", code="success", data=gym_accessa_data)
                    return Response(success_data, status=200) 
                else: # if user try with diffrent gym or same gym with diffent device with in 30 minutes or diffrent device 
                    error_data =  error_response(message="your today session already taken same time from other gym or device, Please contact support for more detials", code="not_found", data={})
                    return Response(error_data, status=200)
            elif not request_data["second_session"]: #send confirmation popup message if same day second section 
                error_data =  error_response(message="your today session already taken same time from other gym or device, Please contact support for more detials", code="confirmation", data=request_data)
                return Response(error_data, status=200)
        
        if not gym_access or request_data["second_session"]:
            print(user_data.id)
            sessions_left_value = UserSubscription.objects.filter(user=user_data, expire_on__gte=timezone.now().date(), is_active=True).first()
            if (sessions_left_value and sessions_left_value.sessions_left<=0) or not sessions_left_value: 
                # print(sessions_left_value["sessions_left"])
                error_data =  error_response(message="Please enroll class to continue your workout", code="not_found", data={})
                return Response(error_data, status=200) 
                
            print(sessions_left_value.sessions_left)
            gym_data = Gym.objects.filter(gym_id=request_data["gym_id"], status='A').first()
            if not gym_data:
                error_data =  error_response(message="Gym is not valid, Please try again sometime", code="not_found", data={})
                return Response(error_data, status=200)
            
            request_data["gym"] = gym_data.id
            request_data["user"] = user_data.id
            print("request_data - ", request_data)
            serializer = GymAccessLogSerializer(data=request_data)
            if serializer.is_valid():
                serializer.save()
                gym_log_data = serializer.data
                try:
                    #if create or update WorkoutSchedule while acccess gym
                    workout_schedule_id = create_workout(user_data, None, gym_log_data)
                    gym_log_data["workout_schedule_id"] = workout_schedule_id
                except Exception as e:
                    print("The create_workout error : ",e)

                success_data =  success_response(message="Successfully accessed", code="success", data=gym_log_data)
                return Response(success_data, status=200) 
            else:
                error_data =  error_response(message=serializer.errors, code="serializer", data={})
                return Response(error_data, status=200) 
        
        error_data =  error_response(message="No plans available, Please select valid plan", code="not_found", data={})
        return Response(error_data, status=200) 
    


class ScheduleView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # print(request.data)
        sessio_type = request.query_params.get('type', 'u')  # u- upcoming , p- past 
        user_data = request.user
        if sessio_type == 'p': # Past session based on scheduled_at
            workout_schedule = WorkoutSchedule.objects.filter(user = user_data, scheduled_at__lt=date.today()).order_by("-scheduled_at")
        else:
            workout_schedule = WorkoutSchedule.objects.filter(user = user_data, scheduled_at__gte=date.today()).order_by("-scheduled_at")
        if workout_schedule:
            workout_schedule_data = WorkoutScheduleSerializer(workout_schedule, many=True).data
            success_data =  success_response(message="Success", code="success", data=workout_schedule_data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message="No data found", code="not_found", data={})
            return Response(error_data, status=200) 

        
    def post(self, request): #Register User
        # print(request.data)
        request_data = request.data
        user_data = request.user

        if 'scheduled_at' not in request_data:
            error_data =  error_response(message="Scheduled data is missing", code="missing_value", data={})
            return Response(error_data, status=200) 
        
        request_data["user"] = user_data.id
        serializer = WorkoutScheduleSerializer(data = request_data)
        if serializer.is_valid():
            workout_schedule_data = serializer.save()
            success_data =  success_response(message="Successfully scheduled workout", code="success", data=serializer.data)
            return Response(success_data, status=200)
        else:
            error_data =  error_response(message=serializer.errors, code="serializer", data={})
            return Response(error_data, status=200) 

    def patch(self, request, pk):
        user_data = request.user
        request_data = request.data
        exercise_all = request_data.pop("exercise")
        workout_data = WorkoutSchedule.objects.filter(pk=pk, user=user_data).first()
        serializer = WorkoutScheduleSerializer(workout_data, data=request_data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            workout_schedule_data = serializer.data
            
            for exercise in exercise_all: # add or update exercise data
                ex_id = exercise.get('id', None)
                if ex_id:
                    exercise_data = WorkoutExercise.objects.filter(id=ex_id, workout_schedule=instance.id).first()

                    if exercise.get('delete', False):
                        exercise_data.delete()
                    else:
                        exercise_serializer = WorkoutExerciseSerializer(exercise_data, data=exercise, partial=True)
                        if exercise_serializer.is_valid():
                            exercise_serializer.save()
                else:
                    exercise["workout_schedule"] = instance.id
                    exercise_serializer = WorkoutExerciseSerializer(data=exercise)
                    if exercise_serializer.is_valid():
                        exercise_serializer.save()
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
              