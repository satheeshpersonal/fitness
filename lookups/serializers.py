from rest_framework import serializers
from .models import WorkoutType, ExerciseName, GymFeature
from FitnessApp.utils.media import thumbnail_url

class WorkoutTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutType
        # fields = '__all__'  # include all fields
        fields = ['id', 'name']
        # read_only_fields = ['subscription_id', 'order_id', 'created_at']  # only these are read-only
    
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data['plan'] = instance.plan.name
#         data['premim_type'] = instance.plan.get_premim_type_display()

#         return data

class ExerciseNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseName
        fields = ['id', 'name']

class GymFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymFeature
        fields = ['id', 'name', 'icon', 'details']

    icon = serializers.ImageField(use_url=True, required=False, allow_null=True)

    def to_representation(self, instance):
        # Feature icons only ever render as small pills/badges (biggest use is
        # a 20x20px icon on the gym-detail page) — every caller was getting
        # the full-resolution original from Cloudinary for that.
        data = super().to_representation(instance)
        if data.get('icon'):
            data['icon'] = thumbnail_url(data['icon'], width=80, height=80)
        return data