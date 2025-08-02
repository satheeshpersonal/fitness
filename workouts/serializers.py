from rest_framework import serializers
from .models import GymAccessLog, WorkoutSchedule, WorkoutExercise
from lookups.serializers import WorkoutTypeSerializer
from accounts.functions import gym_response

class GymAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymAccessLog
        fields = '__all__'  # include all fields
        read_only_fields = ['gym_access_id', 'access_date']  # only these are read-only
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['gym'] =  gym_response(instance.gym)
        # data['gym_name'] = instance.gym.name
        # data['address'] = instance.gym.address
        # data['city'] = instance.gym.city
        # data['state'] = instance.gym.state
        # data['country'] = instance.gym.country

        # data['profile_icon'] = None
        # if instance.gym.profile_icon:
        #     data['profile_icon'] = instance.gym.profile_icon


        return data
    

class WorkoutExerciseSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkoutExercise
        fields = '__all__'  # include all fields
        read_only_fields = ['created_at']  # only these are read-only

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     workout_types = instance.workout_type.all()
    #     data['workout_type'] =  WorkoutTypeSerializer(workout_types, many=True).data
    #     if instance.gym:
    #         data['gym'] =  gym_response(instance.gym)

    #     return data


class WorkoutScheduleSerializer(serializers.ModelSerializer):
    # workout_type = WorkoutTypeSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutSchedule
        fields = '__all__'  # include all fields
        read_only_fields = ['created_at', 'updated_at']  # only these are read-only

    def to_representation(self, instance):
        data = super().to_representation(instance)
        workout_types = instance.workout_type.all()
        data['workout_type'] =  WorkoutTypeSerializer(workout_types, many=True).data

        exercise_all = WorkoutExercise.objects.filter(workout_schedule=instance.id, status = 'A').order_by("created_at")
        data['exercise'] = WorkoutExerciseSerializer(exercise_all, many=True).data

        if instance.gym:
            data['gym'] =  gym_response(instance.gym)

        return data
    
