from rest_framework import serializers
from .models import GymAccessLog, WorkoutSchedule, WorkoutExercise, SetGoal
from lookups.models import WorkoutType
from lookups.serializers import WorkoutTypeSerializer
from accounts.functions import gym_response, thumbnail_url, DEFAULT_GYM_ICON_URL
from accounts.serializers import UserDetailsSerializer

class GymAccessLogSerializer(serializers.ModelSerializer):
    # user_details is only needed by the gym-owner screens (who checked in).
    # The member-facing screens (their own gym logs, scan success, session
    # details) never read it, so it's built only when a caller opts in with
    # context={"with_user": True} — otherwise it was a nested serializer +
    # thumbnail build on every row for data nobody rendered.
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = GymAccessLog
        fields = '__all__'  # include all fields
        read_only_fields = ['gym_access_id', 'access_date']  # only these are read-only

    def get_user_details(self, obj):
        if not self.context.get("with_user"):
            return None
        return UserDetailsSerializer(obj.user).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['gym'] =  gym_response(instance.gym)
        if not self.context.get("with_user"):
            data.pop("user_details", None)
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
    # Was WorkoutTypeSerializer(many=True, read_only=True) — read_only meant
    # whatever "workout_type" the app sent was silently dropped by is_valid(),
    # so the muscles picked on the Schedule Workout screen never reached the
    # DB. PrimaryKeyRelatedField accepts a plain list of ids (what the app
    # sends) and DRF's ModelSerializer.create()/update() calls .set() on the
    # M2M automatically; to_representation() below still returns full
    # {id, name, ...} objects for reads.
    workout_type = serializers.PrimaryKeyRelatedField(
        many=True, queryset=WorkoutType.objects.all(), required=False
    )
    gym = serializers.SerializerMethodField()
    # A workout with no gym attached previously left the app with nothing to
    # put in the <img src>. gym_icon is always populated — the real gym's
    # icon (or the shared default if that gym has none), or the shared
    # default outright when there's no gym at all — so the frontend never
    # needs its own fallback/placeholder logic.
    gym_icon = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSchedule
        fields = '__all__'  # include all fields
        read_only_fields = ['created_at', 'updated_at']  # only these are read-only

    exercise = WorkoutExerciseSerializer(
        source="exercises",
        many=True,
        read_only=True
    )

    def get_gym(self, obj):
        if obj.gym:
            return gym_response(obj.gym)

        return None

    def get_gym_icon(self, obj):
        if obj.gym:
            return gym_response(obj.gym)['profile_icon']

        return thumbnail_url(DEFAULT_GYM_ICON_URL)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['workout_type'] = WorkoutTypeSerializer(instance.workout_type.all(), many=True).data

        return data
    

class SetGoalSerializer(serializers.ModelSerializer):

    class Meta:
        model = SetGoal
        fields = '__all__'  # include all fields
        read_only_fields = ['created_at']  # only these are read-only

