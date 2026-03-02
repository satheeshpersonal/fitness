from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
import json
from FitnessApp.utils.response import success_response, error_response
from .models import WorkoutType, ExerciseName, GymFeature
from .serializers import WorkoutTypeSerializer, ExerciseNameSerializer, GymFeatureSerializer


# Create your views here.
class WorkoutTypeView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """

    def get(self, request):
        workout_type = WorkoutType.objects.filter(status = 'A').order_by("position")
        workout_type_data = WorkoutTypeSerializer(workout_type, many=True).data
        success_data =  success_response(message=f"success", code="success", data=workout_type_data)
        return Response(success_data, status=200)


class ExerciseNameView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """

    def get(self, request):
        workout_types = request.query_params.get('workout_types', None) 
        exercise_name_data = []
        if workout_types:
            workout_types_list = [int(wt.strip()) for wt in workout_types.split(',')]
            exercise_name = ExerciseName.objects.filter(workout_type__in=workout_types_list, status = 'A').order_by("workout_type__position","position")
            exercise_name_data = ExerciseNameSerializer(exercise_name, many=True).data
        success_data =  success_response(message=f"success", code="success", data=exercise_name_data)
        return Response(success_data, status=200)


class GymFeatureView(APIView):
    """
    Handles both POST (create) and PATCH (partial update) for CustomUser
    """

    def get(self, request):
        gym_feature_list = []
        
        gym_feature = GymFeature.objects.filter(status = 'A').order_by("position")
        if gym_feature:
            gym_feature_list = GymFeatureSerializer(gym_feature, many=True).data
        success_data =  success_response(message=f"success", code="success", data=gym_feature_list)
        return Response(success_data, status=200)
